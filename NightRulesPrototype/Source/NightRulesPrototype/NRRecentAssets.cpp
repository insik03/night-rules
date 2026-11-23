#include "NRGame.h"
#include "Engine/World.h"
#include "Engine/StaticMesh.h"
#include "Engine/PointLight.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "TimerManager.h"
#include "HAL/PlatformMisc.h"

void ANRGameMode::BuildRecentAssets()
{
    auto Add=[this](const TCHAR* MeshName,const FString& Id,FVector At,float Yaw=0.f)->ANRProp* {
        const FString Name=FString(TEXT("SM_RA_"))+MeshName;
        const FString Path=TEXT("/Game/PrototypeAssets/RecentAssetsV1/")+Name+TEXT(".")+Name;
        auto* Model=LoadObject<UStaticMesh>(nullptr,*Path);
        if(!Model){UE_LOG(LogTemp,Error,TEXT("Recent asset missing: %s"),*Path);return nullptr;}
        auto* P=Prop(TEXT("recent_")+Id,TEXT(""),At,FVector(1));
        P->Mesh->SetStaticMesh(Model);P->Mesh->EmptyOverrideMaterials();
        P->SetActorScale3D(FVector(1));P->SetActorRotation(FRotator(0,Yaw,0));
        const FBox B=P->Mesh->CalcBounds(P->Mesh->GetComponentTransform()).GetBox();
        P->SetActorLocation(At+FVector(0,0,At.Z-B.Min.Z));P->Home=P->GetActorLocation();
        P->Label->SetVisibility(false);
        return P;
    };
    if(auto* Skin=Add(TEXT("ExteriorSkin"),TEXT("exterior"),FVector::ZeroVector)) {
        Skin->Id=TEXT("exterior_cladding");
        Skin->Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    }
    for(int32 F=0;F<3;++F) {
        const float Z=F*320.f;
        ANRProp* Counter=nullptr;
        for(auto* P:Props) if(P->Id==TEXT("counter") && FMath::Abs(P->GetActorLocation().Z-Z)<2) {Counter=P;break;}
        if(Counter) {
            const FBox B=Counter->Mesh->CalcBounds(Counter->Mesh->GetComponentTransform()).GetBox();
            // Place on the actual worktop, keeping space for the existing kettle.
            Add(TEXT("RiceCooker"),FString::Printf(TEXT("rice_%d"),F),FVector(B.Max.X-40,(B.Min.Y+B.Max.Y)/2,B.Max.Z+.1f));
        }
        const float TL=F==0?1680.f:2575.f;
        const float SL=F==0?2550.f:2175.f;
        Add(TEXT("Trashcan"),FString::Printf(TEXT("bin_%d"),F),FVector(TL+45,-360,Z+.1f));
        Add(TEXT("Bucket"),FString::Printf(TEXT("bucket_%d"),F),FVector(SL+45,-380,Z+.1f));
    }
    Add(TEXT("Washer"),TEXT("washer"),FVector(2900,-750,960.1f));
    Add(TEXT("Cabinet"),TEXT("cabinet"),FVector(3300,-750,960.1f));
    Add(TEXT("LaundryBasket"),TEXT("basket"),FVector(3060,-750,960.1f));
    // A real fixture under the laundry canopy keeps new props readable at night.
    Prop(TEXT("fixture_roof_laundry"),TEXT(""),FVector(3100,-615,1172),FVector(90,15,8));
    auto* LaundryLight=GetWorld()->SpawnActor<APointLight>(FVector(3100,-615,1155),FRotator::ZeroRotator);
    auto* LC=Cast<UPointLightComponent>(LaundryLight->GetLightComponent());
    LC->SetIntensity(1250.f*.7f);LC->SetAttenuationRadius(580);LC->SetLightColor(FLinearColor(.78f,.81f,.75f));
    InteriorLights.Add(LC);LightIntensities.Add(1250.f*.7f);

}

