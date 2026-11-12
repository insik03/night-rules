#include "NRGame.h"
#include "Camera/PlayerCameraManager.h"
#include "Engine/World.h"
#include "Engine/GameViewportClient.h"
#include "InputKeyEventArgs.h"
#include "TimerManager.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "HAL/PlatformMisc.h"

FString ANRGameMode::ObjectiveText() const
{
    if(Finale.Active)return FinaleObjective();
    if(IntroComplete && FirstComplaintRequired()) return TEXT("민원 장부에 호수와 시간을 적자");
    if(!IntroComplete) return IntroCallPending?TEXT("첫 통화를 끝까지 듣자."):TEXT("관리실 전화를 받자.");
    if(DreamActive) return TEXT("문밖의 소리를 듣자.");
    if(Evidence.Contains(TEXT("dream_wake")) && !Evidence.Contains(TEXT("wake_trace"))) return TEXT("관리실 책상에 없던 물건이 놓여 있다.");
    if(Evidence.Contains(TEXT("wake_trace")) && !PowerOut && !PowerRepaired) return TEXT("방금 본 흔적을 되짚어 보자.");
    if(Threat) return TEXT("계단으로 내려가 피하자.\nShift를 누르면 달릴 수 있다.");
    if(ThreatPending) return TEXT("문에서 물러나 복도 소리를 살피자.");
    if(PowerOut) return HasFuse?TEXT("1층 복도 끝 분전함에 퓨즈를 교체하자."):TEXT("공용주방 조리대에서 예비 퓨즈를 찾자.");
    if(Evidence.Contains(TEXT("202_avoided")) && !Evidence.Contains(TEXT("202_safe_report"))) return TEXT("관리실 PC에 조사 내용을 남기자.");
    if(!PowerRepaired)
    {
        if(!Evidence.Contains(TEXT("minseo"))) return TEXT("203호 문밖에서 민원인과 대화하자.");
        return TEXT("202호 소음 민원을 확인하자.");
    }
    if(!Evidence.Contains(TEXT("service_ledger"))) return TEXT("1층 관리실 옆 창고의 청소 선반에서 장부를 확인하자.");
    if(!Evidence.Contains(TEXT("lost_tag"))) return TEXT("공용 세면대의 열쇠표를 확인하자.");
    if(!ReportFiled) return TEXT("관리실 PC에 조사 결과를 보고하자.");
    if(!Evidence.Contains(TEXT("manager_call"))) return TEXT("관리실에서 관리자 전화를 받자.");
    if(ComplaintLog.Plan==0) return TEXT("민원 장부에 후속 조사 방침을 정하자.\n장부를 열고 [4] 방침 작성.");
    const bool CheckWitness=ComplaintLog.Plan!=2,CheckTechnical=ComplaintLog.Plan!=1;
    if(CheckTechnical && !Evidence.Contains(TEXT("log_recording_reviewed")) && !MonitorOff) return TEXT("3번 모니터의 2층 녹화를 되감아 확인하자.");
    if(!MonitorOff && !CCTVReset) return TEXT("모니터 옆 스위치로 CCTV 전원을 끄자.");
    if(CheckWitness && !Evidence.Contains(TEXT("resident_105"))) return TEXT("민원 장부의 방침대로 105호 증언을 확인하자.");
    if(CheckWitness && !Evidence.Contains(TEXT("resident_203")) && !Evidence.Contains(TEXT("resident_203_safe"))) return TEXT("민원 장부의 방침대로 203호 증언을 대조하자.");
    if(CheckTechnical && !Evidence.Contains(TEXT("sealed_panel"))) return TEXT("민원 장부의 방침대로 2층 서쪽(왼쪽) 비상문 옆 점검구를 조사하자.");
    if(!CCTVReset) return DemoSeconds-MonitorOffAt<60?TEXT("CCTV 전원이 꺼진 채로 1분이 지나기를 기다리자. 기록을 다시 볼 수 있다."):TEXT("관리실 CCTV 전원을 다시 켜자.");
    if(!RoundFiled) return TEXT("관리실 PC에 민원 장부의 방침에 따른 조사 결과를 보고하자.");
    return EndingPending?TEXT("수화기 너머의 소리를 듣자."):TEXT("관리실 전화가 울린다.");
}

