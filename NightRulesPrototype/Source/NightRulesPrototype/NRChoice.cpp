#include "NRGame.h"
#include "Engine/World.h"
#include "Engine/GameViewportClient.h"
#include "InputKeyEventArgs.h"
#include "TimerManager.h"
#include "Components/StaticMeshComponent.h"
#include "Camera/CameraComponent.h"
#include "HAL/PlatformMisc.h"

void ANRGameMode::Tick202Choice()
{
    if(!IntroComplete || IntroCallPending || Paused || Dead || Finished || !Page.IsEmpty() || DreamActive || RoomEntered || Threat || ThreatPending) return;
    if(Evidence.Contains(TEXT("dream_wake")) || Evidence.Contains(TEXT("202_avoided")) || !Evidence.Contains(TEXT("minseo"))) return;
    if(!Evidence.Contains(TEXT("uv")) && !Evidence.Contains(TEXT("physical"))) return;
    const FVector At=Player->GetActorLocation(),Door=NRLayout::DoorAnchor(1,1);
    // Returning to the office is a valid decision too. Merely scanning from beside
    // the door is not a choice; the player must actually withdraw with it closed.
    if(At.Z>250 && At.Z<640 && (At.Y>-100 || FVector::Dist2D(At,Door)<280)) return;
    if(!SubtitleLines.IsEmpty()) return;
    ANRProp* DoorProp=nullptr;for(auto* P:Props) if(P->Id==TEXT("door_202")) DoorProp=P;
    if(!DoorProp || DoorProp->Open) return;
    ShowDocument(TEXT("202_avoided"));EncounterDone=true;
    DemoSound(TEXT("metal_rattle"),Door+FVector(0,30,100),.5f);
    DemoSound(TEXT("knock"),Door+FVector(0,30,100),.45f);
    Record(TEXT("choice"),Evidence.Contains(TEXT("uv"))?TEXT("202_avoided_after_uv"):TEXT("202_avoided_after_inspection"));
    SaveCheckpoint();
}

