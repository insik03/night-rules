#include "NRGame.h"
#include "Camera/CameraComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/InputComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Animation/AnimSequence.h"
#include "Engine/World.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Widgets/Layout/SScrollBox.h"
#include "TimerManager.h"
#include "HAL/PlatformMisc.h"
#include "Kismet/KismetRenderingLibrary.h"

namespace {
ANRProp* FindFinal(ANRGameMode* G,const FString& Id) {for(auto* P:G->Props)if(P->Id==Id)return P;return nullptr;}
bool Inside307(FVector P) {return P.Z>660 && P.Z<900 && P.X>NRLayout::RoomLeft(6)+5 && P.X<NRLayout::RoomLeft(7)-5 && P.Y>0 && P.Y<220;}
}

void ANRGameMode::SetupFinale()
{
    FString Raw;TSharedPtr<FJsonObject> Data;
    if(FFileHelper::LoadFileToString(Raw,*(FPaths::ProjectContentDir()/TEXT("Data/endings.json"))) && FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Raw),Data))
        for(const auto& Entry:Data->GetObjectField(TEXT("documents"))->Values)Documents.Add(FString(*Entry.Key),Entry.Value->AsString());
    else UE_LOG(LogTemp,Error,TEXT("Final-night documents could not be loaded"));
    if(auto* PC=Player->GetController<APlayerController>())PC->InputComponent->BindKey(EKeys::Enter,IE_Pressed,this,&ANRGameMode::ConfirmFinale);
    // All props reuse already imported meshes. No generated assets or paid services.
    auto Copy=[this](const TCHAR* Id,const TCHAR* Name,const TCHAR* Source,FVector Center,FVector2D Facing,FVector Size=FVector::ZeroVector) {
        auto* Original=FindFinal(this,Source);auto* P=Prop(Id,Name,Center,FVector(1));
        if(Original){P->Mesh->SetStaticMesh(Original->Mesh->GetStaticMesh());P->Mesh->EmptyOverrideMaterials();P->SetActorScale3D(FVector(1));}
        if(!Size.IsNearlyZero())P->SetActorScale3D(Size/(P->Mesh->GetStaticMesh()->GetBounds().BoxExtent*2));
        Face(P,Facing);P->AddActorWorldOffset(Center-P->Mesh->Bounds.Origin);P->Home=P->GetActorLocation();FinaleProps.Add(P);return P;
    };
    auto* Port=Copy(TEXT("final_port"),TEXT("관리실 반환 단자 확인"),TEXT("breaker"),FVector(-25,-625,146),FVector2D(1,0),FVector(26,8,34));
    auto* Isolator=Copy(TEXT("final_isolator"),TEXT("307호 회선 차단 / 복원"),TEXT("breaker"),FVector(-25,-770,146),FVector2D(1,0),FVector(26,8,34));
    auto* Box=Copy(TEXT("final_box"),TEXT("307호 회선함"),TEXT("breaker"),FVector(NRLayout::RoomLeft(6)+9,78,790),FVector2D(1,0),FVector(35,8,46));
    auto* Seal=Copy(TEXT("final_seal"),TEXT("비상문 봉인 잠금 / 해제"),TEXT("sealed_panel"),FVector(-490,-35,780),FVector2D(1,0),FVector(24,8,32));
    auto* Tools=Copy(TEXT("final_tools"),TEXT("외부 비상계단 정비함"),TEXT("breaker"),FVector(3550,-188,1090),FVector2D(0,1),FVector(42,12,48));
    auto* Key=Copy(TEXT("final_key"),TEXT("307호 회선함 열쇠"),TEXT("lost_tag"),NRLayout::DoorAnchor(2,6)+FVector(0,-25,2),FVector2D(0,-1));
    Key->AddActorWorldOffset(FVector(0,0,640.1f-Key->Mesh->Bounds.GetBox().Min.Z));Key->Home=Key->GetActorLocation();
    auto* Note=Copy(TEXT("final_note"),TEXT("도윤의 마지막 점검 쪽지"),TEXT("service_ledger"),FVector::ZeroVector,FVector2D(0,-1));
    auto* Phone=Copy(TEXT("final_phone"),TEXT("관리실로 직접 발신"),TEXT("phone"),FVector::ZeroVector,FVector2D(0,-1));
    auto Desktop=[this](ANRProp* Item,ANRProp* Desk){
        // This desk mesh includes its high wall shelf. Trace beneath that shelf
        // to seat objects on the actual writing surface, not the overall bounds.
        const FVector At=Desk->GetActorLocation();FHitResult Hit;FCollisionQueryParams Q;Q.bTraceComplex=true;
        const FVector Top(At.X,183,At.Z+98),Bottom(At.X,183,At.Z+20);
        if(Desk->Mesh->LineTraceComponent(Hit,Top,Bottom,Q)){
            Item->AddActorWorldOffset(FVector(At.X-Item->Mesh->Bounds.Origin.X,183-Item->Mesh->Bounds.Origin.Y,Hit.ImpactPoint.Z+.1f-Item->Mesh->Bounds.GetBox().Min.Z));Item->Home=Item->GetActorLocation();
        }else {PlaceOn(Item,Desk,FVector2D(At.X,183));UE_LOG(LogTemp,Error,TEXT("Final-night desktop surface missing"));}
    };
    for(auto* P:Props)if(P->Id==TEXT("roomdesk") && P->GetActorLocation().Z>600 && P->GetActorLocation().Z<800){
        const float X=P->GetActorLocation().X;
        if(X>NRLayout::RoomLeft(1) && X<NRLayout::RoomLeft(2))Desktop(Note,P);
        if(X>NRLayout::RoomLeft(6) && X<NRLayout::RoomLeft(7))Desktop(Phone,P);
    }
    auto* Depart=Copy(TEXT("final_depart"),TEXT("외부 계단으로 내려가기"),TEXT("sealed_panel"),FVector(-793,-135,788),FVector2D(1,0),FVector(24,4,20));
    for(auto* P:{Port,Isolator,Box,Seal,Tools,Depart}) {
        const FVector FaceVector=P->GetActorRightVector();
        P->Label->SetWorldLocation(P->Mesh->Bounds.Origin+FaceVector*9);P->Label->SetWorldRotation(FaceVector.Rotation());
        P->Label->SetText(FText::FromString(P==Port?TEXT("관리실 반환"):P==Isolator?TEXT("307 회선"):P==Box?TEXT("307 → 관리실"):P==Seal?TEXT("봉인 잠금"):P==Tools?TEXT("비상문 정비"):TEXT("계단 아래")));
        P->Label->SetWorldSize(5);P->Label->SetTextRenderColor(FColor(210,200,170));P->Label->SetVisibility(true);
    }
    ApplyFinaleWorld();
}