void ANRGameMode::QueueThreat(bool AfterResident)
{
    if(Threat || ThreatPending) return;
    ThreatPending=true; PreludeTime=0; PreludeCue=false; RoomEntered=true;
    Ghost->SetActorHiddenInGame(true);
    if(!AfterResident) ShowDocument(TEXT("encounter_prelude"));
    DemoSound(TEXT("chair_drag"),NRLayout::RoomCenter(1,1)+FVector(0,0,60),.45f);
    Record(TEXT("encounter"),TEXT("dialogue_before_appearance"));
}

void ANRGameMode::TickPrelude(float D)
{
    if(!ThreatPending || DreamActive || Paused || Dead || !Page.IsEmpty() || !SubtitleLines.IsEmpty()) return;
    if(!PreludeCue)
    {
        PreludeCue=true; FlickerTime=2.5f;
        DemoSound(TEXT("distant_steps"),FVector(1215,NRLayout::CorridorY,410),.6f);
        Record(TEXT("encounter"),TEXT("audible_warning"));
    }
    PreludeTime+=D;
    if(PreludeTime<3.f) return;
    ThreatPending=false;
    if(Player->GetActorLocation().Z<250)
    {
        EncounterDone=true; Record(TEXT("encounter"),TEXT("left_before_appearance")); return;
    }
    StartThreat();
}


void ANRGameMode::StartDream()
{
    if(DreamActive || Evidence.Contains(TEXT("dream_wake")) || Evidence.Contains(TEXT("202_avoided"))) return;
    DreamActive=true; DreamTime=0; DreamBeat=0; RoomEntered=true;
    Ghost->SetActorHiddenInGame(true);
    for(auto* P:Props) if(P->Id==TEXT("door_202")) P->SetDoor(false);
    DemoSound(TEXT("door_slam"),NRLayout::DoorAnchor(1,1)+FVector(0,0,100),.65f);
    ShowDocument(TEXT("dream_locked"));
    Record(TEXT("encounter"),TEXT("202_locked_no_chase"));
}
void ANRGameMode::TickDream(float D)
{
    if(!DreamActive || Paused || Dead || !Page.IsEmpty()) return;
    const float Before=DreamTime; DreamTime+=D;
    // Let each spoken beat finish before the next beat or the silence/blackout.
    if(!SubtitleLines.IsEmpty()) {
        if(Before<9 && DreamTime>=9) { DreamTime=8.99f; }
        else if(Before<16 && DreamTime>=16) { DreamTime=15.99f; }
    }
    const FVector Door=NRLayout::DoorAnchor(1,1)+FVector(0,-35,110);
    // Isolated knocks accelerate, then stop completely before the blackout.
    const float Beats[]={3,6,8,9.5f,10.7f,11.7f,12.5f,13.2f,13.8f,14.3f,14.7f,15,15.3f,15.6f};
    while(DreamBeat<UE_ARRAY_COUNT(Beats) && DreamTime>=Beats[DreamBeat])
    { DemoSound(TEXT("knock"),Door,.35f+.025f*DreamBeat); ++DreamBeat; }
    if(Before<9 && DreamTime>=9) ShowDocument(TEXT("dream_voice"));
    if(Before<16 && DreamTime>=16) { StopVoice(); SubtitleLines.Reset(); Notice.Empty(); Record(TEXT("scare"),TEXT("knocks_stop")); }
    if(DreamTime>=18)
    {
        Player->GetCharacterMovement()->StopMovementImmediately();
        if(auto* PC=Player->GetController<APlayerController>()) PC->PlayerCameraManager->SetManualCameraFade(FMath::Clamp((DreamTime-18)/2,0.f,1.f),FLinearColor::Black,false);
    }
    if(DreamTime<22) return;
    DreamActive=false; EncounterDone=true; FlickerTime=0;
    Player->UnCrouch(); Player->SprintHeld=false;
    Player->SetActorLocation(NRLayout::OfficePoint(FVector(85,-395,100)));
    Player->GetController()->SetControlRotation(FRotator(0,100,0));
    if(auto* PC=Player->GetController<APlayerController>()) { PC->FlushPressedKeys(); PC->PlayerCameraManager->StartCameraFade(1,0,2,FLinearColor::Black,false,false); }
    for(auto* P:Props) if(P->Id==TEXT("door_office")) P->SetDoor(true);
    WakeTrace->SetActorHiddenInGame(false); WakeTrace->SetActorEnableCollision(true);
    ShowDocument(TEXT("dream_wake"));
    Record(TEXT("encounter"),TEXT("office_awakening")); SaveCheckpoint();
}

