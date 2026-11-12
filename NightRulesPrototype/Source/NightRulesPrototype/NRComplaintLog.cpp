#include "NRGame.h"
#include "NRMechanics.h"
#include "Components/AudioComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Components/InputComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "Widgets/Layout/SScrollBox.h"

void ANRGameMode::SetupComplaintLog()
{
    auto* Log=Prop(TEXT("complaint_log"),TEXT("민원 장부 쓰기"),FVector::ZeroVector,FVector(30,22,2));
    Log->SetActorRotation(FRotator(0,180,0)); Log->Label->SetVisibility(false);
    // Clear writing area between the two displays.
    for(auto* P:Props) if(P->Id==TEXT("desk")) { PlaceOn(Log,P,FVector2D(0,-249)); break; }
    ComplaintPenSound=LoadObject<USoundBase>(nullptr,TEXT("/Game/Audio/pen_scratch.pen_scratch"));
    if(auto* PC=Player->GetController<APlayerController>()) if(PC->InputComponent)
    {
        PC->InputComponent->BindKey(EKeys::One,IE_Pressed,this,&ANRGameMode::SelectComplaintKey);
        PC->InputComponent->BindKey(EKeys::Two,IE_Pressed,this,&ANRGameMode::SelectComplaintKey);
        PC->InputComponent->BindKey(EKeys::Three,IE_Pressed,this,&ANRGameMode::SelectComplaintKey);
        PC->InputComponent->BindKey(EKeys::Four,IE_Pressed,this,&ANRGameMode::SelectComplaintKey);
    }
}

FString ANRGameMode::ComplaintClock() const
{
    return ShiftClock(Elapsed);
}

FString ANRGameMode::ShiftClock(float At,bool Seconds) const
{
    const int32 Clock=NRMechanics::ShiftClockSeconds(At,FirstCall);
    return Seconds?FString::Printf(TEXT("%02d:%02d:%02d"),(Clock/3600)%24,(Clock/60)%60,Clock%60)
        :FString::Printf(TEXT("%02d:%02d"),(Clock/3600)%24,(Clock/60)%60);
}

FString ANRGameMode::ServiceLedgerText()
{
    // First opening is historical. The second opening adds one persistent line.
    if(Evidence.Contains(TEXT("service_ledger")) && ComplaintLog.LedgerLine.IsEmpty()) {
        for(const auto& Row:ComplaintLog.Rows) if(Row.Source==TEXT("first_call")) {
            ComplaintLog.LedgerLine=Documents.FindRef(TEXT("service_ledger_new")).Replace(TEXT("{{time}}"),*Row.Time);
            Record(TEXT("ledger_new_line"),ComplaintLog.LedgerLine);
            break;
        }
    }
    return Documents.FindRef(TEXT("service_ledger"))+(ComplaintLog.LedgerLine.IsEmpty()?FString():TEXT("\n\n")+ComplaintLog.LedgerLine);
}

void ANRGameMode::BeginComplaintDialogue(const FString& Key)
{
    if(ComplaintLog.Sources.Contains(Key)) return;
    if(!Documents.Contains(TEXT("complaint_rooms_")+Key)) return;
    // Capture receipt time now; creating the blank waits until the dialogue ends.
    ComplaintLog.PendingSource=Key; ComplaintLog.PendingTime=ComplaintClock();
}

void ANRGameMode::FinishComplaintDialogue()
{
    const FString Key=ComplaintLog.PendingSource, Time=ComplaintLog.PendingTime;
    if(Key.IsEmpty()) return;
    ComplaintLog.PendingSource.Empty(); ComplaintLog.PendingTime.Empty();
    if(ComplaintLog.Sources.Contains(Key)) return;
    FComplaintRow Row; Row.Source=Key; Row.Time=Time;
    // Option data lives in day1.json so all player-facing text has a single authoring source.
    TArray<FString> Rooms, Contents;
    Documents.FindRef(TEXT("complaint_rooms_")+Key).ParseIntoArrayLines(Rooms,true);
    Documents.FindRef(TEXT("complaint_contents_")+Key).ParseIntoArrayLines(Contents,true);
    Row.Rooms=Rooms; Row.Contents=Contents;
    ComplaintLog.PendingSource.Empty(); ComplaintLog.PendingTime.Empty();
    if(Row.Rooms.Num()!=3 || Row.Contents.Num()!=3) return;
    ComplaintLog.Rows.Add(Row); ComplaintLog.Sources.Add(Key);
    Evidence.Add(TEXT("complaint_blank_")+Key);
    Record(TEXT("complaint_blank"),Key+TEXT(" / ")+Time);
}

