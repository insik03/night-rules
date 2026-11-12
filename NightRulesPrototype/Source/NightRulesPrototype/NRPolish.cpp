#include "NRGame.h"
#include "Engine/World.h"
#include "Engine/GameViewportClient.h"
#include "InputKeyEventArgs.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/AudioComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Sound/SoundBase.h"
#include "Sound/SoundAttenuation.h"
#include "Animation/AnimSequence.h"
#include "AudioMixerBlueprintLibrary.h"
#include "Misc/App.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "TimerManager.h"
#include "HAL/PlatformMisc.h"

void ANRGameMode::PolishTest()
{
    struct FState { int32 Failures=0, Stage=0, RouteStep=0; float Time=0; FTimerHandle Timer; FVector Calf; float Volume=1; float BoneTravel=0; };
    auto T=MakeShared<FState>(); T->Volume=MasterVolume;
    auto Check=[T](bool OK,const TCHAR* Name){UE_LOG(LogTemp,Display,TEXT("NR_POLISH %s %s"),OK?TEXT("PASS"):TEXT("FAIL"),Name);if(!OK)++T->Failures;};
    Page.Empty(); Paused=false; FirstCall=99999; IntroComplete=true;
    bool Sealed=true;
    for(float Y:{-260.f,-400.f,-590.f,-780.f}) {
        const float Z=Y<-616?450:FMath::Clamp((-Y-200)/26*20+140,140.f,580.f);
        for(float X:{3400.f,4000.f}) {
            FHitResult Hit; FCollisionQueryParams Q;Q.AddIgnoredActor(Player);Q.AddIgnoredActor(Ghost);
            Sealed &= GetWorld()->LineTraceSingleByChannel(Hit,FVector(3700,Y,Z),FVector(X,Y,Z),ECC_Visibility,Q);
        }
    }
    Check(Sealed,TEXT("both stair shaft sides block rays along the whole flight and landing"));
    FString VoiceJson;TSharedPtr<FJsonObject> Manifest;
    const bool Loaded=FFileHelper::LoadFileToString(VoiceJson,*(FPaths::ProjectContentDir()/TEXT("Data/voices.json"))) && FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(VoiceJson),Manifest);
    int32 Rows=0,ExpectedSpoken=0,Spoken=0;TSet<FString> Assets;bool Complete=Loaded;
    if(Loaded) for(const auto& Pair:Manifest->Values) {
        const FString DocumentKey(*Pair.Key);
        const auto& AuthoredRows=Pair.Value->AsArray();
        TArray<FString> Expected;Documents.FindRef(DocumentKey).ParseIntoArrayLines(Expected,true);
        if(!Expected.IsEmpty())Expected.RemoveAt(0);
        Complete &= Expected.Num()==AuthoredRows.Num();
        bool HasSpeech=false;
        for(int32 I=0;I<AuthoredRows.Num();++I) {
            const auto Row=AuthoredRows[I]->AsObject();++Rows;
            Complete &= Expected.IsValidIndex(I) && Expected[I].TrimStartAndEnd()==Row->GetStringField(TEXT("subtitle"));
            const FString Asset=Row->GetStringField(TEXT("asset"));
            if(!Asset.IsEmpty()){HasSpeech=true;++ExpectedSpoken;Assets.Add(Asset);}
        }
        // Silent inspection notices and dynamic reports intentionally have no voice queue.
        if(!HasSpeech)continue;
        // Each manifest key is checked as authored; heard-call variants are their own keys.
        StopVoice();SubtitleLines.Reset();Notice.Empty();Page.Empty();IntroCallPending=false;Evidence.Remove(TEXT("second_call"));
        ShowDocument(DocumentKey);
        Complete &= VoiceLines.Num()==AuthoredRows.Num() && SubtitleLines.Num()==AuthoredRows.Num();
        for(int32 I=0;I<AuthoredRows.Num();++I) {
            if(!VoiceLines.IsValidIndex(I) || !SubtitleLines.IsValidIndex(I)){Complete=false;continue;}
            const auto Row=AuthoredRows[I]->AsObject();const bool Voiced=!Row->GetStringField(TEXT("asset")).IsEmpty();
            Complete &= SubtitleLines[I].Text==Row->GetStringField(TEXT("subtitle")) && (VoiceLines[I]!=nullptr)==Voiced;
            if(VoiceLines[I]){++Spoken;Complete &= VoiceLines[I]->GetDuration()>.1f && SubtitleLines[I].Duration>=VoiceLines[I]->GetDuration();}
        }
    }
    UE_LOG(LogTemp,Display,TEXT("NR_POLISH_VOICE rows=%d expected_spoken=%d played=%d unique_clips=%d"),Rows,ExpectedSpoken,Spoken,Assets.Num());
    Check(Complete && Rows>0 && ExpectedSpoken>0 && Spoken==ExpectedSpoken,TEXT("all manifest rows match authored text and every spoken row loads its clip"));
    StopVoice();SubtitleLines.Reset();Notice.Empty();Page.Empty();
    IntroCallPending=false;ShowDocument(TEXT("spare_fuse"));Check(!ActiveVoice && !VoiceLines.ContainsByPredicate([](USoundBase* Clip){return Clip!=nullptr;}),TEXT("written quotes and inspection text remain silent"));
    IntroCallPending=false; ShowDocument(TEXT("final_call"));
    float Total=0;for(const auto& Line:SubtitleLines)Total+=Line.Duration;
    Tick(Total+.1f);Check(Finished && !ActiveVoice,TEXT("last call finishes only after its final voiced subtitle"));
    Finished=false; EndingPending=false; Page.Empty();StopVoice();SubtitleLines.Reset();Notice.Empty();
    Check(LocalAudioAttenuation && LocalAudioAttenuation->Attenuation.OcclusionVolumeAttenuation>=.6f,TEXT("walls muffle sounds without making them nearly inaudible"));
    FApp::SetUnfocusedVolumeMultiplier(1.f);ApplyVolume(1.f);
    UAudioMixerBlueprintLibrary::StartRecordingOutput(this,6);
    IntroCallPending=false;ShowDocument(TEXT("manager_call"));Sound(TEXT("phone_ring"),Player->GetActorLocation());
    Check(ActiveVoice && ActiveVoice->IsPlaying(),TEXT("narrative speech is actively playing through the audio component"));
    auto* Run=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/PrototypeAssets/GhostMeshy/A_CaretakerRun.A_CaretakerRun"));
    Check(GhostVisual && Run,TEXT("separate pursuit run clip is installed"));
    if(GhostVisual && Run) {GhostVisual->PlayAnimation(Run,true);GhostVisual->SetPlayRate(1);Ghost->SetActorHiddenInGame(false);T->Calf=GhostVisual->GetBoneLocation(TEXT("LeftLeg"),EBoneSpaces::ComponentSpace);}
    GetWorld()->GetTimerManager().SetTimer(T->Timer,[this,T,Check]() {
        T->Time+=.1f;
        if(T->Stage==0 && GhostVisual) T->BoneTravel=FMath::Max(T->BoneTravel,FVector::Dist(T->Calf,GhostVisual->GetBoneLocation(TEXT("LeftLeg"),EBoneSpaces::ComponentSpace)));
        if(T->Stage==0 && T->Time>.9f) {
            Check(GhostVisual && GhostVisual->GetBoneIndex(TEXT("LeftLeg"))>=0 && T->BoneTravel>1.f,TEXT("run animation changes actual leg-bone pose"));
            T->Stage=1;
        }
        if(T->Stage==1 && T->Time>5) {
            UAudioMixerBlueprintLibrary::StopRecordingOutput(this,EAudioRecordingExportType::WavFile,TEXT("polish_audio_output"),FPaths::ProjectSavedDir()/TEXT("Verification"));
            StopVoice();SubtitleLines.Reset();Notice.Empty();Ghost->SetActorHiddenInGame(true);EndingPending=false;IntroCallPending=false;
            Player->SetActorLocation(FVector(3610,-140,90));Player->GetController()->SetControlRotation(FRotator(0,-90,0));
            auto* V=GetWorld()->GetGameViewport();V->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::W,IE_Pressed,1,1,FInputDeviceId::CreateFromInternalId(0),false,V->Viewport));
            T->Stage=2;
        }
        const FVector At=Player->GetActorLocation();
        if(T->Stage==2) {
            const TArray<FVector> Route={FVector(3610,-790,250),FVector(3790,-790,250),FVector(3790,-250,410),FVector(3790,-135,410),FVector(3790,-250,410),FVector(3790,-790,250),FVector(3610,-790,250),FVector(3610,-250,90),FVector(3610,-135,90)};
            if(FVector::Dist2D(At,Route[T->RouteStep])<25 && FMath::Abs(At.Z-Route[T->RouteStep].Z)<40) {
                ++T->RouteStep;
                if(T->RouteStep==4)Check(true,TEXT("held W climbs both half flights to the next corridor"));
                if(T->RouteStep==Route.Num()){Check(true,TEXT("held W descends safely to the first floor"));T->Stage=4;}
            }
            if(T->Stage==2)Player->GetController()->SetControlRotation((Route[T->RouteStep]-At).Rotation());
        }
        if(T->Time>55 && T->Stage<4) {UE_LOG(LogTemp,Error,TEXT("STAIR_STUCK stage=%d at=%s"),T->Stage,*At.ToString());Check(false,TEXT("stairs traversal timed out"));T->Stage=4;}
        if(T->Stage==4) {
            auto* V=GetWorld()->GetGameViewport();V->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::W,IE_Released,0,1,FInputDeviceId::CreateFromInternalId(0),false,V->Viewport));
            ApplyVolume(T->Volume);SavePreferences();const int32 Failures=T->Failures; FTimerHandle Timer=T->Timer;
            UE_LOG(LogTemp,Display,TEXT("NR_POLISH_COMPLETE failures=%d"),Failures);
            GetWorld()->GetTimerManager().ClearTimer(Timer);FPlatformMisc::RequestExitWithStatus(false,Failures?1:0);
        }
    },.1f,true);
}
