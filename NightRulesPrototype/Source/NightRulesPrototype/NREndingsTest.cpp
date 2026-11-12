#include "NRGame.h"
#include "Camera/CameraComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
#include "Engine/GameViewportClient.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "InputKeyEventArgs.h"
#include "TimerManager.h"
#include "HAL/PlatformMisc.h"

namespace {
ANRProp* FindEnd(ANRGameMode* G,const TCHAR* Id){for(auto* P:G->Props)if(P->Id==Id)return P;return nullptr;}
void ClearEnd(ANRGameMode* G){G->StopVoice();G->Page.Empty();G->SubtitleLines.Reset();G->Notice.Empty();}
}

// Branch integration tests use production interactions, with explicit location/time fixtures.
// They are not a first-play duration measurement or a full keyboard walkthrough.
void ANRGameMode::FinaleTest()
{
    int32 Failures=0;
    auto Check=[&](bool OK,const TCHAR* Name){UE_LOG(LogTemp,Display,TEXT("NR_FINALE %s %s"),OK?TEXT("PASS"):TEXT("FAIL"),Name);if(!OK)++Failures;};
    auto Act=[&](const TCHAR* Id){ClearEnd(this);auto* P=FindEnd(this,Id);if(!P){Check(false,Id);return;}Use(P);};
    auto Transcript=[this]{FString Text;for(const auto& Line:SubtitleLines)Text+=Line.Text+TEXT("\n");return Text;};
    auto Reset=[&]{StartFinale();ClearEnd(this);};
    // Exercise DAY 1 hearing through real phone interaction, transition and retry.
    for(int32 History=0;History<3;++History) {
        Evidence.Remove(TEXT("final_call"));Evidence.Remove(TEXT("final_call_ignored"));
        Finale.Active=false;IntroComplete=true;IntroCallPending=false;PhoneStage=3;ClearEnd(this);
        if(History==1) {Use(FindEnd(this,TEXT("phone")));ClearEnd(this);}
        if(History==2) Evidence.Add(TEXT("final_call_ignored"));
        Reset();SaveCheckpoint();Evidence.Remove(TEXT("final_call"));Evidence.Remove(TEXT("final_call_ignored"));RestoreCheckpoint();ClearEnd(this);
        Check(Evidence.Contains(TEXT("final_call"))==(History==1),TEXT("DAY1 307 hearing survives final-night transition and checkpoint"));
        FinishFinale(TEXT("RED"));TickFinale(1.1f);
        const FString Scene=Transcript().Replace(TEXT("\n"),TEXT(""));
        Check(Scene.Contains(History==1?TEXT("그날 들었던 말"):TEXT("한 번도 들어 본 적 없는 말")),TEXT("RED uses heard, ignored or missing-history scene correctly"));
        Check(Scene.Contains(TEXT("‘이번에는 문 좀 열어주세요.’")),TEXT("both RED scenes quote the original DAY1 line"));
        Check(SubtitleLines.Last().Speaker==TEXT("나 · 목소리"),TEXT("both RED scenes label the player's own speech"));
        Check(History!=1 || SubtitleLines[0].Speaker==TEXT("전화 너머 · 관리자"),TEXT("RED handover belongs to manager"));
        Check(History==1 || SubtitleLines[0].Speaker==TEXT("나 · 독백"),TEXT("unheard RED starts with inner monologue"));
    }
    Evidence.Remove(TEXT("final_call"));Evidence.Remove(TEXT("final_call_ignored"));Reset();
    auto Card=[&](const TCHAR* Outcome){
        bool Reviewed=false;
        for(int32 I=0;I<180 && !Finished;++I) {
            Tick(.5f);
            if(!Reviewed && Finale.SceneBeat==1) {
                Reviewed=true;
                Check(SubtitleLines.ContainsByPredicate([](const FSubtitleLine& Line){return Line.Speaker==TEXT("나 · 독백");}),TEXT("ending narration is labelled as inner monologue"));
                if(Finale.Outcome==TEXT("RED")) Check(SubtitleLines.Last().Speaker==TEXT("나 · 목소리"),TEXT("RED player's spoken line has player's label"));
            }
        }
        Check(Finished && Page.Contains(Outcome) && !Page.Contains(TEXT("방침")),TEXT("ending card completes without DAY1 investigation plan"));
    };
    Evidence.Add(TEXT("202_avoided"));Evidence.Add(TEXT("final_call_ignored"));Reset();
    Check(Evidence.Contains(TEXT("202_avoided")) && Evidence.Contains(TEXT("final_call_ignored")),TEXT("DAY1 choices preserved without locking the finale"));
    Check(Documents.Contains(TEXT("final_ending_TRUE")) && Documents.Contains(TEXT("final_ending_RED")) && Documents.Contains(TEXT("final_ending_BLACK")),TEXT("packaged final-night story data loaded"));
    for(const TCHAR* Id:{TEXT("final_phone"),TEXT("final_note")}){auto* P=FindEnd(this,Id);Check(P && P->Mesh->Bounds.GetBox().Min.Z>700 && P->Mesh->Bounds.GetBox().Min.Z<740,TEXT("phone and note rest on desktop rather than high shelf"));}
    Act(TEXT("phone"));Check(Finale.Contacted && Finale.Outcome.IsEmpty(),TEXT("answering a call is not RED"));
    Check(SubtitleLines.Last().Speaker==TEXT("수화기 · 다른 목소리"),TEXT("key instruction is not labelled as manager"));
    Check(!Documents.FindRef(TEXT("final_minseo_rescued")).Contains(TEXT("307")),TEXT("rescue does not invent unimplemented voice impersonation"));
    Act(TEXT("final_isolator"));Act(TEXT("final_isolator"));
    Check(!Transcript().Contains(TEXT("취소")),TEXT("line restore without submitted report never claims cancellation"));
    Act(TEXT("final_box"));Check(!Finale.BoxUnlocked,TEXT("box needs its physical key"));
    auto* Key=FindEnd(this,TEXT("final_key"));
    Check(Key && Key->Mesh->Bounds.GetBox().Min.Z>640 && Key->Mesh->Bounds.GetBox().Min.Z<642 && Key->Mesh->Bounds.Origin.Y<-65,TEXT("307 key lies on corridor floor outside room"));
    Act(TEXT("final_key"));Act(TEXT("final_box"));Act(TEXT("final_box"));Check(!Finale.LureConnected,TEXT("key and box alone do not connect unknown return line"));
    ClearEnd(this);Check(Finale.KeyHeld && Finale.Outcome.IsEmpty() && !Finished && Player->CanMove(),TEXT("key pickup is safe and independent of entry or door closing"));
    Act(TEXT("final_port"));Act(TEXT("final_box"));Check(Finale.LureConnected && Finale.Outcome.IsEmpty(),TEXT("connection remains reversible before calling"));
    auto* Door=FindEnd(this,TEXT("door_307"));Check(Door!=nullptr,TEXT("307 door exists"));
    Player->SetActorLocation(NRLayout::RoomCenter(2,6)+FVector(0,0,90));
    if(Door){Door->SetDoor(true);Door->Tick(1);}
    Act(TEXT("final_phone"));Check(Finale.Outcome.IsEmpty(),TEXT("open door prevents RED"));
    if(Door){Door->SetDoor(false);Door->Tick(1);}
    Act(TEXT("final_isolator"));Act(TEXT("final_phone"));Check(Finale.Outcome.IsEmpty(),TEXT("disabled line prevents RED even inside closed room"));
    Act(TEXT("final_isolator"));Act(TEXT("final_phone"));Check(Finale.Outcome==TEXT("RED") && !Finished && !Player->CanMove(),TEXT("closed room plus live return call starts RED scene"));Card(TEXT("RED"));
    ConfirmFinale();ClearEnd(this);Check(Finale.Outcome.IsEmpty() && !Finished && !Finale.KeyHeld && Player->CanMove(),TEXT("Enter restarts an independent ending attempt"));
    Act(TEXT("final_seal"));Check(Finale.Sealed,TEXT("escape seal requires rooftop tool"));
    Act(TEXT("final_tools"));Act(TEXT("final_seal"));Act(TEXT("door_arch_escape_2"));
    Check(!Transcript().Contains(TEXT("태오")),TEXT("opening exit before Taeo contact does not invent his reply"));
    Player->SetActorLocation(FVector(-650,-135,730));Act(TEXT("final_depart"));
    Check(FinaleConfirm==2 && Finale.Outcome.IsEmpty() && Page.Contains(TEXT("15")),TEXT("leaving residents behind requires visible confirmation"));
    Escape();Check(FinaleConfirm==0 && Finale.Outcome.IsEmpty(),TEXT("Escape cancels irreversible departure"));
    Act(TEXT("final_depart"));ConfirmFinale();Check(Finale.Outcome==TEXT("BLACK"),TEXT("confirmed partial evacuation exit gives BLACK"));Card(TEXT("BLACK"));
    Reset();Act(TEXT("final_isolator"));Act(TEXT("roster"));Check(FinaleConfirm==1 && !ExitUnlocked,TEXT("report is not silently filed on PC use"));
    ConfirmFinale();Check(Finale.ReportSubmitted && ExitUnlocked && Finale.Outcome.IsEmpty(),TEXT("report unlocks front door but is not itself an ending"));
    Act(TEXT("final_isolator"));Check(!Finale.ReportSubmitted && !ExitUnlocked,TEXT("restoring line revokes closure report"));
    Check(Transcript().Contains(TEXT("취소")),TEXT("line restore mentions cancellation only after real submission"));
    Act(TEXT("final_isolator"));Act(TEXT("roster"));ConfirmFinale();Act(TEXT("entrance"));ClearEnd(this);
    Player->SetActorLocation(FVector(0,300,90));Tick(.1f);Check(Finale.Outcome==TEXT("BLACK"),TEXT("crossing front exit after unresolved report gives BLACK"));Card(TEXT("BLACK"));
    Reset();Act(TEXT("door_105"));Act(TEXT("door_204"));Act(TEXT("door_301"));
    Check(Finale.CheckedFloors==7 && EvacuatedCount()==0,TEXT("resident contact alone never counts as actual evacuation"));
    Act(TEXT("door_arch_shower_2"));Act(TEXT("door_arch_shower_2"));Act(TEXT("final_tools"));Act(TEXT("final_seal"));
    Check(!Transcript().Contains(TEXT("취소")),TEXT("unsealing without report never claims cancellation"));
    Act(TEXT("door_arch_escape_2"));
    Check(Transcript().Contains(TEXT("복도 쪽에서 태오")),TEXT("contacted Taeo calls from the established corridor position"));
    Player->SetActorLocation(FVector(-400,-135,730));Act(TEXT("door_arch_escape_2"));ClearEnd(this);
    Page=TEXT("paused document");Tick(40);Check(EvacuatedCount()==0,TEXT("reading does not progress evacuation"));Page.Empty();
    Paused=true;Tick(40);Check(EvacuatedCount()==0,TEXT("pause does not progress evacuation"));Paused=false;
    for(int32 I=0;I<180 && Finale.Evacuating;++I)Tick(.5f);
    Check(EvacuatedCount()==15 && Finale.Outcome.IsEmpty(),TEXT("all three groups and Minseo acknowledge evacuation before ending"));
    SaveCheckpoint();Finale.MinseoEvacuated=false;Die();RestoreCheckpoint();ClearEnd(this);
    Check(!Dead && !Finished && EvacuatedCount()==15 && Finale.ExitOpen && Player->CanMove(),TEXT("death restores physical progress and does not become an ending"));
    Player->SetActorLocation(FVector(-650,-135,730));Act(TEXT("final_depart"));Check(Finale.Outcome==TEXT("TRUE"),TEXT("all residents plus crossing real exit gives TRUE without entering 202"));Card(TEXT("TRUE"));
    Reset();Act(TEXT("final_isolator"));Act(TEXT("roster"));ConfirmFinale();Act(TEXT("final_tools"));Act(TEXT("final_seal"));
    Check(!Finale.ReportSubmitted && Transcript().Contains(TEXT("취소")),TEXT("unsealing revokes and describes a submitted report"));
    Reset();Finale.Tools=true;Act(TEXT("final_seal"));Act(TEXT("door_arch_escape_2"));ClearEnd(this);
    Player->SetActorLocation(FVector(800,-135,730));TickFinale(2);Check(!Threat && Finale.PursuitTime>0,TEXT("final pursuit has an audible lead-in"));
    TickFinale(3);Check(Threat && Finale.ChaseSpent,TEXT("corridor return after exit opened triggers one pursuit"));
    Ghost->SetActorLocation(Player->GetActorLocation());TickFinale(2);Check(Dead && Finale.Outcome.IsEmpty(),TEXT("ghost contact kills instead of awarding an ending"));
    RestoreCheckpoint();ClearEnd(this);Check(!Dead && !Threat && Finale.ExitOpen,TEXT("retry resumes before chase without redoing exit tools"));
    UE_LOG(LogTemp,Display,TEXT("NR_FINALE_COMPLETE failures=%d"),Failures);FPlatformMisc::RequestExitWithStatus(false,Failures?1:0);
}