bool ANRGameMode::FirstComplaintWritten() const
{
    return ComplaintLog.Rows.ContainsByPredicate([](const FComplaintRow& Row){return Row.Source==TEXT("first_call") && Row.Written && !Row.Unauthored;});
}
bool ANRGameMode::FirstComplaintRequired() const
{
    return Evidence.Contains(TEXT("first_call")) && !FirstComplaintWritten();
}

void ANRGameMode::ArmComplaintAnomaly(bool Entered)
{
    if(ComplaintLog.AnomalyReady || ComplaintLog.AnomalySeen) return;
    ComplaintLog.AnomalyReady=true; ComplaintLog.Entered=Entered;
    Record(TEXT("complaint_anomaly"),Entered?TEXT("armed_after_awakening"):TEXT("armed_after_no_entry_report"));
}

void ANRGameMode::OpenComplaintLog()
{
    CCTVView=false; RulesView=false; PaperView=false; ComplaintView=true;
    Evidence.Add(TEXT("complaint_log")); Record(TEXT("read"),TEXT("complaint_log"));
    if(ComplaintLog.AnomalyReady && !ComplaintLog.AnomalySeen && FirstComplaintWritten())
    {
        int32 Last=INDEX_NONE;
        for(int32 I=0;I<ComplaintLog.Rows.Num();++I) if(ComplaintLog.Rows[I].Written && !ComplaintLog.Rows[I].Unauthored) Last=I;
        FComplaintRow Row; Row.Source=TEXT("anomaly"); Row.Written=true; Row.Unauthored=true;
        const FString Key=ComplaintLog.Entered?TEXT("complaint_anomaly_entered"):TEXT("complaint_anomaly_avoided");
        Row.Time=ComplaintClock(); Row.Content=Documents.FindRef(Key).Replace(TEXT("{{time}}"),*Row.Time); Row.InkChars=Row.Content.Len();
        ComplaintLog.Rows.Insert(Row,Last+1); ComplaintLog.AnomalySeen=true;
        Evidence.Add(TEXT("complaint_anomaly")); Record(TEXT("complaint_anomaly"),Row.Content);
        SaveCheckpoint();
        if(ComplaintPenSound) {
            ComplaintPen=UGameplayStatics::SpawnSound2D(this,ComplaintPenSound,.35f);
            ComplaintPenTime=.3f;
        }
    }
    ComplaintEditing=INDEX_NONE; ComplaintStep=0;
    ComplaintPlanning=FirstComplaintWritten() && Evidence.Contains(TEXT("manager_call")) && ComplaintLog.Plan==0;
    // The opening call remains the required line even if another optional complaint arrived first.
    for(int32 I=0;I<ComplaintLog.Rows.Num();++I) if(!ComplaintLog.Rows[I].Written && ComplaintLog.Rows[I].Source==TEXT("first_call")) { ComplaintEditing=I; break; }
    if(ComplaintEditing==INDEX_NONE) for(int32 I=0;I<ComplaintLog.Rows.Num();++I) if(!ComplaintLog.Rows[I].Written) { ComplaintEditing=I; break; }
    Page=ComplaintLogText(true);
    if(DocumentScroll) DocumentScroll->ScrollToStart();
}

FString ANRGameMode::ComplaintLogText(bool Choices) const
{
    FString Text=TEXT("내 민원 장부 — 오늘\n\n");
    for(const auto& Row:ComplaintLog.Rows) {
        if(Row.Unauthored) Text+=Row.Content;
        else if(Row.Written) Text+=Row.Time+TEXT(" / ")+Row.Room+TEXT(" / ")+Row.Content;
        else if(Row.InkChars>0) Text+=(Row.Time+TEXT(" / ")+Row.Room+TEXT(" / ")+Row.Content).Left(Row.InkChars);
        else Text+=TEXT("__:__ / ___호 / ______");
        Text+=TEXT("\n");
    }
    if(ComplaintLog.Rows.IsEmpty()) Text+=TEXT("아직 접수한 민원이 없다.\n");
    Text+=TEXT("\n후속 조사 방침: ")+InvestigationPlanName()+TEXT("\n");
    if(Choices && ComplaintPlanning && !RoundFiled) {
        Text+=Documents.FindRef(TEXT("log_plan_choices"));
    }
    else if(Choices && ComplaintWriting!=INDEX_NONE) Text+=TEXT("\n펜으로 기입하는 중…");
    else if(Choices && ComplaintLog.Rows.IsValidIndex(ComplaintEditing)) {
        const auto& Row=ComplaintLog.Rows[ComplaintEditing];
        FString Title=Documents.FindRef(Row.Source); int32 End=0; if(Title.FindChar(TEXT('\n'),End)) Title=Title.Left(End);
        Text+=TEXT("\n기입할 민원: ")+Title+TEXT("\n")+(ComplaintStep==0?TEXT("호수 선택"):TEXT("내용 선택"));
        if(ComplaintStep==1) Text+=TEXT(" · ")+Row.Room;
        const auto& Options=ComplaintStep==0?Row.Rooms:Row.Contents;
        for(int32 I=0;I<Options.Num();++I) Text+=FString::Printf(TEXT("\n[%d] %s"),I+1,*Options[I]);
        Text+=TEXT("\n시각은 접수 당시의 시계로 기입한다.");
    } else if(Choices) Text+=TEXT("\n접수한 민원을 모두 기입했다.");
    if(Choices && FirstComplaintWritten() && Evidence.Contains(TEXT("manager_call")) && !RoundFiled && !ComplaintPlanning && ComplaintWriting==INDEX_NONE)Text+=TEXT("\n[4] 후속 조사 방침 작성·수정");
    return Text;
}