void ANRGameMode::ApplyFinaleWorld()
{
    for(auto* P:FinaleProps){const bool Visible=Finale.Active && !(P->Id==TEXT("final_key") && Finale.KeyHeld);P->SetActorHiddenInGame(!Visible);P->SetActorEnableCollision(Visible);}
    if(!Finale.Active)return;
    for(auto* P:Props){
        if(P->Id.StartsWith(TEXT("door_arch_escape_")))P->SetDoor(P->Id==TEXT("door_arch_escape_2") && Finale.ExitOpen);
        if(P->Id==TEXT("door_arch_shower_2"))P->SetDoor(Finale.MinseoRescued);
        if(P->Id==TEXT("door_office"))P->SetDoor(true);
    }
    if(auto* P=FindFinal(this,TEXT("final_box")))P->Caption=Finale.LureConnected?TEXT("반환 회선 분리"):Finale.BoxUnlocked?TEXT("반환 회선 연결"):TEXT("307호 회선함 열기");
    if(auto* P=FindFinal(this,TEXT("final_isolator")))P->Caption=Finale.LineEnabled?TEXT("307호 회선 차단"):TEXT("307호 회선 복원");
    if(auto* P=FindFinal(this,TEXT("final_seal")))P->Caption=Finale.Sealed?TEXT("비상문 봉인 해제"):TEXT("비상문 다시 봉인");
    ExitUnlocked=Finale.ReportSubmitted && Finale.Sealed && !Finale.LineEnabled;
}

