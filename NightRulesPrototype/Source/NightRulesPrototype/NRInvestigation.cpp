#include "NRGame.h"
#include "Engine/World.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Animation/BlendSpace.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Misc/Paths.h"
#include "Camera/CameraComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Engine/StaticMesh.h"
#include "Engine/Texture2D.h"
#include "Engine/TextureRenderTarget2D.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/KismetRenderingLibrary.h"
#include "TimerManager.h"
#include "HAL/PlatformMisc.h"

// The actual player mesh is recorded by every CCTV capture, without occluding the FPS camera.
bool ANRPlayer::ConfigurePlayerLODs(USkeletalMesh* Mesh)
{
#if WITH_EDITOR
    if(!Mesh || Mesh->GetLODNum()<3) return false;
    for(int32 I=1;I<3;++I) {
        auto* LOD=Mesh->GetLODInfo(I);if(!LOD) return false;
        LOD->ReductionSettings.NumOfTrianglesPercentage=I==1?.5f:.2f;
        LOD->ScreenSize.Default=I==1?.45f:.20f;
    }
    Mesh->MarkPackageDirty();return true;
#else
    return false;
#endif
}
bool ANRPlayer::ConfigureLocomotion(UBlendSpace* Blend,const TArray<UAnimSequence*>& Clips)
{
#if WITH_EDITOR
    if(!Blend || Clips.Num()!=5) return false;
    for(auto* Clip:Clips) if(!Clip) return false;
    Blend->SetSkeleton(Clips[0]->GetSkeleton());
    auto& Speed=const_cast<FBlendParameter&>(Blend->GetBlendParameter(0));
    Speed.DisplayName=TEXT("Speed");Speed.Min=0;Speed.Max=350;Speed.GridNum=7;
    auto& Crouch=const_cast<FBlendParameter&>(Blend->GetBlendParameter(1));
    Crouch.DisplayName=TEXT("Crouch");Crouch.Min=0;Crouch.Max=1;Crouch.GridNum=1;
    while(Blend->GetNumberOfBlendSamples()) Blend->DeleteSample(0);
    Blend->AddSample(Clips[0],FVector(0,0,0));
    Blend->AddSample(Clips[1],FVector(220,0,0));
    Blend->AddSample(Clips[2],FVector(350,0,0));
    Blend->AddSample(Clips[3],FVector(0,1,0));
    Blend->AddSample(Clips[4],FVector(110,1,0));
    Blend->AddSample(Clips[4],FVector(350,1,0));
    Blend->ResampleData();Blend->MarkPackageDirty();return true;
#else
    return false;
#endif
}
void ANRPlayer::BuildCCTVBody()
{
    if(PlayerVisual) return;
    auto* Model=LoadObject<USkeletalMesh>(nullptr,TEXT("/Game/PrototypeAssets/Protagonist/SK_Protagonist.SK_Protagonist"));
    auto* Blend=LoadObject<UBlendSpace>(nullptr,TEXT("/Game/PrototypeAssets/Protagonist/BS_Player.BS_Player"));
    if(!Model || !Blend) {UE_LOG(LogTemp,Error,TEXT("Protagonist model/locomotion missing"));return;}
    PlayerVisual=GetMesh();PlayerVisual->SetSkeletalMesh(Model);
    PlayerVisual->SetRelativeLocation(FVector(0,0,-85));
    PlayerVisual->SetRelativeRotation(FRotator(0,-90,0));
    PlayerVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    PlayerVisual->SetVisibleInSceneCaptureOnly(true);PlayerVisual->SetCastShadow(false);
    PlayerVisual->VisibilityBasedAnimTickOption=EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
    PlayerVisual->bEnableUpdateRateOptimizations=false;
    PlayerVisual->PlayAnimation(Blend,true);CCTVBody.Add(PlayerVisual);
    FlashlightVisual->SetHiddenInSceneCapture(true);
}
void ANRPlayer::TickCCTVBody(float D)
{
    if(!PlayerVisual) return;
    BodyCrouch=FMath::FInterpTo(BodyCrouch,bIsCrouched?1.f:0.f,D,10.f);
    PlayerVisual->SetRelativeLocation(FVector(0,0,-GetCapsuleComponent()->GetUnscaledCapsuleHalfHeight()));
    const FVector Velocity=GetVelocity();const float Speed=Velocity.Size2D();
    // Turn the body toward side steps; reverse clip time for backwards travel.
    const float Forward=FVector::DotProduct(Velocity,GetActorForwardVector());
    const float Side=FVector::DotProduct(Velocity,GetActorRightVector());
    const float Yaw=Speed>5?FMath::Clamp(FMath::RadiansToDegrees(FMath::Atan2(Side,FMath::Abs(Forward))),-75.f,75.f):0;
    PlayerVisual->SetRelativeRotation(FMath::RInterpTo(PlayerVisual->GetRelativeRotation(),FRotator(0,-90+Yaw,0),D,10.f));
    if(auto* Anim=PlayerVisual->GetSingleNodeInstance()) {
        Anim->SetBlendSpacePosition(FVector(Speed,BodyCrouch,0));
        Anim->SetPlayRate(Forward< -5?-1.f:1.f);
    }
}
void ANRGameMode::SetupInvestigation()
{
    Player->BuildCCTVBody();
    // A real desk interaction must show the operator, not only an empty corridor.
    const FVector OfficeCamera=NRLayout::OfficePoint(FVector(-115,-220,240));
    CCTVCameras[0]->SetWorldLocation(OfficeCamera);
    CCTVCameras[0]->SetWorldRotation((NRLayout::OfficePoint(FVector(25,-380,100))-OfficeCamera).Rotation());
    CCTVCameras[0]->FOVAngle=100;
    auto Setup=[this](ANRProp* Mark,const TCHAR* Texture,FVector Size,FRotator Rotation) {
        Mark->SetActorScale3D(FVector(1));Mark->Label->SetVisibility(false);
        Mark->Mesh->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Plane.Plane")));
        Mark->Mesh->SetRelativeScale3D(FVector(-Size.X,Size.Y,Size.Z)/100);Mark->SetActorRotation(Rotation);
        Mark->Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);Mark->Mesh->SetCastShadow(false);
        auto* Mat=UMaterialInstanceDynamic::Create(LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/PrototypeAssets/M_UVMark.M_UVMark")),this);
        if(Mat) {Mat->SetTextureParameterValue(TEXT("Feed"),LoadObject<UTexture2D>(nullptr,Texture));Mark->Mesh->SetMaterial(0,Mat);}
        Mark->Mesh->SetVisibility(false);
    };
    Setup(UVMarker,TEXT("/Game/PrototypeAssets/T_UVDoor.T_UVDoor"),FVector(65,24,100),FRotator(0,0,90));
    UVWakeMarker=Prop(TEXT("uv_wake_mark"),TEXT(""),FVector::ZeroVector,FVector(1));
    Setup(UVWakeMarker,TEXT("/Game/PrototypeAssets/T_UVFragment.T_UVFragment"),FVector(11,2.5f,100),FRotator::ZeroRotator);
    // Evidence is present before E is pressed. Decorative parts never intercept
    // the interaction ray or add collision to the doorway.
    auto Metal=[this](FVector At,FVector Size,FLinearColor Color,FRotator Rotation=FRotator::ZeroRotator) {
        auto* Part=Prop(TEXT("clue_surface"),TEXT(""),At,Size);
        Part->Label->SetVisibility(false);Part->SetActorRotation(Rotation);
        Part->Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        auto* Base=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/PrototypeAssets/M_ClueMetal_v1.M_ClueMetal_v1"));
        if(Base) {auto* M=UMaterialInstanceDynamic::Create(Base,this);M->SetVectorParameterValue(TEXT("Tint"),Color);Part->Mesh->SetMaterial(0,M);}
        return Part;
    };
    const FVector Latch=NRLayout::DoorAnchor(1,1)+FVector(48,-1.8f,110);
    const FLinearColor Steel(.31f,.30f,.26f),Cut(.055f,.047f,.036f),Fresh(.62f,.58f,.47f);
    if(WakeTrace) {
        auto* Base=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/PrototypeAssets/M_ClueMetal_v1.M_ClueMetal_v1"));
        if(Base) {auto* M=UMaterialInstanceDynamic::Create(Base,this);M->SetVectorParameterValue(TEXT("Tint"),Steel);WakeTrace->Mesh->SetMaterial(0,M);}
    }
    // An exposed strike slot and bent rim, plus scraped paint around its screws.
    Metal(Latch,FVector(9,.35f,24),Steel);
    Metal(Latch+FVector(0,-.24f,0),FVector(3.8f,.12f,10),Cut);
    Metal(Latch+FVector(2.5f,-.7f,0),FVector(1.1f,1.2f,11),Fresh,FRotator(0,12,0));
    for(float H:{-9.f,9.f}) {
        Metal(Latch+FVector(0,-.45f,H),FVector(1.4f,.35f,1.4f),Cut);
        for(int32 I=0;I<4;++I) {
            const FVector At=Latch+FVector(-3.3f+I*1.6f,-.46f,H-1.4f+I*.5f);
            Metal(At,FVector(.2f,.14f,4.4f+I*.6f),Fresh,FRotator(18+I*8,0,0));
        }
    }
    // Residue on the actual hatch surface, revealed only inside the UV beam.
    const TArray<ANRProp*> Existing=Props;
    for(auto* P:Existing) if(P->Id==TEXT("sealed_panel")) {
        const FBox B=P->Mesh->Bounds.GetBox();
        auto* Print=Prop(TEXT("clue_handprint"),TEXT(""),FVector(B.Max.X+.25f,B.GetCenter().Y-4,B.GetCenter().Z-4),FVector(1));
        UVHandMarker=Print;
        Print->Label->SetVisibility(false);Print->SetActorScale3D(FVector(1));
        Print->Mesh->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Plane.Plane")));
        Print->Mesh->SetRelativeScale3D(FVector(.26f,.34f,1));Print->SetActorRotation(FRotator(0,90,90));
        Print->Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);Print->Mesh->SetCastShadow(false);
        Print->Mesh->SetMaterial(0,LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/PrototypeAssets/M_ClueUVHand_v1.M_ClueUVHand_v1")));
        Print->Mesh->SetVisibility(false);
        Print->AttachToActor(P,FAttachmentTransformRules::KeepWorldTransform);
    }
    // Place the second-floor corridor camera before 202/203 so the player's first investigation is visible.
    CCTVCameras[3]->SetWorldLocation(FVector(420,-185,560));
    CCTVCameras[3]->SetWorldRotation(FRotator(-15,8,0));
}
bool ANRGameMode::UVVisible(ANRProp* Mark,AActor* Surface) const
{
    if(!Mark || !Player || !Player->CanMove() || !Player->UV || !Player->LightOn || Player->UVRemaining<=0) return false;
    const FVector From=Player->Camera->GetComponentLocation(),To=Mark->GetActorLocation()-From;
    if(To.Size()>260 || FVector::DotProduct(To.GetSafeNormal(),Player->Camera->GetForwardVector())<.94f) return false;
    FHitResult Hit;FCollisionQueryParams Q;Q.bTraceComplex=true;Q.AddIgnoredActor(Player);Q.AddIgnoredActor(Mark);
    // Accept a hit on the inspected fragment itself, but never ignore walls/desk.
    const bool Blocked=GetWorld()->LineTraceSingleByChannel(Hit,From,Mark->GetActorLocation(),ECC_Visibility,Q);
    return !Blocked || (Surface && Hit.GetActor()==Surface && FVector::Dist(Hit.ImpactPoint,Mark->GetActorLocation())<20);
}
void ANRGameMode::TickUV()
{
    UVMarker->Mesh->SetVisibility(UVVisible(UVMarker));
    if(UVHandMarker) UVHandMarker->Mesh->SetVisibility(UVVisible(UVHandMarker,UVHandMarker->GetAttachParentActor()));
    if(WakeTrace && !WakeTrace->IsHidden()) {
        const auto B=WakeTrace->Mesh->Bounds;
        UVWakeMarker->SetActorLocation(FVector(B.Origin.X,B.Origin.Y,B.Origin.Z+B.BoxExtent.Z+.5f));
        UVWakeMarker->Mesh->SetVisibility(UVVisible(UVWakeMarker,WakeTrace));
    } else UVWakeMarker->Mesh->SetVisibility(false);
}
FString ANRGameMode::UVClue() const
{
    if(UVVisible(UVMarker)) return TEXT("uv");
    if(WakeTrace && !WakeTrace->IsHidden() && UVVisible(UVWakeMarker,WakeTrace)) return TEXT("uv_fragment");
    if(UVHandMarker && UVVisible(UVHandMarker,UVHandMarker->GetAttachParentActor())) return TEXT("uv_hand");
    return FString();
}
bool ANRGameMode::ReadUVClue()
{
    if(IntroCallPending || DreamActive) return false;
    const FString Key=UVClue();if(Key.IsEmpty()) return false;
    if(Key==TEXT("uv_hand")) UseDemo(Cast<ANRProp>(UVHandMarker->GetAttachParentActor()));
    ShowDocument(Key);
    if(Key==TEXT("uv_fragment") && !Evidence.Contains(TEXT("wake_trace"))) {
        Evidence.Add(TEXT("wake_trace"));Record(TEXT("read"),TEXT("wake_trace"));
    }
    if(Evidence.Contains(TEXT("uv")) && Evidence.Contains(TEXT("uv_fragment"))) {
        const FString Comparison=TEXT("UV 조사 위치\n\n202호 문 옆 벽.\n관리실 책상의 금속 조각.");
        Documents.Add(TEXT("uv_compare"),Comparison);Evidence.Add(TEXT("uv_compare"));
        Record(TEXT("evidence"),TEXT("uv_compare"));
    }
    return true;
}