void ANRGameMode::SelectComplaint(int32 Choice)
{
    if(ComplaintView && ComplaintPlanning && !Paused && !Dead && !Finished) { SelectInvestigationPlan(Choice+1); return; }
    if(!ComplaintView || Page.IsEmpty() || Paused || Dead || Finished || ComplaintWriting!=INDEX_NONE || !ComplaintLog.Rows.IsValidIndex(ComplaintEditing)) return;
    auto& Row=ComplaintLog.Rows[ComplaintEditing];
    const auto& Options=ComplaintStep==0?Row.Rooms:Row.Contents;
    if(!Options.IsValidIndex(Choice)) return;
    Evidence.Add(FString::Printf(TEXT("complaint_choice_%s_%s_%d"),*Row.Source,ComplaintStep==0?TEXT("room"):TEXT("content"),Choice+1));
    Record(TEXT("complaint_choice"),Row.Source+TEXT(" / ")+(ComplaintStep==0?TEXT("room / "):TEXT("content / "))+Options[Choice]);
    if(ComplaintStep==0) { Row.Room=Options[Choice]; ComplaintStep=1; }
    else {
        Row.Content=Options[Choice]; ComplaintWriting=ComplaintEditing; ComplaintInkTime=0;
        if(ComplaintPen) { ComplaintPen->Stop(); ComplaintPen=nullptr; }
        if(ComplaintPenSound) ComplaintPen=UGameplayStatics::SpawnSound2D(this,ComplaintPenSound,.35f);
        ComplaintPenTime=0;
    }
    Page=ComplaintLogText(true);
}

void ANRGameMode::SelectComplaintKey(FKey Key)
{
    if(Key==EKeys::Four) {
        if(ComplaintView && !Paused && !Dead && !Finished && !RoundFiled && FirstComplaintWritten() && Evidence.Contains(TEXT("manager_call")) && ComplaintWriting==INDEX_NONE) {ComplaintPlanning=true;Page=ComplaintLogText(true);if(DocumentScroll)DocumentScroll->ScrollToEnd();}
        return;
    }
    SelectComplaint(Key==EKeys::One?0:Key==EKeys::Two?1:2);
}

void ANRGameMode::TickComplaintLog(float Delta)
{
    if(Paused || Dead || Finished) return;
    if(ComplaintPenTime>0) {
        ComplaintPenTime-=Delta;
        if(ComplaintPenTime<=0 && ComplaintPen) { ComplaintPen->Stop(); ComplaintPen=nullptr; }
    }
    if(!ComplaintView || Page.IsEmpty() || !ComplaintLog.Rows.IsValidIndex(ComplaintWriting)) return;
    auto& Row=ComplaintLog.Rows[ComplaintWriting];
    const FString Line=Row.Time+TEXT(" / ")+Row.Room+TEXT(" / ")+Row.Content;
    ComplaintInkTime+=FMath::Max(0.f,Delta);
    const int32 Count=FMath::FloorToInt(ComplaintInkTime/.05f);
    Row.InkChars=FMath::Min(Line.Len(),Count);
    if(ComplaintPenSound && Row.InkChars<Line.Len() && (!ComplaintPen || !ComplaintPen->IsPlaying()))
        ComplaintPen=UGameplayStatics::SpawnSound2D(this,ComplaintPenSound,.35f);
    if(Row.InkChars==Line.Len()) {
        Row.Written=true;
        Evidence.Add(TEXT("complaint_written_")+Row.Source);
        Record(TEXT("complaint_written"),Row.Source+TEXT(" / ")+Line);
        ComplaintWriting=INDEX_NONE;
        if(ComplaintPen) { ComplaintPen->Stop(); ComplaintPen=nullptr; }
        if(Row.Source==TEXT("first_call")) {
            for(auto* P:Props) if(P->Id==TEXT("door_office")) P->SetDoor(true);
            ComplaintPlanning=Evidence.Contains(TEXT("manager_call")) && ComplaintLog.Plan==0;
        }
        ComplaintEditing=INDEX_NONE; ComplaintStep=0;
        for(int32 I=0;I<ComplaintLog.Rows.Num();++I) if(!ComplaintLog.Rows[I].Written) { ComplaintEditing=I; break; }
        // Save after the full physical act, before leaving the office.
        SaveCheckpoint();
    }
    Page=ComplaintLogText(true);
}

