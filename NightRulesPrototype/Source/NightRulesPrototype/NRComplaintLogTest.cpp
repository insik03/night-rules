#include "NRGame.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "HAL/PlatformMisc.h"

void ANRGameMode::ComplaintLogTest()
{
    int32 Failures=0;
    auto Check=[&](bool OK,const TCHAR* Name){UE_LOG(LogTemp,Display,TEXT("NR_COMPLAINT_LOG %s %s"),OK?TEXT("PASS"):TEXT("FAIL"),Name); if(!OK) ++Failures;};
    auto Find=[this](const TCHAR* Id)->ANRProp* { for(auto* P:Props) if(P->Id==Id) return P; return nullptr; };
    auto* Log=Find(TEXT("complaint_log")); auto* Desk=Find(TEXT("desk")); auto* PC=Find(TEXT("roster"));
    Check(Log && Desk && PC,TEXT("logbook prop and desk exist"));
    if(Log && Desk) {
        const FBox B=Log->Mesh->Bounds.GetBox(), D=Desk->Mesh->Bounds.GetBox();
        Check(FMath::Abs(B.Min.Z-D.Max.Z-.05f)<.3f && B.Min.X>=D.Min.X && B.Max.X<=D.Max.X && B.Min.Y>=D.Min.Y && B.Max.Y<=D.Max.Y,TEXT("PlaceOn seats full logbook on desk"));
        bool Clear=true;
        for(auto* P:Props) if(P->Id==TEXT("phone") || P->Id==TEXT("roster") || P->Id==TEXT("cctv") || P->Id.StartsWith(TEXT("cctv_display_")) || P->Id==TEXT("note") || P->Id==TEXT("cctv_power") || P->Id==TEXT("wake_trace") || P->Sliding)
        {
            const bool Overlap=B.Intersect(P->Mesh->Bounds.GetBox());
            if(Overlap) UE_LOG(LogTemp,Warning,TEXT("NR_COMPLAINT_LOG overlap: %s"),*P->Id);
            Clear &= !Overlap;
        }
        Check(Clear,TEXT("logbook clears phone monitors notes drawers switch and handle fragment"));
        const FVector Eye=NRLayout::OfficePoint(FVector(-57,-432,149)), Aim=B.GetCenter(); FHitResult Hit; FCollisionQueryParams Query; Query.bTraceComplex=true; Query.AddIgnoredActor(Player);
        GetWorld()->LineTraceSingleByChannel(Hit,Eye,Aim+(Aim-Eye).GetSafeNormal()*5,ECC_Visibility,Query);
        Check(Hit.GetActor()==Log && FVector::Dist(Eye,Aim)<260,TEXT("standing eye interaction trace reaches logbook"));
    }
    if(auto* OfficeDoor=Find(TEXT("door_office"))) {
        OfficeDoor->SetDoor(true); OfficeDoor->Tick(1.f);
        FHitResult Hit; FCollisionQueryParams Query; Query.bTraceComplex=true; Query.AddIgnoredActor(Player);
        const bool Blocked=GetWorld()->SweepSingleByChannel(Hit,FVector(NRLayout::OfficeDoorX,-370,90),FVector(NRLayout::OfficeDoorX,-650,90),FQuat::Identity,ECC_Pawn,FCollisionShape::MakeCapsule(28,85),Query);
        Check(!Blocked,TEXT("player capsule can enter relocated office beside the desk"));
        OfficeDoor->SetDoor(false); OfficeDoor->Tick(1.f);
    }
    FirstCall=8; Elapsed=FirstCall; IntroComplete=true; IntroCallPending=false; PhoneStage=AnsweredStage=1;
    for(const TCHAR* Blocker:{TEXT("minseo"),TEXT("dream_wake"),TEXT("202_avoided")}) {
        Evidence.Add(Blocker);Elapsed=FirstCall+SecondCall;PhoneStage=1;Tick(0);
        Check(PhoneStage==1,TEXT("second call does not ring after contact awakening or withdrawal"));Evidence.Remove(Blocker);
    }
    Tick(0);Check(PhoneStage==2,TEXT("second call rings on untouched route"));
    PhoneStage=AnsweredStage=1;Elapsed=FirstCall;
    ShowDocument(TEXT("first_call"));
    Check(ComplaintLog.Rows.IsEmpty(),TEXT("receipt waits until call finishes"));
    float Duration=0; for(const auto& Line:SubtitleLines) Duration+=Line.Duration;
    Tick(Duration+.1f);
    Check(ComplaintLog.Rows.Num()==1 && !ComplaintLog.Rows[0].Written && ComplaintLog.Rows[0].Time==TEXT("02:13"),TEXT("completed call creates blank at receipt clock time"));
    Check(ObjectiveText().Contains(TEXT("민원 장부에 호수와 시간을 적자")),TEXT("first call changes objective to actual handwriting"));
    if(PC) Use(PC);
    Check(!ReportFiled && !Evidence.Contains(TEXT("night_report")),TEXT("PC cannot replace mandatory first writing"));
    if(Log) Use(Log); else OpenComplaintLog();
    Check(Page.Contains(TEXT("__:__ / ___호 / ______")) && ComplaintView,TEXT("E opens enlarged notebook with blanks and choices"));
    SelectComplaintKey(EKeys::Two);
    Check(ComplaintStep==1 && !FirstComplaintWritten(),TEXT("room choice alone does not finish line"));
    SelectComplaintKey(EKeys::Three); TickComplaintLog(.05f);
    Check(ComplaintWriting!=INDEX_NONE && ComplaintLog.Rows[0].InkChars==1 && !FirstComplaintWritten(),TEXT("ink reveals one character per 0.05 seconds"));
    TickComplaintLog(10);
    Check(FirstComplaintWritten() && Evidence.Contains(TEXT("complaint_choice_first_call_room_2")) && Evidence.Contains(TEXT("complaint_choice_first_call_content_3")),TEXT("any room and content choice completes without truth grading"));
    const FString Chosen=ComplaintLog.Rows[0].Room;
    Check(!ComplaintPlanning && !Page.Contains(TEXT("[4]")) && !Page.Contains(TEXT("105호와 203호")),TEXT("first receipt does not reveal manager investigation options"));
    SelectComplaintKey(EKeys::Four);SelectInvestigationPlan(1);
    Check(!ComplaintPlanning && ComplaintLog.Plan==0,TEXT("key four and direct selection cannot bypass manager call"));
    Evidence.Add(TEXT("manager_call"));SelectComplaintKey(EKeys::Four);
    Check(ComplaintPlanning && Page.Contains(TEXT("105호와 203호")),TEXT("manager call enables investigation options"));
    SelectComplaintKey(EKeys::One);
    Check(ComplaintLog.Plan==1 && !ComplaintPlanning,TEXT("number key writes the chosen investigation plan"));
    Escape();
    ShowDocument(TEXT("first_call")); FinishComplaintDialogue();
    Check(ComplaintLog.Rows.Num()==1,TEXT("rereading a conversation does not duplicate blank"));
    ShowDocument(TEXT("resident_104")); FinishComplaintDialogue();
    Check(ComplaintLog.Rows.Num()==2 && FirstComplaintWritten() && !ComplaintLog.Rows[1].Written,TEXT("later complaints leave optional blank without blocking"));
    OpenComplaintLog(); SelectComplaintKey(EKeys::One); SelectComplaintKey(EKeys::One); TickComplaintLog(.1f); Escape();
    Check(!ComplaintLog.Rows[1].Written && ComplaintLog.Rows[1].InkChars==0,TEXT("closing unfinished handwriting cancels its ink"));
    SaveCheckpoint(); ComplaintLog.Rows.Reset(); RestoreCheckpoint();
    Check(ComplaintLog.Rows.Num()==2 && ComplaintLog.Rows[0].Room==Chosen && !ComplaintLog.Rows[1].Written,TEXT("checkpoint restores chosen line and optional blank"));
    PowerRepaired=true; Evidence.Add(TEXT("service_ledger")); Evidence.Add(TEXT("lost_tag"));
    if(PC) Use(PC);
    const FString Report=ComplaintLog.Reports.FindRef(TEXT("night_report"));
    Check(ReportFiled && Report.Contains(Chosen) && Report.Contains(TEXT("확인 불가")) && !Report.Contains(TEXT("{{complaints}}")) && !Report.Contains(TEXT("발신자의 증언과")),TEXT("PC report renders player choices rather than preset 203 verdict"));
    OpenComplaintLog(); Check(!ComplaintLog.AnomalySeen,TEXT("no anomaly before the fixed 202 milestone")); Escape();
    ShowDocument(TEXT("202_safe_report"));
    Check(ComplaintLog.AnomalyReady && !ComplaintLog.AnomalySeen,TEXT("no-entry report arms but does not show anomaly"));
    OpenComplaintLog();
    Check(ComplaintLog.Rows.Num()==3 && ComplaintLog.Rows[1].Unauthored && ComplaintLog.Rows[1].Content==ComplaintClock()+TEXT(" / 202호 / 총무 입실.") && ComplaintWriting==INDEX_NONE,TEXT("safe-route contradiction uses current shift time below last player line"));
    Escape(); RestoreCheckpoint(); OpenComplaintLog();
    Check(ComplaintLog.Rows.Num()==3 && Evidence.Contains(TEXT("complaint_anomaly")),TEXT("reopening and checkpoint restore never add a second anomaly"));
    Check(!ComplaintReportText(Documents[TEXT("round_complete")]).Contains(TEXT("총무 입실")),TEXT("report excludes unauthored line and optional blank"));
    Escape(); OpenJournal(); Check(Page.Contains(Chosen) && Page.Contains(TEXT("총무 입실")) && Page.Contains(TEXT("__:__ / ___호 / ______")),TEXT("J shows player line unauthored line and pending blank")); Escape();
    // Independent entered-route fixture, retaining the player's actual completed first row.
    ComplaintLog.Rows.RemoveAt(1); ComplaintLog.AnomalySeen=false; ComplaintLog.AnomalyReady=false;
    ShowDocument(TEXT("dream_wake")); OpenComplaintLog();
    Check(ComplaintLog.Rows[1].Content==ComplaintClock()+TEXT(" / 202호 / 총무 입실. 문 닫힘. 안에서 대답함."),TEXT("awakening anomaly uses current time without a future timestamp"));
    Escape();Evidence.Remove(TEXT("service_ledger"));ComplaintLog.LedgerLine.Empty();
    ShowDocument(TEXT("service_ledger"));
    Check(Page.Contains(TEXT("과거 점검 기록")) && !Page.Contains(TEXT("오늘 /")) && ComplaintLog.LedgerLine.IsEmpty(),TEXT("first ledger opening has historical records only"));Escape();
    ShowDocument(TEXT("service_ledger"));const FString Ledger=Page;
    Check(Page.Contains(TEXT("오늘 / ")+ComplaintLog.Rows[0].Time) && Page.Contains(TEXT("필체가 내 민원 장부와 같다")),TEXT("second ledger opening adds the actual first receipt time"));Escape();
    ShowDocument(TEXT("service_ledger"));Check(Page==Ledger,TEXT("third ledger opening never duplicates the new line"));Escape();
    ComplaintLog.LedgerLine.Empty();RestoreCheckpoint();ShowDocument(TEXT("service_ledger"));
    Check(Page==Ledger,TEXT("checkpoint retains the ledger line and prevents regeneration"));Escape();
    FComplaintRow ParticleRow;ParticleRow.Written=true;ParticleRow.Room=TEXT("203호");ParticleRow.Time=ComplaintClock();
    const auto SavedRows=ComplaintLog.Rows;
    for(const FString& Content:TArray<FString>{TEXT("의자 끄는 소리"),TEXT("확인 불가"),TEXT("물"),TEXT("잠금")}) {
        ParticleRow.Content=Content;ComplaintLog.Rows={ParticleRow};
        const FString Expected=Content==TEXT("잠금")?TEXT("잠금으로"):Content+TEXT("로");
        Check(ComplaintReportText(TEXT("{{complaints}}")).Contains(Expected),TEXT("report chooses ro euro and rieul exception"));
    }
    ComplaintLog.Rows=SavedRows;
    UE_LOG(LogTemp,Display,TEXT("NR_COMPLAINT_LOG_COMPLETE failures=%d"),Failures);
    FPlatformMisc::RequestExitWithStatus(false,Failures?1:0);
}