void ANRGameMode::StartFinale()
{
    CloseComplaintLog();StopVoice();SubtitleLines.Reset();Notice.Empty();Page.Empty();
    Finale=FFinaleState();Finale.Active=true;FinaleConfirm=0;
    // A retry must not carry final-night findings into a fresh ending attempt.
    for(auto It=Evidence.CreateIterator();It;++It)if(It->StartsWith(TEXT("final_")) && *It!=TEXT("final_call") && *It!=TEXT("final_call_ignored"))It.RemoveCurrent();
    ResetExecution();
    Dead=Finished=Paused=Threat=ThreatPending=DreamActive=EndingPending=IntroCallPending=false;
    IntroComplete=true;PhoneStage=AnsweredStage=3;FinalRings=0;WitnessUntil=0;FlickerTime=0;
    PowerRepaired=true;MonitorOff=false;ReportFiled=true;CCTVReset=true;SetPower(false);LiveCCTV();
    CCTVView=RulesView=PaperView=false;Ghost->SetActorHiddenInGame(true);
    Player->SetActorLocation(NRLayout::OfficePoint(FVector(85,-395,90)));Player->GetController()->SetControlRotation(FRotator(0,130,0));
    Player->GetCharacterMovement()->SetMovementMode(MOVE_Walking);Player->GetCharacterMovement()->StopMovementImmediately();Player->UnCrouch();
    Player->GetController<APlayerController>()->PlayerCameraManager->SetManualCameraFade(0,FLinearColor::Black,false);
    for(auto* P:Props)if(P->Id.StartsWith(TEXT("door_")) || P->Id==TEXT("entrance")){P->SetDoor(false);P->Tick(1);}
    ApplyFinaleWorld();SaveCheckpoint();
    Page=Documents.FindRef(TEXT("final_test_intro"));if(DocumentScroll)DocumentScroll->ScrollToStart();
    Record(TEXT("chapter"),TEXT("final_night_test_start"));
}

int32 ANRGameMode::EvacuatedCount() const
{
    return ((Finale.EvacuatedFloors&1)?5:0)+((Finale.EvacuatedFloors&2)?4:0)+((Finale.EvacuatedFloors&4)?5:0)+(Finale.MinseoEvacuated?1:0);
}
FString ANRGameMode::FinaleReport() const
{
    FString Text=TEXT("최종밤 재실·대피 기록\n\n");
    for(int32 F=0;F<3;++F)Text+=FString::Printf(TEXT("%d층 %d명: %s\n"),F+1,F==1?4:5,(Finale.EvacuatedFloors&(1<<F))?TEXT("외부 계단 인계 확인"):(Finale.CheckedFloors&(1<<F))?TEXT("응답 확인 / 대피 전"):TEXT("재실 미확인"));
    Text+=TEXT("203호 민서: ")+FString(Finale.MinseoEvacuated?TEXT("외부 계단 인계 확인"):Finale.MinseoRescued?TEXT("샤워실 밖 구조 / 대피 전"):Finale.MinseoLocated?TEXT("3층 샤워실에서 응답 / 구조 전"):TEXT("위치 미확인"));
    Text+=FString::Printf(TEXT("\n\n대피 확인 %d / 15명\n비상 통로: %s\n307호 회선: %s"),EvacuatedCount(),Finale.ExitOpen?TEXT("개방"):Finale.Sealed?TEXT("봉인"):TEXT("잠금 해제 / 닫힘"),Finale.LineEnabled?TEXT("연결됨"):TEXT("차단됨"));
    return Text;
}
FString ANRGameMode::FinaleObjective() const
{
    if(!Finale.Outcome.IsEmpty())return TEXT("");
    if(Threat || Finale.PursuitTime>0)return TEXT("열어 둔 서쪽 비상문으로 빠져나가자.");
    if(!Finale.Contacted)return TEXT("관리실에서 마지막 근무 전화를 받자.");
    if(Finale.ReportSubmitted)return TEXT("종료 보고를 제출했다. 현관에서 퇴근하거나 조사를 계속할 수 있다.");
    if(Finale.Evacuating)return TEXT("비상문에서 계단 쪽의 대피 응답을 확인하자.");
    if(Finale.ExitOpen)return TEXT("남은 사람과 대피 상황을 확인하자. [J] 재실 기록");
    if(Finale.LureConnected)return TEXT("307호 회선이 연결됐다. 문과 발신 단자를 다시 살펴보자.");
    if(Finale.MinseoLocated && !Finale.MinseoRescued)return TEXT("3층 샤워실 바깥의 걸림을 확인하자.");
    return TEXT("현재 사람과 비상문, 307호의 반환 회선을 조사하자.");
}