void ANRGameMode::CloseComplaintLog()
{
    if(ComplaintPen) { ComplaintPen->Stop(); ComplaintPen=nullptr; }
    ComplaintPenTime=0;
    if(ComplaintLog.Rows.IsValidIndex(ComplaintWriting)) {
        auto& Row=ComplaintLog.Rows[ComplaintWriting];
        Row.InkChars=0; Row.Room.Empty(); Row.Content.Empty();
    }
    ComplaintWriting=ComplaintEditing=INDEX_NONE; ComplaintStep=0; ComplaintInkTime=0; ComplaintView=false; ComplaintPlanning=false;
}

bool ANRGameMode::IsComplaintReport(const FString& Key) const
{
    return Key==TEXT("night_report") || Key==TEXT("night_report_safe") || Key==TEXT("202_safe_report") || Key==TEXT("round_complete");
}

FString ANRGameMode::ComplaintReportText(const FString& Template) const
{
    FString Rows;
    for(const auto& Row:ComplaintLog.Rows) if(Row.Written && !Row.Unauthored)
        Rows+=Row.Time+TEXT(" 접수. ")+Row.Room+TEXT(" — ")+Row.Content+(NRMechanics::NeedsEuro(Row.Content.IsEmpty()?0:Row.Content[Row.Content.Len()-1])?TEXT("으로"):TEXT("로"))+TEXT(" 장부에 기록했다.\n");
    if(Rows.IsEmpty()) Rows=TEXT("기입한 민원 없음.\n");
    FString Findings=TEXT("조사 방침: ")+InvestigationPlanName()+TEXT("\n");
    if(Evidence.Contains(TEXT("resident_105")))Findings+=TEXT("105호: 문밖 진술 청취.\n");
    if(Evidence.Contains(TEXT("resident_203")) || Evidence.Contains(TEXT("resident_203_safe")))Findings+=TEXT("203호: 두 번째 문밖 진술 청취.\n");
    if(Evidence.Contains(TEXT("log_recording_reviewed")))Findings+=TEXT("CCTV: 2층 녹화 화면을 직접 되감아 확인.\n");
    if(Evidence.Contains(TEXT("sealed_panel")))Findings+=TEXT("2층 서쪽(왼쪽) 비상문 옆 점검구: 봉인과 안쪽 소리 확인.\n");
    return Template.Replace(TEXT("{{complaints}}"),*Rows.TrimEnd()).Replace(TEXT("{{investigation}}"),*Findings.TrimEnd());
}

FString ANRGameMode::InvestigationPlanName() const
{
    return ComplaintLog.Plan==1?TEXT("입주민 증언 대조"):ComplaintLog.Plan==2?TEXT("CCTV·설비 조사"):ComplaintLog.Plan==3?TEXT("증언과 설비 모두 확인"):TEXT("미작성");
}

void ANRGameMode::SelectInvestigationPlan(int32 Plan)
{
    if(Plan<1 || Plan>3 || RoundFiled || !FirstComplaintWritten() || !Evidence.Contains(TEXT("manager_call"))) return;
    ComplaintLog.Plan=Plan;ComplaintPlanning=false;
    Record(TEXT("investigation_plan"),InvestigationPlanName());
    SaveCheckpoint();
    if(ComplaintView)Page=ComplaintLogText(true);
}

bool ANRGameMode::InvestigationPlanComplete() const
{
    if(ComplaintLog.Plan<1 || ComplaintLog.Plan>3) return false;
    const bool Witness=Evidence.Contains(TEXT("resident_105")) && (Evidence.Contains(TEXT("resident_203")) || Evidence.Contains(TEXT("resident_203_safe")));
    const bool Technical=Evidence.Contains(TEXT("sealed_panel")) && Evidence.Contains(TEXT("log_recording_reviewed"));
    return (ComplaintLog.Plan==2 || Witness) && (ComplaintLog.Plan==1 || Technical);
}
