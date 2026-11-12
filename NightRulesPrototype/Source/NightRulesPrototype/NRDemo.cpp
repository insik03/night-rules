#include "NRGame.h"
#include "Components/PointLightComponent.h"
#include "Components/AudioComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"
#include "Sound/SoundAttenuation.h"
#include "Engine/World.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/PlayerController.h"
#include "HAL/PlatformMisc.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Kismet/KismetRenderingLibrary.h"
#include "Materials/MaterialInterface.h"

void ANRGameMode::DemoSound(const FString& Name,FVector At,float Volume)
{
    const FString Path=TEXT("/Game/Audio/")+Name+TEXT(".")+Name;
    if(auto* S=LoadObject<USoundBase>(nullptr,*Path))
        UGameplayStatics::PlaySoundAtLocation(this,S,At,FRotator::ZeroRotator,Volume,1.f,0.f,LocalAudioAttenuation);
}
void ANRGameMode::SetupDemo()
{
    LocalAudioAttenuation=NewObject<USoundAttenuation>(this);
    auto& A=LocalAudioAttenuation->Attenuation;
    A.bAttenuate=true; A.bSpatialize=true; A.AttenuationShapeExtents=FVector(180); A.FalloffDistance=1800;
    A.bEnableOcclusion=true; A.OcclusionTraceChannel=ECC_Visibility; A.OcclusionVolumeAttenuation=.65f;
    A.OcclusionLowPassFilterFrequency=2600;
    WakeTrace=Prop(TEXT("wake_trace"),TEXT("금속 조각"),FVector(15,-312,85),FVector(12,3,3));
    WakeTrace->SetActorHiddenInGame(true); WakeTrace->SetActorEnableCollision(false);
    auto* Breaker=Prop(TEXT("breaker"),TEXT("분전함"),FVector(3340,219,140),FVector(42,8,58));
    Breaker->Caption=TEXT("분전함 조사 / 전원 복구"); Breaker->Label->SetText(FText::FromString(TEXT("전기")));
    auto* Fuse=Prop(TEXT("spare_fuse"),TEXT("예비 퓨즈"),FVector(865,-620,90),FVector(16,7,5));
    // An upright binder exposes its cover above the shelf lip at normal eye height.
    // A flat sheet here was physically grounded but impossible to target from below.
    auto* Ledger=Prop(TEXT("service_ledger"),TEXT("전임 총무 장부"),FVector(NRLayout::StoreX(300),-775,145),FVector(26,4,19));
    auto* FoundKey=Prop(TEXT("lost_tag"),TEXT("젖은 열쇠표"),FVector(2800,-600,85),FVector(16,10,2));
    auto* Switch=Prop(TEXT("cctv_power"),TEXT("CCTV 전원 스위치"),FVector(47,-308,85),FVector(12,10,8));
    Prop(TEXT("sealed_panel"),TEXT("봉인된 점검구"),FVector(-486,-35,452),FVector(48,6,68));
    Breaker->SetActorRotation(FRotator(0,180,0));
    for(auto* P:Props) if(P->Id==TEXT("sealed_panel")) Face(P,FVector2D(1,0));
    auto Ground=[this](ANRProp* Item,ANRProp* Support,FVector2D XY)
    {
        PlaceOn(Item,Support,XY);
        const FBox B=Support->Mesh->Bounds.GetBox(); FHitResult Hit; FCollisionQueryParams Query;
        Query.bTraceComplex=true;
        if(Support->Mesh->LineTraceComponent(Hit,FVector(XY.X,XY.Y,B.Max.Z+5),FVector(XY.X,XY.Y,B.Min.Z-5),Query))
        {
            const float Bottom=Item->Mesh->Bounds.GetBox().Min.Z-Item->GetActorLocation().Z;
            Item->SetActorLocation(FVector(XY.X,XY.Y,Hit.ImpactPoint.Z-Bottom+.05f)); Item->Home=Item->GetActorLocation();
        }
    };
    // Trace the real support surface: the sink bounding box includes a tall tap.
    for(auto* P:Props)
    {
        if(P->Id.StartsWith(TEXT("fixture")))
        {
            TArray<UMaterialInterface*> Original;
            for(int32 I=0;I<P->Mesh->GetNumMaterials();++I) Original.Add(P->Mesh->GetMaterial(I));
            FixtureMaterials.Add(P->Mesh,Original);
        }
        if(P->Id==TEXT("desk")) { Ground(Switch,P,FVector2D(100,-250)); Ground(WakeTrace,P,FVector2D(65,-252)); }
        if(P->Id==TEXT("counter") && P->GetActorLocation().Z<200) Ground(Fuse,P,FVector2D(900,-840));
        if(P->Id==TEXT("shelves") && FMath::IsNearlyEqual(P->GetActorLocation().X,NRLayout::StoreX(310.f)) && P->GetActorLocation().Z<200) Ground(Ledger,P,FVector2D(NRLayout::StoreX(300),-790));
        if(P->Id==TEXT("sink") && P->GetActorLocation().Z<200) {
            // Test the item's actual centre, not only its origin; the basin is recessed.
            const FBox B=P->Mesh->Bounds.GetBox();bool Placed=false;
            for(float X:{B.GetCenter().X-15,B.GetCenter().X,B.GetCenter().X+15}) {
                for(float Y:{B.Min.Y+12,B.GetCenter().Y,B.Max.Y-12}) {
                    Ground(FoundKey,P,FVector2D(X,Y));
                    const FBox I=FoundKey->Mesh->Bounds.GetBox();FHitResult H;FCollisionQueryParams Q;Q.bTraceComplex=true;
                    const FVector At(I.GetCenter().X,I.GetCenter().Y,I.Min.Z);
                    if(P->Mesh->LineTraceComponent(H,At+FVector(0,0,.5f),At-FVector(0,0,2),Q) && FMath::Abs(H.ImpactPoint.Z-I.Min.Z)<.3f) {Placed=true;break;}
                }
                if(Placed)break;
            }
        }
    }
    const TArray<TPair<FString,FVector>> Loops={
        {TEXT("fluorescent_hum"),FVector(0,-340,235)},
        {TEXT("fluorescent_hum"),FVector(1100,NRLayout::CorridorY,555)},
        {TEXT("room_tone"),FVector(865,-550,110)},
        {TEXT("room_tone"),FVector(2800,-550,110)}};
    for(const auto& Entry:Loops)
    {
        const FString Path=TEXT("/Game/Audio/")+Entry.Key+TEXT(".")+Entry.Key;
        if(auto* S=LoadObject<USoundBase>(nullptr,*Path))
        {
            auto* C=UGameplayStatics::SpawnSoundAtLocation(this,S,Entry.Value,FRotator::ZeroRotator,.55f,1.f,0.f,LocalAudioAttenuation,nullptr,false);
            if(C) AmbientLoops.Add(C);
        }
    }
}
void ANRGameMode::SetPower(bool Out)
{
    PowerOut=Out;
    ApplyLightState(Out);
    for(auto* C:AmbientLoops) if(C) C->SetVolumeMultiplier(Out?.08f:.55f);
}
void ANRGameMode::ApplyLightState(bool Out)
{
    // Eight rapid cuts (70ms dark / 50ms lit), then a 240ms lit interval.
    // Time-based so the cadence is identical at different frame rates.
    const float Burst=FMath::Fmod(ThreatTime,1.2f);
    const bool ChaseDark=Threat && Burst<.96f && FMath::Fmod(Burst,.12f)<.07f;
    if(LastAppliedOut==Out && LastChaseDark==ChaseDark) return;
    LastAppliedOut=Out; LastChaseDark=ChaseDark;
    auto Corridor=[](const FVector& At){return FMath::Abs(At.Y-NRLayout::CorridorY)<100;};
    for(int32 I=0;I<InteriorLights.Num();++I) if(InteriorLights[I])
        InteriorLights[I]->SetIntensity((Out || (ChaseDark && Corridor(InteriorLights[I]->GetComponentLocation())))?0.f:LightIntensities[I]);
    auto* UnlitTube=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/PrototypeAssets/M_Ceiling.M_Ceiling"));
    for(const auto& Entry:FixtureMaterials)
        for(int32 I=0;I<Entry.Value.Num();++I) Entry.Key->SetMaterial(I,(Out || (ChaseDark && Corridor(Entry.Key->GetComponentLocation())))?UnlitTube:Entry.Value[I]);
}
bool ANRGameMode::DemoReady() const
{
    return PowerRepaired && ReportFiled && RoundFiled && CCTVReset;
}
bool ANRGameMode::UseDemo(ANRProp* P)
{
    if(P->Id==TEXT("roster") && FirstComplaintRequired())
    { Message(TEXT("보고 전에 민원 장부에 호수와 시간을 적자.")); return true; }
    if(P->Id==TEXT("roster") && Evidence.Contains(TEXT("202_avoided")) && !Evidence.Contains(TEXT("202_safe_report")))
    { ShowDocument(TEXT("202_safe_report")); Record(TEXT("choice"),TEXT("202_no_entry_report")); SaveCheckpoint(); return true; }
    if(P->Id==TEXT("phone") && PhoneStage==2 && ReportFiled && !Evidence.Contains(TEXT("manager_call")))
    { ShowDocument(TEXT("manager_call")); AnsweredStage=PhoneStage; return true; }
    if((P->Id==TEXT("cctv") || P->Id.StartsWith(TEXT("cctv_display_"))) && MonitorOff) { ShowDocument(TEXT("cctv_off")); return true; }
    if(P->Id==TEXT("cctv_power"))
    {
        if(!ReportFiled) { Message(TEXT("지금은 정상 작동 중이다. 녹화 장비 전원을 건드릴 이유가 없다.")); return true; }
        if(!MonitorOff)
        {
            MonitorOff=true; MonitorOffAt=DemoSeconds; LiveCCTV();
            for(auto* Target:CCTVTargets) UKismetRenderingLibrary::ClearRenderTarget2D(this,Target,FLinearColor::Black);
            ShowDocument(TEXT("cctv_off")); DemoSound(TEXT("radio_static"),P->GetActorLocation(),.3f);
        }
        else if(DemoSeconds-MonitorOffAt<60)
            ShowDocument(TEXT("cctv_wait"));
        else
        {
            MonitorOff=false; CCTVReset=true;
            for(auto* C:CCTVCameras) C->CaptureScene();
            ShowDocument(TEXT("cctv_recovered")); Record(TEXT("demo"),TEXT("cctv_reset"));
        }
        return true;
    }
    if(P->Id==TEXT("sealed_panel"))
    {
        if(!Evidence.Contains(TEXT("manager_call"))) { ShowDocument(TEXT("panel_early")); return true; }
        ShowDocument(TEXT("sealed_panel")); DemoSound(TEXT("pipe_knock"),P->GetActorLocation()+FVector(0,-100,0),.65f);
        if(!ScareEvents.Contains(TEXT("panel_flicker"))) { ScareEvents.Add(TEXT("panel_flicker")); FlickerTime=3; }
        return true;
    }
    if(Evidence.Contains(TEXT("manager_call")) && P->Id==TEXT("door_105"))
    { P->SetDoor(false); ShowDocument(TEXT("resident_105")); DemoSound(TEXT("metal_rattle"),P->GetActorLocation()+FVector(0,70,0),.25f); return true; }
    if(Evidence.Contains(TEXT("manager_call")) && P->Id==TEXT("door_203"))
    {
        P->SetDoor(false);
        if(Evidence.Contains(TEXT("202_avoided"))) {
            ShowDocument(TEXT("resident_203_safe"));ScareEvents.Add(TEXT("202_pursuit_avoided"));
            DemoSound(TEXT("distant_steps"),NRLayout::DoorAnchor(1,1)+FVector(0,80,80),.2f);
            Record(TEXT("choice"),TEXT("no_202_pursuit"));return true;
        }
        ShowDocument(TEXT("resident_203"));
        if(!ScareEvents.Contains(TEXT("second_round_chase")))
        {
            SaveCheckpoint(); ScareEvents.Add(TEXT("second_round_chase")); EncounterDone=false; QueueThreat(true);
        }
        return true;
    }
    if(P->Id==TEXT("roster") && ReportFiled && Evidence.Contains(TEXT("manager_call")))
    {
        if(!InvestigationPlanComplete() || !CCTVReset)
        { ShowDocument(TEXT("round_pending")); return true; }
        RoundFiled=true; ShowDocument(TEXT("round_complete")); Record(TEXT("demo"),TEXT("round_filed")); return true;
    }
    if(P->Id==TEXT("spare_fuse"))
    {
        if(Collected.Contains(P->Id)) return true;
        HasFuse=true; Collected.Add(P->Id); P->SetActorHiddenInGame(true); P->SetActorEnableCollision(false);
        ShowDocument(TEXT("spare_fuse")); Record(TEXT("demo"),TEXT("fuse_collected")); return true;
    }
    if(P->Id==TEXT("breaker"))
    {
        if(!PowerOut) { ShowDocument(TEXT("breaker_before")); return true; }
        if(!HasFuse) { ShowDocument(TEXT("breaker_missing")); return true; }
        HasFuse=false; PowerRepaired=true; SetPower(false); FlickerTime=1.5f;
        DemoSound(TEXT("power_return"),P->GetActorLocation(),.55f);
        ShowDocument(TEXT("breaker_fixed")); Record(TEXT("demo"),TEXT("power_restored")); SaveCheckpoint(); return true;
    }
    if(P->Id==TEXT("service_ledger") || P->Id==TEXT("lost_tag"))
    {
        ShowDocument(P->Id);
        if(!ScareEvents.Contains(P->Id))
        {
            ScareEvents.Add(P->Id);
            DemoSound(P->Id==TEXT("lost_tag")?TEXT("pipe_knock"):TEXT("metal_rattle"),P->GetActorLocation()+FVector(0,160,30),.45f);
            Record(TEXT("scare"),P->Id);
        }
        return true;
    }
    if(P->Id==TEXT("roster") && PowerRepaired && Evidence.Contains(TEXT("service_ledger")) && Evidence.Contains(TEXT("lost_tag")) && !ReportFiled)
    {
        CCTVStoppedAt=Elapsed; ReportFiled=true; ShowDocument(Evidence.Contains(TEXT("202_avoided"))?TEXT("night_report_safe"):TEXT("night_report")); Record(TEXT("demo"),TEXT("report_filed"));
        PhoneStage=2; AnsweredStage=1; RingTimer=3; SaveCheckpoint(); return true;
    }
    return false;
}
void ANRGameMode::TickDemo(float D)
{
    if(!Player || !IntroComplete || Dead || Finished || Paused || (!Page.IsEmpty() && !CCTVView) || DreamActive) return;
    DemoSeconds+=D;
    auto Once=[this](const FString& Key,bool Condition,const FString& Audio,FVector At)
    {
        if(!Condition || ScareEvents.Contains(Key)) return false;
        ScareEvents.Add(Key); Record(TEXT("scare"),Key); DemoSound(Audio,At); return true;
    };
    const FVector At=Player->GetActorLocation();
    if(Once(TEXT("corridor_flicker"),At.Z>350 && DemoSeconds>20,TEXT("power_trip"),At+FVector(180,0,150))) FlickerTime=2.5f;
    Once(TEXT("chair_scrape"),At.Z>350 && At.Z<640 && FMath::Abs(At.X-NRLayout::DoorAnchor(1,1).X)<450,TEXT("chair_drag"),NRLayout::RoomCenter(1,1)+FVector(0,0,60));
    Once(TEXT("kitchen_steps"),At.Z<250 && At.Y<-300 && At.X>600 && At.X<1100 && DemoSeconds>50,TEXT("distant_steps"),FVector(865,-550,420));
    // The calm awakening and its physical clue precede the next disruption.
    if(!PowerRepaired && !PowerOut && !Threat && !ThreatPending && Once(TEXT("blackout"),(Evidence.Contains(TEXT("wake_trace")) || Evidence.Contains(TEXT("202_safe_report"))) && SubtitleLines.IsEmpty(),TEXT("power_trip"),At))
    {
        SetPower(true); ShowDocument(TEXT("blackout")); SaveCheckpoint();
    }
    FlickerTime=FMath::Max(0.f,FlickerTime-D);
    const bool Off=FlickerTime>0 && FMath::Sin(FlickerTime*31)>.05f;
    ApplyLightState(PowerOut || Off);
    Once(TEXT("behind_breath"),PowerOut && At.X>2100 && At.Y<-950,TEXT("breath_near"),At-Player->GetActorForwardVector()*100);
    Once(TEXT("return_rattle"),PowerRepaired && NRLayout::InStore(At) && At.Y<-800,TEXT("metal_rattle"),FVector(NRLayout::StoreX(95),-790,160));
    if(Once(TEXT("office_slam"),PowerRepaired && NRLayout::InOffice(At),TEXT("door_slam"),FVector(NRLayout::OfficeDoorX,-480,100)))
        for(auto* P:Props) if(P->Id==TEXT("door_office")) P->SetDoor(false); // Reopenable, never a soft lock.
    AmbientTimer-=D;
    if(AmbientTimer<=0)
    {
        AmbientTimer=31.f+FMath::Fmod(DemoSeconds,19.f);
        DemoSound(PowerOut?TEXT("pipe_knock"):TEXT("distant_steps"),At+FVector(350,220,At.Z<250?320:0),.16f);
    }
}
void ANRGameMode::DemoTest()
{
    int32 Failures=0;
    auto Check=[&](bool OK,const TCHAR* Name){UE_LOG(LogTemp,Display,TEXT("NR_DEMO %s %s"),OK?TEXT("PASS"):TEXT("FAIL"),Name); if(!OK) ++Failures;};
    IntroComplete=true; IntroCallPending=false; Page.Empty(); Notice.Empty();
    ShowDocument(TEXT("first_call"));FinishComplaintDialogue();StopVoice();SubtitleLines.Reset();Notice.Empty();OpenComplaintLog();
    SelectComplaintKey(EKeys::One);SelectComplaintKey(EKeys::One);TickComplaintLog(10);Escape();
    ANRProp *Fuse=nullptr,*Breaker=nullptr,*Ledger=nullptr,*Tag=nullptr,*PC=nullptr;
    for(auto* P:Props) { if(P->Id==TEXT("spare_fuse")) Fuse=P; if(P->Id==TEXT("breaker")) Breaker=P; if(P->Id==TEXT("service_ledger")) Ledger=P; if(P->Id==TEXT("lost_tag")) Tag=P; if(P->Id==TEXT("roster")) PC=P; }
    Check(Fuse && Breaker && Ledger && Tag && PC,TEXT("investigation props exist"));
    Check(InteriorLights.Num()>20 && AmbientLoops.Num()==4,TEXT("interior lighting and ambient loops registered"));
    Check(!DemoReady(),TEXT("cannot end immediately after 202"));
    Evidence.Add(TEXT("wake_trace")); SubtitleLines.Reset(); TickDemo(0);
    Check(PowerOut && ScareEvents.Contains(TEXT("blackout")),TEXT("physical aftermath triggers blackout"));
    bool Dark=true; for(auto* C:InteriorLights) Dark&=C->Intensity==0;
    Check(Dark,TEXT("blackout disables actual light components"));
    if(Fuse && Breaker && Ledger && Tag && PC)
    {
        const TArray<TPair<ANRProp*,FVector>> SightChecks={
            {Fuse,FVector(900,-700,149)}, {Ledger,FVector(NRLayout::StoreX(310),-660,149)}, {Tag,FVector(1845,-620,149)}};
        for(const auto& Entry:SightChecks)
        {
            FHitResult Hit; FCollisionQueryParams Query; Query.bTraceComplex=true; Query.AddIgnoredActor(Player);
            const FVector Direction=(Entry.Key->Mesh->Bounds.Origin-Entry.Value).GetSafeNormal();
            GetWorld()->LineTraceSingleByChannel(Hit,Entry.Value,Entry.Value+Direction*260,ECC_Visibility,Query);
            if(Hit.GetActor()!=Entry.Key) UE_LOG(LogTemp,Display,TEXT("NR_DEMO_DIAG %s hit=%s at=%s bounds=%s mesh=%s coll=%d"),*Entry.Key->Id,*GetNameSafe(Hit.GetActor()),*Hit.ImpactPoint.ToString(),*Entry.Key->Mesh->Bounds.GetBox().ToString(),*GetNameSafe(Entry.Key->Mesh->GetStaticMesh()),(int32)Entry.Key->Mesh->GetCollisionEnabled());
            Check(Hit.GetActor()==Entry.Key,*FString::Printf(TEXT("%s visible to standing player's interaction trace"),*Entry.Key->Id));
        }
        for(auto* Item:{Fuse,Ledger,Tag})
        {
            const FBox B=Item->Mesh->Bounds.GetBox(); const FVector Base(B.GetCenter().X,B.GetCenter().Y,B.Min.Z);
            FHitResult Hit; FCollisionQueryParams Query; Query.bTraceComplex=true; Query.AddIgnoredActor(Item); Query.AddIgnoredActor(Player);
            const bool Supported=GetWorld()->LineTraceSingleByChannel(Hit,Base+FVector(0,0,.5),Base-FVector(0,0,2),ECC_Visibility,Query);
            Check(Supported && FMath::Abs(Hit.ImpactPoint.Z-B.Min.Z)<.3f,*FString::Printf(TEXT("%s grounded on real surface"),*Item->Id));
        }
        Use(Breaker); Check(PowerOut && !PowerRepaired,TEXT("breaker requires physical fuse"));
        Use(Fuse); Use(Fuse); Check(HasFuse && Fuse->IsHidden(),TEXT("fuse pickup is unique"));
        Use(Breaker); Check(PowerRepaired && !PowerOut && !HasFuse,TEXT("fuse restores power"));
        Use(Ledger); Use(Tag); Use(PC); Check(ReportFiled && !DemoReady(),TEXT("first report opens second investigation instead of ending"));
        SaveCheckpoint(); PowerRepaired=false; ReportFiled=false; SetPower(true); RestoreCheckpoint();
        Check(PowerRepaired && !PowerOut && ReportFiled,TEXT("checkpoint restores puzzle and lighting"));
        ANRProp *Phone=nullptr,*Switch=nullptr,*Resident105=nullptr,*Resident203=nullptr,*Panel=nullptr;
        for(auto* P:Props) { if(P->Id==TEXT("phone")) Phone=P; if(P->Id==TEXT("cctv_power")) Switch=P; if(P->Id==TEXT("door_105")) Resident105=P; if(P->Id==TEXT("door_203")) Resident203=P; if(P->Id==TEXT("sealed_panel")) Panel=P; }
        Check(Phone && Switch && Resident105 && Resident203 && Panel,TEXT("second investigation props exist"));
        if(Phone && Switch && Resident105 && Resident203 && Panel)
        {
            const FBox PanelBox=Panel->Mesh->Bounds.GetBox();bool ClearPanel=true;
            for(auto* P:Props) if(P!=Panel && P->Mesh->GetStaticMesh()) {
                const FString MeshName=P->Mesh->GetStaticMesh()->GetName();
                if(P->Id.StartsWith(TEXT("door_")) || MeshName.Contains(TEXT("Window")) || MeshName.Contains(TEXT("Pillar")) || MeshName.Contains(TEXT("Column")))
                    ClearPanel &= !PanelBox.Intersect(P->Mesh->Bounds.GetBox());
            }
            Check(PanelBox.Max.X<-450 && ClearPanel,TEXT("west hatch clears windows columns and doors"));
            FHitResult PanelHit;FCollisionQueryParams PanelQuery;PanelQuery.bTraceComplex=true;PanelQuery.AddIgnoredActor(Player);
            const FVector Eye(-350,-50,469),Aim=PanelBox.GetCenter();
            GetWorld()->LineTraceSingleByChannel(PanelHit,Eye,Aim+(Aim-Eye).GetSafeNormal()*5,ECC_Visibility,PanelQuery);
            Check(PanelHit.GetActor()==Panel && FVector::Dist(Eye,Aim)<260,TEXT("standing west corridor eye can target hatch"));
            Check(!GetWorld()->SweepSingleByChannel(PanelHit,FVector(290,-135,410),FVector(-350,-50,410),FQuat::Identity,ECC_Pawn,FCollisionShape::MakeCapsule(28,85),PanelQuery),TEXT("west hatch approach has capsule clearance"));
            Use(Phone);StopVoice();SubtitleLines.Reset();OpenComplaintLog();SelectComplaintKey(EKeys::One);Escape();
            Check(ComplaintLog.Plan==1,TEXT("notebook selects testimony after manager call"));
            Use(Switch); Check(MonitorOff && !CCTVReset,TEXT("CCTV power can be switched off"));
            Use(Switch); Check(MonitorOff && !CCTVReset,TEXT("immediate CCTV restart is rejected"));
            Use(Resident105); Use(Resident203); Check(ThreatPending && !Threat,TEXT("resident dialogue precedes the second threat"));
            Threat=false; ThreatPending=false; Ghost->SetActorHiddenInGame(true); Use(Panel); DemoSeconds+=61; Use(Switch); Use(PC);
            Check(DemoReady() && RoundFiled && !MonitorOff,TEXT("second round and recovered recording allow final call"));
        }
    }
    UE_LOG(LogTemp,Display,TEXT("NR_DEMO_COMPLETE failures=%d"),Failures);
    FPlatformMisc::RequestExitWithStatus(false,Failures?1:0);
}