void ANRGameMode::FinaleWalkTest()
{
    struct FRun {FTimerHandle Timer;float Time=0,ConfirmAt=0;int32 Failures=0;bool Confirming=false,Sent=false;};auto S=MakeShared<FRun>();
    auto Check=[S](bool OK,const TCHAR* Name){UE_LOG(LogTemp,Display,TEXT("NR_FINALE_WALK %s %s"),OK?TEXT("PASS"):TEXT("FAIL"),Name);if(!OK)++S->Failures;};
    StartFinale();ClearEnd(this);Finale.Tools=true;Finale.Sealed=false;Finale.ExitOpen=true;ApplyFinaleWorld();
    for(auto* P:Props)if(P->Id.StartsWith(TEXT("door_"))){if(P->Id==TEXT("door_307") || P->Id==TEXT("door_302") || P->Id==TEXT("door_arch_roof"))P->SetDoor(true);P->Tick(1);}
    struct FReach{const TCHAR* Id;FVector Eye;};
    for(const auto& R:TArray<FReach>{{TEXT("final_port"),FVector(115,-625,149)},{TEXT("final_isolator"),FVector(115,-770,149)},{TEXT("final_box"),FVector(1840,70,789)},{TEXT("final_phone"),FVector(1870,30,789)},{TEXT("final_note"),FVector(715,30,789)},{TEXT("final_tools"),FVector(3550,-60,1109)},{TEXT("final_seal"),FVector(-350,-50,789)},{TEXT("final_key"),FVector(1785,-150,789)},{TEXT("final_depart"),FVector(-650,-135,789)}}){
        auto* P=FindEnd(this,R.Id);if(!P){Check(false,R.Id);continue;}FHitResult Hit;FCollisionQueryParams Q;Q.bTraceComplex=true;Q.AddIgnoredActor(Player);
        const FVector Aim=P->Mesh->Bounds.Origin;GetWorld()->LineTraceSingleByChannel(Hit,R.Eye,Aim+(Aim-R.Eye).GetSafeNormal()*5,ECC_Visibility,Q);
        const bool OK=Hit.GetActor()==P && FVector::Dist(R.Eye,Aim)<260;
        if(!OK)UE_LOG(LogTemp,Warning,TEXT("NR_FINALE_WALK blocked %s by %s at %s target %s"),R.Id,*GetNameSafe(Hit.GetActor()),*Hit.ImpactPoint.ToString(),*Aim.ToString());Check(OK,R.Id);
    }
    Player->SetActorLocation(FVector(-365,-135,730));Player->GetController()->SetControlRotation(FRotator(0,180,0));Player->GetController()->SetIgnoreLookInput(true);
    auto Key=[this](FKey K,EInputEvent Event){auto* V=GetWorld()->GetGameViewport();V->InputKey(FInputKeyEventArgs::CreateSimulated(K,Event,Event==IE_Pressed?1.f:0.f,1,FInputDeviceId::CreateFromInternalId(0),false,V->Viewport));};
    // Allow the intro modal to close before pressing W; production input flushes modal keys.
    GetWorld()->GetTimerManager().SetTimer(S->Timer,[this,S,Check,Key]{
        S->Time+=.1f;if(S->Time<.3f)return;
        if(S->Confirming){
            if(!S->Sent && S->Time>S->ConfirmAt+.5f){Key(EKeys::Enter,IE_Pressed);Key(EKeys::Enter,IE_Released);S->Sent=true;}
            if(S->Time<S->ConfirmAt+1)return;
            Check(Finale.ReportSubmitted && ExitUnlocked && Page.IsEmpty(),TEXT("actual Enter input confirms visible report modal"));
            UE_LOG(LogTemp,Display,TEXT("NR_FINALE_WALK_COMPLETE failures=%d at=%s"),S->Failures,*Player->GetActorLocation().ToString());
            const int32 N=S->Failures;FTimerHandle T=S->Timer;GetWorld()->GetTimerManager().ClearTimer(T);FPlatformMisc::RequestExitWithStatus(false,N?1:0);
            return;
        }
        if(S->Time<.5f)Key(EKeys::W,IE_Pressed);
        if(Player->GetActorLocation().X<-620 || S->Time>8){
            Key(EKeys::W,IE_Released);Check(Player->GetActorLocation().X<-620 && Player->GetActorLocation().Z>690,TEXT("real W input crosses opened 3F escape door onto supported landing"));
            StartFinale();ClearEnd(this);if(auto* P=FindEnd(this,TEXT("final_isolator")))Use(P);ClearEnd(this);if(auto* P=FindEnd(this,TEXT("roster")))Use(P);
            S->Confirming=true;S->ConfirmAt=S->Time;
        }
    },.1f,true);
}

