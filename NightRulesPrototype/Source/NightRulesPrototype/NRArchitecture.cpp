#include "NRGame.h"
#include "Engine/World.h"
#include "Engine/StaticMesh.h"
#include "Engine/PointLight.h"
#include "Engine/DirectionalLight.h"
#include "Engine/Light.h"
#include "EngineUtils.h"
#include "Components/AudioComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SpotLightComponent.h"
#include "Components/TextRenderComponent.h"
#include "Components/CapsuleComponent.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Materials/MaterialInterface.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "TimerManager.h"
#include "HAL/PlatformMisc.h"

ANRProp* ANRGameMode::ArchitecturePanel(const TCHAR* Asset,FVector At,FVector Size,float Yaw)
{
    auto* P=Prop(TEXT("architecture_skin"),TEXT(""),At,FVector(1));
    const FString Name(Asset),Path=TEXT("/Game/PrototypeAssets/Architecture/")+Name+TEXT(".")+Name;
    if(auto* M=LoadObject<UStaticMesh>(nullptr,*Path)) {
        P->Mesh->SetStaticMesh(M); P->Mesh->EmptyOverrideMaterials();
        P->SetActorScale3D(Size/(M->GetBounds().BoxExtent*2));
    } else { UE_LOG(LogTemp,Error,TEXT("Missing architecture module %s"),*Path); P->SetActorHiddenInGame(true); }
    P->SetActorRotation(FRotator(0,Yaw,0)); P->Label->SetVisibility(false);
    P->Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    if(Name!=TEXT("SM_AM_FireEscape") && Name!=TEXT("SM_AM_TileFloor") && Name!=TEXT("SM_AM_TileWall"))
        if(auto* Mat=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/PrototypeAssets/Architecture/M_AM_WallpaperV3.M_AM_WallpaperV3")))P->Mesh->SetMaterial(0,Mat);
    if(At.Z>=640 && At.Z<910 && Name!=TEXT("SM_AM_FireEscape")) {
        const FString Clean=Name==TEXT("SM_AM_TileFloor")?TEXT("M_AM_CleanFloor"):Name==TEXT("SM_AM_TileWall")?TEXT("M_AM_CleanTile"):TEXT("M_AM_CleanWallpaperV3");
        if(auto* M=LoadObject<UMaterialInterface>(nullptr,*(TEXT("/Game/PrototypeAssets/Architecture/")+Clean+TEXT(".")+Clean))) P->Mesh->SetMaterial(0,M);
    }
    return P;
}

void ANRGameMode::BuildArchitecture()
{
    auto Light=[this](FVector At,float Power=1700.f) {
        auto* L=GetWorld()->SpawnActor<APointLight>(At,FRotator::ZeroRotator);
        auto* C=Cast<UPointLightComponent>(L->GetLightComponent()); C->SetIntensity(Power*.7f);C->SetAttenuationRadius(650);
        C->SetLightColor(At.Z>=640?FLinearColor(.82f,.80f,.74f):FLinearColor(.82f,.77f,.67f));
        InteriorLights.Add(C);LightIntensities.Add(Power*.7f);
    };
    auto Wall=[this](FVector At,FVector Size,bool Tile=false) {
        // Exact solid collision is separate from Meshy's decorative triangulation.
        auto* B=Prop(TEXT("architecture_collision"),TEXT(""),At,Size);B->Label->SetVisibility(false);B->Mesh->SetVisibility(false);B->Mesh->SetCastShadow(false);
        const bool Turn=Size.Y>Size.X;const float Length=Turn?Size.Y:Size.X;
        const int32 Count=FMath::Max(1,FMath::CeilToInt(Length/150.f));
        for(int32 N=0;N<Count;++N) {
            FVector Pos=At; Pos[Turn?1:0]+=-Length/2+(N+.5f)*Length/Count;
            ArchitecturePanel(Tile?TEXT("SM_AM_TileWall"):TEXT("SM_AM_Wall"),Pos,FVector(Length/Count,Turn?Size.X:Size.Y,Size.Z),Turn?90:0);
        }
    };
    auto Opening=[&](float L,float R,float Y,float Z,float DoorX,bool Tile=false,float Width=87.f,float Height=205.5f) {
        const float A=DoorX-Width/2,B=DoorX+Width/2;
        if(A>L)Wall(FVector((L+A)/2,Y,Z+130),FVector(A-L,12,260),Tile);
        if(R>B)Wall(FVector((B+R)/2,Y,Z+130),FVector(R-B,12,260),Tile);
        Wall(FVector(DoorX,Y,Z+(260+Height)/2),FVector(Width,12,260-Height),Tile);
    };
    auto SideOpening=[&](float X,float Top,float Bottom,float Z,float DoorY) {
        const float A=DoorY+43.5f,B=DoorY-43.5f;
        Wall(FVector(X,(Top+A)/2,Z+130),FVector(12,Top-A,260));
        Wall(FVector(X,(Bottom+B)/2,Z+130),FVector(12,B-Bottom,260));
        Wall(FVector(X,DoorY,Z+232.75f),FVector(12,87,54.5f));
    };
    auto TiledFloor=[this](float L,float R,float Z) {
        for(float X=L+75;X<R;X+=150) for(float Y=-275;Y>-900;Y-=150)
            ArchitecturePanel(TEXT("SM_AM_TileFloor"),FVector(FMath::Min(X,R-40),FMath::Max(Y,-850.f),Z+.15f),FVector(FMath::Min(150.f,R-L),150,.3f));
    };
    // Align the rotated mesh's rear bound to the wall's inner face (cm).
    // Do not assume the pivot is the bounds centre or resize an existing asset.
    auto AlignRearToWall=[](ANRProp* Fixture,int32 Axis,double InnerFace) {
        const FBox Bounds=Fixture->Mesh->CalcBounds(Fixture->Mesh->GetComponentTransform()).GetBox();
        FVector At=Fixture->GetActorLocation();
        At[Axis]+=InnerFace-Bounds.Min[Axis];
        Fixture->SetActorLocation(At);
        Fixture->Home=At;
    };
    for(int32 F=0;F<3;++F) {
        const float Z=F*320.f;
        // No rear corridor: the whole southern elevation ends at y=-900.
        Box(FVector(1500,-335,Z-10),FVector(4000,1130,20));
        Box(FVector(3700,15,Z-10),FVector(400,430,20));
        auto* Ceiling=Prop(TEXT("architecture_ceiling"),TEXT(""),FVector(1500,-335,Z+280),FVector(4000,1130,40));
        if(auto* M=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/PrototypeAssets/M_Ceiling.M_Ceiling")))Ceiling->Mesh->SetMaterial(0,M);
        auto* EndCeiling=Prop(TEXT("architecture_ceiling"),TEXT(""),FVector(3700,15,Z+280),FVector(400,430,40));
        EndCeiling->Mesh->SetMaterial(0,Ceiling->Mesh->GetMaterial(0));
        Wall(FVector(1700,-900,Z+130),FVector(4400,16,260));
        Wall(FVector(3900,-335,Z+130),FVector(16,1130,260));
        // West emergency exit, not an extra internal passage.
        SideOpening(-500,230,-900,Z,-135);
        Door(FString::Printf(TEXT("door_arch_escape_%d"),F),TEXT("비상계단"),FVector(-500,-135,Z),-90);
        if(F==0) {
            Opening(-500,350,230,Z,0,false,190,226);
        } else {
            // The window module's opening is 64cm right of its centre.
            // Leave a real 60x80cm aperture instead of a solid wall behind it.
            constexpr float WX=-11.f;
            Wall(FVector(-75,230,Z+60),FVector(850,16,120));
            Wall(FVector(-75,230,Z+230),FVector(850,16,60));
            Wall(FVector((-500+WX-30)/2,230,Z+160),FVector(WX-30+500,16,80));
            Wall(FVector((WX+30+350)/2,230,Z+160),FVector(350-WX-30,16,80));
            Prop(TEXT("glass"),TEXT(""),FVector(WX,230,Z+160),FVector(60,3,80));
            for(float X:{WX-29.f,WX+29.f})
                Prop(TEXT("trim"),TEXT(""),FVector(X,230,Z+160),FVector(2,18,80));
            for(float H:{121.f,199.f})
                Prop(TEXT("trim"),TEXT(""),FVector(WX,230,Z+H),FVector(60,18,2));
        }
        // Widened east end: keep exterior but remove its corridor-facing divider.
        Wall(FVector(3505,230,Z+130),FVector(790,16,260));
        for(int32 I=0;I<=12;++I) Wall(FVector(NRLayout::RoomLeft(I),80,Z+130),FVector(10,300,260));
        for(int32 I=0;I<12;++I)Room(F,I);

        if(F==0) {
            // Former storage split equally; the former office is now unobstructed lobby.
            Wall(FVector(-35,-690,130),FVector(12,420,260));
            Wall(FVector(265,-480,65),FVector(330,12,130));
            // End the frame at the side wall's INNER face (430 - 12/2),
            // not its centreline; the old right jamb was buried inside that wall.
            constexpr float WL=100, WR=424, WB=126, WT=260, Border=8, Depth=18;
            const float WC=(WL+WR)/2, WH=WT-WB;
            Prop(TEXT("glass"),TEXT(""),FVector(WC,-480,(WB+WT)/2),FVector(WR-WL-2*Border,3,WH-2*Border));
            for(float X:{WL+Border/2,WR-Border/2})
                Prop(TEXT("trim"),TEXT(""),FVector(X,-480,(WB+WT)/2),FVector(Border,Depth,WH-2*Border));
            Prop(TEXT("trim"),TEXT(""),FVector(WC,-480,(WB+WT)/2),FVector(6,Depth,WH-2*Border));
            for(float H:{WB+Border/2,WT-Border/2})
                Prop(TEXT("trim"),TEXT(""),FVector(WC,-480,H),FVector(WR-WL,Depth,Border));
            Opening(-35,100,-480,0,NRLayout::OfficeDoorX);
            Door(TEXT("door_office"),TEXT("관리실"),FVector(NRLayout::OfficeDoorX,-480,0),180)->SetDoor(false);
            Opening(-500,-35,-480,0,NRLayout::StoreDoorX);
            Door(TEXT("door_arch_rear_0"),TEXT("창고"),FVector(NRLayout::StoreDoorX,-480,0),180);
        } else {
            SideOpening(140,-200,-480,Z,-310);
            Door(FString::Printf(TEXT("door_arch_store_%d"),F),TEXT("관리 수납실"),FVector(140,-310,Z),90)->SetDoor(false);
            Wall(FVector(0,-200,Z+130),FVector(280,12,260));
            SideOpening(-140,-200,-480,Z,-330);
            Door(FString::Printf(TEXT("door_arch_side_%d"),F),TEXT("옆 수납방"),FVector(-140,-330,Z),-90);
            Wall(FVector(-320,-200,Z+130),FVector(360,12,260));
            Opening(-500,430,-480,Z,290);
            Door(FString::Printf(TEXT("door_arch_rear_%d"),F),TEXT("후면 창고"),FVector(290,-480,Z),180);
        }
        // Keep both entrances free of furniture; investigation supplies live in the left-hand store.

        const float KEnd=F==0?1680:2175,ToiletL=F==0?1680:2575,ToiletR=F==0?2550:3500;
        const float ShowerL=F==0?2550:2175,ShowerR=F==0?3500:2575;
        const float KC=(430+KEnd)/2,TC=(ToiletL+ToiletR)/2,SC=(ShowerL+ShowerR)/2;
        for(float X:{430.f,KEnd,ToiletL,ToiletR,ShowerL,ShowerR})Wall(FVector(X,-550,Z+130),FVector(12,700,260),X!=430.f);
        for(const auto& Area:{FVector(430,KEnd,KC),FVector(ToiletL,ToiletR,TC),FVector(ShowerL,ShowerR,SC)}) {
            Opening(Area.X,Area.Y,-200,Z,Area.Z,true);
            TiledFloor(Area.X,Area.Y,Z);
            Light(FVector(Area.Z,-520,Z+235),2200);
            Prop(TEXT("fixture_common"),TEXT(""),FVector(Area.Z,-520,Z+257),FVector(90,15,8));
        }
        Door(FString::Printf(TEXT("door_arch_kitchen_%d"),F),TEXT("공용주방"),FVector(KC,-200,Z),180);
        Door(FString::Printf(TEXT("door_arch_toilet_%d"),F),TEXT("화장실"),FVector(TC,-200,Z),180);
        Door(FString::Printf(TEXT("door_arch_shower_%d"),F),TEXT("샤워실"),FVector(SC,-200,Z),180);
        // Existing furniture only. Counters on far wall, away from entrances.
        const float CounterX=F==0?900:1350;
        auto* Counter=Prop(TEXT("counter"),TEXT("주방 조리대"),FVector(CounterX,-840,Z),FVector(240,65,88));Counter->SetActorRotation(FRotator(0,180,0));
        Prop(FString::Printf(TEXT("fridge_%d"),F),TEXT("냉장고 열기 / 닫기"),FVector(KEnd-55,-815,Z),FVector(1))->SetActorRotation(FRotator(0,180,0));
        for(float X:F==0?TArray<float>{760,1330}:TArray<float>{900,1700}) {
            auto* T=Prop(TEXT("dining"),TEXT("공용 식탁"),FVector(X,-550,Z),FVector(1));T->SetActorScale3D(FVector(4.f/3.f,4.f/3.f,1));
            for(float Y:{-415.f,-685.f})Face(Prop(TEXT("commonchair"),TEXT(""),FVector(X,Y,Z),FVector(1)),FVector2D(0,Y<-550?1:-1));
        }
        auto* Sink=Prop(TEXT("sink"),TEXT("세면대"),FVector(ToiletL+60,-620,Z),FVector(1));
        Face(Sink,FVector2D(1,0));
        AlignRearToWall(Sink,0,ToiletL+6.0); // 12 cm partition; current SM_Sink: ToiletL+33.5.
        const float Pitch=(ToiletR-ToiletL-210)/3;
        for(int32 N=0;N<3;++N) {
            const float X=ToiletL+210+(N+.5f)*Pitch;
            Wall(FVector(X-Pitch/2,-760,Z+100),FVector(8,280,200),true);
            auto* Toilet=Prop(TEXT("toilet"),TEXT("공용화장실"),FVector(X,-840,Z),FVector(1));
            Face(Toilet,FVector2D(0,1));
            AlignRearToWall(Toilet,1,-892.0); // y=-900 wall, 16 cm thick; current SM_Toilet: -862.5.
        }
        // Stall entrances face the internal aisle; fixtures will be dressed later.
        const int32 Stalls=F==0?4:2; const float SP=(ShowerR-ShowerL-30)/Stalls;
        for(int32 N=1;N<Stalls;++N)Wall(FVector(ShowerL+15+N*SP,-760,Z+100),FVector(7,280,200),true);
        for(int32 N=0;N<Stalls;++N) {
            auto* Rail=Prop(TEXT("shower_rail"),TEXT(""),FVector(ShowerL+15+(N+.5f)*SP,-620,Z+205),FVector(SP-10,3,3));
            Rail->Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        }
        for(int32 N=0;N<8;++N) {
            const float X=-250+N*550, Y=X<350?0:NRLayout::CorridorY;
            Light(FVector(X,Y,Z+235));Prop(TEXT("fixture_corridor"),TEXT(""),FVector(X,Y,Z+257),FVector(90,15,8));
        }
        Light(FVector(F==0?NRLayout::StoreDoorX:0,-690,Z+235),1300);Light(FVector(290,-340,Z+235),1300);
    }
    // Six half-flights: every floor exits at the same north corridor landing.
    Wall(FVector(3500,-550,610),FVector(16,700,1220));
    // Stairwell has no floor ceiling: close the 60cm inter-storey exterior bands.
    for(int32 F=0;F<3;++F) {
        Wall(FVector(3700,-900,F*320+290),FVector(400,16,60));
        Wall(FVector(3900,-550,F*320+290),FVector(16,700,60));
    }
    Box(FVector(3700,-550,-10),FVector(400,700,20));
    for(int32 F=0;F<3;++F) {
        const float Z=F*320;
        Box(FVector(3700,-250,Z-10),FVector(400,100,20));
        Box(FVector(3700,-800,Z+150),FVector(400,200,20));
        for(int32 Half=0;Half<2;++Half) {
            const float X=Half?3790:3610, BZ=Z+Half*160;
            for(int32 N=0;N<8;++N) {
                const float Y=Half?-675+N*50:-325-N*50;
                // Thin treads preserve headroom below the next storey's flight.
                auto* Step=Prop(TEXT("stair_step"),TEXT(""),FVector(X,Y,BZ+(N+1)*20-6),FVector(180,50,12));
                Step->Mesh->SetCollisionResponseToChannel(ECC_Pawn,ECR_Ignore);
                if(auto* M=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/PrototypeAssets/M_Concrete.M_Concrete")))Step->Mesh->SetMaterial(0,M);
            }
            auto* Ramp=Prop(TEXT("stair_walk_ramp"),TEXT(""),FVector(X,-500,BZ+80),FVector(180,431,4));
            Ramp->SetActorRotation(FRotator(0,0,Half?-21.801f:21.801f));Ramp->SetActorHiddenInGame(true);Ramp->Mesh->SetCastShadow(false);
            Ramp->Mesh->SetCollisionResponseToAllChannels(ECR_Ignore);Ramp->Mesh->SetCollisionResponseToChannel(ECC_Pawn,ECR_Block);
            auto* SlopedBase=Prop(TEXT("stair_concrete_base"),TEXT(""),FVector(X,-500,BZ+70),FVector(180,431,12));
            SlopedBase->SetActorRotation(FRotator(0,0,Half?-21.801f:21.801f));SlopedBase->Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            if(auto* M=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/PrototypeAssets/M_Concrete.M_Concrete")))SlopedBase->Mesh->SetMaterial(0,M);
            auto* Rail=Prop(TEXT("stair_rail"),TEXT(""),FVector(Half?3708:3692,-500,BZ+175),FVector(4,431,4));
            Rail->SetActorRotation(FRotator(0,0,Half?-21.801f:21.801f));
            for(int32 N=0;N<5;++N)Prop(TEXT("rail_post"),TEXT(""),FVector(Half?3708:3692,-300-N*100,BZ+(Half?160-N*40:N*40)+45),FVector(4,4,90));
        }
        Light(FVector(3700,-780,Z+385),2000);
    }
    // Fourth-level roof and stair head; same footprint as floors below.
    Box(FVector(1500,-335,950),FVector(4000,1130,20));Box(FVector(3700,15,950),FVector(400,430,20));Box(FVector(3700,-250,950),FVector(400,100,20));
    for(float X:{-500.f,3900.f})Wall(FVector(X,-335,1015),FVector(16,1130,110));
    for(float Y:{-900.f,230.f})Wall(FVector(1700,Y,1015),FVector(4400,16,110));
    Wall(FVector(3900,-550,1090),FVector(16,700,260));Wall(FVector(3700,-900,1090),FVector(400,16,260));
    Opening(3500,3900,-200,960,3790);Door(TEXT("door_arch_roof"),TEXT("옥상"),FVector(3790,-200,960),0);
    auto* Head=Prop(TEXT("architecture_ceiling"),TEXT(""),FVector(3700,-550,1240),FVector(400,700,40));
    Head->Mesh->SetMaterial(0,LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/PrototypeAssets/M_Concrete.M_Concrete")));
    // Covered laundry area and clothesline structure, no new small laundry props.
    for(float X:{2800.f,3400.f})for(float Y:{-400.f,-830.f})Prop(TEXT("roof_laundry_post"),TEXT(""),FVector(X,Y,1065),FVector(6,6,210));
    Prop(TEXT("roof_laundry_cover"),TEXT(""),FVector(3100,-615,1180),FVector(650,480,12));
    for(float Y:{-300.f,-520.f,-740.f}) {
        for(float X:{750.f,2150.f})Prop(TEXT("roof_line_post"),TEXT(""),FVector(X,Y,1055),FVector(5,5,190));
        auto* Line=Prop(TEXT("roof_clothesline"),TEXT(""),FVector(1450,Y,1140),FVector(1400,1,1));Line->Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    }
    // Meshy fire escape is decorative outside the walkable landing. Its noisy
    // triangulation is never used as player collision; closed railings prevent falls.
    for(int32 F=0;F<3;++F)ArchitecturePanel(TEXT("SM_AM_FireEscape"),FVector(-650,-470,F*320+207.5f),FVector(680,165,435),90);
    for(int32 F=0;F<3;++F) {
        Box(FVector(-650,-135,F*320-10),FVector(300,180,20));
        for(float Y:{-225.f,-45.f})Prop(TEXT("escape_guard"),TEXT(""),FVector(-650,Y,F*320+55),FVector(300,7,110));
        Prop(TEXT("escape_guard"),TEXT(""),FVector(-800,-135,F*320+55),FVector(7,180,110));
    }
    for(auto* P:Props) if(P->Id==TEXT("structure")) {
        const float Z=P->GetActorLocation().Z;
        const TCHAR* Name=FMath::IsNearlyEqual(Z,630.f)?TEXT("M_AM_CleanFloor"):FMath::IsNearlyEqual(Z,950.f)?TEXT("M_AM_RoofFloor"):TEXT("M_AM_LinoleumV2a");
        if(Name) if(auto* M=LoadObject<UMaterialInterface>(nullptr,*(FString(TEXT("/Game/PrototypeAssets/Architecture/"))+Name+TEXT(".")+Name))) P->Mesh->SetMaterial(0,M);
    }
}

void ANRGameMode::RelocateOffice()
{
    for(auto* P:Props)if(P->Id==TEXT("wake_trace") || P->Id==TEXT("cctv_power") || P->Id==TEXT("complaint_log"))OfficeAssembly.AddUnique(P);
    for(auto* P:OfficeAssembly) {
        const bool OnRearWall=P->Id==TEXT("rules") || P->Id==TEXT("clock");
        P->SetActorLocation(OnRearWall?NRLayout::OfficeWallPoint(P->GetActorLocation()):NRLayout::OfficePoint(P->GetActorLocation()));
        P->Home=P->GetActorLocation();
    }
    // The office light is spawned at its final position in BuildWorld.
    for(auto* C:AmbientLoops)if(FMath::Abs(C->GetComponentLocation().X)<1 && FMath::Abs(C->GetComponentLocation().Y+340)<1)
        C->SetWorldLocation(NRLayout::OfficePoint(C->GetComponentLocation()));
}

void ANRGameMode::ArchitectureTest()
{
    FirstCall=999999;IntroComplete=true;Page.Empty();
    for(auto* P:Props)if(P->Id.StartsWith(TEXT("door_"))){P->SetDoor(true);P->Tick(1.f);}
    FTimerHandle Timer;GetWorld()->GetTimerManager().SetTimer(Timer,[this]{
        int32 Failures=0;
        auto Check=[&](bool OK,const FString& Text){UE_LOG(LogTemp,Display,TEXT("NR_ARCHITECTURE %s %s"),OK?TEXT("PASS"):TEXT("FAIL"),*Text);if(!OK)++Failures;};
        FCollisionQueryParams Q;Q.bTraceComplex=true;Q.AddIgnoredActor(Player);Q.AddIgnoredActor(Ghost);
        for(auto* P:Props) if(P->Id==TEXT("architecture_skin")) Check(P->Mesh->GetStaticMesh() && !P->IsHidden(),TEXT("Meshy architecture asset loaded"));
        auto Clear=[&](FVector A,FVector B,const FString& Name){
            FHitResult Hit;bool Block=GetWorld()->SweepSingleByChannel(Hit,A,B,FQuat::Identity,ECC_Pawn,FCollisionShape::MakeCapsule(28,80),Q);
            if(Block)UE_LOG(LogTemp,Error,TEXT("ARCH_BLOCK %s actor=%s at=%s"),*Name,*GetNameSafe(Hit.GetActor()),*Hit.ImpactPoint.ToString());
            Check(!Block,Name);
        };
        for(int32 F=0;F<3;++F) {
            const float Z=F*320.f+90;
            const float KC=F==0?1055.f:1302.5f,TC=F==0?2115:3037.5f,SC=F==0?3025:2375;
            for(float X:{KC,TC,SC})Clear(FVector(X,-135,Z),FVector(X,-340,Z),FString::Printf(TEXT("floor %d common entry %.0f"),F+1,X));
            const float StoreX=F==0?NRLayout::StoreDoorX:290;
            Clear(FVector(StoreX,-340,Z),FVector(StoreX,-670,Z),FString::Printf(TEXT("floor %d rear storage entrance"),F+1));
            if(F==0) {
                Clear(FVector(NRLayout::OfficeDoorX,-370,Z),FVector(NRLayout::OfficeDoorX,-650,Z),TEXT("new office entrance clears desk and wall"));
                Clear(FVector(-340,-100,Z),FVector(-340,-390,Z),TEXT("former office now unobstructed lobby"));
                Check(NRLayout::InOffice(Player->GetActorLocation()),TEXT("player starts inside entrance-right office"));
                for(auto* P:Props) {
                    if(P->Id==TEXT("desk") || P->Id==TEXT("rules") || P->Id==TEXT("phone") || P->Id==TEXT("uv_guide"))
                        Check(NRLayout::InOffice(P->GetActorLocation()),TEXT("office essentials in entrance-right half"));
                    if(P->Id==TEXT("service_ledger") || P->Id==TEXT("toolbox") || P->Id==TEXT("cart_cleaning"))
                        Check(NRLayout::InStore(P->GetActorLocation()),TEXT("storage essentials in entrance-left half"));
                }
                FHitResult Partition;
                Check(GetWorld()->SweepSingleByChannel(Partition,FVector(-120,-720,Z),FVector(60,-720,Z),FQuat::Identity,ECC_Pawn,FCollisionShape::MakeCapsule(28,80),Q),TEXT("central wall separates office and storage"));
            } else Clear(FVector(290,-310,Z),FVector(65,-310,Z),TEXT("upper management side door"));
            if(F>0)Clear(FVector(-70,-330,Z),FVector(-300,-330,Z),TEXT("upper management connects side room"));
            for(float X:{600.f,1700.f,2800.f}){
                FHitResult H;bool Back=GetWorld()->LineTraceSingleByChannel(H,FVector(X,-800,Z),FVector(X,-1000,Z),ECC_Visibility,Q);
                Check(Back,TEXT("southern exterior wall closes former rear corridor"));
                bool Floor=GetWorld()->LineTraceSingleByChannel(H,FVector(X,-1100,Z),FVector(X,-1100,Z-200),ECC_Visibility,Q);
                Check(!Floor,TEXT("no remaining second-corridor floor"));
            }
            Clear(FVector(3200,-135,Z),FVector(3200,100,Z),TEXT("widened hall end is open"));
        }
        for(int32 F=1;F<3;++F) {
            const FVector W(-11,230,F*320.f+160);
            bool FoundGlass=false,Blocked=false;
            for(auto* P:Props) {
                if(P->Id==TEXT("glass") && P->GetActorLocation().Equals(W,.1f))FoundGlass=true;
                if(P->Id==TEXT("architecture_collision") && P->Mesh->Bounds.GetBox().IsInside(W))Blocked=true;
            }
            Check(FoundGlass && !Blocked,TEXT("upper lobby window aperture is not sealed by wall"));
        }
        for(auto* P:Props)if(P->Id==TEXT("toolbox")) {
            Check(P->Mesh->GetStaticMesh() && P->Mesh->GetStaticMesh()->GetName()==TEXT("SM_AP_Toolbox"),TEXT("approved Tripo toolbox loaded"));
            const FBox B=P->Mesh->Bounds.GetBox();
            Check(FMath::Abs(B.Min.Z-.1f)<.3f && FMath::Abs(B.GetSize().X-50)<.2f,TEXT("toolbox rests on floor at authored size"));
        }
        int32 Leaves=0;
        for(auto* P:Props)if(P->Id==TEXT("entrance")){++Leaves;P->SetDoor(false);}
        Check(Leaves==2,TEXT("building entrance has two leaves"));
        FHitResult EntranceHit;
        Check(GetWorld()->SweepSingleByChannel(EntranceHit,FVector(0,100,90),FVector(0,360,90),FQuat::Identity,ECC_Pawn,FCollisionShape::MakeCapsule(28,80),Q),TEXT("closed entrance blocks passage"));
        for(auto* P:Props)if(P->Id==TEXT("entrance"))P->SetDoor(true);
        Clear(FVector(0,100,90),FVector(0,360,90),TEXT("open double entrance provides clear passage"));
        UE_LOG(LogTemp,Display,TEXT("NR_ARCHITECTURE_COMPLETE failures=%d"),Failures);FPlatformMisc::RequestExitWithStatus(false,Failures?1:0);
    },1.f,false);
}

void ANRGameMode::ArchitecturePreview(int32 Floor)
{
    Floor=FMath::Clamp(Floor,1,4);const float Z=(Floor-1)*320;
    FirstCall=999999;IntroComplete=true;Page.Empty();Notice.Empty();
    Player->GetCharacterMovement()->DisableMovement();Player->Lamp->SetVisibility(false);Player->FlashlightVisual->SetVisibility(false);
    Player->SetActorEnableCollision(false);Player->SetActorLocation(FVector(1700,-1550,Z+3000));
    Player->GetController()->SetControlRotation(FRotator(-68,90,0));Player->Camera->FieldOfView=76;
    if(FParse::Param(FCommandLine::Get(),TEXT("NRArchitectureDetail"))) {
        Player->SetActorLocation(FVector(-35,-1400,Z+1250));
        Player->GetController()->SetControlRotation(FRotator(-58,90,0));Player->Camera->FieldOfView=66;
    }
    Player->Camera->PostProcessSettings.bOverride_AutoExposureBias=true;Player->Camera->PostProcessSettings.AutoExposureBias=.7f;
    Player->Camera->PostProcessSettings.bOverride_AutoExposureMinBrightness=true;
    Player->Camera->PostProcessSettings.bOverride_AutoExposureMaxBrightness=true;
    Player->Camera->PostProcessSettings.AutoExposureMinBrightness=2;
    Player->Camera->PostProcessSettings.AutoExposureMaxBrightness=2;
    for(TActorIterator<ALight> It(GetWorld());It;++It)It->GetLightComponent()->SetVisibility(false);
    for(auto* P:Props) {
        const FVector At=P->GetActorLocation();
        if(At.Z<Z-20 || At.Z>Z+262 || At.Y>250 || At.Y<-1000 || At.X>4000 || At.X<-820 || P->Id==TEXT("sky") || P->Id.StartsWith(TEXT("fixture")) || P->Id==TEXT("architecture_ceiling") || P->Id==TEXT("roof_laundry_cover"))P->SetActorHiddenInGame(true);
        if(P->Id.StartsWith(TEXT("door_arch_"))){P->SetDoor(true);P->Tick(1);}
    }
    // Inspection-only fill reveals the geometry; play lighting remains at 70%.
    auto* Sun=GetWorld()->SpawnActor<ADirectionalLight>(FVector(0,0,2000),FRotator(-60,-70,0));Sun->GetLightComponent()->SetIntensity(3.f);
    for(float X:{0.f,900.f,1800.f,2800.f,3700.f}){
        auto* L=GetWorld()->SpawnActor<APointLight>(FVector(X,-300,Z+800),FRotator::ZeroRotator);
        auto* C=Cast<UPointLightComponent>(L->GetLightComponent());C->SetIntensity(12000);C->SetAttenuationRadius(2200);
    }
    Player->DisableInput(Cast<APlayerController>(Player->GetController()));
    FTimerHandle Shot,Exit;
    GetWorld()->GetTimerManager().SetTimer(Shot,[this,Floor]{Player->GetController<APlayerController>()->ConsoleCommand(TEXT("HighResShot 1"));},6,false);
    GetWorld()->GetTimerManager().SetTimer(Exit,[]{FPlatformMisc::RequestExit(false);},10,false);
}