bool ANRGameMode::UseFinale(ANRProp* P)
{
    if(Dead || Finished || !Finale.Outcome.IsEmpty())return true;
    const FString Id=P->Id;
    auto Read=[this](const TCHAR* Key,const FString& Extra=FString()){ShowDocument(Key,Extra);SaveCheckpoint();};
    auto Paper=[this](const TCHAR* Key){CloseComplaintLog();CCTVView=RulesView=PaperView=false;Evidence.Add(Key);Page=Documents.FindRef(Key);if(DocumentScroll)DocumentScroll->ScrollToStart();SaveCheckpoint();};
    if(Id==TEXT("phone")){Finale.Contacted=true;Read(TEXT("final_manager"));return true;}
    if(Id==TEXT("complaint_log")){Paper(TEXT("final_plan"));Page+=TEXT("\n\n")+FinaleReport();return true;}
    if(Id==TEXT("door_105") || Id==TEXT("door_204") || Id==TEXT("door_301")){
        const int32 F=Id==TEXT("door_105")?0:Id==TEXT("door_204")?1:2;
        Finale.CheckedFloors|=1<<F;Read(F==0?TEXT("final_floor1"):F==1?TEXT("final_floor2"):TEXT("final_floor3"));return true;
    }
    if(Id==TEXT("door_203")){Read(TEXT("final_empty203"));return true;}
    if(Id==TEXT("door_arch_shower_2")){
        if(!Finale.MinseoLocated){Finale.MinseoLocated=true;Read(TEXT("final_minseo_located"));DemoSound(TEXT("knock"),P->GetActorLocation()+FVector(0,-60,140),.5f);}
        else if(!Finale.MinseoRescued){Finale.MinseoRescued=true;P->SetDoor(true);Read(TEXT("final_minseo_rescued"));}
        else Read(TEXT("final_minseo_waiting"));
        return true;
    }
    if(Id==TEXT("final_port")){Finale.ReturnPortKnown=true;Paper(TEXT("final_port_note"));return true;}
    if(Id==TEXT("final_note")){Paper(TEXT("final_doyun"));return true;}
    if(Id==TEXT("final_key")){Finale.KeyHeld=true;ApplyFinaleWorld();Read(TEXT("final_key_taken"));return true;}
    if(Id==TEXT("final_tools")){Finale.Tools=true;Read(TEXT("final_tools_taken"));return true;}
    if(Id==TEXT("final_isolator")){
        const bool Submitted=Finale.ReportSubmitted;
        Finale.LineEnabled=!Finale.LineEnabled;Finale.ReportSubmitted=false;ApplyFinaleWorld();
        Read(Finale.LineEnabled?TEXT("final_line_on"):TEXT("final_line_off"),Submitted && Finale.LineEnabled?Documents.FindRef(TEXT("final_report_revoked")):FString());return true;
    }
    if(Id==TEXT("final_box")){
        if(!Finale.KeyHeld){Read(TEXT("final_box_locked"));return true;}
        if(!Finale.BoxUnlocked){Finale.BoxUnlocked=true;ApplyFinaleWorld();Paper(TEXT("final_box_label"));return true;}
        if(!Finale.ReturnPortKnown){Paper(TEXT("final_box_unknown"));return true;}
        Finale.LureConnected=!Finale.LureConnected;ApplyFinaleWorld();Read(Finale.LureConnected?TEXT("final_connected"):TEXT("final_disconnected"));return true;
    }
    if(Id==TEXT("final_phone")){
        auto* Door=FindFinal(this,TEXT("door_307"));
        if(!Finale.LineEnabled || !Finale.LureConnected){Read(TEXT("final_phone_dead"));return true;}
        if(!Door || Door->Open || FMath::Abs(FMath::FindDeltaAngleDegrees(Door->GetActorRotation().Yaw,Door->ClosedYaw))>.5f || !Inside307(Player->GetActorLocation())){Read(TEXT("final_phone_open"));return true;}
        FinishFinale(TEXT("RED"));return true;
    }
    if(Id==TEXT("final_seal")){
        if(Finale.Sealed && !Finale.Tools){Read(TEXT("final_need_tools"));return true;}
        if(Finale.Evacuating){Read(TEXT("final_people_crossing"));return true;}
        const bool Submitted=Finale.ReportSubmitted;
        Finale.Sealed=!Finale.Sealed;Finale.ExitOpen=false;Finale.ReportSubmitted=false;ApplyFinaleWorld();
        Read(Finale.Sealed?TEXT("final_resealed"):TEXT("final_unsealed"),Submitted && !Finale.Sealed?Documents.FindRef(TEXT("final_report_revoked")):FString());return true;
    }
    if(Id.StartsWith(TEXT("door_arch_escape_"))){
        if(Id!=TEXT("door_arch_escape_2")){Read(TEXT("final_other_exit"));return true;}
        if(Finale.Sealed){Read(TEXT("final_escape_locked"));return true;}
        if(!Finale.ExitOpen){Finale.ExitOpen=true;Finale.ReportSubmitted=false;ApplyFinaleWorld();Read(TEXT("final_exit_open"),(Finale.CheckedFloors & 4)?Documents.FindRef(TEXT("final_exit_taeo")):FString());return true;}
        if(!Finale.Evacuating){
            const int32 Missing=Finale.CheckedFloors & ~Finale.EvacuatedFloors;
            if(!Missing && !(Finale.MinseoRescued && !Finale.MinseoEvacuated)){Read(TEXT("final_no_group"));return true;}
            Finale.Evacuating=true;Finale.EvacTime=0;Read(TEXT("final_evac_start"));
        }
        return true;
    }
    if(Id==TEXT("final_depart")){
        if(!Finale.ExitOpen || Player->GetActorLocation().X>-540 || FMath::Abs(Player->GetActorLocation().Z-730)>100){Read(TEXT("final_cross_first"));return true;}
        if(EvacuatedCount()==15){FinishFinale(TEXT("TRUE"));return true;}
        FinaleConfirm=2;Page=FinaleReport()+TEXT("\n\n아직 대피가 확인되지 않은 사람이 있다.\n계단 아래로 떠나면 돌아올 수 없다.\n[Enter] 남은 요청을 두고 떠난다.\n[Esc] 돌아가 확인한다.");return true;
    }
    if(Id==TEXT("roster")){
        if(Finale.Sealed && !Finale.LineEnabled && EvacuatedCount()<15){
            FinaleConfirm=1;Page=FinaleReport()+TEXT("\n\n미해결·미확인 요청을 남긴 채 근무 종료를 제출합니다.\n[Enter] 이 상태로 종료 보고 제출\n[Esc] 취소하고 조사 계속");
        }else{Paper(TEXT("final_terminal"));Page+=TEXT("\n\n")+FinaleReport();}
        return true;
    }
    if(Id==TEXT("entrance")){
        if(!ExitUnlocked){Read(TEXT("final_front_locked"));return true;}
        for(auto* Door:Props)if(Door->Id==Id)Door->SetDoor(true);return true;
    }
    if(Id.StartsWith(TEXT("door_"))){
        if(Id.StartsWith(TEXT("door_arch_")) || Id==TEXT("door_office") || TSet<FString>{TEXT("door_103"),TEXT("door_106"),TEXT("door_109"),TEXT("door_201"),TEXT("door_202"),TEXT("door_209"),TEXT("door_302"),TEXT("door_307"),TEXT("door_310")}.Contains(Id)){
            P->SetDoor(!P->Open);DemoSound(TEXT("metal_rattle"),P->GetActorLocation(),.25f);
        }else Message(TEXT("이 방은 조용하다. 층별 연락 담당에게 남은 사람을 확인할 수 있다."),3,TEXT("문밖"));
        return true;
    }
    // Avoid replaying DAY 1 fuse/report puzzles in this final-night slice.
    if(Id==TEXT("breaker") || Id==TEXT("spare_fuse") || Id==TEXT("wake_trace") || Id==TEXT("sealed_panel")){Read(TEXT("final_old_inspection"));return true;}
    if(Id==TEXT("cctv_power")){MonitorOff=!MonitorOff;if(!MonitorOff)LiveCCTV();else for(auto* Target:CCTVTargets)UKismetRenderingLibrary::ClearRenderTarget2D(this,Target,FLinearColor::Black);Read(MonitorOff?TEXT("final_monitor_off"):TEXT("final_monitor_on"));return true;}
    return false;
}

