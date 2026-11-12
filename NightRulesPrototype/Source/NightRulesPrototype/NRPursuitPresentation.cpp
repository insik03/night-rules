#include "NRGame.h"
#include "Animation/AnimSequence.h"
#include "Camera/CameraComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/AudioComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"
#include "AudioMixerBlueprintLibrary.h"
#include "Misc/App.h"
#include "Misc/Paths.h"
#include "TimerManager.h"
#include "HAL/PlatformMisc.h"

void ANRGameMode::SetupPursuitFoley()
{
    for(int32 I=0;I<5;++I) {
        for(bool IsGhost:{false,true}) {
            const FString Name=FString::Printf(TEXT("step_%s_%02d"),IsGhost?TEXT("ghost"):TEXT("player"),I);
            if(auto* S=LoadObject<USoundBase>(nullptr,*(TEXT("/Game/Audio/Footsteps/")+Name+TEXT(".")+Name)))
                (IsGhost?GhostFootsteps:PlayerFootsteps).Add(S);
        }
    }
    ChairRunClip=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/PrototypeAssets/GhostMeshy/A_CaretakerChairRun.A_CaretakerChairRun"));
    ChairKillClip=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/PrototypeAssets/GhostMeshy/A_CaretakerChairKill.A_CaretakerChairKill"));
    if(GhostVisual) for(auto* P:Props) if(P->Id==TEXT("chair") && P->Mesh->GetStaticMesh()) {
        PursuitChair=NewObject<UStaticMeshComponent>(Ghost,TEXT("PursuitChair"));
        PursuitChair->SetupAttachment(Ghost->GetRootComponent());PursuitChair->SetStaticMesh(P->Mesh->GetStaticMesh());
        for(int32 M=0;M<P->Mesh->GetNumMaterials();++M)PursuitChair->SetMaterial(M,P->Mesh->GetMaterial(M));
        PursuitChair->SetCollisionEnabled(ECollisionEnabled::NoCollision);PursuitChair->RegisterComponent();
        const FBox B=PursuitChair->GetStaticMesh()->GetBoundingBox();
        const float Scale=100.f/FMath::Max(B.GetSize().Z,1.f);PursuitChair->SetWorldScale3D(FVector(Scale));
        ChairGripLocal=FVector(B.GetCenter().X,B.Max.Y-3.f/Scale,B.Max.Z-5.f/Scale)*Scale;
        PursuitChair->SetVisibility(false);break;
    }
    if(auto* S=LoadObject<USoundBase>(nullptr,TEXT("/Game/Audio/chair_drag.chair_drag"))) {
        ChairDragAudio=NewObject<UAudioComponent>(Ghost,TEXT("ChairDragAudio"));
        ChairDragAudio->SetupAttachment(Ghost->GetRootComponent());ChairDragAudio->SetSound(S);
        ChairDragAudio->bAutoActivate=false;ChairDragAudio->bAutoDestroy=false;
        ChairDragAudio->AttenuationSettings=LocalAudioAttenuation;ChairDragAudio->RegisterComponent();
    }
}

void ANRGameMode::PlayFootstep(bool IsGhost,FVector At,float Strength)
{
    const auto& Clips=IsGhost?GhostFootsteps:PlayerFootsteps;if(Clips.IsEmpty())return;
    int32& Last=IsGhost?LastGhostFootstep:LastPlayerFootstep;
    const int32 Index=Last<0?FMath::RandRange(0,Clips.Num()-1):(Last+FMath::RandRange(1,FMath::Max(1,Clips.Num()-1)))%Clips.Num();
    Last=Index;
    UGameplayStatics::PlaySoundAtLocation(this,Clips[Index],At,FRotator::ZeroRotator,
        Strength*(IsGhost?1.05f:.85f),FMath::FRandRange(.96f,1.04f),0,LocalAudioAttenuation);
}

