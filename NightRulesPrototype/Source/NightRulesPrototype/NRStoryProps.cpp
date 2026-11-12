#include "NRGame.h"
#include "Engine/World.h"
#include "Engine/StaticMesh.h"
#include "Engine/Texture2D.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Camera/CameraComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformMisc.h"
#include "TimerManager.h"

void ANRGameMode::SetupStoryProps()
{
    const TMap<FString,FString> Names={{TEXT("note"),TEXT("T_PredecessorNote")},{TEXT("service_ledger"),TEXT("T_ServiceLedgerCover")},{TEXT("uv_guide"),TEXT("T_UVGuide")}};
    for(const auto& Entry:Names)StoryTextures.Add(Entry.Key,LoadObject<UTexture2D>(nullptr,*(TEXT("/Game/PrototypeAssets/StoryProps/")+Entry.Value+TEXT(".")+Entry.Value)));
    auto* Guide=Prop(TEXT("uv_guide"),TEXT("UV 점검등 사용 안내"),NRLayout::OfficeWallPoint(FVector(-160,-471,143)),FVector(30,1,40));Guide->Label->SetVisibility(false);
    for(auto* P:Props) {
        if(!StoryTextures.Contains(P->Id))continue;
        const FBox B=P->Mesh->Bounds.GetBox();const bool Flat=P->Id==TEXT("note");
        auto* Face=NewObject<UStaticMeshComponent>(P,TEXT("StoryPaperFace"));P->AddInstanceComponent(Face);
        Face->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Plane.Plane")));
        Face->SetCollisionEnabled(ECollisionEnabled::NoCollision);Face->SetCastShadow(false);Face->RegisterComponent();
        Face->SetWorldLocation(Flat?FVector(B.GetCenter().X,B.GetCenter().Y,B.Max.Z+.06f):FVector(B.GetCenter().X,B.Max.Y+.06f,B.GetCenter().Z));
        Face->SetWorldRotation(Flat?FRotator(0,180,0):FRotator(0,0,90));
        Face->SetWorldScale3D(Flat?FVector((B.GetSize().X-.2f)/100,(B.GetSize().Y-.2f)/100,1):FVector((B.GetSize().X-1)/100,(B.GetSize().Z-1)/100,1));
        auto* M=UMaterialInstanceDynamic::Create(LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/PrototypeAssets/StoryProps/M_StoryPaper.M_StoryPaper")),this);
        M->SetTextureParameterValue(TEXT("Feed"),StoryTextures[P->Id]);Face->SetMaterial(0,M);Face->AttachToComponent(P->Mesh,FAttachmentTransformRules::KeepWorldTransform);
    }
}

void ANRGameMode::StoryPropsTest()
{
    int32 Failures=0; FirstCall=999999;Page.Empty();
    auto Check=[&](bool OK,const TCHAR* What){UE_LOG(LogTemp,Display,TEXT("NR_STORY_PROPS %s %s"),OK?TEXT("PASS"):TEXT("FAIL"),What);if(!OK)++Failures;};
    for(const TCHAR* Font:{TEXT("NanumMyeongjo-Regular.ttf"),TEXT("NanumBrushScript-Regular.ttf")})Check(IFileManager::Get().FileExists(*(FPaths::ProjectContentDir()/TEXT("Fonts")/Font)),TEXT("font available in packaged game"));
    for(const TCHAR* Key:{TEXT("note"),TEXT("service_ledger"),TEXT("uv_guide")}) {
        ANRProp* P=nullptr;for(auto* Candidate:Props)if(Candidate->Id==Key)P=Candidate;
        bool Face=false;if(P){TArray<UStaticMeshComponent*> Parts;P->GetComponents(Parts);for(auto* C:Parts)if(C->GetName()==TEXT("StoryPaperFace"))Face=C->GetMaterial(0)!=nullptr && C->GetCollisionEnabled()==ECollisionEnabled::NoCollision;}
        Check(P && Face && StoryTextures.FindRef(Key),TEXT("physical paper has loaded artwork without intercepting interaction"));
        if(P)Use(P);Check(Page.Contains(Documents.FindRef(Key)),TEXT("E reads complete authored content"));
        if(FString(Key)!=TEXT("service_ledger"))Check(PaperView && StoryDocumentBrush.GetResourceObject()==StoryTextures.FindRef(Key),TEXT("reader uses the same artwork as physical prop"));
        Escape();Check(!PaperView && !RulesView,TEXT("closing paper restores normal view"));
    }
    Red=true;RuleInk=.7f;ShowDocument(TEXT("rules"));TickDisplays(0);
    Check(RulesView && RulesUIMaterial && StoryDocumentBrush.GetResourceObject()==RulesUIMaterial,TEXT("rules reader shows shared animated artwork"));
    if(RulesUIMaterial && RulesMaterial)Check(FMath::IsNearlyEqual(RulesUIMaterial->K2_GetScalarParameterValue(TEXT("Progress")),RulesMaterial->K2_GetScalarParameterValue(TEXT("Progress"))),TEXT("reader and wall reveal identical note progress"));
    Escape();OpenComplaintLog();Check(!PaperView && !RulesView && ComplaintView,TEXT("writing log does not inherit a document image"));
    UE_LOG(LogTemp,Display,TEXT("NR_STORY_PROPS_COMPLETE failures=%d"),Failures);FPlatformMisc::RequestExitWithStatus(false,Failures?1:0);
}

void ANRGameMode::StoryPreview(const FString& Kind)
{
    FirstCall=999999;Page.Empty();Notice.Empty();Player->GetCharacterMovement()->DisableMovement();
    if(Kind==TEXT("rules") || Kind==TEXT("rules-red")) {
        Player->SetActorLocation(NRLayout::OfficeWallPoint(FVector(0,-355,90)));Player->GetController()->SetControlRotation(FRotator(-6,-90,0));
        if(Kind==TEXT("rules-red")){Red=true;RuleInk=1;Evidence.Add(TEXT("rules_rebuttal"));}
    } else if(Kind==TEXT("note-world")) {
        for(auto* P:Props)if(P->Id==TEXT("note")){const FVector At=P->GetActorLocation();Player->SetActorLocation(At+FVector(0,-95,10));Player->GetController()->SetControlRotation((At-Player->Camera->GetComponentLocation()).Rotation());}
    } else if(Kind==TEXT("ledger-world")) {
        Player->SetActorLocation(FVector(NRLayout::StoreX(300),-670,90));Player->GetController()->SetControlRotation(FRotator(0,-90,0));
    } else {
        if(Kind==TEXT("rules-reader")){Red=true;RuleInk=1;ShowDocument(TEXT("rules"));}
        else ShowDocument(Kind);
    }
    FTimerHandle Shot,Exit;GetWorld()->GetTimerManager().SetTimer(Shot,[this]{Player->GetController<APlayerController>()->ConsoleCommand(TEXT("Shot SHOWUI"));},4,false);
    GetWorld()->GetTimerManager().SetTimer(Exit,[]{FPlatformMisc::RequestExit(false);},6,false);
}