void ANRGameMode::ConfirmFinale()
{
    if(Dead)return;
    if(Finished){StartFinale();return;}
    if(!Finale.Active || Paused || !Finale.Outcome.IsEmpty())return;
    const int32 Choice=FinaleConfirm;FinaleConfirm=0;
    if(Choice==1 && Finale.Sealed && !Finale.LineEnabled && EvacuatedCount()<15){
        Page.Empty();Finale.ReportSubmitted=true;ApplyFinaleWorld();ShowDocument(TEXT("final_report_submitted"));SaveCheckpoint();
    }else if(Choice==2 && Finale.ExitOpen && Player->GetActorLocation().X<-540 && EvacuatedCount()<15){Page.Empty();FinishFinale(TEXT("BLACK"));}
}

void ANRGameMode::FinishFinale(const FString& Outcome)
{
    if(!Finale.Active || Dead || Finished || !Finale.Outcome.IsEmpty())return;
    if(Outcome!=TEXT("TRUE") && Outcome!=TEXT("BLACK") && Outcome!=TEXT("RED"))return;
    Finale.Outcome=Outcome;Finale.SceneTime=0;Finale.SceneBeat=0;FinaleConfirm=0;
    CloseComplaintLog();StopVoice();SubtitleLines.Reset();Page.Empty();Notice.Empty();EndingPending=false;
    Threat=ThreatPending=false;Ghost->SetActorHiddenInGame(true);ApplyLightState(false);
    CCTVView=RulesView=PaperView=false;Player->GetCharacterMovement()->StopMovementImmediately();
    Player->GetController<APlayerController>()->PlayerCameraManager->SetManualCameraFade(1,FLinearColor::Black,false);
    Record(TEXT("ending_action"),Outcome+TEXT(" / ")+FString::FromInt(EvacuatedCount()));
}