void ANRGameMode::TickPursuitChair(float D)
{
    const bool Visible=GhostVisual && !Ghost->IsHidden() && (Threat || ExecutionActive);
    if(PursuitChair) {
        PursuitChair->SetVisibility(Visible);
        if(Visible) {
            // The grip follows the animated hand, never an independent floating actor.
            float Tilt=-12;
            if(ExecutionActive) {
                const float Raise=FMath::SmoothStep(.55f,1.5f,ExecutionTime);
                const float Strike=FMath::SmoothStep(1.72f,1.94f,ExecutionTime);
                Tilt=FMath::Lerp(FMath::Lerp(-12.f,115.f,Raise),-55.f,Strike);
            }
            const FVector Hand=GhostVisual->GetBoneLocation(TEXT("RightHand"));
            // Drag with the seat trailing; turn its legs toward the victim when lifting.
            const float Turn=ExecutionActive?FMath::SmoothStep(.3f,.85f,ExecutionTime):0.f;
            FRotator Rotation(0,Ghost->GetActorRotation().Yaw-90+180*Turn,Tilt);
            if(!ExecutionActive || ExecutionTime<.55f) {
                // Pivot about the hand while a trailing pair of legs stays at floor height.
                const FBox Bounds=PursuitChair->GetStaticMesh()->GetBoundingBox();
                const FVector Scale=PursuitChair->GetComponentScale();
                const float Floor=Ghost->GetActorLocation().Z-90.f;
                float Best=MAX_flt;
                for(float Angle=-50;Angle<=50;Angle+=2) {
                    const FRotator Candidate(0,Rotation.Yaw,Angle);float Bottom=MAX_flt;
                    for(int32 Corner=0;Corner<8;++Corner) {
                        const FVector V((Corner&1)?Bounds.Max.X:Bounds.Min.X,(Corner&2)?Bounds.Max.Y:Bounds.Min.Y,(Corner&4)?Bounds.Max.Z:Bounds.Min.Z);
                        Bottom=FMath::Min(Bottom,(Hand+Candidate.RotateVector(V*Scale-ChairGripLocal)).Z);
                    }
                    const float Error=FMath::Abs(Bottom-Floor-1.f)+FMath::Abs(Angle+12.f)*.003f;
                    if(Error<Best){Best=Error;Rotation.Roll=Angle;}
                }
            }
            PursuitChair->SetWorldLocationAndRotation(Hand-Rotation.RotateVector(ChairGripLocal),Rotation);
        }
    }
    const bool Dragging=Visible && !Paused && (Page.IsEmpty() || CCTVView)
        && ((!ExecutionActive && GhostSpeed>30) || (ExecutionActive && ExecutionTime<.55f));
    if(ChairDragAudio) {
        if(Dragging) {
            ChairDragAudio->SetWorldLocation(PursuitChair?PursuitChair->Bounds.Origin:Ghost->GetActorLocation());
            ChairDragAudio->SetVolumeMultiplier(ExecutionActive?.42f:.27f);
            if(!ChairDragAudio->IsPlaying())ChairDragAudio->Play();
        } else if(ChairDragAudio->IsPlaying())ChairDragAudio->Stop();
    }
}

void ANRGameMode::TickExecution(float D)
{
    ExecutionTime+=D;
    const float Lower=FMath::SmoothStep(0.f,.55f,ExecutionTime);
    Player->Camera->SetRelativeLocation(ExecutionCameraHome+FVector(0,0,-52.f*Lower));
    const FVector Head=GhostVisual->GetBoneLocation(TEXT("Head"));
    FRotator Aim=(Head-Player->Camera->GetComponentLocation()).Rotation();
    Aim.Roll=FMath::Lerp(0.f,-8.f,Lower);
    Player->GetController()->SetControlRotation(FMath::RInterpTo(Player->GetControlRotation(),Aim,D,9));
    TickPursuitChair(D);
    if(!ExecutionHit && ExecutionTime>=1.94f) {
        ExecutionHit=true;
        if(auto* S=LoadObject<USoundBase>(nullptr,TEXT("/Game/Audio/Footsteps/chair_strike.chair_strike")))UGameplayStatics::PlaySound2D(this,S,.9f);
        Player->GetController<APlayerController>()->PlayerCameraManager->SetManualCameraFade(1,FLinearColor::Black,false);
        Record(TEXT("death_impact"),TEXT("chair_strike"));
        UE_LOG(LogTemp,Display,TEXT("NR_EXECUTION_HIT world_time=%.4f"),GetWorld()->GetTimeSeconds());
    }
    if(ExecutionTime>=2.8f) {
        ExecutionActive=false;Page=TEXT("붙잡혔다.\n\n의자 끄는 소리가 멎었다.");
        if(PursuitChair)PursuitChair->SetVisibility(false);
        UpdatePointerInput(true);
    }
}