void ANRGameMode::InvestigationPlanTest()
{
    int32 Failures=0;
    auto Check=[&](bool OK,const TCHAR* Name){UE_LOG(LogTemp,Display,TEXT("NR_INVESTIGATION_PLAN %s %s"),OK?TEXT("PASS"):TEXT("FAIL"),Name);if(!OK)++Failures;};
    auto Find=[this](const TCHAR* Id)->ANRProp*{for(auto* P:Props)if(P->Id==Id)return P;return nullptr;};
    auto Clear=[this]{StopVoice();SubtitleLines.Reset();Notice.Empty();Page.Empty();};
    SaveCheckpoint();
    const auto FreshCheckpoint=Checkpoint;
    const auto FreshComplaint=ComplaintCheckpoint;
    const auto FreshFinale=FinaleCheckpoint;
    FirstCall=99999;IntroComplete=true;IntroCallPending=false;Clear();
    auto* PC=Find(TEXT("roster"));auto* Monitor=Find(TEXT("cctv_display_2"));
    Check(PC && Monitor,TEXT("report terminal and second-floor monitor exist"));
    if(!PC || !Monitor){FPlatformMisc::RequestExitWithStatus(false,1);return;}
    // Establish a real completed receipt through the same notebook controls.
    ShowDocument(TEXT("first_call"));FinishComplaintDialogue();Clear();OpenComplaintLog();
    SelectComplaintKey(EKeys::One);SelectComplaintKey(EKeys::One);TickComplaintLog(10);
    SelectComplaintKey(EKeys::Two);Check(ComplaintLog.Plan==0,TEXT("planning is unavailable before manager call"));Escape();
    RecordTimer=0;TickDisplays(.51f);RecordTimer=0;TickDisplays(.51f);
    Use(Monitor);ReplayCCTV(0);
    Check(!Evidence.Contains(TEXT("log_recording_reviewed")),TEXT("early replay cannot satisfy later investigation"));Escape();
    PowerRepaired=true;ReportFiled=true;CCTVReset=true;Evidence.Add(TEXT("manager_call"));
    OpenComplaintLog();SelectComplaintKey(EKeys::Two);Escape();
    Check(ComplaintLog.Plan==2,TEXT("notebook number choice sets technical route after manager call"));
    Use(PC);Check(!RoundFiled,TEXT("technical report rejected without inspection and replay"));Clear();
    Use(Find(TEXT("sealed_panel")));Clear();Use(Monitor);ReplayCCTV(1);
    Check(!Evidence.Contains(TEXT("log_recording_reviewed")),TEXT("latest frame alone is not a rewind"));
    ReplayCCTV(0);Escape();
    Check(Evidence.Contains(TEXT("log_recording_reviewed")),TEXT("actual previous-frame viewing records inspection"));
    Use(PC);
    Check(RoundFiled && DemoReady() && !Evidence.Contains(TEXT("resident_105")) && !Evidence.Contains(TEXT("resident_203")) && !ThreatPending,TEXT("technical route reaches final call without resident revisit or its pursuit"));
    Check(ComplaintLog.Reports.FindRef(TEXT("round_complete")).Contains(TEXT("2층 녹화")) && !ComplaintLog.Reports.FindRef(TEXT("round_complete")).Contains(TEXT("105호: 문밖")),TEXT("report contains only actually gathered findings"));
    SelectInvestigationPlan(1);Check(ComplaintLog.Plan==2,TEXT("filed plan cannot be changed retrospectively"));
    // Independent witness fixture, preserving the receipt but removing technical findings.
    RoundFiled=false;Clear();Evidence.Remove(TEXT("sealed_panel"));Evidence.Remove(TEXT("log_recording_reviewed"));
    OpenComplaintLog();SelectComplaintKey(EKeys::Four);SelectComplaintKey(EKeys::One);Escape();
    Check(ComplaintLog.Plan==1,TEXT("notebook key four allows a pre-report change"));
    Use(Find(TEXT("door_105")));Clear();Use(PC);Check(!RoundFiled,TEXT("one testimony cannot complete witness route"));Clear();
    Evidence.Add(TEXT("202_avoided"));Use(Find(TEXT("door_203")));Clear();
    // Prevent the safe-entry report from intercepting this late-round test fixture.
    Evidence.Add(TEXT("202_safe_report"));Use(PC);
    Check(RoundFiled && !Evidence.Contains(TEXT("sealed_panel")) && !Evidence.Contains(TEXT("log_recording_reviewed")),TEXT("witness route completes without technical findings"));
    RoundFiled=false;Clear();OpenComplaintLog();SelectComplaintKey(EKeys::Four);SelectComplaintKey(EKeys::Three);Escape();
    Use(PC);Check(!RoundFiled,TEXT("combined route rejects testimony alone"));Clear();
    Use(Find(TEXT("sealed_panel")));Clear();Use(Monitor);ReplayCCTV(0);Escape();
    CCTVReset=false;Use(PC);Check(!RoundFiled,TEXT("all plans still require restoring CCTV power"));Clear();CCTVReset=true;
    SaveCheckpoint();ComplaintLog.Plan=0;RestoreCheckpoint();
    Check(ComplaintLog.Plan==3 && InvestigationPlanComplete(),TEXT("checkpoint preserves plan and gathered findings"));
    SelectInvestigationPlan(0);SelectInvestigationPlan(4);Check(ComplaintLog.Plan==3,TEXT("invalid choices cannot erase plan"));
    Use(PC);Check(RoundFiled && DemoReady(),TEXT("combined route accepts testimony and technical investigation"));
    // Independent progression fixtures use production interactions and notebook
    // keys. Spatial traversal is covered separately by the held-W walk tests.
    auto Listen=[this]{
        if(!Page.IsEmpty())Escape();
        for(int32 Pass=0;Pass<10 && !SubtitleLines.IsEmpty();++Pass) {
            float Remaining=MessageTime;
            for(int32 I=SubtitleIndex+1;I<SubtitleLines.Num();++I)Remaining+=SubtitleLines[I].Duration;
            Tick(Remaining+.01f);
            if(!Page.IsEmpty())break;
        }
    };
    for(bool Entered:{false,true}) for(int32 Plan:{1,2,3}) {
        Checkpoint=FreshCheckpoint;ComplaintCheckpoint=FreshComplaint;FinaleCheckpoint=FreshFinale;RestoreCheckpoint();
        FirstCall=8;Tick(8);Use(Find(TEXT("phone")));Listen();
        OpenComplaintLog();SelectComplaintKey(EKeys::One);SelectComplaintKey(EKeys::One);TickComplaintLog(10);Escape();
        Check(FirstComplaintWritten() && ComplaintLog.Plan==0,TEXT("route fixture writes receipt before manager planning"));
        // Record genuine pre-report CCTV frames for the later rewind.
        RecordTimer=0;TickDisplays(.51f);RecordTimer=0;TickDisplays(.51f);
        Player->SetActorLocation(FVector(865,-135,410));Use(Find(TEXT("door_203")));Listen();
        Player->SetActorLocation(FVector(635,-135,410));Use(Find(TEXT("door_202")));Listen();
        if(Entered) {
            Use(Find(TEXT("door_202")));Player->SetActorLocation(FVector(635,40,410));Tick(0);
            for(int32 I=0;I<400 && DreamActive;++I)Tick(.25f);
            Check(Evidence.Contains(TEXT("dream_wake")),TEXT("entered route reaches awakening through nightmare ticks"));
            Listen();Use(Find(TEXT("wake_trace")));Listen();
        } else {
            Player->SetActorLocation(FVector(980,-135,410));Tick202Choice();Listen();
            Player->SetActorLocation(NRLayout::OfficePoint(FVector(85,-395,90)));Use(PC);Listen();
            Check(Evidence.Contains(TEXT("202_safe_report")) && !RoomEntered,TEXT("avoided route files actual no-entry report"));
        }
        Use(Find(TEXT("spare_fuse")));Listen();Use(Find(TEXT("breaker")));Listen();
        Use(Find(TEXT("service_ledger")));Listen();Use(Find(TEXT("lost_tag")));Listen();Use(PC);Listen();
        Check(ReportFiled && PowerRepaired,TEXT("each route repairs power and files first report"));
        Use(Find(TEXT("phone")));Listen();OpenComplaintLog();
        SelectComplaintKey(Plan==1?EKeys::One:Plan==2?EKeys::Two:EKeys::Three);Escape();
        Check(ComplaintLog.Plan==Plan,TEXT("each route selects its plan using notebook number key"));
        if(Plan!=1){Use(Find(TEXT("sealed_panel")));Listen();Use(Monitor);ReplayCCTV(0);Escape();}
        Use(Find(TEXT("cctv_power")));Listen();
        if(Plan!=2) {
            Use(Find(TEXT("door_105")));Listen();
            Player->SetActorLocation(NRLayout::OfficePoint(FVector(85,-395,90)));
            Use(Find(TEXT("door_203")));Listen();
            // Leaving before the audible prelude is a production escape condition.
            TickPrelude(3.1f);
        }
        for(int32 I=0;I<61;++I)Tick(1);
        Use(Find(TEXT("cctv_power")));Listen();Use(PC);
        Check(DemoReady() && RoundFiled && !Dead,TEXT("each entry and plan combination clears late-game gates"));
        if(Plan==2)Check(!Evidence.Contains(TEXT("resident_105")) && !Evidence.Contains(TEXT("resident_203")) && !Evidence.Contains(TEXT("resident_203_safe")),TEXT("technical completion never fabricates revisits"));
        SelectInvestigationPlan(Plan==1?2:1);Check(ComplaintLog.Plan==Plan,TEXT("submitted plan stays immutable on every route"));
        Player->SetActorLocation(NRLayout::OfficePoint(FVector(85,-395,90)));Tick(0);Use(Find(TEXT("phone")));Listen();
        const bool Completed=Finished && Evidence.Contains(TEXT("final_call")) && RoomEntered==Entered;
        UE_LOG(LogTemp,Display,TEXT("NR_DAY1_ROUTE entered=%d plan=%d finished=%d failures=%d"),Entered,Plan,Completed,Completed?0:1);
        Check(Completed,TEXT("all entry and investigation plans finish DAY1 through final voiced call"));
    }
    UE_LOG(LogTemp,Display,TEXT("NR_INVESTIGATION_PLAN_COMPLETE failures=%d"),Failures);
    FPlatformMisc::RequestExitWithStatus(false,Failures?1:0);
}