void ANRGameMode::InvestigationTest()
{
    struct FState {int32 Failures=0,Stage=0; FTimerHandle Timer; TArray<FColor> Empty,Body,Replay; FVector Leg; float Travel=0;};
    auto S=MakeShared<FState>();
    auto Check=[S](bool OK,const TCHAR* Name){UE_LOG(LogTemp,Display,TEXT("NR_INVESTIGATION %s %s"),OK?TEXT("PASS"):TEXT("FAIL"),Name);if(!OK)++S->Failures;};
    FirstCall=99999;IntroComplete=true;IntroCallPending=false;Page.Empty();Paused=false;StopVoice();SubtitleLines.Reset();Notice.Empty();
    Player->SetActorLocation(FVector(725,-153,410));Player->GetController()->SetControlRotation(FRotator(-18,90,0));Player->Camera->SetWorldRotation(FRotator(-18,90,0));
    Player->UVRemaining=45;Player->UV=false;Player->LightOn=true;
    Check(UVClue().IsEmpty(),TEXT("ordinary flashlight cannot reveal or record UV markings"));
    Player->UV=true;TickUV();Check(UVClue()==TEXT("uv") && UVMarker->Mesh->IsVisible(),TEXT("aiming UV at 202 reveals the actual world marking"));
    Player->Camera->SetWorldRotation(FRotator(0,-90,0));Check(!ReadUVClue(),TEXT("looking away cannot award the clue"));
    Player->Camera->SetWorldRotation(FRotator(-18,90,0));Player->LightOn=false;Check(UVClue().IsEmpty(),TEXT("switched-off UV does not reveal evidence"));Player->LightOn=true;
    Player->UVRemaining=0;Check(UVClue().IsEmpty(),TEXT("empty cartridge cannot reveal evidence"));Player->UVRemaining=45;
    // Same wall, opposite side: angle/distance pass, visibility must still fail.
    Player->SetActorLocation(FVector(725,35,410));Player->Camera->SetWorldRotation(FRotator(-11,-90,0));Check(UVClue().IsEmpty(),TEXT("UV cannot reveal evidence through a wall"));
    Player->SetActorLocation(FVector(725,-153,410));Player->Camera->SetWorldRotation(FRotator(-18,90,0));
    Check(ReadUVClue() && Evidence.Contains(TEXT("uv")) && !ActiveVoice,TEXT("visible mark records silent evidence with E"));
    WakeTrace->SetActorHiddenInGame(false);TickUV();
    Player->SetActorLocation(UVWakeMarker->GetActorLocation()+FVector(0,-90,40));
    const FRotator Look=(UVWakeMarker->GetActorLocation()-Player->Camera->GetComponentLocation()).Rotation();Player->GetController()->SetControlRotation(Look);Player->Camera->SetWorldRotation(Look);
    Check(ReadUVClue() && Evidence.Contains(TEXT("uv_compare")) && Evidence.Contains(TEXT("wake_trace")) && !ActiveVoice,TEXT("second UV clue joins actual evidence without dubbing or story softlock"));
    if(UVHandMarker) {
        const FVector HandAt=UVHandMarker->GetActorLocation();
        Player->SetActorLocation(HandAt+FVector(105,0,-42));
        const FRotator HandLook=(HandAt-Player->Camera->GetComponentLocation()).Rotation();
        Player->GetController()->SetControlRotation(HandLook);Player->Camera->SetWorldRotation(HandLook);
        Player->UV=false;TickUV();
        Check(!UVHandMarker->Mesh->IsVisible() && UVClue().IsEmpty(),TEXT("hand residue is absent under ordinary light"));
        Player->UV=true;TickUV();
        Check(UVHandMarker->Mesh->IsVisible() && UVClue()==TEXT("uv_hand"),TEXT("aimed UV reveals hatch residue"));
        Check(ReadUVClue() && Evidence.Contains(TEXT("uv_hand")) && !Evidence.Contains(TEXT("sealed_panel")),TEXT("early UV hand recording does not bypass the manager's later inspection"));
        Player->LightOn=false;TickUV();Check(!UVHandMarker->Mesh->IsVisible(),TEXT("hand residue vanishes with the light off"));Player->LightOn=true;
        Player->Camera->SetWorldRotation(HandLook+FRotator(0,180,0));TickUV();Check(!UVHandMarker->Mesh->IsVisible(),TEXT("hand residue vanishes outside the UV beam"));
    } else Check(false,TEXT("physical hatch residue exists"));
    Red=true;RuleInk=0;Page.Empty();RulesView=false;Player->SetActorLocation(NRLayout::OfficePoint(FVector(85,-300,100)));Player->Camera->SetWorldRotation(FRotator(0,90,0));TickRuleAnnotations(5.f);
    Check(RuleInk==0,TEXT("red note waits until the board is first looked at"));
    ShowDocument(TEXT("rules"));TickRuleAnnotations(1.f);
    Check(RuleInk>0 && RuleInk<.1f && !Evidence.Contains(TEXT("rules_rebuttal")) && RuleInkText(false).Len()<RuleDenial.Len(),TEXT("red note is written stroke by stroke while watched"));
    for(int32 I=0;I<40 && RuleInk<ReplyStart-.02f;++I) TickRuleAnnotations(1.f);
    Check(RuleInkText(false)==RuleDenial && RuleInkText(true).IsEmpty() && Evidence.Contains(TEXT("rules_denial_seen")),TEXT("denial is finished before the reply starts"));
    // Upstairs and not reading: the note waits.
    const FVector Before=Player->GetActorLocation();
    Page.Empty();RulesView=false;Player->SetActorLocation(FVector(725,-153,410));const float Held=RuleInk;TickRuleAnnotations(5.f);
    Check(RuleInk==Held,TEXT("note waits mid-stroke while the player is out of the office"));
    // In the office but facing away, it writes faster than while watched.
    Player->SetActorLocation(NRLayout::OfficePoint(FVector(85,-300,100)));Player->Camera->SetWorldRotation(FRotator(0,90,0));TickRuleAnnotations(1.f);
    Check(RuleInk-Held>.1f,TEXT("note writes faster when the player looks away"));
    Player->SetActorLocation(Before);ShowDocument(TEXT("rules"));
    for(int32 I=0;I<40 && !Evidence.Contains(TEXT("rules_rebuttal"));++I) TickRuleAnnotations(1.f);
    TickDisplays(0);
    Check(AnnotatedRule==2 && Evidence.Contains(TEXT("rules_rebuttal")) && RulesShownStage==2 && RuleInkText(true)==RuleReply,TEXT("opposing red note appears beside the targeted rule on wall and reader"));
    SaveCheckpoint();Evidence.Remove(TEXT("rules_rebuttal"));RestoreCheckpoint();
    Check(Evidence.Contains(TEXT("rules_rebuttal")),TEXT("rule annotation state survives checkpoint restore"));
    Page.Empty();RulesView=false;
    PowerRepaired=true;SetPower(false);
    Player->UV=false;Player->LightOn=false;StopVoice();SubtitleLines.Reset();Notice.Empty();
    Player->SetActorLocation(FVector(700,-140,410));Player->GetController()->SetControlRotation(FRotator(0,0,0));Player->SetActorRotation(FRotator::ZeroRotator);
    Check(Player->PlayerVisual && Player->CCTVBody.Num()==1 && Player->PlayerVisual->bVisibleInSceneCaptureOnly,TEXT("player body exists only in capture views"));
    for(auto* P:Player->CCTVBody) P->SetVisibility(false);
    GetWorld()->GetTimerManager().SetTimer(S->Timer,[this,S,Check] {
        ++S->Stage;
        if(S->Stage==1) {
            CCTVCameras[3]->CaptureScene();UKismetRenderingLibrary::ReadRenderTarget(this,CCTVTargets[3],S->Empty,false);
            for(auto* P:Player->CCTVBody) P->SetVisibility(true);
        }
        if(S->Stage==2) {
            CCTVCameras[3]->CaptureScene();UKismetRenderingLibrary::ReadRenderTarget(this,CCTVTargets[3],S->Body,false);
            int32 Changed=0;for(int32 I=0;I<S->Body.Num();++I) if(S->Empty.IsValidIndex(I) && FMath::Abs(int32(S->Body[I].R)-S->Empty[I].R)+FMath::Abs(int32(S->Body[I].G)-S->Empty[I].G)+FMath::Abs(int32(S->Body[I].B)-S->Empty[I].B)>35) ++Changed;
            UE_LOG(LogTemp,Display,TEXT("CCTV body changed pixels=%d"),Changed);Check(Changed>150,TEXT("player is actually visible in live CCTV pixels"));
            UKismetRenderingLibrary::ExportRenderTarget(this,CCTVTargets[3],FPaths::ProjectSavedDir()/TEXT("Verification"),TEXT("cctv_player.png"));
            RecordTimer=0;TickDisplays(.51f);ReplayCCTV(1);UKismetRenderingLibrary::ReadRenderTarget(this,ReplayTargets[3],S->Replay,false);
            S->Leg=Player->PlayerVisual->GetBoneLocation(TEXT("LeftFoot"));
        }
        if(S->Stage==3) {
            Player->GetCharacterMovement()->Velocity=FVector(220,0,0);Player->TickCCTVBody(.12f);
            Player->PlayerVisual->TickAnimation(.25f,false);Player->PlayerVisual->RefreshBoneTransforms();
            Check(!Player->PlayerVisual->GetBoneLocation(TEXT("LeftFoot")).Equals(S->Leg,.1f),TEXT("actual movement changes the skeletal foot pose"));
            Player->GetCharacterMovement()->StopMovementImmediately();Player->SetActorLocation(FVector(1020,-140,410));
        }
        if(S->Stage==4) {
            CCTVCameras[3]->CaptureScene();TArray<FColor> Moved,Replay;UKismetRenderingLibrary::ReadRenderTarget(this,CCTVTargets[3],Moved,false);UKismetRenderingLibrary::ReadRenderTarget(this,ReplayTargets[3],Replay,false);
            Check(Moved!=S->Body && S->Replay==Replay,TEXT("live image follows movement while selected replay preserves earlier position"));
            LiveCCTV();for(auto* P:Props) if(P->Id==TEXT("cctv")) Use(P);
            Player->GetController<APlayerController>()->ConsoleCommand(TEXT("Shot SHOWUI"));
        }
        if(S->Stage==5) {
            const int32 Failures=S->Failures;FTimerHandle Handle=S->Timer;UE_LOG(LogTemp,Display,TEXT("NR_INVESTIGATION_COMPLETE failures=%d"),Failures);
            GetWorld()->GetTimerManager().ClearTimer(Handle);FPlatformMisc::RequestExitWithStatus(false,Failures?1:0);
        }
    },1.f,true);
}

