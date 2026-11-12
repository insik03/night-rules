#include "NRGame.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"

void ANRProp::SetupCorePanels()
{
    if(!CorePanels.IsEmpty()) return;
    auto AddPanel=[this](const TCHAR* Name,FVector Pivot)
    {
        const FString Path=FString(TEXT("/Game/PrototypeAssets/CoreProps/"))+Name+TEXT(".")+Name;
        auto* Model=LoadObject<UStaticMesh>(nullptr,*Path);
        if(!Model) return;
        auto* Part=NewObject<UStaticMeshComponent>(this,Name); AddInstanceComponent(Part);
        Part->SetupAttachment(Mesh); Part->SetStaticMesh(Model); Part->SetRelativeLocation(Pivot);
        Part->SetMobility(EComponentMobility::Movable); Part->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
        Part->RegisterComponent(); CorePanels.Add(Part);
    };
    // Imported FBX mirrors Blender's Y. These pivots match the preparation manifest.
    if(Id.StartsWith(TEXT("fridge_")))
    {
        AddPanel(TEXT("SM_CP_FridgeDoor"),FVector(29.2,19,0));
        AddPanel(TEXT("SM_CP_FreezerDoor"),FVector(29.2,19,0));
    }
    else if(Id.StartsWith(TEXT("wardrobe_"))) AddPanel(TEXT("SM_CP_WardrobeDoor"),FVector(20.7,14.5,0));
}

void ANRProp::ApplyCorePanelPose()
{
    for(auto* Panel:CorePanels) if(Panel) Panel->SetRelativeRotation(FRotator(0,CorePanelAngle,0));
}