void ANRGameMode::RecentAssetsTest()
{
    FirstCall=999999;IntroComplete=true;Page.Empty();
    FTimerHandle Timer;GetWorld()->GetTimerManager().SetTimer(Timer,[this]{
        int32 Failures=0,Toilets=0,Sinks=0,Recent=0,People=0;
        auto Check=[&](bool OK,const FString& Text){UE_LOG(LogTemp,Display,TEXT("NR_ASSETS %s %s"),OK?TEXT("PASS"):TEXT("FAIL"),*Text);if(!OK)++Failures;};
        for(const auto& Pair:ResidentActors)if(Pair.Value.IsValid())++People;
        Check(People==6,TEXT("six resident actors loaded"));
        for(auto* P:Props) {
            if(P->Id==TEXT("desk")) {
                const FBox B=P->Mesh->CalcBounds(P->Mesh->GetComponentTransform()).GetBox();
                Check(P->Mesh->GetStaticMesh()->GetName()==TEXT("SM_RA_DeskBody"),TEXT("repaired desk loaded"));
                Check(B.GetSize().Equals(FVector(264,55,75),.3f),TEXT("desk matches 264x55x75 cm"));
            }
            if(P->Id.StartsWith(TEXT("drawer_"))) {
                Check(P->Mesh->GetStaticMesh()->GetName().StartsWith(TEXT("SM_RA_Drawer")),TEXT("closed solid drawer mesh loaded"));
                const FVector Before=P->GetActorLocation();
                Use(P);P->Tick(1.f);
                Check(P->Open && FMath::Abs(P->GetActorLocation().Y-Before.Y+38)<.3f,TEXT("drawer opens 38 cm"));
                if(P->StoredItem)Check(!P->StoredItem->IsHidden(),TEXT("UV cartridge visible in open drawer"));
                Use(P);P->Tick(1.f);
                Check(!P->Open && P->GetActorLocation().Equals(Before,.3f),TEXT("drawer closes to original pivot"));
            }

            const bool Sanitary=P->Id==TEXT("toilet") || P->Id==TEXT("sink");
            if(!Sanitary && !P->Id.StartsWith(TEXT("recent_")))continue;
            if(P->Id==TEXT("toilet"))++Toilets;else if(P->Id==TEXT("sink"))++Sinks;else ++Recent;
            UStaticMesh* M=P->Mesh->GetStaticMesh();
            Check(M && M->GetName().StartsWith(TEXT("SM_RA_")),P->Id+TEXT(" uses generated mesh"));
            Check(P->GetActorScale3D().Equals(FVector(1),.001f),P->Id+TEXT(" no runtime stretch"));
            const FBox B=P->Mesh->CalcBounds(P->Mesh->GetComponentTransform()).GetBox();
            UE_LOG(LogTemp,Display,TEXT("NR_ASSET_BOUNDS id=%s mesh=%s min=%s max=%s"),*P->Id,*GetNameSafe(M),*B.Min.ToString(),*B.Max.ToString());
            if(Sanitary) {
                const float Floor=FMath::RoundToFloat(P->GetActorLocation().Z/320.f)*320.f;
                Check(FMath::Abs(B.Min.Z-Floor)<.3f,P->Id+TEXT(" floor contact"));
                if(P->Id==TEXT("toilet"))Check(FMath::Abs(B.Min.Y+892)<.3f && B.Max.Y<-620,P->Id+TEXT(" rear wall and stall aisle clear"));
                else {
                    const float TL=Floor<100?1680.f:2575.f;
                    Check(FMath::Abs(B.Min.X-(TL+6))<.3f,P->Id+TEXT(" rear wall contact"));
                }
            }
        }
        Check(Toilets==9 && Sinks==3 && Recent==12,TEXT("all 24 fixture and prop placements loaded"));
        FCollisionQueryParams Q;Q.bTraceComplex=true;Q.AddIgnoredActor(Player);Q.AddIgnoredActor(Ghost);
        for(int32 F=0;F<3;++F) {
            FHitResult Hit;
            const bool Block=GetWorld()->SweepSingleByChannel(Hit,FVector(400,-135,F*320+90),FVector(3400,-135,F*320+90),FQuat::Identity,ECC_Pawn,FCollisionShape::MakeCapsule(28,80),Q);
            Check(!Block,FString::Printf(TEXT("floor %d chase corridor remains clear"),F+1));
        }
        UE_LOG(LogTemp,Display,TEXT("NR_RECENT_ASSETS_COMPLETE failures=%d"),Failures);
        FPlatformMisc::RequestExitWithStatus(false,Failures?1:0);
    },1.f,false);
}
