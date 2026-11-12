#include "NRGame.h"
#include "Animation/AnimSequence.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"

namespace {
struct FResidentSpec { int32 Room; const TCHAR* Asset; };
const FResidentSpec Residents[]={{203,TEXT("Minseo")},{301,TEXT("Taeo")},{105,TEXT("Jeongsuk")},
    {204,TEXT("Junho")},{208,TEXT("Jiwoo")},{104,TEXT("Arun")}};
FVector ResidentHome(int32 Room) {
    // Existing occupied rooms; feet clear the room door, bed and wardrobe fronts.
    const float SideOffset=(Room==204 || Room==104)?-2.f:-10.f;
    return NRLayout::DoorAnchor(Room/100-1,Room%100-1)+FVector(SideOffset,85,.5f);
}
}

void ANRGameMode::BuildResidentVisuals()
{
    for(const auto& Spec:Residents) {
        const FString Base=FString(TEXT("/Game/PrototypeAssets/ResidentsV1/"))+Spec.Asset+TEXT("/");
        const FString Name=FString(TEXT("SK_"))+Spec.Asset;
        auto* Mesh=LoadObject<USkeletalMesh>(nullptr,*(Base+Name+TEXT(".")+Name));
        const FString ClipName=FString(TEXT("A_"))+Spec.Asset+TEXT("_Idle");
        auto* Clip=LoadObject<UAnimSequence>(nullptr,*(Base+ClipName+TEXT(".")+ClipName));
        if(!Mesh || !Clip) { UE_LOG(LogTemp,Warning,TEXT("Resident asset missing: %s"),Spec.Asset); continue; }
        auto* Actor=GetWorld()->SpawnActor<AActor>();
        if(!Actor)continue;
        auto* Visual=NewObject<USkeletalMeshComponent>(Actor,TEXT("ResidentVisual"));
        Actor->AddInstanceComponent(Visual);Actor->SetRootComponent(Visual);
        Visual->SetSkeletalMesh(Mesh);Visual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Visual->SetCanEverAffectNavigation(false);
        Visual->VisibilityBasedAnimTickOption=EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered;
        Visual->bEnableUpdateRateOptimizations=true;Visual->RegisterComponent();
        Actor->SetActorLocation(ResidentHome(Spec.Room));Face(Actor,FVector2D(0,-1));
        Actor->Tags.Add(FName(*FString::Printf(TEXT("Resident_%d"),Spec.Room)));
        Visual->PlayAnimation(Clip,true);Visual->SetPosition((Spec.Room%7)*.31f,false);
        ResidentActors.Add(Spec.Room,Actor);
    }
    // Optional greetings are authored in day1.json; they grant no new clues.
}

void ANRGameMode::EndResidentConversation()
{
    if(auto* Door=ResidentConversationDoor.Get())Door->SetDoor(false);
    ResidentConversationDoor.Reset();ResidentConversationRemaining=0;
    for(auto& Link:ResidentDoorChain)if(auto* Part=Link.Get())Part->DestroyComponent();
    ResidentDoorChain.Empty();
}

void ANRGameMode::BeginResidentConversation(const FString& Key)
{
    int32 Room=0;
    if(Key==TEXT("minseo"))Room=203;
    else if(Key==TEXT("resident_104"))Room=104;
    else if(Key==TEXT("resident_105") || Key==TEXT("resident_105_early"))Room=105;
    else if(Key==TEXT("resident_204_greeting"))Room=204;
    else if(Key==TEXT("resident_208_greeting"))Room=208;
    else if(Key==TEXT("resident_301_greeting"))Room=301;
    if(!Room || Finale.Active || !Player || Threat || Dead)return;
    if(!ResidentActors.FindRef(Room).IsValid())return;
    ANRProp* Door=nullptr;
    const FString Id=FString::Printf(TEXT("door_%d"),Room);
    for(auto* P:Props)if(P->Id==Id){Door=P;break;}
    if(!Door || FVector::Dist(Player->GetActorLocation(),Door->GetActorLocation()+FVector(0,0,85))>240)return;
    EndResidentConversation();ResidentConversationDoor=Door;
    // Locked occupancy remains false for saving/story logic. Only a 10-degree slit opens.
    Door->SetDoor(false);Door->TargetYaw=Door->ClosedYaw+10.f*NRLayout::FrontSign;
    Door->SetActorTickEnabled(true);
    ResidentConversationRemaining=FMath::Max(1.f,MessageTime);
    for(int32 I=SubtitleIndex+1;I<SubtitleLines.Num();++I)ResidentConversationRemaining+=SubtitleLines[I].Duration;
    if(auto* LinkMesh=LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cylinder.Cylinder"))) {
        for(int32 I=0;I<7;++I) {
            auto* Link=NewObject<UStaticMeshComponent>(Door);Door->AddInstanceComponent(Link);
            Link->SetStaticMesh(LinkMesh);Link->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            Link->SetCanEverAffectNavigation(false);Link->RegisterComponent();ResidentDoorChain.Add(Link);
        }
    }
}

void ANRGameMode::TickResidentVisuals(float Delta)
{
    for(const auto& Pair:ResidentActors)if(auto* Actor=Pair.Value.Get()) {
        bool Hidden=false;FVector At=ResidentHome(Pair.Key);
        if(Finale.Active) {
            if(Pair.Key==203) {
                // The existing final-night rescue places Minseo in the 3F shower room.
                At=FVector(2375,-320,640.5f);Hidden=Finale.MinseoEvacuated;
            } else Hidden=(Finale.EvacuatedFloors & (1<<(Pair.Key/100-1)))!=0;
        }
        Actor->SetActorHiddenInGame(Hidden);Actor->SetActorLocation(At);
        Face(Actor,FVector2D(0,Finale.Active && Pair.Key==203?1:-1));
        if(auto* Visual=Actor->FindComponentByClass<USkeletalMeshComponent>())
            Visual->bPauseAnims=Paused || Dead || Finished || (!Page.IsEmpty() && !CCTVView);
    }
    auto* Door=ResidentConversationDoor.Get();if(!Door)return;
    if(Dead || Finished || Threat || DreamActive || Finale.Active || SubtitleLines.IsEmpty() ||
        FVector::Dist(Player->GetActorLocation(),Door->GetActorLocation()+FVector(0,0,85))>260) {
        EndResidentConversation();return;
    }
    if(!Paused && Page.IsEmpty())ResidentConversationRemaining-=Delta;
    if(ResidentConversationRemaining<=0){EndResidentConversation();return;}
    const FVector Start=Door->Home+FRotator(0,Door->ClosedYaw,0).RotateVector(FVector(70,5,145));
    const FVector End=Door->GetActorLocation()+Door->GetActorRotation().RotateVector(FVector(68,5,145));
    // Seven small metal segments follow the changing gap; never a collision barrier.
    for(int32 I=0;I<ResidentDoorChain.Num();++I)if(auto* Link=ResidentDoorChain[I].Get()) {
        const float T0=float(I)/ResidentDoorChain.Num(),T1=float(I+1)/ResidentDoorChain.Num();
        const FVector A=FMath::Lerp(Start,End,T0)-FVector(0,0,3*FMath::Sin(T0*PI));
        const FVector B=FMath::Lerp(Start,End,T1)-FVector(0,0,3*FMath::Sin(T1*PI));
        Link->SetWorldLocation((A+B)*.5f);Link->SetWorldRotation(FRotationMatrix::MakeFromZ(B-A).Rotator());
        Link->SetWorldScale3D(FVector(.009f,.009f,FMath::Max(.5f,(B-A).Size())/100.f));
    }
}