void ANRGameMode::Choice202Test()
{
    int32 Failures=0;
    auto Check=[&](bool OK,const TCHAR* Name){UE_LOG(LogTemp,Display,TEXT("NR_CHOICE202 %s %s"),OK?TEXT("PASS"):TEXT("FAIL"),Name);if(!OK)++Failures;};
    auto Clear=[this]{StopVoice();SubtitleLines.Reset();Notice.Empty();Page.Empty();};
    auto Find=[this](const TCHAR* Id)->ANRProp*{for(auto* P:Props)if(P->Id==Id)return P;return nullptr;};
    auto* Door=Find(TEXT("door_202"));auto* Resident=Find(TEXT("door_203"));auto* PC=Find(TEXT("roster"));
    FirstCall=99999;IntroComplete=true;IntroCallPending=false;Clear();
    ShowDocument(TEXT("first_call"));FinishComplaintDialogue();Clear();OpenComplaintLog();
    SelectComplaintKey(EKeys::One);SelectComplaintKey(EKeys::One);TickComplaintLog(10);Escape();
    Evidence.Add(TEXT("minseo"));Player->SetActorLocation(FVector(725,-153,410));Player->GetController()->SetControlRotation(FRotator(-18,90,0));Player->Camera->SetWorldRotation(FRotator(-18,90,0));
    Player->UVRemaining=45;Player->UV=true;Player->LightOn=true;
    Check(ReadUVClue() && Evidence.Contains(TEXT("uv")),TEXT("real UV aiming supplies the risk evidence"));Clear();Player->UV=false;
    Tick202Choice();Check(!Evidence.Contains(TEXT("202_avoided")),TEXT("reading a warning alone does not decide the route"));
    Door->SetDoor(true);Player->SetActorLocation(FVector(980,-135,410));Tick202Choice();
    Check(!Evidence.Contains(TEXT("202_avoided")),TEXT("leaving the door open does not count as safe withdrawal"));
    Door->SetDoor(false);const FVector Before=Player->GetActorLocation();Tick202Choice();
    Check(Evidence.Contains(TEXT("202_avoided")) && !RoomEntered && !DreamActive && !Threat && WakeTrace->IsHidden() && Player->GetActorLocation()==Before,TEXT("closed-door withdrawal avoids confinement without teleport or fabricated aftermath"));
    Check(Documents.FindRef(TEXT("202_avoided")).Contains(TEXT("문을 열지 않고 202호 앞을 떠났다")),TEXT("withdrawal text does not claim the door was opened or player stayed in corridor"));
    Check(ObjectiveText().Contains(TEXT("관리실 PC")) && !ObjectiveText().Contains(TEXT("들어가")),TEXT("after withdrawal the objective leads to the PC without prescribing entry"));
    Clear();SaveCheckpoint();Evidence.Remove(TEXT("202_avoided"));RestoreCheckpoint();
    Check(Evidence.Contains(TEXT("202_avoided")) && WakeTrace->IsHidden(),TEXT("checkpoint preserves the safe route without dream evidence"));
    // Before reporting, choosing to open the door again honestly cancels withdrawal.
    Evidence.Add(TEXT("physical"));Player->SetActorLocation(FVector(635,-135,410));Use(Door);
    Check(!Evidence.Contains(TEXT("202_avoided")) && Door->Open,TEXT("reopening before reporting revokes the safe choice"));
    Door->SetDoor(false);Player->SetActorLocation(FVector(980,-135,410));Clear();Tick202Choice();Clear();
    Player->SetActorLocation(NRLayout::OfficePoint(FVector(85,-395,90)));Use(PC);
    Check(Evidence.Contains(TEXT("202_safe_report")) && !Evidence.Contains(TEXT("wake_trace")) && !ActiveVoice,TEXT("PC accepts a silent no-entry report without the mandatory nightmare item"));
    Clear();TickDemo(0);Check(PowerOut && !DreamActive,TEXT("safe report unlocks the next incident"));
    Clear();Use(Find(TEXT("spare_fuse")));Use(Find(TEXT("breaker")));Use(Find(TEXT("service_ledger")));Use(Find(TEXT("lost_tag")));Use(PC);
    Check(PowerRepaired && ReportFiled && Evidence.Contains(TEXT("night_report_safe")),TEXT("safe route reaches power repair and truthful main report"));
    Use(Find(TEXT("phone")));Clear();OpenComplaintLog();SelectComplaintKey(EKeys::One);Escape();
    Check(ComplaintLog.Plan==1,TEXT("safe route chooses testimony in notebook after manager call"));
    Use(Find(TEXT("cctv_power")));Clear();
    Use(Find(TEXT("door_105")));Clear();Use(Resident);
    Check(Evidence.Contains(TEXT("resident_203_safe")) && !ThreatPending && !Threat && ScareEvents.Contains(TEXT("202_pursuit_avoided")),TEXT("resident testimony acknowledges non-entry and its linked pursuit is avoided"));
    Check(!Documents.FindRef(TEXT("resident_203_safe")).Contains(TEXT("전 방에서 나오지 않았어요")) && SubtitleLines.ContainsByPredicate([](const FSubtitleLine& Line){return Line.Speaker==TEXT("나 · 독백");}),TEXT("safe testimony avoids the second-call contradiction and narration has its own label"));
    Clear();Use(Find(TEXT("sealed_panel")));Clear();DemoSeconds=MonitorOffAt+61;Use(Find(TEXT("cctv_power")));Clear();Use(PC);
    Check(DemoReady() && RoundFiled && !RoomEntered,TEXT("all late-game gates accept the safe route"));
    Clear();Red=true;Tick(0);Use(Find(TEXT("phone")));float Duration=0;for(const auto& Line:SubtitleLines)Duration+=Line.Duration;
    Tick(Duration+.1f);Check(Finished && Page.Contains(TEXT("들어가지 않고")),TEXT("safe route completes DAY1 without ever entering 202"));
    // Independent unsafe branch fixture: reading UV must not make entry harmless.
    Finished=false;EndingPending=false;Clear();Evidence.Reset();ScareEvents.Reset();Evidence.Add(TEXT("uv"));Evidence.Add(TEXT("minseo"));Evidence.Add(TEXT("physical"));
    RoomEntered=false;DreamActive=false;Threat=false;ThreatPending=false;PowerOut=false;PowerRepaired=false;ReportFiled=false;RoundFiled=false;PhoneStage=0;
    WakeTrace->SetActorHiddenInGame(true);Player->SetActorLocation(FVector(635,40,410));Door->SetDoor(true);Tick(0);
    Check(DreamActive && RoomEntered && !Evidence.Contains(TEXT("202_avoided")),TEXT("ignoring UV and crossing the threshold still triggers confinement"));
    Clear();TickDream(10);Clear();TickDream(10);Clear();TickDream(10);
    Check(Evidence.Contains(TEXT("dream_wake")) && !WakeTrace->IsHidden(),TEXT("unsafe branch retains the nightmare aftermath"));
    Clear();Evidence.Add(TEXT("manager_call"));Use(Resident);
    Check(ThreatPending && Evidence.Contains(TEXT("resident_203")),TEXT("unsafe branch retains its later pursuit"));
    // Real Minseo denies only the impersonator's second call, on every meeting route.
    auto Transcript=[this]{FString Text;for(const auto& Line:SubtitleLines)Text+=Line.Text;return Text.Replace(TEXT(" "),TEXT(""));};
    for(const TCHAR* Key:{TEXT("minseo"),TEXT("resident_203"),TEXT("resident_203_safe"),TEXT("final_minseo_located"),TEXT("final_minseo_rescued"),TEXT("final_minseo_waiting")}) {
        Evidence.Remove(TEXT("second_call"));Clear();ShowDocument(Key);
        Check(!Transcript().Contains(TEXT("전화요?")),TEXT("unheard second call never adds Minseo denial"));
        Evidence.Add(TEXT("second_call"));SaveCheckpoint();Evidence.Remove(TEXT("second_call"));RestoreCheckpoint();
        Clear();ShowDocument(Key);
        Check(Transcript().Contains(TEXT("전화요?저관리실에전화한적없는데요.202호문도안열었어요.")),TEXT("checkpoint-preserved second-call hearing adds Minseo denial"));
        Check(Evidence.Contains(Key) && !Evidence.Contains(FString(Key)+TEXT("_second_call")),TEXT("dialogue variants preserve canonical evidence and complaint keys"));
        Check(SubtitleLines.ContainsByPredicate([](const FSubtitleLine& Line){return Line.Text.StartsWith(TEXT("“전화요?")) && Line.Speaker!=TEXT("나 · 독백");}),TEXT("denial remains Minseo's spoken line"));
    }
    UE_LOG(LogTemp,Display,TEXT("NR_CHOICE202_COMPLETE failures=%d"),Failures);FPlatformMisc::RequestExitWithStatus(false,Failures?1:0);
}