void ANRGameMode::TickFinale(float D)
{
    if(Dead || Finished || Paused || (!Page.IsEmpty() && !CCTVView))return;
    auto* PC=Player->GetController<APlayerController>();
    if(!Finale.Outcome.IsEmpty()){
        Finale.SceneTime+=D;
        if(Finale.SceneBeat==0 && Finale.SceneTime>=1){
            Finale.SceneBeat=1;
            if(Finale.Outcome==TEXT("RED")){
                if(auto* Phone=FindFinal(this,TEXT("final_phone")))PC->SetControlRotation((Phone->Mesh->Bounds.Origin-Player->Camera->GetComponentLocation()).Rotation());
                DemoSound(TEXT("phone_ring"),Player->GetActorLocation(),.55f);
            }else{
                Player->SetActorLocation(FVector(0,440,90));Player->GetCharacterMovement()->SetMovementMode(MOVE_None);PC->SetControlRotation(FRotator(0,-90,0));
                DemoSound(Finale.Outcome==TEXT("TRUE")?TEXT("distant_steps"):TEXT("phone_ring"),FVector(0,240,100),.4f);
            }
            PC->PlayerCameraManager->SetManualCameraFade(0,FLinearColor::Black,false);
            TArray<FString> Speakers;
            FString SceneKey=TEXT("final_scene_")+Finale.Outcome;
            if(Finale.Outcome==TEXT("TRUE")) Speakers={TEXT("계단 아래 · 정숙"),TEXT("나 · 독백"),TEXT("계단 쪽 · 목소리"),TEXT("나 · 독백")};
            else if(Finale.Outcome==TEXT("RED")) {
                // Missing DAY 1 history (including direct finale tests) means unheard.
                const bool Heard=Evidence.Contains(TEXT("final_call"));
                SceneKey=Heard?TEXT("final_scene_RED"):TEXT("final_scene_RED_unheard");
                Speakers={Heard?TEXT("전화 너머 · 관리자"):TEXT("나 · 독백"),TEXT("나 · 독백"),TEXT("나 · 독백"),TEXT("나 · 독백"),TEXT("나 · 목소리")};
            }
            Message(Documents.FindRef(SceneKey),0,TEXT("전화 너머 · 관리자"),Speakers.IsEmpty()?nullptr:&Speakers);
        }
        if(Finale.SceneBeat==1 && Finale.SceneTime>=7){
            Finale.SceneBeat=2;DemoSound(Finale.Outcome==TEXT("TRUE")?TEXT("metal_rattle"):TEXT("knock"),Player->GetActorLocation()+FVector(0,-70,0),.4f);
        }
        if(Finale.SceneTime>=15 && SubtitleLines.IsEmpty()){
            Finished=true;Page=Documents.FindRef(TEXT("final_ending_")+Finale.Outcome);
            if(Finale.Outcome==TEXT("BLACK"))Page+=Finale.ReportSubmitted?TEXT("\n\n종료 보고를 승인한 뒤, 현관으로 나왔다.\n다음 총무에게 전화를 걸라는 문자가 도착했다."):TEXT("\n\n통로는 열었지만 대피가 끝나기 전에 계단을 내려갔다.\n전화 너머에서 다음 근무자의 목소리가 들렸다.");
            Page+=FString::Printf(TEXT("\n\n대피 확인: %d / 15명\n\n최종밤 엔딩 시연 완료. DAY 2~4와 전체 플레이타임은 아직 미구현·미검증입니다."),EvacuatedCount());
            if(DocumentScroll)DocumentScroll->ScrollToStart();Record(TEXT("ending_complete"),Finale.Outcome);
        }
        return;
    }
    const FVector At=Player->GetActorLocation();
    // Stage evacuation acknowledgements only at the opened route. These are off-screen
    // residents using the stairs, not a simulated crowd navigation system.
    if(Finale.Evacuating && Finale.ExitOpen && At.Z>640 && At.Z<900 && At.X<100 && SubtitleLines.IsEmpty()){
        Finale.EvacTime+=D;
        for(int32 F=0;F<3;++F)if(Finale.EvacTime>=(F+1)*4 && (Finale.CheckedFloors&(1<<F)) && !(Finale.EvacuatedFloors&(1<<F))){
            Finale.EvacuatedFloors|=1<<F;DemoSound(TEXT("distant_steps"),FVector(-680,-135,640),.55f);
            Message(FString::Printf(TEXT("‘%d층 %d명, 계단으로 나왔어요.’"),F+1,F==1?4:5),2.5f,F==0?TEXT("정숙"):F==1?TEXT("2층 입주민"):TEXT("태오"));SaveCheckpoint();break;
        }
        if(Finale.EvacTime>=16){
            if(Finale.MinseoRescued && !Finale.MinseoEvacuated){Finale.MinseoEvacuated=true;Message(TEXT("‘저도 나왔어요. 총무님, 아직 안에 계세요?’"),3,TEXT("계단 아래 · 민서"));}
            Finale.Evacuating=false;SaveCheckpoint();
        }
    }
    // Only opening the escape route arms the final pursuit. It never starts while
    // working on the roof, the exterior landing, or the narrow stairs.
    if(Finale.ExitOpen && !Finale.ChaseSpent && At.Z>690 && At.Z<810 && At.X>500 && At.X<2200 && At.Y>-190 && At.Y<-75){
        if(Finale.PursuitTime==0){SaveCheckpoint();Finale.PursuitTime=.001f;DemoSound(TEXT("chair_drag"),FVector(2700,-135,730),.7f);}
        if(SubtitleLines.IsEmpty())Finale.PursuitTime+=D;
        if(Finale.PursuitTime>=4){
            Finale.ChaseSpent=true;Finale.PursuitTime=0;Threat=true;ThreatTime=0;GhostSpeed=0;GhostStepTime=0;
            const float X=FMath::Max(At.X+850.f,2800.f);Ghost->SetActorLocation(FVector(FMath::Min(X,3350.f),-135,730));Ghost->SetActorHiddenInGame(false);
            if(GhostVisual){GhostVisual->PlayAnimation(ChairRunClip?ChairRunClip:LoadObject<UAnimSequence>(nullptr,TEXT("/Game/PrototypeAssets/GhostMeshy/A_CaretakerRun.A_CaretakerRun")),true);GhostVisual->SetPlayRate(0);}
            Record(TEXT("encounter"),TEXT("final_escape_pursuit"));
        }
    }else if(!Threat && Finale.PursuitTime>0){Finale.PursuitTime=0;SaveCheckpoint();}
    if(Threat){
        ThreatTime+=D;ApplyLightState(false);
        if(ThreatTime>1){
            // This encounter is confined to the already-open straight 3F corridor.
            // Never cut through walls or teleport to another floor.
            const FVector Goal(At.X,-135,730),From=Ghost->GetActorLocation();FVector Delta=Goal-From;
            GhostSpeed=FMath::FInterpConstantTo(GhostSpeed,GhostChaseSpeed*GhostLurch(),D,600);const float Travel=FMath::Min(Delta.Size(),GhostSpeed*D);
            FHitResult Hit;FCollisionQueryParams Q;Q.AddIgnoredActor(Ghost);Q.AddIgnoredActor(Player);
            if(!GetWorld()->SweepSingleByChannel(Hit,From,From+Delta.GetSafeNormal()*Travel,FQuat::Identity,ECC_Visibility,FCollisionShape::MakeSphere(20),Q)){
                Ghost->SetActorLocation(From+Delta.GetSafeNormal()*Travel);Ghost->SetActorRotation(FRotator(0,Delta.Rotation().Yaw,0));
                if(GhostVisual)GhostVisual->SetPlayRate(D>0?Travel/(D*367.4f):0);
                if(Travel>.01f && D>0){GhostStepTime-=Travel/367.4f;if(GhostStepTime<=0){GhostStepTime+=GhostRunCycle*.5f;PlayFootstep(true,Ghost->GetActorLocation()-FVector(0,0,80));}}
            }
            else {GhostSpeed=0;if(GhostVisual)GhostVisual->SetPlayRate(0);}
            if(FMath::Abs(At.Z-730)<100 && FVector::Dist2D(At,Ghost->GetActorLocation())<65){Die();return;}
            if(At.X<-540 || At.Z<640){Threat=false;Ghost->SetActorHiddenInGame(true);ApplyLightState(false);SaveCheckpoint();}
        }
    }
    if(Finale.ReportSubmitted && ExitUnlocked && At.Z<240 && At.Y>275 && FMath::Abs(At.X)<140){FinishFinale(TEXT("BLACK"));return;}
    if(At.Z<-500)Die();
}