FString ANRGameMode::RuleInkText(bool Reply) const
{
    // The enlarged reader shows exactly as much as the wall: same progress, same order.
    const FString& Text=Reply?RuleReply:RuleDenial;
    const float T=Reply?(RuleInk-ReplyStart)/(.98f-ReplyStart):RuleInk/(ReplyStart-.02f);
    return Text.Left(FMath::CeilToInt(Text.Len()*FMath::Clamp(T,0.f,1.f)));
}
void ANRGameMode::TickRuleAnnotations(float D)
{
    if(Evidence.Contains(TEXT("rules_rebuttal"))) RuleInk=1;    // restored checkpoints keep a finished note
    if(!Red || Paused || Dead || Finished || RuleInk>=1) return;
    const FVector Eye=Player->Camera->GetComponentLocation(),At=NRLayout::OfficeWallPoint(FVector(0,-469,140)),Pos=Player->GetActorLocation();
    const bool Watching=RulesView || (Page.IsEmpty() && FVector::Dist(Eye,At)<240 && FVector::DotProduct((At-Eye).GetSafeNormal(),Player->Camera->GetForwardVector())>.8f);
    const bool InOffice=NRLayout::InOffice(Pos);
    // The note writes itself: slowly while watched, faster when the player looks away,
    // and it waits mid-stroke while the player is out of the office.
    // Nothing is written until the board is first looked at, so the first sight is always ink in motion.
    if(Watching) Evidence.Add(TEXT("rules_ink_started"));
    if(!Evidence.Contains(TEXT("rules_ink_started")) || (!Watching && !InOffice)) return;
    // The reply only starts once the finished denial has been seen, so it is caught appearing.
    const float Cap=Evidence.Contains(TEXT("rules_denial_seen"))?1.f:ReplyStart-.02f;
    const float Before=RuleInk;
    RuleInk=FMath::Min(Cap,RuleInk+D*(Watching?.045f:.12f));
    if(Watching && RuleInk>=ReplyStart-.02f) Evidence.Add(TEXT("rules_denial_seen"));
    RuleScratchTime-=D;
    if(RuleInk>Before && RuleScratchTime<=0) { DemoSound(TEXT("pen_scratch"),At,Watching?.22f:.4f); RuleScratchTime=1.2f; }
    if(RuleInk<1) return;
    Evidence.Add(TEXT("rules_rebuttal"));
    Documents.Add(TEXT("rules_rebuttal"),FString::Printf(TEXT("%d번 규칙 옆 붉은 글씨\n\n%s\n그 옆에 다시 글씨가 생겼다.\n%s\n모양은 같지만 서로 반대되는 말이다. 어느 쪽이 맞는지는 알 수 없다."),AnnotatedRule,*RuleDenial,*RuleReply));
    Record(TEXT("red"),TEXT("rule_specific_rebuttal"));
}