void ANRGameMode::WithdrawalWalkTest()
{
    struct FState { FTimerHandle Timer; int32 Failures=0; float Time=0,DoneAt=0; FVector Start; bool Done=false; };
    auto S=MakeShared<FState>();
    auto Check=[S](bool OK,const TCHAR* Name){UE_LOG(LogTemp,Display,TEXT("NR_WITHDRAWAL %s %s"),OK?TEXT("PASS"):TEXT("FAIL"),Name);if(!OK)++S->Failures;};
    auto Key=[this](EInputEvent Event){auto* V=GetWorld()->GetGameViewport();V->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::W,Event,Event==IE_Pressed?1.f:0.f,1,FInputDeviceId::CreateFromInternalId(0),false,V->Viewport));};
    IntroComplete=true;FirstCall=99999;Page.Empty();Evidence.Add(TEXT("minseo"));
    Player->SetActorLocation(FVector(725,-153,410));Player->GetController()->SetIgnoreLookInput(true);
    Player->GetController()->SetControlRotation(FRotator(-18,90,0));Player->Camera->SetWorldRotation(FRotator(-18,90,0));Player->UVRemaining=45;Player->UV=true;
    Check(ReadUVClue(),TEXT("player scans the warning before walking away"));
    StopVoice();SubtitleLines.Reset();Notice.Empty();Player->UV=false;Player->GetController()->SetControlRotation(FRotator(0,0,0));S->Start=Player->GetActorLocation();Key(IE_Pressed);
    GetWorld()->GetTimerManager().SetTimer(S->Timer,[this,S,Check,Key]{
        S->Time+=.1f;
        if(!S->Done && (Evidence.Contains(TEXT("202_avoided")) || S->Time>6)) {
            Key(IE_Released);S->Done=true;S->DoneAt=S->Time;
            Check(Evidence.Contains(TEXT("202_avoided")) && FVector::Dist2D(S->Start,Player->GetActorLocation())>150,TEXT("real held-W movement triggers withdrawal on the built corridor"));
            Check(!DreamActive && !RoomEntered && Player->GetActorLocation().Z>350 && WakeTrace->IsHidden(),TEXT("choice preserves player location and avoids the mandatory awakening"));
            Check(ObjectiveText().Contains(TEXT("관리실 PC")) && !ObjectiveText().Contains(TEXT("들어가")),TEXT("actual walking changes the objective to office reporting"));
            Player->GetController<APlayerController>()->ConsoleCommand(TEXT("Shot SHOWUI"));
        }
        if(S->Done && S->Time>S->DoneAt+1) {
            const int32 Failures=S->Failures;FTimerHandle Timer=S->Timer;UE_LOG(LogTemp,Display,TEXT("NR_WITHDRAWAL_COMPLETE failures=%d"),Failures);
            GetWorld()->GetTimerManager().ClearTimer(Timer);FPlatformMisc::RequestExitWithStatus(false,Failures?1:0);
        }
    },.1f,true);
}