// Explicit staging fixtures for review screenshots, not evidence of a full human walkthrough.
void ANRGameMode::FinalePreview(const FString& Name)
{
    StartFinale();ClearEnd(this);Finale.Contacted=true;
    auto Act=[this](const TCHAR* Id){ClearEnd(this);if(auto* P=FindEnd(this,Id))Use(P);};
    if(Name==TEXT("report")){Act(TEXT("final_isolator"));Act(TEXT("roster"));}
    else if(Name==TEXT("RED")){
        Act(TEXT("final_port"));Act(TEXT("final_key"));Act(TEXT("final_box"));Act(TEXT("final_box"));
        Player->SetActorLocation(NRLayout::RoomCenter(2,6)+FVector(0,0,90));if(auto* Door=FindEnd(this,TEXT("door_307"))){Door->SetDoor(false);Door->Tick(1);}Act(TEXT("final_phone"));
    }else if(Name==TEXT("TRUE") || Name==TEXT("escape")){
        Finale.CheckedFloors=7;Finale.EvacuatedFloors=7;Finale.MinseoLocated=Finale.MinseoRescued=Finale.MinseoEvacuated=true;Finale.Tools=true;Finale.Sealed=false;Finale.ExitOpen=true;ApplyFinaleWorld();
        for(auto* P:Props)if(P->Id==TEXT("door_arch_escape_2"))P->Tick(1);
        Player->SetActorLocation(FVector(-650,-135,730));Player->GetController()->SetControlRotation(FRotator(0,0,0));
        if(Name==TEXT("TRUE"))Act(TEXT("final_depart"));
    }else if(Name==TEXT("BLACK")){Act(TEXT("final_isolator"));Act(TEXT("roster"));ConfirmFinale();ClearEnd(this);Player->SetActorLocation(FVector(0,300,90));TickFinale(.1f);}
    else if(Name==TEXT("307")){
        Player->SetActorLocation(FVector(1895,-5,730));Player->GetController()->SetControlRotation(FRotator(-8,118,0));Player->LightOn=true;
    }else {Page=Documents.FindRef(TEXT("final_test_intro"));}
    const bool Ending=Name==TEXT("TRUE") || Name==TEXT("RED") || Name==TEXT("BLACK");
    FTimerHandle Shot,Exit;
    GetWorld()->GetTimerManager().SetTimer(Shot,[this]{Player->GetController<APlayerController>()->ConsoleCommand(TEXT("Shot SHOWUI"));},Ending?36.f:5.f,false);
    GetWorld()->GetTimerManager().SetTimer(Exit,[]{FPlatformMisc::RequestExit(false);},Ending?39.f:8.f,false);
}