void ANRGameMode::ResetExecution()
{
    if(ExecutionTime>0 && Player)Player->Camera->SetRelativeLocation(ExecutionCameraHome);
    ExecutionActive=false;ExecutionHit=false;ExecutionTime=0;
    if(ChairDragAudio)ChairDragAudio->Stop();
    if(PursuitChair)PursuitChair->SetVisibility(false);
    if(GhostVisual)GhostVisual->bPauseAnims=false;
}

void ANRGameMode::PursuitPresentationTest()
{
    auto Errors=MakeShared<int32>(0);
    auto Check=[Errors](bool OK,const TCHAR* Label){if(!OK)++*Errors;UE_LOG(LogTemp,Display,TEXT("NR_PURSUIT %s %s"),OK?TEXT("PASS"):TEXT("FAIL"),Label);};
    Check(PlayerFootsteps.Num()==5 && GhostFootsteps.Num()==5,TEXT("ten cooked footstep variants loaded"));
    Check(ChairRunClip && ChairKillClip && PursuitChair,TEXT("chair animations and existing chair mesh loaded"));
    Check(GhostVisual && GhostVisual->GetBoneIndex(TEXT("RightHand"))!=INDEX_NONE,TEXT("animated hand grip exists"));
    FirstCall=99999;IntroComplete=true;Page.Empty();StopVoice();SubtitleLines.Reset();Notice.Empty();
    Player->SetActorLocation(FVector(900,-135,410));Player->GetController()->SetControlRotation(FRotator(0,0,0));SaveCheckpoint();
    FApp::SetUnfocusedVolumeMultiplier(1);ApplyVolume(1);UAudioMixerBlueprintLibrary::StartRecordingOutput(this,8);
    for(int I=0;I<8;++I) {
        FTimerHandle H;GetWorld()->GetTimerManager().SetTimer(H,[this,I,Check]{
            const int Previous=I<4?LastPlayerFootstep:LastGhostFootstep;
            PlayFootstep(I>=4,Player->GetActorLocation(),.9f);
            Check(Previous!=(I<4?LastPlayerFootstep:LastGhostFootstep),TEXT("successive footfalls use different samples"));
        },.1f+I*.28f,false);
    }
    FTimerHandle Catch,Impact,Restore,End;
    GetWorld()->GetTimerManager().SetTimer(Catch,[this,Check]{StartThreat();Ghost->SetActorLocation(Player->GetActorLocation()+FVector(90,0,0));Ghost->SetActorRotation(FRotator(0,180,0));Die();Check(Dead && ExecutionActive && Page.IsEmpty(),TEXT("catch locks gameplay before showing retry page"));},2.6f,false);
    GetWorld()->GetTimerManager().SetTimer(Impact,[this,Check]{Check(ExecutionHit && !ExecutionActive && !Page.IsEmpty(),TEXT("strike then black retry screen completed"));},5.7f,false);
    GetWorld()->GetTimerManager().SetTimer(Restore,[this,Check]{RestoreCheckpoint();Check(!Dead && !ExecutionActive && Player->Camera->GetRelativeLocation().Equals(ExecutionCameraHome,.1f) && !PursuitChair->IsVisible(),TEXT("retry restores camera and hides carried chair"));},6.f,false);
    GetWorld()->GetTimerManager().SetTimer(End,[this,Errors]{UAudioMixerBlueprintLibrary::StopRecordingOutput(this,EAudioRecordingExportType::WavFile,TEXT("pursuit_audio_output"),FPaths::ProjectSavedDir()/TEXT("Verification"));UE_LOG(LogTemp,Display,TEXT("NR_PURSUIT_COMPLETE failures=%d"),*Errors);FPlatformMisc::RequestExitWithStatus(false,*Errors?1:0);},7.3f,false);
}
