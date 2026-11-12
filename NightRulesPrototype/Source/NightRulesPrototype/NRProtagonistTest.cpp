#include "NRGame.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Engine/SkeletalMesh.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Animation/BlendSpace.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/KismetRenderingLibrary.h"
#include "Misc/Paths.h"
#include "HAL/PlatformMisc.h"
#include "TimerManager.h"
#include "ImageUtils.h"
#include "Engine/TextureRenderTarget2D.h"

void ANRGameMode::ProtagonistTest()
{
    struct FState {int32 Stage=0,Failures=0;FTimerHandle Timer;float StandingHead=0;FVector Foot;};
    auto S=MakeShared<FState>();
    auto Check=[S](bool OK,const TCHAR* Name){UE_LOG(LogTemp,Display,TEXT("NR_PLAYER %s %s"),OK?TEXT("PASS"):TEXT("FAIL"),Name);if(!OK)++S->Failures;};
    auto* Body=Player->PlayerVisual;
    Check(Body && Body->GetSkeletalMeshAsset() && Body->GetSingleNodeInstance(),TEXT("cooked protagonist mesh and animation instance loaded"));
    if(!Body || !Body->GetSkeletalMeshAsset() || !Body->GetSingleNodeInstance()){FPlatformMisc::RequestExitWithStatus(false,1);return;}
    Check(Body->GetSkeletalMeshAsset()->GetLODNum()==3,TEXT("three runtime LODs present"));
    Check(Body->GetBoneIndex(TEXT("LeftFoot"))!=INDEX_NONE && Body->GetBoneIndex(TEXT("Head"))!=INDEX_NONE,TEXT("rig contains actual head and feet"));
    Check(Body->bVisibleInSceneCaptureOnly && Player->CCTVBody.Num()==1,TEXT("skeletal body replaces proxies and stays out of FPS view"));
    auto* Blend=Cast<UBlendSpace>(Body->GetSingleNodeInstance()->GetCurrentAsset());
    Check(Blend && Blend->GetBlendSamples().Num()==6,TEXT("idle walk run and crouch samples cooked"));
    FirstCall=99999;StopVoice();Page.Empty();Notice.Empty();SubtitleLines.Reset();
    Player->GetCharacterMovement()->DisableMovement();Player->SetActorLocation(FVector(700,-140,405));Player->SetActorRotation(FRotator::ZeroRotator);
    auto* Capture=CCTVCameras[3];const FVector At=Player->GetActorLocation();
    Capture->SetWorldLocation(At+FVector(230,-25,35));Capture->SetWorldRotation((At+FVector(0,0,5)-Capture->GetComponentLocation()).Rotation());Capture->FOVAngle=65;
    Body->PrimaryComponentTick.SetTickFunctionEnable(false);
    GetWorld()->GetTimerManager().SetTimer(S->Timer,[this,S,Check,Body] {
        ++S->Stage;
        if(S->Stage<=4) {
            const FVector Inputs[]={FVector(0,0,0),FVector(220,0,0),FVector(350,0,0),FVector(110,1,0)};
            const TCHAR* Names[]={TEXT("player_idle.png"),TEXT("player_walk.png"),TEXT("player_run.png"),TEXT("player_crouch.png")};
            Body->GetSingleNodeInstance()->SetBlendSpacePosition(Inputs[S->Stage-1]);
            Body->TickAnimation(.4f,false);Body->RefreshBoneTransforms();Body->UpdateComponentToWorld();
            const float Head=Body->GetBoneLocation(TEXT("Head")).Z;
            const FVector Foot=Body->GetBoneLocation(TEXT("LeftFoot"));
            if(S->Stage==1){S->StandingHead=Head;S->Foot=Foot;}
            if(S->Stage==2) Check(!Foot.Equals(S->Foot,1),TEXT("walking advances the skinned foot pose"));
            if(S->Stage==4) Check(Head<S->StandingHead-15,TEXT("crouch lowers the skeleton without scaling the body"));
            CCTVCameras[3]->CaptureScene();
            FImage Image;
            Check(FImageUtils::GetRenderTargetImage(CCTVTargets[3],Image) && FImageUtils::SaveImageByExtension(*(FPaths::ProjectSavedDir()/TEXT("Verification")/Names[S->Stage-1]),Image),TEXT("runtime capture saved as PNG"));
        }
        if(S->Stage==5) {
            const int32 Failures=S->Failures;FTimerHandle Handle=S->Timer;
            UE_LOG(LogTemp,Display,TEXT("NR_PLAYER_COMPLETE failures=%d"),Failures);
            GetWorld()->GetTimerManager().ClearTimer(Handle);FPlatformMisc::RequestExitWithStatus(false,Failures?1:0);
        }
    },1.f,true);
}