void ANRGameMode::FeedbackTest()
{
    auto Failures=MakeShared<int32>(0);
    auto Check=[Failures](bool OK,const TCHAR* Name){UE_LOG(LogTemp,Display,TEXT("NR_FEEDBACK %s %s"),OK?TEXT("PASS"):TEXT("FAIL"),Name); if(!OK) ++*Failures;};
    Check(ObjectiveText().Contains(TEXT("전화")),TEXT("opening objective asks for the call"));
    IntroComplete=true; Page.Empty(); Paused=false;
    ANRProp* Drawer=nullptr; for(auto* P:Props) if(P->Id==TEXT("drawer_4")) Drawer=P;
    Check(Drawer && Drawer->StoredItem,TEXT("desk has an independent drawer with a cartridge"));
    if(Drawer && Drawer->StoredItem)
    {
        auto* Cart=Drawer->StoredItem; const int32 Count=Player->Cartridges;
        Use(Cart); Check(Cart->IsHidden() && Player->Cartridges==Count,TEXT("closed drawer prevents hidden pickup"));
        Use(Drawer); Drawer->Tick(1);
        Check(Drawer->Open && Drawer->Slide==38 && !Cart->IsHidden() && FMath::Abs(Cart->GetActorLocation().Y-(Cart->Home.Y-38))<.1f,TEXT("drawer slides and carries its cartridge"));
        FHitResult Hit; FCollisionQueryParams Query; Query.bTraceComplex=true; Query.AddIgnoredActor(Player);
        const FVector Eye=NRLayout::OfficePoint(FVector(-100,-346,147)), Aim=Cart->Mesh->Bounds.Origin;
        GetWorld()->LineTraceSingleByChannel(Hit,Eye,Aim+(Aim-Eye).GetSafeNormal()*5,ECC_Visibility,Query);
        Check(Hit.GetActor()==Cart,TEXT("open drawer cartridge is reachable by the interaction trace"));
        SaveCheckpoint(); Use(Cart); Use(Cart);
        Check(Player->Cartridges==Count+1,TEXT("drawer cartridge is collected exactly once"));
        RestoreCheckpoint();
        Check(Drawer->Open && !Cart->IsHidden() && Player->Cartridges==Count,TEXT("checkpoint restores drawer contents"));
        Use(Drawer); Drawer->Tick(1); Check(Cart->IsHidden() && !Cart->GetActorEnableCollision(),TEXT("closing drawer hides and blocks contents again"));
    }
    for(auto* Container:Props) if(Container->Id==TEXT("fridge_0") || Container->Id==TEXT("wardrobe_101") || Container->Id==TEXT("wardrobe_101_left"))
    {
        Check(Container->CorePanels.Num()>0,TEXT("cabinet has separate interactive doors"));
        Use(Container); Container->Tick(1);
        Check(Container->Open && FMath::IsNearlyEqual(Container->CorePanelAngle,-100.f),TEXT("cabinet opens through normal interaction"));
        SaveCheckpoint(); Use(Container); Container->Tick(1); RestoreCheckpoint();
        Check(Container->Open && FMath::IsNearlyEqual(Container->CorePanelAngle,-100.f),TEXT("checkpoint restores cabinet door pose immediately"));
        Use(Container); Container->Tick(1);
        Check(!Container->Open && FMath::IsNearlyZero(Container->CorePanelAngle),TEXT("cabinet closes through normal interaction"));
    }
    ANRProp *Resident=nullptr,*Neighbour=nullptr;
    for(auto* P:Props) { if(P->Id==TEXT("door_203")) Resident=P; if(P->Id==TEXT("door_104")) Neighbour=P; }
    Check(Resident && Neighbour,TEXT("occupied doors exist"));
    if(Resident && Neighbour)
    {
        Use(Resident); Check(!Resident->Open && Evidence.Contains(TEXT("minseo")),TEXT("resident speaks through a closed door"));
        Use(Neighbour); Check(!Neighbour->Open && Evidence.Contains(TEXT("resident_104")),TEXT("optional neighbour can answer without room access"));
    }
    Player->SetActorLocation(FVector(635,40,410));
    StartDream(); TickDream(10);
    Check(DreamActive && !Threat && Ghost->IsHidden(),TEXT("202 locks and knocks without spawning a chase"));
    Paused=true; const float DreamBefore=DreamTime; TickDream(10);
    Check(DreamTime==DreamBefore,TEXT("pause freezes the nightmare")); Paused=false;
    Check(DreamTime<9,TEXT("nightmare waits for the opening spoken beat"));
    StopVoice(); SubtitleLines.Reset(); TickDream(.1f);
    Check(SubtitleSource==TEXT("문밖의 목소리"),TEXT("nightmare advances to the voice at the door"));
    TickDream(10); Check(DreamTime<16,TEXT("nightmare silence waits until the voice finishes"));
    StopVoice(); SubtitleLines.Reset(); TickDream(6.1f);
    Check(!DreamActive && Player->GetActorLocation().Z<250 && !WakeTrace->IsHidden() && Evidence.Contains(TEXT("dream_wake")),TEXT("awakening relocates player and leaves a physical trace"));
    FHitResult TraceHit; FCollisionQueryParams TraceQuery; TraceQuery.bTraceComplex=true; TraceQuery.AddIgnoredActor(Player);
    const FVector TraceEye=NRLayout::OfficePoint(FVector(85,-395,149)), TraceAim=WakeTrace->Mesh->Bounds.Origin;
    GetWorld()->LineTraceSingleByChannel(TraceHit,TraceEye,TraceAim+(TraceAim-TraceEye).GetSafeNormal()*5,ECC_Visibility,TraceQuery);
    Check(TraceHit.GetActor()==WakeTrace,TEXT("aftermath clue can be targeted from the awakening position"));
    const FVector Bottom=FVector(TraceAim.X,TraceAim.Y,WakeTrace->Mesh->Bounds.GetBox().Min.Z);
    TraceQuery.AddIgnoredActor(WakeTrace);
    Check(GetWorld()->LineTraceSingleByChannel(TraceHit,Bottom+FVector(0,0,.5),Bottom-FVector(0,0,1),ECC_Visibility,TraceQuery) && FMath::Abs(TraceHit.ImpactPoint.Z-Bottom.Z)<.3f,TEXT("aftermath clue rests on the desk surface"));
    SaveCheckpoint(); RestoreCheckpoint();
    Check(!DreamActive && !WakeTrace->IsHidden(),TEXT("checkpoint preserves the aftermath without replaying the trap"));
    Player->SetActorLocation(FVector(650,-135,410));
    ShowDocument(TEXT("resident_203"));
    QueueThreat(true); TickPrelude(20);
    Check(ThreatPending && !Threat && Ghost->IsHidden(),TEXT("dialogue cannot be interrupted by an instant apparition"));
    SubtitleLines.Reset(); Notice.Empty(); TickPrelude(1);
    Check(ThreatPending && !Threat && PreludeCue,TEXT("audible prelude occurs before appearance"));
    TickPrelude(2.1f);
    Check(Threat && !ThreatPending && !Ghost->IsHidden(),TEXT("threat begins after dialogue and warning"));
    UPointLightComponent *Corridor=nullptr,*Office=nullptr;
    for(auto* L:InteriorLights)
    {
        const auto At=L->GetComponentLocation();
        if(FMath::Abs(At.Y-NRLayout::CorridorY)<5) Corridor=L;
        if(FMath::Abs(At.Y-(-340+NRLayout::OfficeShiftY))<5 && FMath::Abs(At.X-NRLayout::OfficeShift)<5) Office=L;
    }
    ThreatTime=.05f; ApplyLightState(false);
    Check(Corridor && Office && Corridor->Intensity==0 && Office->Intensity>0,TEXT("chase flicker affects corridor, not office"));
    ThreatTime=.57f; ApplyLightState(false);
    Check(Corridor && Corridor->Intensity>0,TEXT("corridor lights return between chase flashes"));
    int32 Transitions=0; bool WasDark=false;
    for(int32 I=0;I<120;++I) {
        ThreatTime=I*.01f; ApplyLightState(false);
        const bool IsDark=Corridor && Corridor->Intensity==0;
        Transitions+=IsDark!=WasDark; WasDark=IsDark;
    }
    Check(Transitions>=16,TEXT("chase lights produce eight rapid flashes per burst"));
    ThreatTime=3.65f; ApplyLightState(false);
    Check(Corridor && Corridor->Intensity==0,TEXT("rapid flicker continues during pursuit"));
    auto* DarkTube=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/PrototypeAssets/M_Ceiling.M_Ceiling"));
    bool HasTube=false, TubesDark=true;
    for(const auto& Entry:FixtureMaterials) if(FMath::Abs(Entry.Key->GetComponentLocation().Y-NRLayout::CorridorY)<100)
        for(int32 I=0;I<Entry.Value.Num();++I) {HasTube=true; TubesDark &= Entry.Key->GetMaterial(I)==DarkTube;}
    Check(HasTube && TubesDark,TEXT("visible fluorescent fixtures go dark with their lights"));
    Threat=false; ThreatPending=false; ApplyLightState(false); Ghost->SetActorHiddenInGame(true);
    Check(Corridor && Corridor->Intensity>0,TEXT("ending chase during blackout restores corridor immediately"));
    bool TubesRestored=true;
    for(const auto& Entry:FixtureMaterials) for(int32 I=0;I<Entry.Value.Num();++I) TubesRestored &= Entry.Key->GetMaterial(I)==Entry.Value[I];
    Check(TubesRestored,TEXT("ending chase restores original fixture materials"));
    ApplyLightState(true);
    Check(Corridor && Office && Corridor->Intensity==0 && Office->Intensity==0,TEXT("story power failure still overrides chase lighting"));
    ApplyLightState(false);
    Evidence.Add(TEXT("wake_trace")); PowerOut=true; HasFuse=false;
    Check(ObjectiveText().Contains(TEXT("퓨즈")),TEXT("blackout objective directs player to the fuse"));
    PowerOut=false; EncounterDone=true; RoomEntered=false; DemoSeconds=0;
    Player->SetActorLocation(FVector(NRLayout::StoreX(290),-690,90)); Player->GetController()->SetControlRotation(FRotator::ZeroRotator);
    Player->GetCharacterMovement()->StopMovementImmediately();
    auto Key=[this](FKey K,EInputEvent E){auto* V=GetWorld()->GetGameViewport(); V->InputKey(FInputKeyEventArgs::CreateSimulated(K,E,1,1,FInputDeviceId::CreateFromInternalId(0),false,V->Viewport));};
    const FVector Start=Player->GetActorLocation();
    Key(EKeys::LeftShift,IE_Pressed); Key(EKeys::W,IE_Pressed);
    auto Stage=MakeShared<int32>(0); FTimerHandle Timer;
    GetWorld()->GetTimerManager().SetTimer(Timer,[this,Check,Failures,Stage,Key,Start]{
        if(*Stage==0)
        {
            Check(Player->GetCharacterMovement()->MaxWalkSpeed==350 && FVector::Dist2D(Start,Player->GetActorLocation())>60,TEXT("Shift plus W produces sprint movement"));
            Key(EKeys::LeftControl,IE_Pressed);
        }
        else if(*Stage==1)
        {
            Check(Player->bIsCrouched && Player->GetCapsuleComponent()->GetUnscaledCapsuleHalfHeight()<60,TEXT("Ctrl lowers the actual collision capsule"));
            Key(EKeys::LeftControl,IE_Released); Key(EKeys::LeftShift,IE_Released);
        }
        else
        {
            Key(EKeys::W,IE_Released);
            Check(!Player->bIsCrouched && Player->GetCharacterMovement()->MaxWalkSpeed==220,TEXT("releasing keys restores standing and walking"));
            UE_LOG(LogTemp,Display,TEXT("NR_FEEDBACK_COMPLETE failures=%d"),*Failures);
            FPlatformMisc::RequestExitWithStatus(false,*Failures?1:0); return;
        }
        ++*Stage;
    },.4f,true);
}