void ANRGameMode::OfficeCCTVTest()
{
    struct FState { int32 Stage=0,Failures=0; FTimerHandle Timer; FVector Start; TArray<FColor> Without; };
    auto S=MakeShared<FState>();S->Start=Player->GetActorLocation();
    auto Check=[S](bool OK,const TCHAR* Name){UE_LOG(LogTemp,Display,TEXT("NR_OFFICE_CCTV %s %s"),OK?TEXT("PASS"):TEXT("FAIL"),Name);if(!OK)++S->Failures;};
    FirstCall=99999;Notice.Empty();SubtitleLines.Reset();Player->GetController()->SetIgnoreLookInput(true);
    // Keep the actual spawn position. Aim at the same screen surface used by the player.
    FVector Aim;
    for(auto* P:Props) if(P->Id==TEXT("cctv")) {
        TArray<UStaticMeshComponent*> Parts;P->GetComponents(Parts);
        for(auto* Part:Parts) if(Part->GetName()==TEXT("DisplaySurface")) Aim=Part->GetComponentLocation();
    }
    const FRotator Look=(Aim-Player->Camera->GetComponentLocation()).Rotation();Player->GetController()->SetControlRotation(Look);Player->Camera->SetWorldRotation(Look);
    GetWorld()->GetTimerManager().SetTimer(S->Timer,[this,S,Check] {
        ++S->Stage;
        if(S->Stage==1) {
            Check(Player->Focus && Player->Focus->Id==TEXT("cctv"),TEXT("real start-position crosshair targets the desk CCTV"));
            Player->Interact();
            Check(CCTVView && !Page.IsEmpty(),TEXT("normal player interaction opens live CCTV without teleporting"));
            Check(FVector::Dist2D(S->Start,Player->GetActorLocation())<2,TEXT("player stays at the actual desk position"));
            for(auto* Part:Player->CCTVBody) Part->SetVisibility(false);
        }
        if(S->Stage==2) {
            CCTVCameras[0]->CaptureScene();UKismetRenderingLibrary::ReadRenderTarget(this,CCTVTargets[0],S->Without,false);
            for(auto* Part:Player->CCTVBody) Part->SetVisibility(true);
        }
        if(S->Stage==3) {
            CCTVCameras[0]->CaptureScene();TArray<FColor> With;UKismetRenderingLibrary::ReadRenderTarget(this,CCTVTargets[0],With,false);
            int32 Changed=0;for(int32 I=0;I<With.Num();++I) if(S->Without.IsValidIndex(I) && FMath::Abs(int32(With[I].R)-S->Without[I].R)+FMath::Abs(int32(With[I].G)-S->Without[I].G)+FMath::Abs(int32(With[I].B)-S->Without[I].B)>40) ++Changed;
            UE_LOG(LogTemp,Display,TEXT("Office operator visible pixels=%d"),Changed);
            Check(Changed>500,TEXT("live office camera renders the operator at the desk"));
            Check(MonitorMaterial->K2_GetTextureParameterValue(TEXT("Feed"))==CCTVTargets[0],TEXT("physical desk monitor shows the same office camera"));
        }
        if(S->Stage==4) Player->GetController<APlayerController>()->ConsoleCommand(TEXT("Shot SHOWUI"));
        if(S->Stage==5) {
            const int32 Failures=S->Failures;FTimerHandle Timer=S->Timer;
            UE_LOG(LogTemp,Display,TEXT("NR_OFFICE_CCTV_COMPLETE failures=%d"),Failures);
            GetWorld()->GetTimerManager().ClearTimer(Timer);FPlatformMisc::RequestExitWithStatus(false,Failures?1:0);
        }
    },1.f,true);
}
