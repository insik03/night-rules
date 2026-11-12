#include "NRGame.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Animation/AnimSequence.h"
#include "Camera/CameraComponent.h"
#include "Components/SpotLightComponent.h"
#include "Components/AudioComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInterface.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Engine/Texture2D.h"
#include "Engine/PointLight.h"
#include "Engine/World.h"
#include "Engine/GameViewportClient.h"
#include "UnrealClient.h"
#include "Framework/Application/SlateApplication.h"
#include "InputKeyEventArgs.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerInput.h"
#include "Components/InputComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetRenderingLibrary.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "Styling/CoreStyle.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "HAL/PlatformMisc.h"
#include "TimerManager.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Sound/SoundBase.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SSlider.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScaleBox.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/SBoxPanel.h"
#include "NRMechanics.h"
#include "AudioMixerBlueprintLibrary.h"

namespace { ANRGameMode* GM(const UObject* Object) { return Cast<ANRGameMode>(UGameplayStatics::GetGameMode(Object)); } }

ANRController::ANRController() { OverridePlayerInputClass=UPlayerInput::StaticClass(); }

ANRProp::ANRProp()
{
    Mesh=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh")); SetRootComponent(Mesh);
    Mesh->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube")));
    Label=CreateDefaultSubobject<UTextRenderComponent>(TEXT("Label")); Label->SetupAttachment(Mesh);
    Label->SetWorldSize(18); Label->SetHorizontalAlignment(EHTA_Center);
    Label->SetTextRenderColor(FColor(180,190,185));
    PrimaryActorTick.bCanEverTick=true; PrimaryActorTick.bStartWithTickEnabled=false;
}
void ANRProp::Tick(float D)
{
    // Hinged doors swing toward TargetYaw instead of snapping.
    Super::Tick(D);
    if(CorePanels.Num()>0)
    {
        CorePanelAngle=FMath::FInterpConstantTo(CorePanelAngle,Open?-100.f:0.f,D,150.f);
        ApplyCorePanelPose();
        if(CorePanelAngle==(Open?-100.f:0.f)) SetActorTickEnabled(false);
        return;
    }
    if(Sliding)
    {
        Slide=FMath::FInterpConstantTo(Slide,Open?38.f:0.f,D,65.f);
        SetActorLocation(Home+FVector(0,-Slide,0));
        if(StoredItem) StoredItem->SetActorLocation(StoredItem->Home+FVector(0,-Slide,0));
        if(Slide==(Open?38.f:0.f)) SetActorTickEnabled(false);
        return;
    }
    const float Yaw=GetActorRotation().Yaw, Delta=FMath::FindDeltaAngleDegrees(Yaw,TargetYaw);
    if(FMath::Abs(Delta)<.5f) { SetActorRotation(FRotator(0,TargetYaw,0)); SetActorTickEnabled(false); return; }
    SetActorRotation(FRotator(0,Yaw+FMath::Clamp(Delta,-220*D,220*D),0));
}
void ANRProp::Configure(const FString& Key,const FString& Name,FVector Size)
{
    Id=Key; Caption=Name; Home=GetActorLocation(); Mesh->SetWorldScale3D(Size/100);
    Label->SetAbsolute(false,true,true); Label->SetWorldLocation(Home+FVector(0,-Size.Y/2-3,30));
    Label->SetWorldRotation(FRotator(0,-90,0)); Label->SetText(FText::FromString(Key));
    Label->SetVisibility(Key.StartsWith(TEXT("door_")));
    if(Key.StartsWith(TEXT("door_"))) Label->SetText(FText::FromString(Name));
    const TCHAR* Surface=Key==TEXT("glass") ? TEXT("M_Glass") : Key==TEXT("structure") ? (Size.Z<=20 ? ((FMath::Fmod(Home.Z+320.f,320.f)>200.f && FMath::Fmod(Home.Z+320.f,320.f)<300.f) ? TEXT("M_Ceiling") : TEXT("M_Linoleum")) : TEXT("M_Wallpaper")) : TEXT("Worn_wood");
    const FString MaterialPath=FString(TEXT("/Game/PrototypeAssets/"))+Surface+TEXT(".")+Surface;
    if(auto* Material=LoadObject<UMaterialInterface>(nullptr,*MaterialPath)) Mesh->SetMaterial(0,Material);
    FString Asset;
    if(Key==TEXT("toolbox")) Asset=TEXT("SM_AP_Toolbox");
    else if(Key==TEXT("phone")) Asset=TEXT("SM_CP_Phone");
    else if(Key.StartsWith(TEXT("cart_"))) Asset=TEXT("SM_CP_Cartridge");
    else if(Key==TEXT("chair") || Key==TEXT("officechair") || Key==TEXT("commonchair")) Asset=TEXT("SM_PH_Chair");
    else if(Key==TEXT("entrance")) Asset=TEXT("SM_EntranceDoor");
    else if(Key==TEXT("desk")) Asset=TEXT("SM_CP_DeskBody");
    else if(Key.StartsWith(TEXT("drawer_"))) Asset=TEXT("SM_CP_Drawer")+FString::FromInt(7-FCString::Atoi(*Key.Right(1)));
    else if(Key.StartsWith(TEXT("fridge_"))) Asset=TEXT("SM_CP_FridgeBody");
    else if(Key.StartsWith(TEXT("wardrobe_"))) Asset=TEXT("SM_CP_WardrobeBody");
    else if(Key==TEXT("microwave")) Asset=TEXT("SM_PH_Microwave");
    else if(Key==TEXT("shelves")) Asset=TEXT("SM_PH_Shelves");
    else if(Key==TEXT("kettle")) Asset=TEXT("SM_PH_Kettle");
    else if(Key==TEXT("pot")) Asset=TEXT("SM_PH_Pot");
    else if(Key==TEXT("counter")) Asset=TEXT("SM_KitchenCounter");
    else if(Key==TEXT("dining")) Asset=TEXT("SM_CP_RoundTable");
    else if(Key==TEXT("barebed")) Asset=TEXT("SM_CP_BedFrame");
    else if(Key==TEXT("bed")) Asset=TEXT("SM_PH_Bed");
    else if(Key.StartsWith(TEXT("door_"))) Asset=TEXT("SM_CP_Door");
    else if(Key==TEXT("doorframe")) Asset=TEXT("SM_GS_DoorFrame");
    else if(Key==TEXT("roomdesk")) Asset=TEXT("SM_GS_Desk");
    else if(Key==TEXT("wallshelf")) Asset=TEXT("SM_GS_WallShelf");
    else if(Key==TEXT("aircon")) Asset=TEXT("SM_GS_AirCon");
    else if(Key==TEXT("extinguisher")) Asset=TEXT("SM_PH_Extinguisher");
    else if(Key==TEXT("clock")) Asset=TEXT("SM_PH_WallClock");
    else if(Key==TEXT("cctvcam")) Asset=TEXT("SM_PH_SecurityCamera");
    else if(Key==TEXT("breaker")) Asset=TEXT("SM_GS_Breaker");
    else if(Key==TEXT("sealed_panel")) Asset=TEXT("SM_GS_Hatch");
    else if(Key==TEXT("service_ledger")) Asset=TEXT("SM_GS_Binder");
    else if(Key==TEXT("spare_fuse")) Asset=TEXT("SM_GS_Fuse");
    else if(Key==TEXT("lost_tag")) Asset=TEXT("SM_GS_KeyTag");
    else if(Key==TEXT("complaint_log")) Asset=TEXT("SM_GS_Logbook");
    else if(Key==TEXT("toilet")) Asset=TEXT("SM_Toilet");
    else if(Key==TEXT("sink")) Asset=TEXT("SM_Sink");
    else if(Key==TEXT("locker")) Asset=TEXT("SM_Locker");
    else if(Key==TEXT("roster")) Asset=TEXT("SM_PH_CRT");
    else if(Key==TEXT("cctv") || Key.StartsWith(TEXT("cctv_display_"))) Asset=TEXT("SM_CP_CRT");
    else if(Key.StartsWith(TEXT("fixture"))) Asset=TEXT("SM_Fluorescent");
    if(!Asset.IsEmpty())
    {
        const FString Path=(Asset.StartsWith(TEXT("SM_AP_")) ? TEXT("/Game/PrototypeAssets/ApprovedV2/") : Asset.StartsWith(TEXT("SM_CP_")) ? TEXT("/Game/PrototypeAssets/CoreProps/") : Asset.StartsWith(TEXT("SM_PH_")) || Asset.StartsWith(TEXT("SM_GS_")) ? TEXT("/Game/ThirdParty/PolyHaven/") : TEXT("/Game/PrototypeAssets/"))+Asset+TEXT(".")+Asset;
        if(auto* Model=LoadObject<UStaticMesh>(nullptr,*Path))
        { Mesh->SetStaticMesh(Model); Mesh->SetWorldScale3D(FVector(1)); Mesh->EmptyOverrideMaterials(); }
    }
    // Door leaves pivot on the hinge; the room number sits on the corridor-side plate.
    if(Asset==TEXT("SM_CP_Door")) { Label->SetRelativeLocation(FVector(39,-NRLayout::FrontSign*4.1f,166)); Label->SetWorldSize(6); Label->SetTextRenderColor(FColor(40,40,40)); }
    // Frame collision hull would seal the opening; the walls already block.
    if(Asset==TEXT("SM_GS_DoorFrame")) Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    SetupCorePanels();
}
void ANRProp::SetDoor(bool Value)
{
    Open=Value;
    if(CorePanels.Num()>0) { SetActorTickEnabled(true); return; }
    if(Sliding) { Caption=Open?TEXT("책상 서랍 닫기"):TEXT("책상 서랍 열기"); SetActorTickEnabled(true); return; }
    if(Id==TEXT("entrance"))
    {
        const float Side=Home.X<0?-1.f:1.f;
        SetActorLocation(Home+(Value?FVector(Side*45,45,0):FVector::ZeroVector));
        SetActorRotation(FRotator(0,Value?-Side*90.f:0.f,0));
        return;
    }
    // Every interior door opens 90 degrees into its room.
    TargetYaw=ClosedYaw+(Value?90.f*NRLayout::FrontSign:0.f); SetActorTickEnabled(true);
    Mesh->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
}

ANRPlayer::ANRPlayer()
{
    OverrideInputComponentClass=UInputComponent::StaticClass();
    PrimaryActorTick.bCanEverTick=true; GetCapsuleComponent()->InitCapsuleSize(28,85);
    Camera=CreateDefaultSubobject<UCameraComponent>(TEXT("Camera")); Camera->SetupAttachment(GetRootComponent());
    Camera->SetRelativeLocation(FVector(0,0,62)); Camera->bUsePawnControlRotation=true; Camera->FieldOfView=85;
    Lamp=CreateDefaultSubobject<USpotLightComponent>(TEXT("Flashlight")); Lamp->SetupAttachment(Camera);
    Lamp->SetRelativeLocation(FVector(15,0,-8)); Lamp->SetIntensity(1120); Lamp->SetAttenuationRadius(1600);
    Lamp->SetInnerConeAngle(14); Lamp->SetOuterConeAngle(30);
    FlashlightVisual=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("FlashlightVisual"));
    FlashlightVisual->SetupAttachment(Camera);
    FlashlightVisual->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Game/PrototypeAssets/CoreProps/SM_CP_Flashlight.SM_CP_Flashlight")));
    FlashlightVisual->SetRelativeLocation(FVector(27,13,-18));
    FlashlightVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision); FlashlightVisual->SetCastShadow(false);
    GetCharacterMovement()->MaxWalkSpeed=220; GetCharacterMovement()->MaxStepHeight=30;
    GetCharacterMovement()->BrakingDecelerationWalking=1000;
    bUseControllerRotationYaw=true;
}
bool ANRPlayer::CanMove() const { const auto* G=GM(this); return G && !G->Dead && !G->Finished && G->Finale.Outcome.IsEmpty() && !G->Paused && G->Page.IsEmpty() && !(G->DreamActive && G->DreamTime>=18); }
void ANRPlayer::SetupPlayerInputComponent(UInputComponent* I)
{
    Super::SetupPlayerInputComponent(I);
    I->BindKey(EKeys::LeftShift,IE_Pressed,this,&ANRPlayer::SprintStart);
    I->BindKey(EKeys::LeftShift,IE_Released,this,&ANRPlayer::SprintStop);
    I->BindKey(EKeys::LeftControl,IE_Pressed,this,&ANRPlayer::CrouchStart);
    I->BindKey(EKeys::LeftControl,IE_Released,this,&ANRPlayer::CrouchStop);
    GetCharacterMovement()->GetNavAgentPropertiesRef().bCanCrouch=true;
    GetCharacterMovement()->SetCrouchedHalfHeight(50.f);
    GetCharacterMovement()->MaxWalkSpeedCrouched=110.f;
    I->BindAxis("Forward",this,&ANRPlayer::Forward); I->BindAxis("Right",this,&ANRPlayer::Right);
    I->BindAxis("Turn",this,&ANRPlayer::Turn); I->BindAxis("LookUp",this,&ANRPlayer::Look);
    I->BindAction("Interact",IE_Pressed,this,&ANRPlayer::Interact);
    I->BindAction("Light",IE_Pressed,this,&ANRPlayer::ToggleLight);
    I->BindAction("UV",IE_Pressed,this,&ANRPlayer::ToggleUV);
    I->BindAction("Reload",IE_Pressed,this,&ANRPlayer::Reload);
    I->BindAction("Journal",IE_Pressed,this,&ANRPlayer::Journal);
    I->BindAction("Escape",IE_Pressed,this,&ANRPlayer::Escape);
    I->BindAction("Restart",IE_Pressed,this,&ANRPlayer::Restart);
}
void ANRPlayer::SprintStart() { if(CanMove()) SprintHeld=true; }
void ANRPlayer::SprintStop() { SprintHeld=false; }
void ANRPlayer::CrouchStart() { if(CanMove()) { SprintHeld=false; Crouch(); } }
void ANRPlayer::CrouchStop() { UnCrouch(); }
void ANRPlayer::Forward(float V) { if(CanMove()) AddMovementInput(GetActorForwardVector(),V); }
void ANRPlayer::Right(float V) { if(CanMove()) AddMovementInput(GetActorRightVector(),V); }
void ANRPlayer::Turn(float V) { if(CanMove()) AddControllerYawInput(V*GM(this)->MouseSensitivity); }
void ANRPlayer::Look(float V) { if(CanMove()) AddControllerPitchInput(V*GM(this)->MouseSensitivity); }
void ANRPlayer::Interact() { if(CanMove()) { if(GM(this)->ReadUVClue()) return; if(Focus) GM(this)->Use(Focus); } }
void ANRPlayer::ToggleLight() { if(CanMove()) LightOn=!LightOn; }
void ANRPlayer::ToggleUV()
{
    if(!CanMove()) return;
    if(UVRemaining<=0) { GM(this)->Message(Cartridges>0?TEXT("장착된 카트리지가 비었다. T로 새 카트리지를 끼우자."):TEXT("장착된 카트리지가 없다.")); return; }
    UV=!UV; LightOn=true; GM(this)->Record(TEXT("flashlight"),UV?TEXT("uv"):TEXT("normal"));
}
void ANRPlayer::Reload()
{
    if(!CanMove()) return;
    if(UVRemaining>0) { GM(this)->Message(TEXT("장착된 카트리지에 잔량이 있습니다. Q로 UV 전환.")); return; }
    if(Cartridges<=0) { GM(this)->Message(TEXT("예비 카트리지가 없다.")); return; }
    --Cartridges; UVRemaining=GM(this)->UVCapacity; GM(this)->Record(TEXT("cartridge"),TEXT("loaded"));
    GM(this)->Message(GM(this)->Evidence.Contains(TEXT("uv"))?TEXT("장착 완료 · UV 45초. Q로 UV를 켜고 수상한 표시를 비춰 보자.\n밝게 드러난 흔적을 보며 E로 기록한다."):TEXT("장착 완료 · UV 45초. Q로 UV를 켜고 흔적이 남았을 만한 곳을 비춰 보자.\n밝게 드러난 흔적을 보며 E로 기록한다."));
}
void ANRPlayer::Journal() { if(CanMove()) GM(this)->OpenJournal(); }
void ANRPlayer::Escape() { if(auto* G=GM(this)) G->Escape(); }
void ANRPlayer::Restart()
{
    auto* G=GM(this); if(!G) return;
    if(G->ExecutionActive) return;
    if(G->Dead || G->Paused) G->RestoreCheckpoint();
    else if(G->Finished) UGameplayStatics::OpenLevel(this,FName(TEXT("/Engine/Maps/Entry")));
}
void ANRPlayer::Tick(float D)
{
    Super::Tick(D); auto* G=GM(this); if(!G) return;
    if(!CanMove()) SprintHeld=false;
    GetCharacterMovement()->MaxWalkSpeed=SprintHeld && !bIsCrouched?350.f:220.f;
    FVector CameraAt=Camera->GetRelativeLocation();
    CameraAt.Z=FMath::FInterpTo(CameraAt.Z,bIsCrouched?35.f:62.f,D,12.f);
    Camera->SetRelativeLocation(CameraAt);
    TickCCTVBody(D);
    Focus=nullptr;
    if(CanMove())
    {
        UVRemaining=NRMechanics::Drain(UVRemaining,D,UV && LightOn);
        if(UV && UVRemaining<=0) { UV=false; G->Message(TEXT("UV 소진. 일반광으로 전환됩니다.")); }
        if(GetVelocity().Size2D()>20 && GetCharacterMovement()->IsMovingOnGround())
        { StepTime-=D; if(StepTime<=0) { G->PlayFootstep(false,GetActorLocation()-FVector(0,0,80),bIsCrouched?.25f:SprintHeld?1.f:.7f); StepTime=bIsCrouched?.8f:SprintHeld?.35f:.55f; } }
        // Use visible triangles for interaction. A sink's coarse movement hull
        // bridges its tap and counter and otherwise hides objects on the counter.
        FHitResult Hit; FCollisionQueryParams Params; Params.bTraceComplex=true; Params.AddIgnoredActor(this);
        const FVector Start=Camera->GetComponentLocation();
        if(GetWorld()->LineTraceSingleByChannel(Hit,Start,Start+Camera->GetForwardVector()*260,ECC_Visibility,Params)) Focus=Cast<ANRProp>(Hit.GetActor());
    }
    // Close inspection must preserve scratches/prints instead of bleaching them.
    Lamp->SetIntensity(UV?1260.f:1120.f);
    Lamp->SetVisibility(LightOn); Lamp->SetLightColor(UV ? FLinearColor(.38f,.08f,1.f) : FLinearColor(1,.88f,.72f));
}

ANRGameMode::ANRGameMode() { PrimaryActorTick.bCanEverTick=true; DefaultPawnClass=ANRPlayer::StaticClass(); PlayerControllerClass=ANRController::StaticClass(); }
void ANRGameMode::LoadData()
{
    FString Raw; TSharedPtr<FJsonObject> Data;
    if(!FFileHelper::LoadFileToString(Raw,*(FPaths::ProjectContentDir()/TEXT("Data/day1.json"))) || !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Raw),Data))
    { UE_LOG(LogTemp,Error,TEXT("Missing or invalid Content/Data/day1.json")); return; }
    FirstCall=Data->GetNumberField(TEXT("first_call_seconds")); WitnessWindow=Data->GetNumberField(TEXT("witness_window_seconds"));
    SecondCall=Data->GetNumberField(TEXT("second_call_seconds")); UVCapacity=Data->GetNumberField(TEXT("uv_capacity_seconds"));
    const auto Annotation=Data->GetObjectField(TEXT("rule_annotation"));
    AnnotatedRule=Annotation->GetIntegerField(TEXT("rule")); RuleDenial=Annotation->GetStringField(TEXT("denial")); RuleReply=Annotation->GetStringField(TEXT("reply"));
    for(const auto& Item:Data->GetObjectField(TEXT("documents"))->Values) Documents.Add(FString(*Item.Key),Item.Value->AsString());
}
void ANRGameMode::BeginPlay()
{
    Super::BeginPlay(); LoadPreferences(); LoadData(); BuildWorld(); BuildResidentVisuals();
    Player=Cast<ANRPlayer>(UGameplayStatics::GetPlayerCharacter(this,0));
    if(Player) { Player->SetActorLocation(NRLayout::OfficePoint(FVector(85,-395,100))); Player->GetController()->SetControlRotation(FRotator(0,110,0)); Player->GetCharacterMovement()->SetMovementMode(MOVE_Walking); Player->GetCharacterMovement()->Activate(true); }
    SetupCCTV();
    if(FParse::Param(FCommandLine::Get(),TEXT("NRCCTVStackTest"))) GetWorld()->GetTimerManager().SetTimerForNextTick(this,&ANRGameMode::CCTVStackTest);
    for(auto* P:Props) if(P->Id==TEXT("rules"))
    {
        auto* Surface=NewObject<UStaticMeshComponent>(P,TEXT("RulesSurface")); P->AddInstanceComponent(Surface);
        Surface->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Plane.Plane")));
        Surface->SetWorldLocation(NRLayout::OfficeWallPoint(FVector(0,-469.9f,140))); Surface->SetWorldRotation(FRotator(0,0,90)); Surface->SetWorldScale3D(FVector(.68f,.88f,1));
        Surface->SetCollisionEnabled(ECollisionEnabled::NoCollision); Surface->SetCastShadow(false); Surface->RegisterComponent();
        RulesMaterial=UMaterialInstanceDynamic::Create(LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/PrototypeAssets/M_RulesInk.M_RulesInk")),this);
        RulesMaterial->SetTextureParameterValue(TEXT("Feed"),LoadObject<UTexture2D>(nullptr,TEXT("/Game/PrototypeAssets/T_RulesPage.T_RulesPage"))); Surface->SetMaterial(0,RulesMaterial);
    }
    SetupDemo();
    SetupPursuitFoley();
    SetupScore();
    SetupComplaintLog();
    RelocateOffice();
    SetupStoryProps();
    SetupFinale();
    if(FParse::Param(FCommandLine::Get(),TEXT("NRComplaintLogTest"))) GetWorld()->GetTimerManager().SetTimerForNextTick(this,&ANRGameMode::ComplaintLogTest);
    if(FParse::Param(FCommandLine::Get(),TEXT("NRInvestigationPlanTest"))) GetWorld()->GetTimerManager().SetTimerForNextTick(this,&ANRGameMode::InvestigationPlanTest);
    BuildScreen(); Page.Empty(); Message(TEXT("WASD 이동 / 마우스 시점 / E 조사 / F 손전등 / J 기록"),12);
    UpdatePointerInput(true);
    if(FParse::Param(FCommandLine::Get(),TEXT("NRPointerTest"))) GetWorld()->GetTimerManager().SetTimerForNextTick(this,&ANRGameMode::PointerInputTest);
    Record(TEXT("session"),TEXT("start")); SaveCheckpoint();
    if(FParse::Param(FCommandLine::Get(),TEXT("NRFinale")))StartFinale();
    if(FParse::Param(FCommandLine::Get(),TEXT("NRFinaleTest")))GetWorld()->GetTimerManager().SetTimerForNextTick(this,&ANRGameMode::FinaleTest);
    if(FParse::Param(FCommandLine::Get(),TEXT("NRFinaleWalkTest")))GetWorld()->GetTimerManager().SetTimerForNextTick(this,&ANRGameMode::FinaleWalkTest);
    FString EndingPreview;if(FParse::Value(FCommandLine::Get(),TEXT("NRFinalePreview="),EndingPreview))FinalePreview(EndingPreview);
    if(FParse::Param(FCommandLine::Get(),TEXT("NRPolishTest"))) GetWorld()->GetTimerManager().SetTimerForNextTick(this,&ANRGameMode::PolishTest);
    if(FParse::Param(FCommandLine::Get(),TEXT("NRCrawlPreview"))) GetWorld()->GetTimerManager().SetTimerForNextTick(this,&ANRGameMode::CrawlPreview);
    if(FParse::Param(FCommandLine::Get(),TEXT("NRScoreTest"))) GetWorld()->GetTimerManager().SetTimerForNextTick(this,&ANRGameMode::ScoreTest);
    if(FParse::Param(FCommandLine::Get(),TEXT("NRPursuitTest"))) GetWorld()->GetTimerManager().SetTimerForNextTick(this,&ANRGameMode::PursuitPresentationTest);
    if(FParse::Param(FCommandLine::Get(),TEXT("NRArchitectureTest"))) ArchitectureTest();
    if(FParse::Param(FCommandLine::Get(),TEXT("NRStoryPropsTest"))) GetWorld()->GetTimerManager().SetTimerForNextTick(this,&ANRGameMode::StoryPropsTest);
    FString PaperPreview;if(FParse::Value(FCommandLine::Get(),TEXT("NRStoryPreview="),PaperPreview))StoryPreview(PaperPreview);
    int32 ArchitectureFloor=0; if(FParse::Value(FCommandLine::Get(),TEXT("NRArchitectureFloor="),ArchitectureFloor)) ArchitecturePreview(ArchitectureFloor);
    if(FParse::Param(FCommandLine::Get(),TEXT("NRStairPreview"))) {
        FirstCall=9999; Notice.Empty(); SubtitleLines.Reset();
        Player->SetActorLocation(FVector(3700,-150,90)); Player->GetController()->SetControlRotation(FRotator(16,-90,0));
        FTimerHandle Shot,Exit;
        GetWorld()->GetTimerManager().SetTimer(Shot,[this]{Player->GetController<APlayerController>()->ConsoleCommand(TEXT("Shot SHOWUI"));},5.f,false);
        GetWorld()->GetTimerManager().SetTimer(Exit,[]{FPlatformMisc::RequestExit(false);},8.f,false);
    }
    if(FParse::Param(FCommandLine::Get(),TEXT("NRRunPreview"))) {
        UAudioMixerBlueprintLibrary::StartRecordingOutput(this,8);
        UE_LOG(LogTemp,Display,TEXT("NR_CAPTURE_AUDIO_START world_time=%.4f"),GetWorld()->GetTimeSeconds());
        FTimerHandle AudioEnd;GetWorld()->GetTimerManager().SetTimer(AudioEnd,[this]{UAudioMixerBlueprintLibrary::StopRecordingOutput(this,EAudioRecordingExportType::WavFile,TEXT("chair_chase_audio"),FPaths::ProjectSavedDir()/TEXT("Verification"));},7.6f,false);
        FirstCall=9999; IntroComplete=true; Notice.Empty(); SubtitleLines.Reset();
        Player->SetActorLocation(FVector(900,NRLayout::CorridorY,410)); Player->GetController()->SetControlRotation(FRotator(-6,0,0));
        // Film real pursuit: route finding, collision, speed-matched animation and death.
        StartThreat(); ThreatTime=2.5f; // Skip only the pre-movement warning for this capture.
        Ghost->SetActorLocation(FVector(2300,NRLayout::CorridorY,410)); Ghost->SetActorRotation(FRotator(0,180,0));
        FTimerHandle Shot,Exit,Trace,Check;
        GetWorld()->GetTimerManager().SetTimer(Trace,[this]{UE_LOG(LogTemp,Display,TEXT("NR_RUN_CAPTURE distance=%.1f speed=%.1f dead=%d"),FVector::Dist2D(Ghost->GetActorLocation(),Player->GetActorLocation()),GhostSpeed,Dead);},.25f,true);
        GetWorld()->GetTimerManager().SetTimer(Check,[this]{const bool Caught=Dead && Ghost->GetActorLocation().X<1000;UE_LOG(LogTemp,Display,TEXT("NR_RUN_CAPTURE_COMPLETE failures=%d"),Caught?0:1);},6.f,false);
        GetWorld()->GetTimerManager().SetTimer(Shot,[this]{Player->GetController<APlayerController>()->ConsoleCommand(TEXT("Shot SHOWUI"));},2.5f,false);
        GetWorld()->GetTimerManager().SetTimer(Exit,[]{FPlatformMisc::RequestExit(false);},8.f,false);
    }
    SetupInvestigation();
    if(FParse::Param(FCommandLine::Get(),TEXT("NROfficeCCTVTest"))) GetWorld()->GetTimerManager().SetTimerForNextTick(this,&ANRGameMode::OfficeCCTVTest);
    if(FParse::Param(FCommandLine::Get(),TEXT("NRProtagonistTest"))) GetWorld()->GetTimerManager().SetTimerForNextTick(this,&ANRGameMode::ProtagonistTest);
    if(FParse::Param(FCommandLine::Get(),TEXT("NRInvestigationTest"))) GetWorld()->GetTimerManager().SetTimerForNextTick(this,&ANRGameMode::InvestigationTest);
    if(FParse::Param(FCommandLine::Get(),TEXT("NRExperienceTest"))) GetWorld()->GetTimerManager().SetTimerForNextTick(this,&ANRGameMode::ExperienceTest);
    const bool RulesReplyPreview=FParse::Param(FCommandLine::Get(),TEXT("NRRulesReplyPreview"));
    const bool RulesPreview=RulesReplyPreview || FParse::Param(FCommandLine::Get(),TEXT("NRRulesPreview"));
    const bool SettingsPreview=FParse::Param(FCommandLine::Get(),TEXT("NRSettingsPreview"));
    const bool ReplayPreview=FParse::Param(FCommandLine::Get(),TEXT("NRReplayPreview"));
    if(RulesPreview || SettingsPreview || ReplayPreview) {
        Notice.Empty(); SubtitleLines.Reset(); FirstCall=9999;
        if(RulesPreview) { Player->SetActorLocation(NRLayout::OfficeWallPoint(FVector(0,-355,90))); Player->GetController()->SetControlRotation(FRotator(-6,-90,0)); }
        if(RulesReplyPreview) { Red=true; ShowDocument(TEXT("rules")); }
        if(SettingsPreview) { Escape(); SettingsOpen=true; }
        if(ReplayPreview) for(auto* P:Props) if(P->Id==TEXT("cctv")) Use(P);
        FTimerHandle Select,Shot,Exit;
        if(ReplayPreview) GetWorld()->GetTimerManager().SetTimer(Select,[this]{ReplayCCTV(0);},4.f,false);
        GetWorld()->GetTimerManager().SetTimer(Shot,[this]{Player->GetController<APlayerController>()->ConsoleCommand(TEXT("Shot SHOWUI"));},6.f,false);
        GetWorld()->GetTimerManager().SetTimer(Exit,[]{FPlatformMisc::RequestExit(false);},8.f,false);
    }
    if(FParse::Param(FCommandLine::Get(),TEXT("NRUVFragmentPreview"))) {
        FirstCall=9999;IntroComplete=true;Notice.Empty();SubtitleLines.Reset();
        WakeTrace->SetActorHiddenInGame(false);Player->UV=true;Player->UVRemaining=45;
        Player->SetActorLocation(NRLayout::OfficePoint(FVector(65,-345,90)));Player->GetController()->SetControlRotation(FRotator(-40,90,0));
        FTimerHandle Shot,Exit;
        GetWorld()->GetTimerManager().SetTimer(Shot,[this]{Player->GetController<APlayerController>()->ConsoleCommand(TEXT("Shot SHOWUI"));},5.f,false);
        GetWorld()->GetTimerManager().SetTimer(Exit,[]{FPlatformMisc::RequestExit(false);},8.f,false);
    }
    if(FParse::Param(FCommandLine::Get(),TEXT("NRWithdrawalWalkTest"))) GetWorld()->GetTimerManager().SetTimerForNextTick(this,&ANRGameMode::WithdrawalWalkTest);
    if(FParse::Param(FCommandLine::Get(),TEXT("NRChoice202Test"))) GetWorld()->GetTimerManager().SetTimerForNextTick(this,&ANRGameMode::Choice202Test);
    if(FParse::Param(FCommandLine::Get(),TEXT("NRFeedbackTest"))) GetWorld()->GetTimerManager().SetTimerForNextTick(this,&ANRGameMode::FeedbackTest);
    if(FParse::Param(FCommandLine::Get(),TEXT("NRDemoWalk"))) GetWorld()->GetTimerManager().SetTimerForNextTick(this,&ANRGameMode::DemoWalkTest);
    if(FParse::Param(FCommandLine::Get(),TEXT("NRDemoTest"))) GetWorld()->GetTimerManager().SetTimerForNextTick(this,&ANRGameMode::DemoTest);
    if(FParse::Param(FCommandLine::Get(),TEXT("NRPresentationTest"))) GetWorld()->GetTimerManager().SetTimerForNextTick(this,&ANRGameMode::InspectPresentation);
    if(FParse::Param(FCommandLine::Get(),TEXT("NRSubtitlePreview")))
    {
        Player->SetActorLocation(NRLayout::OfficePoint(FVector(85,-395,90)));
        for(auto* P:Props) if(P->Id==TEXT("phone")) Player->GetController()->SetControlRotation((P->Mesh->Bounds.Origin-Player->Camera->GetComponentLocation()).Rotation());
        SubtitleLines.Reset(); Notice=TEXT("“총무님, 아까 202호 안에서 문을 두드리셨잖아요. 그런데 지금 관리실에 계신 게 맞아요?”\n문 너머 목소리가 멎고, 복도 끝에서 같은 말이 들린다.");
        SubtitleSource=TEXT("203호 · 김민서");
        FTimerHandle Shot,Exit;
        GetWorld()->GetTimerManager().SetTimer(Shot,[this]{Player->GetController<APlayerController>()->ConsoleCommand(TEXT("Shot SHOWUI"));},5.f,false);
        GetWorld()->GetTimerManager().SetTimer(Exit,[]{FPlatformMisc::RequestExit(false);},8.f,false);
    }
    if(FParse::Param(FCommandLine::Get(),TEXT("NRDrawerPreview")))
    {
        IntroComplete=true; Notice.Empty(); SubtitleLines.Reset();
        Player->SetActorLocation(FVector(-85,-367,90)); Player->GetController()->SetControlRotation(FRotator(-46,107,0));
        for(auto* P:Props) if(P->Id==TEXT("drawer_4")) Use(P);
        FTimerHandle Shot,Exit;
        GetWorld()->GetTimerManager().SetTimer(Shot,[this]{Player->GetController<APlayerController>()->ConsoleCommand(TEXT("Shot SHOWUI"));},5.f,false);
        GetWorld()->GetTimerManager().SetTimer(Exit,[]{FPlatformMisc::RequestExit(false);},8.f,false);
    }
    if(FParse::Param(FCommandLine::Get(),TEXT("NRPausePreview")))
    {
        Escape();
        FTimerHandle Shot,Exit;
        GetWorld()->GetTimerManager().SetTimer(Shot,[this]{Player->GetController<APlayerController>()->ConsoleCommand(TEXT("Shot SHOWUI"));},5.f,false);
        GetWorld()->GetTimerManager().SetTimer(Exit,[]{FPlatformMisc::RequestExit(false);},8.f,false);
    }
    if(FParse::Param(FCommandLine::Get(),TEXT("NRBlackoutPreview")))
    {
        Player->SetActorLocation(FVector(1150,NRLayout::CorridorY,410)); Player->GetController()->SetControlRotation(FRotator(-5,0,0));
        SetPower(true); Paused=true; Notice.Empty();
        FTimerHandle Shot,Exit;
        GetWorld()->GetTimerManager().SetTimer(Shot,[this]{Player->GetController<APlayerController>()->ConsoleCommand(TEXT("Shot SHOWUI"));},7.f,false);
        GetWorld()->GetTimerManager().SetTimer(Exit,[]{FPlatformMisc::RequestExit(false);},10.f,false);
    }
    if(FParse::Param(FCommandLine::Get(),TEXT("NRGhostPreview")))
    {
        Player->SetActorLocation(FVector(900,NRLayout::CorridorY,410)); Player->GetController()->SetControlRotation(FRotator(-8,0,0));
        Ghost->SetActorLocation(FVector(1170,NRLayout::CorridorY,410)); Ghost->SetActorRotation(FRotator(0,180,0)); Ghost->SetActorHiddenInGame(false);
        Paused=true;
        UE_LOG(LogTemp,Display,TEXT("GHOST_VISUAL_CHECK mesh=%s animation=%s"),GhostVisual?TEXT("loaded"):TEXT("missing"),GhostVisual && GhostVisual->IsPlaying()?TEXT("playing"):TEXT("missing"));
        FTimerHandle Shot,Exit;
        GetWorld()->GetTimerManager().SetTimer(Shot,[this]{Player->GetController<APlayerController>()->ConsoleCommand(TEXT("Shot SHOWUI"));},7.f,false);
        GetWorld()->GetTimerManager().SetTimer(Exit,[]{FPlatformMisc::RequestExit(false);},10.f,false);
    }
    const bool PreviewUpperCCTV=FParse::Param(FCommandLine::Get(),TEXT("NRCCTVUpperPreview"));
    const bool PreviewCCTV=FParse::Param(FCommandLine::Get(),TEXT("NRCCTVPreview")) || PreviewUpperCCTV;
    const bool PreviewMessage=FParse::Param(FCommandLine::Get(),TEXT("NRMessagePreview"));
    const bool PreviewDesk=FParse::Param(FCommandLine::Get(),TEXT("NRDeskPreview"));
    if(PreviewCCTV || PreviewMessage || PreviewDesk)
    {
        Player->SetActorLocation(NRLayout::OfficePoint(FVector(72,-407,90))); Player->GetController()->SetControlRotation(FRotator(-22,124,0));
        if(PreviewDesk) { Player->SetActorLocation(NRLayout::OfficePoint(FVector(0,-447,90))); Player->GetController()->SetControlRotation(FRotator(-16,90,0)); }
        if(PreviewCCTV) for(auto* P:Props) if(P->Id==TEXT("cctv")) Use(P);
        if(PreviewUpperCCTV) { for(int32 M=1;M<=3;++M)SwitchCCTVChannel(M,1); }
        if(PreviewMessage) ShowDocument(TEXT("rules"));
        FTimerHandle Shot,Exit;
        GetWorld()->GetTimerManager().SetTimer(Shot,[this]{Player->GetController<APlayerController>()->ConsoleCommand(TEXT("Shot SHOWUI"));},7.f,false);
        GetWorld()->GetTimerManager().SetTimer(Exit,[]{FPlatformMisc::RequestExit(false);},10.f,false);
    }
    if(FParse::Param(FCommandLine::Get(),TEXT("NRLogPlanPreview"))) {
        FirstCall=99999;IntroComplete=true;IntroCallPending=false;
        ShowDocument(TEXT("first_call"));FinishComplaintDialogue();StopVoice();SubtitleLines.Reset();Notice.Empty();Page.Empty();
        OpenComplaintLog();SelectComplaintKey(EKeys::One);SelectComplaintKey(EKeys::One);TickComplaintLog(10);
        FTimerHandle Shot,Exit;
        GetWorld()->GetTimerManager().SetTimer(Shot,[this]{Player->GetController<APlayerController>()->ConsoleCommand(TEXT("Shot SHOWUI"));},5.f,false);
        GetWorld()->GetTimerManager().SetTimer(Exit,[]{FPlatformMisc::RequestExit(false);},8.f,false);
    }
    if(FParse::Param(FCommandLine::Get(),TEXT("NRKeyTest")) || FParse::Param(FCommandLine::Get(),TEXT("NRExitTest")))
    {
        struct FKeyTest { int32 Frame=0, Index=0, Failures=0; FVector Start; FTimerHandle Timer; };
        auto Test=MakeShared<FKeyTest>();
        const bool ExitTest=FParse::Param(FCommandLine::Get(),TEXT("NRExitTest"));
        GetWorld()->GetTimerManager().SetTimer(Test->Timer,[this,Test,ExitTest]()
        {
            const FKey Keys[]={EKeys::W,EKeys::S,EKeys::A,EKeys::D};
            auto* Viewport=GetWorld()->GetGameViewport();
            if(++Test->Frame==1)
            {
                Player->SetActorLocation(FVector(-300,0,90)); Player->GetCharacterMovement()->StopMovementImmediately();
                Player->GetController()->SetControlRotation(FRotator::ZeroRotator);
                if(ExitTest) {
                    Player->SetActorLocation(FVector(0,120,90)); Player->GetController()->SetControlRotation(FRotator(0,90,0));
                    ExitUnlocked=true; // Explicit exit-geometry fixture; normal story never grants this yet.
                    for(auto* P:Props) if(P->Id==TEXT("entrance")) { Use(P); break; }
                }
                Test->Start=Player->GetActorLocation();
                Viewport->InputKey(FInputKeyEventArgs::CreateSimulated(Keys[Test->Index],IE_Pressed,1,1,FInputDeviceId::CreateFromInternalId(0),false,Viewport->Viewport));
            }
            if(Test->Frame==7)
            {
                Viewport->InputKey(FInputKeyEventArgs::CreateSimulated(Keys[Test->Index],IE_Released,0,1,FInputDeviceId::CreateFromInternalId(0),false,Viewport->Viewport));
                const FVector Delta=Player->GetActorLocation()-Test->Start;
                UE_LOG(LogTemp,Display,TEXT("NR_KEY_DIAG axis=%.2f canmove=%d mode=%d"),Player->InputComponent->GetAxisValue(TEXT("Forward")),Player->CanMove(),(int32)Player->GetCharacterMovement()->MovementMode);
                const bool Moved=ExitTest ? Delta.Y>100 : Test->Index==0 ? Delta.X>20 : Test->Index==1 ? Delta.X<-20 : Test->Index==2 ? Delta.Y<-20 : Delta.Y>20;
                if(!Moved) ++Test->Failures;
                UE_LOG(LogTemp,Display,TEXT("NR_KEY %s %s displacement=(%.1f,%.1f)"),*Keys[Test->Index].ToString(),Moved?TEXT("PASS"):TEXT("FAIL"),Delta.X,Delta.Y);
                Test->Frame=0;
                if(++Test->Index==(ExitTest?1:4))
                {
                    const int32 Failures=Test->Failures;
                    UE_LOG(LogTemp,Display,TEXT("NR_KEY_COMPLETE failures=%d"),Failures);
                    FPlatformMisc::RequestExitWithStatus(false,Failures?1:0);
                }
            }
        },.1f,true,.5f);
    }
    if(FParse::Param(FCommandLine::Get(),TEXT("NRChaseTest")))
    {
        Page.Empty(); FirstCall=99999;
        // A closed common-room wall forces a turn through the actual 2F kitchen door.
        for(auto* P:Props) if(P->Id==TEXT("door_arch_kitchen_1")) {P->SetDoor(true);P->Tick(1.f);}
        Player->SetActorLocation(FVector(1302.5f,-750,410)); StartThreat();
        FTimerHandle ChaseCheck, ChaseTrace;
        GetWorld()->GetTimerManager().SetTimer(ChaseTrace,[this]{ const FVector At=Ghost->GetActorLocation(); UE_LOG(LogTemp,Display,TEXT("NR_CHASE_TRACE t=%.1f ghost=(%.0f,%.0f) next=(%.0f,%.0f)"),ThreatTime,At.X,At.Y,GhostDestination.X,GhostDestination.Y); },1.f,true);
        auto Routed=MakeShared<bool>(false); const double Began=GetWorld()->GetTimeSeconds();
        GetWorld()->GetTimerManager().SetTimer(ChaseCheck,[this,Routed,Began]{
            const FVector At=Ghost->GetActorLocation();
            *Routed|=At.Y<-650 && FVector::Dist2D(At,Player->GetActorLocation())<350;
            if(!Dead && GetWorld()->GetTimeSeconds()-Began<25) return;
            // Arrival time varies with route updates. Reaching and catching the
            // stationary player is success, not a failure for arriving before 16s.
            const bool Passed=*Routed && Dead;
            UE_LOG(LogTemp,Display,TEXT("NR_CHASE_COMPLETE failures=%d routed=%d caught=%d ghost=(%.1f,%.1f,%.1f)"),Passed?0:1,*Routed,Dead,At.X,At.Y,At.Z);
            FPlatformMisc::RequestExitWithStatus(false,Passed?0:1);
        },.1f,true);
    }
    if(FParse::Param(FCommandLine::Get(),TEXT("NRMapTest"))) GetWorld()->GetTimerManager().SetTimerForNextTick(this,&ANRGameMode::MapTest);
    if(FParse::Param(FCommandLine::Get(),TEXT("NRSmokeTest"))) GetWorld()->GetTimerManager().SetTimerForNextTick(this,&ANRGameMode::SmokeTest);
    FString View; TArray<FString> ViewParts;
    // -NRView=x,y,z,pitch,yaw : screenshot from any spot (layout review).
    if(FParse::Value(FCommandLine::Get(),TEXT("NRView="),View,false) && View.ParseIntoArray(ViewParts,TEXT(","))==5)
    {
        Player->SetActorLocation(FVector(FCString::Atof(*ViewParts[0]),FCString::Atof(*ViewParts[1]),FCString::Atof(*ViewParts[2])));
        Player->GetController()->SetControlRotation(FRotator(FCString::Atof(*ViewParts[3]),FCString::Atof(*ViewParts[4]),0));
        for(auto* P:Props) if(P->Id.StartsWith(TEXT("door_")) && FParse::Param(FCommandLine::Get(),TEXT("NROpenDoors"))) P->SetDoor(true);
    }
    if(!View.IsEmpty() || FParse::Param(FCommandLine::Get(),TEXT("NRPreview")) || FParse::Param(FCommandLine::Get(),TEXT("NRUVPreview")) || FParse::Param(FCommandLine::Get(),TEXT("NREntrancePreview")) || FParse::Param(FCommandLine::Get(),TEXT("NRKitchenPreview")) || FParse::Param(FCommandLine::Get(),TEXT("NRHallPreview")))
    {
        Page.Empty();
        if(FParse::Param(FCommandLine::Get(),TEXT("NRKitchenPreview"))) { Player->SetActorLocation(FVector(820,-810,90)); Player->GetController()->SetControlRotation(FRotator(-4,60,0)); }
        if(FParse::Param(FCommandLine::Get(),TEXT("NRHallPreview"))) { Player->SetActorLocation(FVector(450,NRLayout::CorridorY,410)); Player->GetController()->SetControlRotation(FRotator(0,0,0)); }
        if(FParse::Param(FCommandLine::Get(),TEXT("NREntrancePreview")))
        {
            for(auto* P:Props) if(P->Id==TEXT("entrance")) P->SetDoor(true);
            Player->SetActorLocation(FVector(40,-30,90)); Player->GetController()->SetControlRotation(FRotator(-3,105,0));
        }
        if(FParse::Param(FCommandLine::Get(),TEXT("NRUVPreview")))
        {
            Player->SetActorLocation(FVector(725,-153,410));
            Player->GetController()->SetControlRotation(FRotator(-18,90,0));
            Player->UVRemaining=45; Player->UV=true;
        }
        if(!View.IsEmpty() && FParse::Param(FCommandLine::Get(),TEXT("NRViewUV"))) {Player->UVRemaining=45;Player->UV=true;}
        // Capture fixtures must not steal desktop typing/mouse movement into the
        // player camera while the user continues working in another window.
        Player->DisableInput(Player->GetController<APlayerController>());
        Player->GetController()->SetIgnoreLookInput(true);
        Player->GetController()->SetIgnoreMoveInput(true);
        FTimerHandle CaptureHandle,ExitHandle;
        GetWorld()->GetTimerManager().SetTimer(CaptureHandle,[this]{
            Player->GetController<APlayerController>()->ConsoleCommand(TEXT("Shot SHOWUI"));
        },6.f,false);
        GetWorld()->GetTimerManager().SetTimer(ExitHandle,[]{FPlatformMisc::RequestExit(false);},10.f,false);
    }
}
void ANRGameMode::EndPlay(const EEndPlayReason::Type Reason)
{
    SavePreferences();
    if(Screen.IsValid() && GetWorld() && GetWorld()->GetGameViewport()) GetWorld()->GetGameViewport()->RemoveViewportWidgetContent(Screen.ToSharedRef());
    for(auto* C:AmbientLoops) if(C) C->Stop();
    AmbientLoops.Empty();
    DocumentScroll.Reset(); Screen.Reset(); Super::EndPlay(Reason);
}
ANRProp* ANRGameMode::Prop(const FString& Id,const FString& Name,FVector At,FVector Size)
{
    auto* P=GetWorld()->SpawnActor<ANRProp>(At,FRotator::ZeroRotator); P->Configure(Id,Name,Size); Props.Add(P); return P;
}
void ANRGameMode::PlaceOn(ANRProp* Item,ANRProp* Support,FVector2D XY)
{
    const FBox Base=Support->Mesh->Bounds.GetBox();
    const float BottomOffset=Item->Mesh->Bounds.GetBox().Min.Z-Item->GetActorLocation().Z;
    Item->SetActorLocation(FVector(XY.X,XY.Y,Base.Max.Z-BottomOffset+.05f));
    Item->Home=Item->GetActorLocation();
    // Pickups are static props; only their visibility/collision changes on collection.
}
void ANRGameMode::Box(FVector At,FVector Size)
{
    auto* P=Prop(TEXT("structure"),TEXT(""),At,Size); P->Label->SetVisibility(false);
}
void ANRGameMode::Face(AActor* Actor,FVector2D Dir)
{
    Actor->SetActorRotation(FRotator(0,FMath::RadiansToDegrees(FMath::Atan2(Dir.Y,Dir.X))+90*NRLayout::FrontSign,0));
}
ANRProp* ANRGameMode::Door(const FString& Id,const FString& Name,FVector Center,float WallYaw)
{
    // WallYaw: +X runs along the wall and the room lies on its +Y side. Leaf is 78 cm with a hinge-edge origin.
    const FVector Along=FRotator(0,WallYaw,0).Vector();
    auto* Frame=Prop(TEXT("doorframe"),TEXT(""),Center,FVector(1)); Frame->SetActorRotation(FRotator(0,WallYaw,0));
    auto* Leaf=Prop(Id,Name,Center-Along*39*NRLayout::FrontSign,FVector(78,4,200));
    Leaf->ClosedYaw=Leaf->TargetYaw=WallYaw+(NRLayout::FrontSign>0?0.f:180.f);
    Leaf->SetActorRotation(FRotator(0,Leaf->ClosedYaw,0));
    return Leaf;
}
void ANRGameMode::Room(int32 Floor,int32 Index)
{
    using namespace NRLayout;
    const float Z=Floor*FloorHeight, Left=RoomLeft(Index), Right=Left+RoomPitch, CY=(RoomFront+RoomBack)/2;
    const FString Id=FString::Printf(TEXT("%d%02d"),Floor+1,Index+1);
    static const TSet<int32> Occupied={101,102,104,105,107,203,204,206,208,211,301,303,305,308,311};
    static const TSet<int32> Sparse={103,106,109,201,202,209,302,307,310};
    const int32 Number=(Floor+1)*100+Index+1;
    const bool Vacant=!Occupied.Contains(Number);
    const FVector DoorAt=DoorAnchor(Floor,Index)+FVector(0,5,0);
    // Exact collision behind Meshy skins keeps generated triangles out of movement.
    auto Solid=[this](FVector At,FVector Size) {
        auto* P=Prop(TEXT("architecture_collision"),TEXT(""),At,Size);
        P->Mesh->SetVisibility(false);P->Mesh->SetCastShadow(false);
    };
    Solid(FVector((Left+5+DoorAt.X-43.5f)/2,DoorAt.Y,Z+130),FVector(DoorAt.X-43.5f-Left-5,10,260));
    Solid(FVector((DoorAt.X+43.5f+Right-5)/2,DoorAt.Y,Z+130),FVector(Right-5-DoorAt.X-43.5f,10,260));
    Solid(FVector(DoorAt.X,DoorAt.Y,Z+232.75f),FVector(87,10,54.5f));
    ArchitecturePanel(TEXT("SM_AM_DoorWall"),FVector(Left+115,DoorAt.Y,Z+130),FVector(230,10,260));
    Door(TEXT("door_")+Id,Id,DoorAt,0);
    const float WinX=Right-51,BackY=RoomBack;
    Solid(FVector(Left+115,BackY,Z+60),FVector(230,16,120));
    Solid(FVector(Left+115,BackY,Z+230),FVector(230,16,60));
    Solid(FVector((Left+WinX-30)/2,BackY,Z+160),FVector(WinX-30-Left,16,80));
    Solid(FVector((WinX+30+Right)/2,BackY,Z+160),FVector(Right-WinX-30,16,80));
    ArchitecturePanel(TEXT("SM_AM_WindowWall"),FVector(Left+115,BackY,Z+130),FVector(230,16,260));
    Prop(TEXT("glass"),TEXT(""),FVector(WinX,BackY,Z+160),FVector(60,3,80));
    if(Vacant && !Sparse.Contains(Number))return;
    // Typical mini-room: bed on one wall, desk at the window, adjacent wardrobes on the opposite wall.
    auto* Bed=Prop(Vacant?TEXT("barebed"):TEXT("bed"),TEXT("침대"),FVector(Right-51,BackY-108,Z),FVector(1)); Face(Bed,FVector2D(0,1));
    auto* Desk=Prop(TEXT("roomdesk"),TEXT("붙박이 책상"),FVector(Left+58,BackY-33,Z),FVector(1)); Face(Desk,FVector2D(0,1));
    if(!Vacant) {
        // Two 45 cm cabinets share the left wall, with a 2 cm seam and matching fronts.
        Face(Prop(TEXT("wardrobe_")+Id,TEXT("옷장 1 열기 / 닫기"),FVector(Left+30,85,Z),FVector(45,45,175)),FVector2D(1,0));
        Face(Prop(TEXT("wardrobe_")+Id+TEXT("_left"),TEXT("옷장 2 열기 / 닫기"),FVector(Left+30,132,Z),FVector(45,45,175)),FVector2D(1,0));
    }
    if(!Vacant) {
        auto* Shelf=Prop(TEXT("wallshelf"),TEXT(""),FVector(Right-17.5f,CY-10,Z+155),FVector(1)); Face(Shelf,FVector2D(1,0));
        auto* Air=Prop(TEXT("aircon"),TEXT(""),FVector(Right-75,RoomFront+20,Z+205),FVector(1)); Face(Air,FVector2D(0,-1));
    }
    Prop(TEXT("fixture_room"),TEXT(""),FVector(Left+RoomPitch/2,CY,Z+257),FVector(60,12,8));
    // 202 is vacant: its only chair is the story prop placed in BuildWorld.
    if(!Vacant)
    {
        // Tuck the chair into the desk's knee space beyond the wardrobe pair.
        auto* Chair=Prop(TEXT("commonchair"),TEXT(""),FVector(Left+34,BackY-45,Z),FVector(1));
        Face(Chair,FVector2D(0,1));
    }
}
void ANRGameMode::BuildWorld()
{
    // Three floors with alternating stair flights to the roof; dimensions are centimetres.
    auto Surface=[this](const FString& Key,FVector At,FVector Size,const TCHAR* Material)
    {
        auto* P=Prop(Key,TEXT(""),At,Size);
        const FString Path=FString(TEXT("/Game/PrototypeAssets/"))+Material+TEXT(".")+Material;
        if(auto* M=LoadObject<UMaterialInterface>(nullptr,*Path)) P->Mesh->SetMaterial(0,M);
        return P;
    };
    auto Light=[this](FVector At,float Intensity,FLinearColor Color,float Radius=750)
    {
        Intensity*=.7f; // User requested 30% less map illumination, including restoration after outages.
        auto* L=GetWorld()->SpawnActor<APointLight>(At,FRotator::ZeroRotator);
        auto* C=Cast<UPointLightComponent>(L->GetLightComponent()); C->SetIntensity(Intensity); C->SetAttenuationRadius(Radius); C->SetLightColor(Color);
        if(At.Y<=230 && At.Z<1280) { InteriorLights.Add(C); LightIntensities.Add(Intensity); }
        return C;
    };
    BuildArchitecture();
    // Management office: desk/chair plus a strip behind for one person to lie down.
    const int32 OfficeFurnitureStart=Props.Num();
    // Spawn the light in the final room: moving a static light later left the
    // glowing fixture in the office but its illumination outside in the lobby.
    auto* OfficeLight=Light(NRLayout::OfficePoint(FVector(0,-340,235)),3200,FLinearColor(.90f,.92f,.84f),600);
    OfficeLight->SetMobility(EComponentMobility::Movable);
    OfficeLight->SetSourceRadius(12.f); OfficeLight->SetSourceLength(80.f);
    Prop(TEXT("fixture_office"),TEXT(""),FVector(0,-340,257),FVector(90,15,8));
    // Wall-width desk sits against the window, forward of the side-door swing.
    auto* OfficeDesk=Prop(TEXT("desk"),TEXT(""),FVector(0,-235,0),FVector(264,55,75));
    OfficeDesk->SetActorRotation(FRotator(0,180,0));
    Face(Prop(TEXT("officechair"),TEXT(""),FVector(0,-370,0),FVector(45,45,90)),FVector2D(.1f,1));
    Face(Prop(TEXT("clock"),TEXT("벽시계"),FVector(-85,-472,195),FVector(1)),FVector2D(0,1));
    Prop(TEXT("shelves"),TEXT("관리실 수납 선반"),FVector(110,-520,0),FVector(80,35,155))->SetActorRotation(FRotator(0,90,0));
    auto* Phone=Prop(TEXT("phone"),TEXT("전화 받기"),FVector::ZeroVector,FVector(35,24,14));
    Phone->SetActorRotation(FRotator(0,180,0));
    Phone->SetActorScale3D(FVector(.85f)); PlaceOn(Phone,OfficeDesk,FVector2D(-100,-244));
    auto* Roster=Prop(TEXT("roster"),TEXT("관리실 PC (명단 · 보고)"),FVector::ZeroVector,FVector(50,20,45));
    Roster->SetActorScale3D(FVector(.85f)); Face(Roster,FVector2D(.12f,-1)); PlaceOn(Roster,OfficeDesk,FVector2D(-55,-224));
    // Bottom row of three CRTs; a supported shelf carries the two upper units.
    auto* MonitorBase=Surface(TEXT("monitor_base"),FVector::ZeroVector,FVector(108,34,1.5f),TEXT("M_Concrete"));
    PlaceOn(MonitorBase,OfficeDesk,FVector2D(68,-222));
    const float MonitorBaseTop=MonitorBase->Mesh->Bounds.GetBox().Max.Z;
    for(int32 I=0;I<3;++I) {
        auto* Monitor=Prop(I==0?TEXT("cctv"):FString::Printf(TEXT("cctv_display_%d"),I),TEXT("CCTV 채널 확인 / 전환"),FVector::ZeroVector,FVector(1));
        Face(Monitor,FVector2D(0,-1)); PlaceOn(Monitor,MonitorBase,FVector2D(102-I*34,-222));
    }
    auto* MonitorShelf=Surface(TEXT("monitor_shelf"),FVector(68,-222,MonitorBaseTop+32),FVector(108,34,3),TEXT("M_Concrete"));
    for(float X:{16.f,120.f}) Surface(TEXT("monitor_shelf_leg"),FVector(X,-222,MonitorBaseTop+15.25f),FVector(2,32,30.5f),TEXT("M_Concrete"));
    for(int32 I=3;I<5;++I) {
        auto* Monitor=Prop(FString::Printf(TEXT("cctv_display_%d"),I),TEXT("CCTV 채널 확인 / 전환"),FVector::ZeroVector,FVector(1));
        Face(Monitor,FVector2D(0,-1)); PlaceOn(Monitor,MonitorShelf,FVector2D(85-(I-3)*34,-222));
    }
    Prop(TEXT("rules"),TEXT("야간수칙"),FVector(0,-473,140),FVector(70,5,90));
    auto* Note=Prop(TEXT("note"),TEXT("전임 총무 메모 읽기"),FVector::ZeroVector,FVector(25,20,.3));
    PlaceOn(Note,OfficeDesk,FVector2D(-8,-219));
    auto* StartCart=Prop(TEXT("cart_start"),TEXT("UV 카트리지 줍기"),FVector::ZeroVector,FVector(18,8,8));
    StartCart->SetActorLocation(FVector(-111.4f,-244,56.0f)); StartCart->Home=StartCart->GetActorLocation();
    StartCart->SetActorHiddenInGame(true); StartCart->SetActorEnableCollision(false);
    for(int32 I=4;I<=6;++I)
    {
        auto* Drawer=Prop(FString::Printf(TEXT("drawer_%d"),I),TEXT("책상 서랍 열기"),OfficeDesk->GetActorLocation(),FVector(1));
        Drawer->SetActorRotation(OfficeDesk->GetActorRotation()); Drawer->Sliding=true;
        if(I==4) Drawer->StoredItem=StartCart;
    }
    for(int32 I=OfficeFurnitureStart;I<Props.Num();++I)OfficeAssembly.Add(Props[I]);
    auto* CleaningShelf=Prop(TEXT("shelves"),TEXT("청소용품 선반"),FVector(NRLayout::StoreX(310),-790,0),FVector(80,35,155));
    auto* CleaningCart=Prop(TEXT("cart_cleaning"),TEXT("UV 카트리지 줍기"),FVector::ZeroVector,FVector(18,8,8));
    PlaceOn(CleaningCart,CleaningShelf,FVector2D(NRLayout::StoreX(318),-790));
    auto* Toolbox=Prop(TEXT("toolbox"),TEXT("전임 총무의 공구함"),FVector(NRLayout::StoreX(95),-790,.1f),FVector(50,30,32));
    auto* ToolCart=Prop(TEXT("cart_toolbox"),TEXT("UV 카트리지 줍기"),FVector::ZeroVector,FVector(18,8,8));
    // Support against the actual lid surface, away from the raised handle.
    const FVector ToolXY(NRLayout::StoreX(95)-15,-785,0);
    FHitResult LidHit;FCollisionQueryParams LidQ;LidQ.bTraceComplex=true;
    if(Toolbox->Mesh->LineTraceComponent(LidHit,ToolXY+FVector(0,0,65),ToolXY-FVector(0,0,5),LidQ)) {
        const float Bottom=ToolCart->Mesh->Bounds.GetBox().Min.Z-ToolCart->GetActorLocation().Z;
        ToolCart->SetActorLocation(FVector(ToolXY.X,ToolXY.Y,LidHit.ImpactPoint.Z-Bottom+.05f));
        ToolCart->Home=ToolCart->GetActorLocation();
    } else PlaceOn(ToolCart,Toolbox,FVector2D(ToolXY.X,ToolXY.Y));
    const FVector Door202=NRLayout::DoorAnchor(1,1);
    Face(Prop(TEXT("chair"),TEXT("의자와 바닥 흔적"),NRLayout::RoomCenter(1,1)+FVector(-20,-25,0),FVector(45,45,90)),FVector2D(0,-1));
    UVMarker=Prop(TEXT("uvmark"),TEXT(""),Door202+FVector(90,-.7f,130),FVector(1));
    UVMarker->Mesh->SetVisibility(false); UVMarker->Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    UVMarker->Label->SetText(FText::FromString(TEXT("LOCKS INSIDE"))); UVMarker->Label->SetTextRenderColor(FColor(170,90,255)); UVMarker->Label->SetWorldSize(14); UVMarker->Label->SetVisibility(false);
    Ghost=Prop(TEXT("ghost"),TEXT(""),FVector(2000,0,410),FVector(35,35,180));
    Ghost->Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision); Ghost->SetActorHiddenInGame(true);
    if(auto* Model=LoadObject<USkeletalMesh>(nullptr,TEXT("/Game/PrototypeAssets/GhostMeshy/SK_SmilingCaretaker.SK_SmilingCaretaker")))
    {
        Ghost->Mesh->SetVisibility(false); Ghost->SetActorScale3D(FVector(1));
        GhostVisual=NewObject<USkeletalMeshComponent>(Ghost,TEXT("GhostVisual"));
        GhostVisual->SetupAttachment(Ghost->GetRootComponent()); GhostVisual->SetSkeletalMesh(Model);
        // Keep the Meshy model's UV-mapped PBR material; the old front/back
        // projection materials do not match this mesh or its material slots.
        GhostVisual->SetRelativeLocation(FVector(0,0,-90)); GhostVisual->SetRelativeRotation(FRotator(0,-90,0));
        GhostVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision); GhostVisual->RegisterComponent();
        GhostVisual->PlayAnimation(LoadObject<UAnimSequence>(nullptr,TEXT("/Game/PrototypeAssets/GhostMeshy/A_CaretakerWalk.A_CaretakerWalk")),true);
        GhostVisual->SetPlayRate(.8f);
        GhostVisual->VisibilityBasedAnimTickOption=EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
    }

    // Outdoor forecourt sits opposite office; neighbours never overlap residence rooms.
    // Two 90 cm leaves, meeting handles, opening outward on opposite hinges.
    for(float X:{-45.f,45.f}) {
        auto* Leaf=Prop(TEXT("entrance"),TEXT("현관 양문"),FVector(X,230,0),FVector(1));
        Leaf->Mesh->SetRelativeScale3D(FVector((X<0?1.f:-1.f)*90.f/130.f,1,1));
    }
    for(float X:{-95.f,95.f}) Surface(TEXT("frame"),FVector(X,230,110),FVector(8,24,220),TEXT("M_Concrete"));
    Surface(TEXT("frame"),FVector(0,230,222),FVector(198,24,8),TEXT("M_Concrete"));
    Surface(TEXT("pavement"),FVector(0,625,-10),FVector(600,850,20),TEXT("M_Concrete"));
    Surface(TEXT("pavement"),FVector(2150,640,-10),FVector(3700,820,20),TEXT("M_Concrete"));
    Surface(TEXT("road"),FVector(1800,1350,-12),FVector(6000,600,24),TEXT("M_Asphalt"));
    Surface(TEXT("facade"),FVector(-1050,600,370),FVector(700,1000,740),TEXT("M_Concrete"));
    Surface(TEXT("facade"),FVector(4350,600,370),FVector(700,1000,740),TEXT("M_Concrete"));
    Surface(TEXT("facade"),FVector(1800,1900,400),FVector(6000,300,800),TEXT("M_Concrete"));
    for(int32 Row=0;Row<3;++Row) for(int32 Col=0;Col<18;++Col)
        Surface(TEXT("outside_window"),FVector(-950+Col*320,1745,150+Row*220),FVector(100,4,110),(Col+Row)%4==0?TEXT("M_LitWindow"):TEXT("M_Asphalt"));
    for(float X:{-250.f,250.f}) { Surface(TEXT("streetpole"),FVector(X,800,180),FVector(8,8,360),TEXT("M_Concrete")); Light(FVector(X,800,330),8000,FLinearColor(.9,.65,.35),1200); }
    Light(FVector(1800,1500,500),9000,FLinearColor(.3,.4,.6),3500);
    auto* Sky=Surface(TEXT("sky"),FVector(0,0,0),FVector(200000),TEXT("M_NightSky")); Sky->Mesh->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Sphere.Sphere"))); Sky->Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Documents.Add(TEXT("fridge"),TEXT("입주민 공용 냉장고. 이름이 적힌 용기와 남은 음식이 들어 있다."));
    Documents.Add(TEXT("microwave"),TEXT("공용 전자레인지. 사용 후 내부를 닦아주세요."));
    Documents.Add(TEXT("counter"),TEXT("공용주방. 식사와 설거지는 조용히 해주세요."));
    Documents.Add(TEXT("shelves"),TEXT("공용 수납 선반\n\n입주민의 물건과 관리용 비품이 섞여 있다."));
    Documents.Add(TEXT("toolbox"),TEXT("전임 총무의 공구함\n\n도윤이라는 이름이 적혀 있다. 뚜껑 위에 예비 카트리지 하나가 그대로 놓여 있다."));
    Documents.Add(TEXT("toolbox_lid"),Documents[TEXT("toolbox")]);
    Documents.Add(TEXT("kettle"),TEXT("공용 전기주전자\n\n사용 후 플러그를 뽑아주세요."));
    Documents.Add(TEXT("pot"),TEXT("입주민 냄비\n\n바닥에 오래된 그을음이 남아 있다."));
}

void ANRGameMode::BuildScreen()
{
    if(!GetWorld()->GetGameViewport()) return;
    auto OutlineFont=[](int32 Size){auto Font=FCoreStyle::GetDefaultFontStyle("Regular",Size); Font.OutlineSettings.OutlineSize=2; Font.OutlineSettings.OutlineColor=FLinearColor::Black; return Font;};
    RulesUIMaterial=UMaterialInstanceDynamic::Create(LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/PrototypeAssets/M_RulesInkUI.M_RulesInkUI")),this);
    StoryDocumentBrush.DrawAs=ESlateBrushDrawType::Image;
    auto RulesRows=SNew(SImage).Image(&StoryDocumentBrush)
        .Visibility_Lambda([this]{return RulesView || PaperView?EVisibility::HitTestInvisible:EVisibility::Collapsed;});
    Screen=SNew(SOverlay).Visibility_Lambda([this]{return Page.IsEmpty()?EVisibility::HitTestInvisible:EVisibility::SelfHitTestInvisible;})
    +SOverlay::Slot().HAlign(HAlign_Left).VAlign(VAlign_Top).Padding(24)
    [SNew(STextBlock).Font(FCoreStyle::GetDefaultFontStyle("Regular",16)).Text_Lambda([this]{return FText::FromString(Page.IsEmpty()?StatusText():FString());}).ColorAndOpacity(FLinearColor(.8f,.85f,.8f))]
    +SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Center)
    [SNew(STextBlock).Text(FText::FromString(TEXT("·"))).Font(OutlineFont(28)).ColorAndOpacity(FLinearColor(.9f,.92f,.84f))
     .Visibility_Lambda([this]{return Page.IsEmpty() && !Paused && !Dead && !Finished && !(DreamActive && DreamTime>=18)?EVisibility::HitTestInvisible:EVisibility::Collapsed;})]
    +SOverlay::Slot().HAlign(HAlign_Right).VAlign(VAlign_Top).Padding(24)
    [SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
     .BorderBackgroundColor(FLinearColor(.012f,.016f,.015f,.85f)).Padding(18)
     .Visibility_Lambda([this]{return Page.IsEmpty() && !Paused && !Dead && !Finished?EVisibility::HitTestInvisible:EVisibility::Collapsed;})
     [SNew(SBox).WidthOverride(310)
      [SNew(SVerticalBox)
       +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,8)
       [SNew(STextBlock).Text(FText::FromString(TEXT("야간 근무"))).Font(FCoreStyle::GetDefaultFontStyle("Regular",14)).ColorAndOpacity(FLinearColor(.65f,.72f,.65f))]
       +SVerticalBox::Slot().AutoHeight()
       [SNew(STextBlock).Text_Lambda([this]{return FText::FromString(ObjectiveText());}).WrapTextAt(310).Font(FCoreStyle::GetDefaultFontStyle("Regular",20)).ColorAndOpacity(FLinearColor(.94f,.92f,.84f))]]]]
    +SOverlay::Slot()
    [SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
     .BorderBackgroundColor(FLinearColor(0,0,0,.78f)).HAlign(HAlign_Center).VAlign(VAlign_Center)
     .Visibility_Lambda([this]{return Paused && !Page.IsEmpty()?EVisibility::Visible:EVisibility::Collapsed;})
     [SNew(SBox).WidthOverride(520)
      [SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(FLinearColor(.025f,.033f,.03f,1)).Padding(36)
       [SNew(SVerticalBox)
        +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,8)
        [SNew(STextBlock).Text(FText::FromString(TEXT("야간수칙"))).Font(FCoreStyle::GetDefaultFontStyle("Bold",38)).ColorAndOpacity(FLinearColor(.94f,.92f,.84f))]
        +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,28)
        [SNew(STextBlock).Text(FText::FromString(TEXT("해담고시원  /  일시정지"))).Font(FCoreStyle::GetDefaultFontStyle("Regular",16)).ColorAndOpacity(FLinearColor(.6f,.68f,.61f))]
        +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,10)
        [SAssignNew(PauseResume,SButton).ContentPadding(16).OnClicked_Lambda([this]{Escape(); return FReply::Handled();})[SNew(STextBlock).Text(FText::FromString(TEXT("계속하기   ·   Esc"))).Font(FCoreStyle::GetDefaultFontStyle("Regular",20))]]
        +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,10)
        [SNew(SButton).ContentPadding(16).OnClicked_Lambda([this]{RestoreCheckpoint(); return FReply::Handled();})[SNew(STextBlock).Text(FText::FromString(TEXT("체크포인트로 돌아가기"))).Font(FCoreStyle::GetDefaultFontStyle("Regular",20))]]
        +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,10)
        [SNew(SButton).ContentPadding(16).Visibility_Lambda([this]{return !Finale.Active?EVisibility::Visible:EVisibility::Collapsed;}).OnClicked_Lambda([this]{StartFinale();return FReply::Handled();})[SNew(STextBlock).Text(FText::FromString(TEXT("최종밤 엔딩 테스트 · 중간 날짜 생략"))).Font(FCoreStyle::GetDefaultFontStyle("Regular",18))]]
        +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,10)
        [SNew(SButton).ContentPadding(14).OnClicked_Lambda([this]{SettingsOpen=!SettingsOpen; SavePreferences(); return FReply::Handled();})
         [SNew(STextBlock).Text(FText::FromString(TEXT("설정 · 마우스 / 사운드"))).Font(FCoreStyle::GetDefaultFontStyle("Regular",20))]]
        +SVerticalBox::Slot().AutoHeight().Padding(0,8,0,20)
        [SNew(SVerticalBox).Visibility_Lambda([this]{return SettingsOpen?EVisibility::Visible:EVisibility::Collapsed;})
         +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,8)
         [SNew(STextBlock).Text_Lambda([this]{return FText::FromString(FString::Printf(TEXT("마우스 감도  %.2fx"),MouseSensitivity));}).Font(FCoreStyle::GetDefaultFontStyle("Regular",18))]
         +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,18)
         [SNew(SSlider).Value_Lambda([this]{return (MouseSensitivity-.2f)/2.8f;}).OnValueChanged_Lambda([this](float V){MouseSensitivity=.2f+2.8f*V;}).OnMouseCaptureEnd_Lambda([this]{SavePreferences();})]
         +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,8)
         [SNew(STextBlock).Text_Lambda([this]{return FText::FromString(FString::Printf(TEXT("전체 음량  %.0f%%"),MasterVolume*100));}).Font(FCoreStyle::GetDefaultFontStyle("Regular",18))]
         +SVerticalBox::Slot().AutoHeight()
         [SNew(SSlider).Value_Lambda([this]{return MasterVolume;}).OnValueChanged_Lambda([this](float V){ApplyVolume(V);}).OnMouseCaptureEnd_Lambda([this]{SavePreferences();})]]
        +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,10)
        [SNew(SButton).ContentPadding(10).Visibility_Lambda([this]{return SettingsOpen?EVisibility::Visible:EVisibility::Collapsed;})
         .OnClicked_Lambda([this]{Sound(TEXT("phone_ring"),Player->GetActorLocation());return FReply::Handled();})
         [SNew(STextBlock).Text(FText::FromString(TEXT("소리 확인 · 전화벨 재생"))).Font(FCoreStyle::GetDefaultFontStyle("Regular",18))]]
        +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,28)
        [SNew(SButton).ContentPadding(16).OnClicked_Lambda([]{FPlatformMisc::RequestExit(false); return FReply::Handled();})[SNew(STextBlock).Text(FText::FromString(TEXT("게임 종료"))).Font(FCoreStyle::GetDefaultFontStyle("Regular",20))]]
        +SVerticalBox::Slot().AutoHeight()
        [SNew(STextBlock).Text(FText::FromString(TEXT("WASD 이동    Shift 달리기    Ctrl 앉기\nE 조사·대화    F 손전등    J 기록\nT 카트리지 장착    Q UV 전환"))).Font(FCoreStyle::GetDefaultFontStyle("Regular",15)).ColorAndOpacity(FLinearColor(.65f,.7f,.66f))]
       ]]]]
    +SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Bottom).Padding(24,0,24,28)
    [SNew(SScaleBox).Stretch(EStretch::ScaleToFit)
     .Visibility_Lambda([this]{return !Page.IsEmpty() || Paused || Dead || Finished || (Notice.IsEmpty() && PromptText().IsEmpty())?EVisibility::Collapsed:EVisibility::HitTestInvisible;})
     [SNew(SBox).WidthOverride(960)
      [SNew(SVerticalBox)
       +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,12)
       [SNew(STextBlock).Font(FCoreStyle::GetDefaultFontStyle("Bold",20)).Justification(ETextJustify::Center).WrapTextAt(900)
        .ShadowOffset(FVector2D(1,2)).ShadowColorAndOpacity(FLinearColor::Black)
        .Text_Lambda([this]{return FText::FromString(PromptText());})
        .Visibility_Lambda([this]{return PromptText().IsEmpty()?EVisibility::Collapsed:EVisibility::HitTestInvisible;})]
       +SVerticalBox::Slot().AutoHeight()
       [SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(FLinearColor::Transparent).Padding(22,14)
        .Visibility_Lambda([this]{return Notice.IsEmpty()?EVisibility::Collapsed:EVisibility::HitTestInvisible;})
        [SNew(SVerticalBox)
         +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,8)
         [SNew(STextBlock).Font(OutlineFont(16)).ShadowOffset(FVector2D(1,2)).ShadowColorAndOpacity(FLinearColor::Black).Justification(ETextJustify::Center).WrapTextAt(900)
          .Text_Lambda([this]{return FText::FromString(SubtitleSource);}).ColorAndOpacity(FLinearColor(.7f,.78f,.72f))]
         +SVerticalBox::Slot().AutoHeight()
         [SNew(STextBlock).Font(OutlineFont(26)).ShadowOffset(FVector2D(1,2)).ShadowColorAndOpacity(FLinearColor::Black).Justification(ETextJustify::Center).WrapTextAt(900)
          .Text_Lambda([this]{return FText::FromString(Notice);}).ColorAndOpacity(FLinearColor(.96f,.96f,.92f))]
        ]]
      ]]]
    +SOverlay::Slot().Padding(24)
    [SNew(SScaleBox).Stretch(EStretch::ScaleToFit)
     .Visibility_Lambda([this]{return Page.IsEmpty() || Paused?EVisibility::Collapsed:EVisibility::SelfHitTestInvisible;})
     [SNew(SBox).WidthOverride(1040).HeightOverride_Lambda([this]{return CCTVView?820.f:630.f;})
      [SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).Padding(30)
       .BorderBackgroundColor_Lambda([this]{return ComplaintView?FLinearColor(.82f,.78f,.64f,.99f):FLinearColor(.012f,.019f,.021f,.98f);})
      [SNew(SVerticalBox)
       +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,18)
       [SNew(STextBlock).Font(FCoreStyle::GetDefaultFontStyle("Bold",26)).ColorAndOpacity_Lambda([this]{return ComplaintView?FSlateColor(FLinearColor(.12f,.1f,.07f)):FSlateColor(FLinearColor(.65f,.83f,.75f));})
        .Text_Lambda([this]{return FText::FromString(ComplaintView?TEXT("해담고시원  /  민원 장부"):CCTVView?TEXT("해담고시원  /  CCTV"):Dead?TEXT("해담고시원  /  사건 종료"):Finished?TEXT("해담고시원  /  근무 종료"):Paused?TEXT("해담고시원  /  일시정지"):TEXT("해담고시원  /  기록 열람"));})]
       +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,18)
       [BuildCCTVPanel()]
       +SVerticalBox::Slot().AutoHeight().Padding(0,10,0,10)
       [SNew(SVerticalBox).Visibility_Lambda([this]{return CCTVView?EVisibility::Visible:EVisibility::Collapsed;})
        +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,8)
        [SNew(STextBlock).Text_Lambda([this]{return FText::FromString(CCTVStatus());}).Font(FCoreStyle::GetDefaultFontStyle("Regular",18))]
        +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,10)
        [SNew(SSlider).Value_Lambda([this]{return ReplayIndex<0?1.f:(HistoryCount>1?float(ReplayIndex)/(HistoryCount-1):1.f);})
         .IsEnabled_Lambda([this]{return !MonitorOff && HistoryCount>1;}).OnValueChanged_Lambda([this](float V){ReplayCCTV(V);})]
        +SVerticalBox::Slot().AutoHeight()
        [SNew(SButton).ContentPadding(8).Text(FText::FromString(TEXT("실시간으로 돌아가기"))).OnClicked_Lambda([this]{LiveCCTV(); return FReply::Handled();})]]
       +SVerticalBox::Slot().FillHeight(1)
       [SAssignNew(DocumentScroll,SScrollBox).ScrollBarAlwaysVisible(true)
        +SScrollBox::Slot()
        [SNew(STextBlock).Text_Lambda([this]{return FText::FromString(Page);}).WrapTextAt(930)
         .Visibility_Lambda([this]{return RulesView || PaperView?EVisibility::Collapsed:EVisibility::HitTestInvisible;})
         .Font_Lambda([this]{return FSlateFontInfo(FPaths::ProjectContentDir()/TEXT("Fonts")/(ComplaintView?TEXT("NanumBrushScript-Regular.ttf"):TEXT("NanumMyeongjo-Regular.ttf")),ComplaintView && !ComplaintPlanning?28:22);})
         .ColorAndOpacity_Lambda([this]{return ComplaintView?FSlateColor(FLinearColor(.16f,.13f,.09f)):FSlateColor(FLinearColor(.9f,.91f,.87f));})]
        +SScrollBox::Slot()[RulesRows]]
       +SVerticalBox::Slot().AutoHeight().Padding(0,18,0,0)
       [SNew(STextBlock).Font(FCoreStyle::GetDefaultFontStyle("Regular",18))
        .ColorAndOpacity_Lambda([this]{return ComplaintView?FSlateColor(FLinearColor(.2f,.17f,.11f)):FSlateColor(FLinearColor(.55f,.65f,.65f));})
        .Text_Lambda([this]{return FText::FromString(ComplaintView?TEXT("[1~3] 선택    ·    [4] 조사 방침 수정    ·    [Esc] 닫기    ·    마우스 휠로 스크롤"):Dead?TEXT("[R] 사건 직전으로 돌아가기"):Finished?TEXT("[Enter] 최종밤 테스트 시작·재시작    ·    [R] DAY 1부터 다시 시작"):FinaleConfirm?TEXT("[Enter] 확인    ·    [Esc] 취소하고 조사 계속"):Paused?TEXT("[Esc] 계속    ·    [R] 처음부터 다시 시작"):CCTVView?TEXT("[Esc] 닫기    ·    CCTV 확인 중에도 근무와 사건이 계속됩니다"):TEXT("[Esc] 닫기    ·    마우스 휠로 스크롤    ·    확인 중 근무 시간 정지"));})]
      ]]]];
    // SScrollBox defaults to non-focusable, even when supplied to SetWidgetToFocus.
    DocumentScroll->SetIsFocusable(true);
    GetWorld()->GetGameViewport()->AddViewportWidgetContent(Screen.ToSharedRef());
}
FString ANRGameMode::StatusText() const
{
    if(!Player) return TEXT("");
    // Minimal equipment display; no quest list or source reliability gauge.
    return FString::Printf(TEXT("%s  |  UV %.0f초 · 예비 %d  |  T 장착 · Q 전환 · F 켜기/끄기"),!Player->LightOn?TEXT("손전등 꺼짐"):Player->UV?TEXT("UV"):TEXT("일반광"),Player->UVRemaining,Player->Cartridges);
}
FString ANRGameMode::PromptText() const
{
    if(!Page.IsEmpty() || Dead || Finished || Paused || !Player) return TEXT("");
    const FString Clue=UVClue();
    if(!Clue.IsEmpty()) return Evidence.Contains(Clue)?TEXT("UV 흔적  ·  [J] 기록"):TEXT("[E] 드러난 흔적 기록");
    if(Player->UV && Player->Focus && (Player->Focus->Id==TEXT("rules") || Player->Focus->Id==TEXT("note"))) return TEXT("UV는 글씨의 진위를 판별하지 않는다. 지목된 물건을 비추자.");
    if(!Player->Focus) return TEXT("");
    if(Player->Focus->Id==TEXT("door_202") && (Evidence.Contains(TEXT("uv")) || Evidence.Contains(TEXT("physical")))) return Player->Focus->Open?TEXT("[E] 202호 문 닫기"):TEXT("[E] 202호 문 열기");
    if(Player->Focus->Caption.IsEmpty()) return TEXT("");
    return TEXT("[E] ")+Player->Focus->Caption;
}
void ANRGameMode::ShowDocument(const FString& Key,const FString& Extra)
{
    if(Key==TEXT("complaint_log")) { OpenComplaintLog(); return; }
    CloseComplaintLog();
    FString Source=TEXT("조사");
    for(auto* P:Props) if(P->Id==Key && !P->Caption.IsEmpty()) { Source=P->Caption; break; }
    if(!Documents.Contains(Key)) Documents.Add(Key,Source+TEXT("\n\n특별한 점은 보이지 않는다."));
    // Keep evidence/complaint keys stable; only the dialogue and voice sequence vary.
    const FString HeardVariant=Key+TEXT("_second_call");
    const FString DialogueKey=Evidence.Contains(TEXT("second_call")) && Documents.Contains(HeardVariant)?HeardVariant:Key;
    FString Text=IsComplaintReport(Key)?ComplaintReportText(Documents[Key]):Key==TEXT("service_ledger")?ServiceLedgerText():Documents[DialogueKey];
    if(Key==TEXT("cctv_recovered")) Text=Text.Replace(TEXT("{{freeze_time}}"),*ShiftClock(CCTVStoppedAt));
    if(!Extra.IsEmpty()) Text+=TEXT("\n")+Extra;
    if(IsComplaintReport(Key) || Key==TEXT("cctv_recovered")) ComplaintLog.Reports.Add(Key,Text);
    if(Key==TEXT("dream_wake")) ArmComplaintAnomaly(true);
    if(Key==TEXT("202_safe_report")) ArmComplaintAnomaly(false);
    Evidence.Add(Key); Record(TEXT("read"),Key);
    if(Key==TEXT("service_ledger")) SaveCheckpoint();
    const bool Enlarged=Key==TEXT("rules") || Key==TEXT("roster") || Key==TEXT("note") || Key==TEXT("cctv") || Key==TEXT("uv_guide") || Key==TEXT("service_ledger");
    PaperView=Key==TEXT("note") || Key==TEXT("uv_guide");
    if(Key==TEXT("rules")) {
        StoryDocumentBrush.SetResourceObject(RulesUIMaterial);StoryDocumentBrush.ImageSize=FVector2D(900,900.f*1320/1024);
    } else if(PaperView) {
        auto* Tex=StoryTextures.FindRef(Key);StoryDocumentBrush.SetResourceObject(Tex);
        if(Tex)StoryDocumentBrush.ImageSize=FVector2D(900,900.f*Tex->GetSizeY()/Tex->GetSizeX());
    }
    CCTVView=Enlarged && Key==TEXT("cctv"); RulesView=Enlarged && Key==TEXT("rules");
    if(Enlarged)
    {
        Page=Text;
        if(DocumentScroll) DocumentScroll->ScrollToStart();
        return;
    }
    Page.Empty();
    const bool SurfaceClue=Key==TEXT("physical") || Key==TEXT("uv") || Key==TEXT("uv_fragment") || Key==TEXT("uv_hand") || Key==TEXT("wake_trace") || Key==TEXT("sealed_panel") || Key==TEXT("panel_early");
    if(SurfaceClue) {
        Message(TEXT("조사 위치를 기록했다.  [J]"),2.f,TEXT("기록"));
        return;
    }
    TArray<FString> Lines; Text.ParseIntoArrayLines(Lines,true);
    FString Body=Text;
    if(Lines.Num()>1)
    {
        Source=Lines[0].TrimStartAndEnd(); Lines.RemoveAt(0);
        Body=FString::Join(Lines,TEXT("\n"));
    }
    TArray<FString> Speakers;
    if(Key==TEXT("final_manager")) {
        for(const auto& Line:Lines) Speakers.Add(Line.StartsWith(TEXT("‘열쇠는"))?TEXT("수화기 · 다른 목소리"):Source);
    } else if(Key==TEXT("final_exit_open") && !Extra.IsEmpty()) {
        Speakers.Init(TEXT("복도 쪽 · 태오"),Lines.Num());
    }
    Message(Body,0,Source,Speakers.IsEmpty()?nullptr:&Speakers);
    // Dynamic documents must retain their rendered timestamps and current story text.
    if(!IsComplaintReport(Key) && Key!=TEXT("service_ledger") && Key!=TEXT("cctv_recovered")) StartDocumentVoice(DialogueKey);
    BeginComplaintDialogue(Key);
    BeginResidentConversation(Key);
    EndingPending=Key==TEXT("final_call");
    if(EndingPending) { FinalKnockTime=0; FinalKnockStage=0; }
    if(Key==TEXT("first_call") && !IntroComplete) IntroCallPending=true;
}
void ANRGameMode::Message(const FString& Text,float Duration,const FString& Source,const TArray<FString>* Speakers)
{
    if(IntroCallPending) return; // Do not let pickup/door notices interrupt mandatory opening dialogue.
    EndResidentConversation();
    FinishComplaintDialogue(); // A replacement notice also ends the previous conversation.
    StopVoice();
    // A new utterance replaces the complete queue, including any pending ending from it.
    SubtitleLines.Reset(); SubtitleIndex=0; Notice.Empty(); MessageTime=0; EndingPending=false;
    SubtitleSource=Source;
    TArray<FString> Lines; Text.ParseIntoArrayLines(Lines,true);
    int32 LineIndex=0;
    for(FString Line:Lines)
    {
        Line.TrimStartAndEndInline();
        const bool Spoken=Line.StartsWith(TEXT("‘")) || Line.StartsWith(TEXT("“"));
        const FString Speaker=Spoken?(Speakers && Speakers->IsValidIndex(LineIndex)?(*Speakers)[LineIndex]:Source):TEXT("나 · 독백");
        ++LineIndex;
        while(!Line.IsEmpty())
        {
            int32 Count=FMath::Min(Line.Len(),32);
            if(Line.Len()>Count)
            {
                for(int32 Split=Count;Split>=16;--Split)
                    if(FChar::IsWhitespace(Line[Split-1]) || Line[Split-1]==TEXT('.') || Line[Split-1]==TEXT(',') || Line[Split-1]==TEXT('?') || Line[Split-1]==TEXT('!'))
                    { Count=Split; break; }
            }
            FString Part=Line.Left(Count).TrimStartAndEnd();
            const float Hold=FMath::Max(Duration,FMath::Clamp(1.2f+Part.Len()*.09f,2.f,6.f));
            SubtitleLines.Add(FSubtitleLine{Part,Hold,Speaker});
            Line=Line.Mid(Count).TrimStartAndEnd();
        }
    }
    if(SubtitleLines.IsEmpty()) { SubtitleSource.Empty(); return; }
    Notice=SubtitleLines[0].Text; SubtitleSource=SubtitleLines[0].Speaker; MessageTime=SubtitleLines[0].Duration;
}
void ANRGameMode::Record(const FString& Kind,const FString& Detail)
{
    const FVector At=Player?Player->GetActorLocation():FVector::ZeroVector;
    auto Item=MakeShared<FJsonObject>(); Item->SetNumberField(TEXT("seconds"),Elapsed);
    Item->SetNumberField(TEXT("real_seconds"),GetWorld()?GetWorld()->GetRealTimeSeconds():0);
    Item->SetStringField(TEXT("event"),Kind); Item->SetStringField(TEXT("detail"),Detail);
    Item->SetNumberField(TEXT("x"),At.X); Item->SetNumberField(TEXT("y"),At.Y); Item->SetNumberField(TEXT("z"),At.Z);
    FString Line; const auto Writer=TJsonWriterFactory<TCHAR,TCondensedJsonPrintPolicy<TCHAR>>::Create(&Line);
    FJsonSerializer::Serialize(Item,Writer);
    const FString Path=FPaths::ProjectSavedDir()/TEXT("NightRules/actions.jsonl");
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Path),true);
    FFileHelper::SaveStringToFile(Line+TEXT("\n"),*Path,FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM,&IFileManager::Get(),FILEWRITE_Append);
}
void ANRGameMode::Sound(const FString& Name,FVector Position)
{
    const FString Path=TEXT("/Game/Audio/")+Name+TEXT(".")+Name;
    if(auto* Audio=LoadObject<USoundBase>(nullptr,*Path)) UGameplayStatics::PlaySoundAtLocation(this,Audio,Position,.5f);
}
void ANRGameMode::Use(ANRProp* P)
{
    if(DreamActive) return;
    if(!P) return;
    if(Finale.Active && UseFinale(P))return;
    if(!IntroCallPending && ReadUVClue()) return;
    if(P->Id==TEXT("wake_trace")) { ShowDocument(TEXT("wake_trace")); return; }
    if(IntroCallPending) return;
    if(P->CorePanels.Num()>0)
    {
        P->SetDoor(!P->Open); DemoSound(TEXT("chair_drag"),P->GetActorLocation(),.12f);
        Record(TEXT("container"),P->Id+(P->Open?TEXT("_open"):TEXT("_closed"))); return;
    }
    if(P->Sliding)
    {
        P->SetDoor(!P->Open);
        if(P->StoredItem && !Collected.Contains(P->StoredItem->Id)) { P->StoredItem->SetActorHiddenInGame(!P->Open); P->StoredItem->SetActorEnableCollision(P->Open); }
        DemoSound(TEXT("chair_drag"),P->Mesh->Bounds.Origin,.2f); Record(TEXT("drawer"),P->Id+(P->Open?TEXT("_open"):TEXT("_closed"))); return;
    }
    if(P->Id==TEXT("cart_start"))
    {
        bool Accessible=false; for(auto* Drawer:Props) if(Drawer->StoredItem==P) Accessible=Drawer->Open && Drawer->Slide>25;
        if(!Accessible) return;
    }
    Record(TEXT("interact"),P->Id);
    if(!Finale.Active && UseDemo(P)) return;
    if(P->Id==TEXT("entrance") && !ExitUnlocked)
    { Message(TEXT("야간 근무 중에는 현관이 잠겨 있다. 아직 나갈 수 없다.")); return; }
    if(P->Id.StartsWith(TEXT("door_")) && !IntroComplete)
    { Message(TEXT("관리실 문이 잠겨 있다. 먼저 걸려오는 전화를 받아야 한다.")); return; }
    if(!Finale.Active && P->Id.StartsWith(TEXT("door_")) && FirstComplaintRequired())
    { Message(TEXT("민원 장부에 호수와 시간을 적자.")); return; }
    if(P->Id==TEXT("entrance")) { const bool Open=!P->Open; for(auto* Leaf:Props)if(Leaf->Id==TEXT("entrance"))Leaf->SetDoor(Open); Record(TEXT("entrance"),Open?TEXT("opened"):TEXT("closed")); return; }
    if(P->Id==TEXT("door_office") || P->Id.StartsWith(TEXT("door_arch_"))) { P->SetDoor(!P->Open); return; }
    if(P->Id.StartsWith(TEXT("cart_")))
    {
        if(!NRMechanics::PickupAllowed(Collected.Contains(P->Id))) return;
        Collected.Add(P->Id); ++Player->Cartridges; P->SetActorHiddenInGame(true); P->SetActorEnableCollision(false);
        Message(Evidence.Contains(TEXT("uv"))?TEXT("UV 카트리지 획득. 예비품으로 보관한다."):TEXT("UV 카트리지 획득. T 장착 → Q UV 전환.\nUV를 켜고 흔적이 남았을 만한 곳을 비춰 보자.\n흔적을 보며 E로 기록. 일반광에서는 소모되지 않는다.")); return;
    }
    if(P->Id==TEXT("rules"))
    {
        ReadRules=true; ShowDocument(TEXT("rules"));
        return;
    }
    if(P->Id==TEXT("phone"))
    {
        if(PhoneStage==3)
        {
            if(!EndingPending) ShowDocument(TEXT("final_call"));
            AnsweredStage=PhoneStage; return;
        }
        if(PhoneStage>0 && AnsweredStage<PhoneStage)
        { ShowDocument(PhoneStage==1?TEXT("first_call"):TEXT("second_call")); AnsweredStage=PhoneStage; Record(TEXT("answer"),FString::FromInt(PhoneStage)); }
        else Message(TEXT("수화기에서는 낮은 잡음만 들린다.")); return;
    }
    if(P->Id==TEXT("cctv") || P->Id.StartsWith(TEXT("cctv_display_")))
    {
        CCTVView=true; RulesView=false; PaperView=false; CaptureTime=0; LiveCCTV();
        if(!MonitorOff && (!ReportFiled || CCTVReset)) for(auto* Camera:CCTVCameras) Camera->CaptureScene();
        Page=TEXT("출입 기록  |  열람 시작 시각 ")+ShiftClock(Elapsed,true)+TEXT("\n\n");

        Page+=Elapsed<FirstCall?TEXT("이 시간대에 저장된 감지 기록이 없습니다."):TEXT("02:13 — 2층 움직임 감지. 원본 녹화 파일을 열 수 없습니다.\n현재 화면과 녹화 기록은 서로 다른 시점의 정보입니다.");
        Documents.Add(TEXT("cctv"),Page); Evidence.Add(TEXT("cctv")); Record(TEXT("cctv"),TEXT("monitor_stack"));
        if(DocumentScroll) DocumentScroll->ScrollToStart(); return;
    }
    if(P->Id==TEXT("door_202"))
    {
        if(Evidence.Contains(TEXT("202_safe_report"))) { Message(TEXT("미입실 보고를 마친 방이다. 문은 닫아 두자.")); return; }
        if(!Evidence.Contains(TEXT("physical"))) { ShowDocument(TEXT("physical")); return; }
        if(!P->Open) { Evidence.Remove(TEXT("202_avoided")); SaveCheckpoint(); P->SetDoor(true); Record(TEXT("door"),TEXT("202_open")); }
        else P->SetDoor(false);
        return;
    }
    if(P->Id==TEXT("door_203")) { P->SetDoor(false); ShowDocument(TEXT("minseo")); return; }
    if(P->Id.StartsWith(TEXT("door_")) && TSet<FString>{TEXT("door_103"),TEXT("door_106"),TEXT("door_109"),TEXT("door_201"),TEXT("door_209"),TEXT("door_302"),TEXT("door_307"),TEXT("door_310")}.Contains(P->Id)) { P->SetDoor(!P->Open); return; }
    if(P->Id.StartsWith(TEXT("door_")))
    {
        P->SetDoor(false);
        if(P->Id==TEXT("door_204") || P->Id==TEXT("door_208") || P->Id==TEXT("door_301"))
            ShowDocument(TEXT("resident_")+P->Id.Right(3)+TEXT("_greeting"));
        else ShowDocument(P->Id==TEXT("door_105")?TEXT("resident_105_early"):P->Id==TEXT("door_104")?TEXT("resident_104"):TEXT("resident_quiet"));
        return;
    }
    if(P->Id==TEXT("chair")) { ShowDocument(TEXT("chair")); return; }
    ShowDocument(P->Id);
}
void ANRGameMode::OpenJournal()
{
    if(Finale.Active && !Finale.Outcome.IsEmpty())return;
    CloseComplaintLog();
    CCTVView=false; RulesView=false; PaperView=false;
    Page=ComplaintLogText()+TEXT("\n────────────────────────\n\n발견한 자료\n\n");
    if(Finale.Active)Page=FinaleReport()+TEXT("\n────────────────────────\n\n")+Page;
    TArray<FString> Keys=Evidence.Array(); Keys.Sort();
    for(const auto& Key:Keys) if(const auto* Text=Documents.Find(Key)) {
        if(Key.StartsWith(TEXT("complaint_"))) continue;
        const auto* Report=ComplaintLog.Reports.Find(Key);
        FString Entry=Report?*Report:*Text;
        if(Key==TEXT("service_ledger") && !ComplaintLog.LedgerLine.IsEmpty()) Entry+=TEXT("\n\n")+ComplaintLog.LedgerLine;
        Page+=Entry+TEXT("\n\n────────────────────────\n\n");
    }
    if(Keys.IsEmpty()) Page+=TEXT("아직 기록한 자료가 없습니다.");
    if(DocumentScroll) DocumentScroll->ScrollToStart();
}
void ANRGameMode::Escape()
{
    if(Dead || Finished) return;
    FinaleConfirm=0;
    if(!Page.IsEmpty()) { CloseComplaintLog(); SavePreferences(); SettingsOpen=false; LiveCCTV(); Page.Empty(); CCTVView=false; RulesView=false; PaperView=false; Paused=false; UpdatePointerInput(true); return; }
    Paused=!Paused;
    if(Paused)
    {
        CCTVView=false; RulesView=false; PaperView=false; Page=TEXT("일시정지");
        if(DocumentScroll) DocumentScroll->ScrollToStart();
    }
}
void ANRGameMode::SaveCheckpoint()
{
    if(!Player) return;
    if(Finale.Active && (Threat || Finale.PursuitTime>0 || !Finale.Outcome.IsEmpty()))return;
    FinaleCheckpoint=Finale;
    ComplaintCheckpoint=ComplaintLog;
    Checkpoint.Time=Elapsed; Checkpoint.UV=Player->UVRemaining; Checkpoint.Carts=Player->Cartridges;
    Checkpoint.Phone=PhoneStage; Checkpoint.Answered=AnsweredStage; Checkpoint.Rules=ReadRules;
    Checkpoint.Monitor=MonitorOff; Checkpoint.Reset=CCTVReset; Checkpoint.Round=RoundFiled; Checkpoint.MonitorTime=MonitorOffAt; Checkpoint.CCTVStopTime=CCTVStoppedAt;
    Checkpoint.Out=PowerOut; Checkpoint.Repaired=PowerRepaired; Checkpoint.Fuse=HasFuse; Checkpoint.Report=ReportFiled;
    Checkpoint.DemoTime=DemoSeconds; Checkpoint.Scares=ScareEvents;
    Checkpoint.Intro=IntroComplete;
    Checkpoint.RedText=Red; Checkpoint.Witness=Witnessed; Checkpoint.Room=RoomEntered;
    Checkpoint.Found=Evidence; Checkpoint.Pickups=Collected; Checkpoint.Position=Player->GetActorLocation();
    Checkpoint.Rotation=Player->GetControlRotation(); Checkpoint.Doors.Empty();
    for(auto* P:Props) if(P->Id.StartsWith(TEXT("door_")) || P->Sliding || P->CorePanels.Num()>0) Checkpoint.Doors.Add(P->Id,P->Open);
    HasCheckpoint=true; Record(TEXT("checkpoint"),TEXT("safe_corridor"));
}
void ANRGameMode::RestoreCheckpoint()
{
    if(!HasCheckpoint || !Player) return;
    Finale=FinaleCheckpoint;FinaleConfirm=0;Finished=false;
    Player->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
    CloseComplaintLog(); ComplaintLog=ComplaintCheckpoint;
    StopVoice(); LiveCCTV(); HistoryCount=0; HistoryHead=0; RecordTimer=0;
    Elapsed=Checkpoint.Time; Player->UVRemaining=Checkpoint.UV; Player->Cartridges=Checkpoint.Carts;
    PhoneStage=Checkpoint.Phone; AnsweredStage=Checkpoint.Answered; ReadRules=Checkpoint.Rules;
    MonitorOff=Checkpoint.Monitor; CCTVReset=Checkpoint.Reset; RoundFiled=Checkpoint.Round; MonitorOffAt=Checkpoint.MonitorTime; CCTVStoppedAt=Checkpoint.CCTVStopTime;
    if(MonitorOff) for(auto* Target:CCTVTargets) UKismetRenderingLibrary::ClearRenderTarget2D(this,Target,FLinearColor::Black);
    PowerRepaired=Checkpoint.Repaired; HasFuse=Checkpoint.Fuse; ReportFiled=Checkpoint.Report;
    DemoSeconds=Checkpoint.DemoTime; ScareEvents=Checkpoint.Scares; FlickerTime=0; SetPower(Checkpoint.Out);
    IntroComplete=Checkpoint.Intro; IntroCallPending=false; ExitUnlocked=false;
    RuleReplyDelay=0; Red=Checkpoint.RedText; Witnessed=Checkpoint.Witness; RoomEntered=Checkpoint.Room;
    Evidence=Checkpoint.Found; Collected=Checkpoint.Pickups;
    FinishComplaintDialogue(); // Saved in-flight optional conversations retain their receipt row.
    for(auto* P:Props)
    {
        if(P->Id.StartsWith(TEXT("cart_")) || P->Id==TEXT("spare_fuse")) { const bool Gone=Collected.Contains(P->Id); P->SetActorHiddenInGame(Gone); P->SetActorEnableCollision(!Gone); }
        if(const bool* Open=Checkpoint.Doors.Find(P->Id)) {
            P->SetDoor(*Open);
            if(P->CorePanels.Num()>0) { P->CorePanelAngle=*Open?-100.f:0.f; P->ApplyCorePanelPose(); }
        }
    }
    for(auto* Drawer:Props) if(Drawer->Sliding)
    {
        Drawer->Slide=Drawer->Open?38.f:0.f; Drawer->SetActorLocation(Drawer->Home+FVector(0,-Drawer->Slide,0));
        if(Drawer->StoredItem) {
            const bool Accessible=Drawer->Open && !Collected.Contains(Drawer->StoredItem->Id);
            Drawer->StoredItem->SetActorLocation(Drawer->StoredItem->Home+FVector(0,-Drawer->Slide,0));
            Drawer->StoredItem->SetActorHiddenInGame(!Accessible); Drawer->StoredItem->SetActorEnableCollision(Accessible);
        }
    }
    Player->SetActorLocation(Checkpoint.Position); Player->GetController()->SetControlRotation(Checkpoint.Rotation);
    Player->GetCharacterMovement()->StopMovementImmediately(); Player->UV=false;
    DreamActive=false; DreamTime=0; DreamBeat=0;
    WakeTrace->SetActorHiddenInGame(!Evidence.Contains(TEXT("dream_wake"))); WakeTrace->SetActorEnableCollision(Evidence.Contains(TEXT("dream_wake")));
    if(auto* PC=Player->GetController<APlayerController>()) PC->PlayerCameraManager->SetManualCameraFade(0,FLinearColor::Black,false);
    ThreatPending=false; PreludeCue=false; PreludeTime=0; Player->SprintHeld=false; Player->UnCrouch();
    ResetExecution();
    Dead=false; Threat=false; EncounterDone=false; ThreatTime=0; Paused=false; Page.Empty();
    SubtitleLines.Reset(); SubtitleIndex=0; MessageTime=0; SubtitleSource.Empty();
    EndingPending=false; FinalKnockTime=0; FinalKnockStage=0;
    CCTVView=false; RulesView=false; PaperView=false;
    Ghost->SetActorHiddenInGame(true); RingTimer=0; KnockTimer=0;
    WitnessUntil=0; FinalRings=0; Notice.Empty(); Record(TEXT("checkpoint"),TEXT("restored"));
    ApplyFinaleWorld();
}
void ANRGameMode::EndDemo()
{
    EndingPending=false; Finished=true; CCTVView=false; RulesView=false; PaperView=false;
    const bool Ignored=Evidence.Contains(TEXT("final_call_ignored"));
    Page=FString(TEXT("DAY 1 프로토타입 끝\n\n"))
        +(Evidence.Contains(TEXT("202_avoided"))?TEXT("202호에 들어가지 않고 근무를 마쳤다.\n잠금 사고와 그에 이어지는 추격을 피했다.\n"):TEXT("202호에 진입했다. 잠긴 방과 관리실에서 깨어난 기억이 남았다.\n"))
        +(Ignored?TEXT("307호 전화는 끝내 받지 않았다. 다섯 번째 벨이 끝나자 고시원이 조용해졌다.\n"):TEXT("307호 전화를 받았다. 관리실 문밖의 노크는 아직 멎지 않았다.\n"))
        +TEXT("\n민원 장부의 조사 방침: ")+InvestigationPlanName()+TEXT("\n\n[Enter] 최종밤 엔딩 테스트로 이어가기\n현재 DAY 2~4는 미구현 상태로 생략됩니다. 두 시간 본편 완성본이 아닙니다.");
    if(DocumentScroll) DocumentScroll->ScrollToStart();
    Record(TEXT("demo_end"),FString(Evidence.Contains(TEXT("202_avoided"))?TEXT("avoided_202"):RoomEntered?TEXT("investigated"):TEXT("unresolved"))+(Ignored?TEXT("_307_ignored"):TEXT("_307_answered")));
}
void ANRGameMode::Die()
{
    if(Dead) return;
    const bool ChairCatch=Threat && GhostVisual && ChairKillClip && PursuitChair;
    Dead=true; Threat=false; ThreatPending=false; ApplyLightState(PowerOut); Player->GetCharacterMovement()->StopMovementImmediately();
    CCTVView=false; RulesView=false; PaperView=false;
    StopVoice();SubtitleLines.Reset();Notice.Empty();Player->SprintHeld=false;
    if(ChairCatch) {
        // A long frame can cross the catch radius. Keep the execution camera out
        // of the torso, without moving the apparition through a wall behind it.
        const FVector Away=(Ghost->GetActorLocation()-Player->GetActorLocation()).GetSafeNormal2D();
        const FVector Framed=Player->GetActorLocation()+Away*90.f;
        FHitResult Hit;FCollisionQueryParams Q;Q.AddIgnoredActor(Ghost);Q.AddIgnoredActor(Player);
        if(!GetWorld()->SweepSingleByChannel(Hit,Ghost->GetActorLocation(),Framed,FQuat::Identity,ECC_Visibility,FCollisionShape::MakeSphere(20),Q))Ghost->SetActorLocation(Framed);
        GhostSpeed=0;
        ExecutionActive=true;ExecutionHit=false;ExecutionTime=0;
        ExecutionCameraHome=Player->Camera->GetRelativeLocation();ExecutionLookHome=Player->GetControlRotation();
        Page.Empty();GhostVisual->bPauseAnims=false;GhostVisual->PlayAnimation(ChairKillClip,false);GhostVisual->SetPlayRate(1);
        Ghost->SetActorRotation(FRotator(0,(Player->GetActorLocation()-Ghost->GetActorLocation()).Rotation().Yaw,0));
        Record(TEXT("death"),TEXT("chair_execution"));UpdatePointerInput(true);return;
    }
    DemoSound(TEXT("door_slam"),Player->GetActorLocation(),.55f);
    Page=TEXT("붙잡혔다.\n\n문이 닫히는 소리만 남았다.");
    if(DocumentScroll) DocumentScroll->ScrollToStart();
    Record(TEXT("death"),TEXT("caught"));
}
FVector ANRGameMode::NextGhostWaypoint() const
{
    const FVector Start=Ghost->GetActorLocation(); const FVector Goal(Player->GetActorLocation().X,Player->GetActorLocation().Y,410);
    FCollisionQueryParams Query; Query.AddIgnoredActor(Ghost); Query.AddIgnoredActor(Player);
    auto Clear=[&](const FVector& A,const FVector& B) { FHitResult Hit; return !GetWorld()->SweepSingleByChannel(Hit,A,B,FQuat::Identity,ECC_Visibility,FCollisionShape::MakeSphere(20),Query); };
    if(Clear(Start,Goal)) return Goal;
    TArray<FVector> Nodes={Start};
    for(float X:{-350.f,290.f}) Nodes.Add(FVector(X,0,410));
    for(float X:{290.f,600.f,865.f,1150.f,1700.f,2250.f,2800.f,3350.f,3700.f}) Nodes.Add(FVector(X,NRLayout::CorridorY,410));
    for(float X:{1302.5f,2375.f,3037.5f}) {
        Nodes.Add(FVector(X,NRLayout::CorridorY,410));
        Nodes.Add(FVector(X,-310,410));
        Nodes.Add(FVector(X,-550,410));
        Nodes.Add(FVector(X,-750,410));
    }
    for(float X:{-350.f,290.f,865.f,2800.f}) Nodes.Add(FVector(X,-550,410));
    Nodes.Add(Goal); const int32 Last=Nodes.Num()-1;
    TArray<float> Cost; Cost.Init(MAX_flt,Nodes.Num()); Cost[0]=0;
    TArray<int32> Previous; Previous.Init(-1,Nodes.Num()); TArray<bool> Visited; Visited.Init(false,Nodes.Num());
    for(int32 Step=0;Step<Nodes.Num();++Step)
    {
        int32 Current=-1;
        for(int32 I=0;I<Nodes.Num();++I) if(!Visited[I] && (Current<0 || Cost[I]<Cost[Current])) Current=I;
        if(Current<0 || Cost[Current]==MAX_flt) break;
        if(Current==Last) { int32 Next=Last; while(Previous[Next]>0) Next=Previous[Next]; return Nodes[Next]; }
        Visited[Current]=true;
        for(int32 I=1;I<Nodes.Num();++I)
        {
            if(Visited[I]) continue;
            const float Candidate=Cost[Current]+FVector::Dist(Nodes[Current],Nodes[I]);
            if(Candidate<Cost[I] && Clear(Nodes[Current],Nodes[I])) { Cost[I]=Candidate; Previous[I]=Current; }
        }
    }
    return Start; // Closed doors or furniture block the route; do not phase through them.
}
void ANRGameMode::StartThreat()
{
    if(GhostVisual) { GhostVisual->PlayAnimation(ChairRunClip?ChairRunClip:LoadObject<UAnimSequence>(nullptr,TEXT("/Game/PrototypeAssets/GhostMeshy/A_CaretakerRun.A_CaretakerRun")),true); GhostVisual->SetPlayRate(0.f); }
    Threat=true; ThreatTime=0; GhostRouteTime=0; GhostStepTime=.2f; GhostSpeed=0; RoomEntered=true;
    const FVector Door202=NRLayout::DoorAnchor(1,1);
    // The rear corridor is gone. Keep the only route to the east staircase ahead
    // of the player; pursuit comes from the west, with time to start running.
    const float SpawnX=FMath::Clamp(Player->GetActorLocation().X-1400.f,-350.f,3350.f);
    const FVector Spawn(SpawnX,NRLayout::CorridorY,410);
    Ghost->SetActorLocation(Spawn); Ghost->SetActorHiddenInGame(false);
    Record(TEXT("encounter"),TEXT("late_round_pursuit")); Sound(TEXT("knock"),Door202+FVector(0,0,100));
}
void ANRGameMode::PointerInputTest()
{
    int32 Failures=0;
    auto Check=[&](bool OK,const TCHAR* What){if(!OK)++Failures;UE_LOG(LogTemp,Display,TEXT("NR_POINTER %s %s"),OK?TEXT("PASS"):TEXT("FAIL"),What);};
    auto* PC=Player->GetController<APlayerController>();
    auto* Viewport=GetWorld()->GetGameViewport();
    auto Gameplay=[&] {return !ModalInput && !PC->bShowMouseCursor && Viewport->HideCursorDuringCapture()
        && Viewport->GetMouseCaptureMode()==EMouseCaptureMode::CapturePermanently_IncludingInitialMouseDown
        && Screen->GetVisibility()==EVisibility::HitTestInvisible;};
    Page.Empty(); UpdatePointerInput(true); Check(Gameplay(),TEXT("startup captures mouse and HUD cannot intercept clicks"));
    for(int32 I=0;I<3;++I) {
        Escape(); UpdatePointerInput();
        Check(ModalInput && PC->bShowMouseCursor && Viewport->GetMouseLockMode()==EMouseLockMode::LockAlways,TEXT("pause permits pointer controls inside the window"));
        Escape(); Check(Gameplay(),TEXT("resume immediately hides and captures pointer"));
        ANRProp* Monitor=nullptr;for(auto* P:Props) if(P->Id==TEXT("cctv")){Monitor=P;break;}
        if(Monitor) {Use(Monitor);UpdatePointerInput();Check(CCTVView && PC->bShowMouseCursor,TEXT("CCTV controls retain cursor"));Escape();Check(Gameplay(),TEXT("CCTV close restores gameplay input"));}
        else Check(false,TEXT("CCTV monitor exists"));
        OpenJournal();UpdatePointerInput();Check(ModalInput && PC->bShowMouseCursor,TEXT("journal scroll retains cursor"));
        Escape();Check(Gameplay(),TEXT("journal close restores gameplay input"));
    }
    PC->bShowMouseCursor=true;UpdatePointerInput();Check(Gameplay(),TEXT("unexpected visible cursor is repaired without opening a menu"));
    UE_LOG(LogTemp,Display,TEXT("NR_POINTER_COMPLETE failures=%d"),Failures);
    FPlatformMisc::RequestExitWithStatus(false,Failures?1:0);
}
void ANRGameMode::UpdatePointerInput(bool Force)
{
    if(!Player) return;
    auto* PC=Player->GetController<APlayerController>();
    auto* Viewport=GetWorld()->GetGameViewport();
    if(!PC || !Viewport) return;
    const bool WantsModal=!Page.IsEmpty();
    // Restore capture only after this window has focus; never pull focus back from another app.
    const bool LostCapture=!WantsModal && Viewport->Viewport && Viewport->Viewport->HasFocus()
        && FSlateApplication::Get().IsActive() && !Viewport->Viewport->HasMouseCapture();
    if(Force || ModalInput!=WantsModal || PC->bShowMouseCursor!=WantsModal || LostCapture)
    {
        const bool Changed=ModalInput!=WantsModal;
        ModalInput=WantsModal;
        if(ModalInput)
        {
            // A reading panel must also stop momentum and queued movement from the preceding frame.
            Player->ConsumeMovementInputVector(); Player->GetCharacterMovement()->StopMovementImmediately();
        }
        if(Changed) PC->FlushPressedKeys();
        PC->bShowMouseCursor=ModalInput;
        if(ModalInput) {
            FInputModeGameAndUI Mode; Mode.SetHideCursorDuringCapture(false); Mode.SetLockMouseToViewportBehavior(EMouseLockMode::LockAlways);
            if(Paused && PauseResume) Mode.SetWidgetToFocus(PauseResume.ToSharedRef());
            else if(DocumentScroll) Mode.SetWidgetToFocus(DocumentScroll.ToSharedRef());
            PC->SetInputMode(Mode);
        } else {
            // GameOnly does not reset the cursor-capture flag left behind by GameAndUI.
            Viewport->SetHideCursorDuringCapture(true);
            FInputModeGameOnly Mode; Mode.SetConsumeCaptureMouseDown(false); PC->SetInputMode(Mode);
        }
    }
}
void ANRGameMode::Tick(float D)
{
    Super::Tick(D); if(!Player) return;
    TickResidentVisuals(D);
    TickScore(D);
    if(ExecutionActive) {TickExecution(D);return;}
    TickPursuitChair(D);
    UpdatePointerInput();
    if(Page.IsEmpty()) { CCTVView=false; RulesView=false; PaperView=false; }
    if(ActiveVoice) ActiveVoice->SetPaused(Paused || !Page.IsEmpty());
    if(Dead || Finished)
    {
        StopVoice();
        SubtitleLines.Reset(); SubtitleIndex=0; Notice.Empty(); SubtitleSource.Empty(); MessageTime=0; EndingPending=false;
        return;
    }
    if(GhostVisual) GhostVisual->bPauseAnims=Paused || (!Page.IsEmpty() && !CCTVView);
    if(Paused) return;
    TickComplaintLog(D);
    if(EndingPending && Page.IsEmpty())
    {
        FinalKnockTime+=D;
        if(FinalKnockStage==0 && FinalKnockTime>=3.f)
        {
            DemoSound(TEXT("knock"),NRLayout::OfficePoint(FVector(-65,-300,90)),.35f);
            FinalKnockStage=1; Record(TEXT("scare"),TEXT("final_phone_knock"));
        }
        if(FinalKnockStage==1 && FinalKnockTime>=6.f)
        {
            DemoSound(TEXT("knock"),FVector(NRLayout::OfficeDoorX,-480,120),.65f);
            FinalKnockStage=2; Record(TEXT("scare"),TEXT("final_door_knock"));
        }
    }
    // Subtitles never pause gameplay. An enlarged document hides and suspends them until it closes.
    if(Page.IsEmpty() && SubtitleLines.IsValidIndex(SubtitleIndex))
    {
        MessageTime-=FMath::Max(0.f,D);
        while(MessageTime<=0 && SubtitleLines.IsValidIndex(SubtitleIndex))
        {
            ++SubtitleIndex;
            if(SubtitleLines.IsValidIndex(SubtitleIndex))
            {
                Notice=SubtitleLines[SubtitleIndex].Text; if(!SubtitleLines[SubtitleIndex].Speaker.IsEmpty()) SubtitleSource=SubtitleLines[SubtitleIndex].Speaker; MessageTime+=SubtitleLines[SubtitleIndex].Duration; PlayVoiceLine();
            }
            else
            {
                FinishComplaintDialogue();
                StopVoice();
                SubtitleLines.Reset(); SubtitleIndex=0; Notice.Empty(); SubtitleSource.Empty(); MessageTime=0;
                if(IntroCallPending)
                {
                    IntroCallPending=false; IntroComplete=true;
                    for(auto* P:Props) if(P->Id==TEXT("door_office")) P->SetDoor(FirstComplaintWritten());
                    Record(TEXT("intro"),TEXT("first_call_complete_ledger_pending")); SaveCheckpoint();
                }
                if(EndingPending)
                {
                    EndDemo();
                }
            }
        }
    }
    TickRuleAnnotations(D);
    // All displays and receipts share this clock, including the independent final night.
    if((Page.IsEmpty() || CCTVView) && (Finale.Active || PhoneStage==0 || IntroComplete)) Elapsed+=D;
    TickDisplays(Page.IsEmpty() || CCTVView?D:0.f);
    TickUV();
    if(Finale.Active) {TickFinale(D);return;}
    // Reading freezes investigation timers in this first build to avoid text-speed punishment.
    if(!Page.IsEmpty() && !CCTVView) return;
    if(PhoneStage==0 && Elapsed>=FirstCall) { PhoneStage=1; RingTimer=0; Record(TEXT("event"),TEXT("first_call")); }
    if(IntroComplete && PhoneStage<2 && Elapsed>=FirstCall+SecondCall && NRMechanics::SecondCallAllowed(Evidence.Contains(TEXT("minseo")),Evidence.Contains(TEXT("dream_wake")),Evidence.Contains(TEXT("202_avoided")))) { PhoneStage=2; RingTimer=0; Record(TEXT("event"),TEXT("second_call")); }
    if(PhoneStage>AnsweredStage) { RingTimer-=D; if(RingTimer<=0)
    {
        if(PhoneStage==3 && ++FinalRings>5) { AnsweredStage=3; Evidence.Add(TEXT("final_call_ignored")); Record(TEXT("demo"),TEXT("final_call_ignored")); EndDemo(); return; }
        Sound(TEXT("phone_ring"),NRLayout::OfficePoint(FVector(-65,-300,90))); RingTimer=6;
    } }
    const FVector Pos=Player->GetActorLocation(), Door202=NRLayout::DoorAnchor(1,1);
    const float RoomLeft202=NRLayout::RoomLeft(1);
    // A visit alone no longer materializes the ghost. The resident's account
    // and the broken handle establish the incident before its audible prelude.
    if(!DreamActive && !Evidence.Contains(TEXT("dream_wake")) && !Evidence.Contains(TEXT("202_avoided")) && !Threat && !ThreatPending && Evidence.Contains(TEXT("minseo")) && Evidence.Contains(TEXT("physical")) && Pos.Z>350 && Pos.Z<640 && Pos.X>RoomLeft202+5 && Pos.X<RoomLeft202+NRLayout::RoomPitch-5 && Pos.Y>NRLayout::RoomFront+75)
        StartDream();
    // Story DAY 1: arriving early, the player sees someone slip into 202. Nobody chases.
    ANRProp* Door202Prop=nullptr; for(auto* P:Props) if(P->Id==TEXT("door_202")) { Door202Prop=P; break; }
    if(!Witnessed && IntroComplete && Door202Prop && !Door202Prop->Open && !DreamActive && !Threat && !ThreatPending && !Evidence.Contains(TEXT("physical"))
       && NRMechanics::WitnessWindow(Elapsed,FirstCall,WitnessWindow) && Pos.Z>350 && Pos.Z<640 && Pos.Y<NRLayout::RoomFront && FMath::Abs(Pos.X-Door202.X)<700)
    {
        const FVector Eye=Player->Camera->GetComponentLocation(), Seen=Door202+FVector(0,-15,150);
        FHitResult Block; FCollisionQueryParams Query; Query.AddIgnoredActor(Player); Query.AddIgnoredActor(Ghost); Query.AddIgnoredActor(Door202Prop);
        if(FVector::DotProduct((Seen-Eye).GetSafeNormal(),Player->Camera->GetForwardVector())>.75f && !GetWorld()->LineTraceSingleByChannel(Block,Eye,Seen,ECC_Visibility,Query))
        {
            Witnessed=true; WitnessUntil=Elapsed+1.8f; Door202Prop->SetDoor(true);
            Ghost->SetActorLocation(Door202+FVector(0,60,90)); Ghost->SetActorRotation(FRotator(0,90,0)); Ghost->SetActorHiddenInGame(false);
            if(GhostVisual) GhostVisual->SetPlayRate(1.f);
            Message(TEXT("누군가 202호 안으로 들어갔다."),3); Evidence.Add(TEXT("witness")); Record(TEXT("witness"),TEXT("202_figure"));
        }
    }
    if(WitnessUntil>0 && Elapsed>=WitnessUntil && !Threat && !DreamActive)
    {
        WitnessUntil=0; Ghost->SetActorHiddenInGame(true);
        if(Door202Prop) { Door202Prop->SetDoor(false); DemoSound(TEXT("knock"),Door202+FVector(0,20,100),.3f); }
    }
    Tick202Choice();
    TickDream(D);
    TickPrelude(D);
    if(Threat)
    {
        ThreatTime+=D;
        if(ThreatTime>2.5f)
        {
            GhostRouteTime-=D;
            if(GhostRouteTime<=0) { GhostRouteTime=.45f; GhostDestination=NextGhostWaypoint(); }
            const FVector Delta=GhostDestination-Ghost->GetActorLocation();
            if(!Delta.IsNearlyZero()) Ghost->SetActorRotation(FMath::RInterpTo(Ghost->GetActorRotation(),FRotator(0,Delta.Rotation().Yaw,0),D,12.f));
            GhostSpeed=FMath::FInterpConstantTo(GhostSpeed,GhostChaseSpeed*GhostLurch(),D,900.f);
            const float Travel=FMath::Min(Delta.Size(),GhostSpeed*D);
            const FVector Next=Ghost->GetActorLocation()+Delta.GetSafeNormal()*Travel;
            FHitResult Block; FCollisionQueryParams Query; Query.AddIgnoredActor(Ghost); Query.AddIgnoredActor(Player);
            if(!GetWorld()->SweepSingleByChannel(Block,Ghost->GetActorLocation(),Next,FQuat::Identity,ECC_Visibility,FCollisionShape::MakeSphere(20),Query))
            {
                const bool Moving=FVector::DistSquared(Ghost->GetActorLocation(),Next)>.001f;
                Ghost->SetActorLocation(Next);
                // Measured stance-foot speed of the edited clip: 367.4 cm/s at 1x.
                const float RunRate=D>SMALL_NUMBER?Travel/(D*367.4f):0.f;
                if(GhostVisual) GhostVisual->SetPlayRate(Moving?RunRate:0.f);
                if(Moving)
                {
                    GhostStepTime-=D*RunRate;
                    if(GhostStepTime<=0)
                    {
                        GhostStepTime+=GhostRunCycle*.5f;
                        PlayFootstep(true,Next-FVector(0,0,80));
                    }
                }
            }
            else { GhostSpeed=0; if(GhostVisual) GhostVisual->SetPlayRate(0.f); }
            if(FMath::Abs(Pos.Z-Ghost->GetActorLocation().Z)<120 && FVector::Dist2D(Pos,Ghost->GetActorLocation())<65) Die();
            else if(ThreatTime>8 && Pos.Z<250) { Threat=false; EncounterDone=true; Ghost->SetActorHiddenInGame(true); Record(TEXT("encounter"),TEXT("escaped_downstairs")); }

        }
    }
    if(!DreamActive && !Evidence.Contains(TEXT("dream_wake")) && !Evidence.Contains(TEXT("202_avoided")) && Elapsed>=FirstCall+WitnessWindow && PhoneStage>0 && Pos.Z>350 && Pos.Z<640 && FVector::Dist2D(Pos,Door202)<450)
    { KnockTimer-=D; if(KnockTimer<=0) { Sound(TEXT("knock"),Door202+FVector(0,10,100)); KnockTimer=18; } }
    TickDemo(D);
    // The final call follows power restoration and cross-checking physical records.
    if(!Red && IntroComplete && NRLayout::InOffice(Pos))
    { Red=true; Record(TEXT("red"),TEXT("first_appearance")); }
    if(Red && DemoReady() && PhoneStage<3 && NRLayout::InOffice(Pos))
    { PhoneStage=3; RingTimer=0; Record(TEXT("demo"),TEXT("final_call_ready")); }
    if(Pos.Z<-500) Die();
}

void ANRGameMode::MapTest()
{
    Page.Empty(); FirstCall=99999; IntroComplete=true;
    for(auto* P:Props) if(P->Id==TEXT("door_202") || P->Id==TEXT("door_office")) P->SetDoor(true);
    struct FMapTest { int32 Step=0; float Time=0; FTimerHandle Timer; };
    auto Test=MakeShared<FMapTest>();
    const TArray<FVector> Route={FVector(NRLayout::OfficeShift+85,-750,90),FVector(NRLayout::OfficeDoorX,-750,90),FVector(NRLayout::OfficeDoorX,-650,90),FVector(NRLayout::OfficeDoorX,-560,90),FVector(NRLayout::OfficeDoorX,-370,90),FVector(-70,-135,90),FVector(3610,-135,90),FVector(3610,-790,250),FVector(3790,-790,250),FVector(3790,-250,410),FVector(3790,-135,410),FVector(NRLayout::DoorAnchor(1,1).X,-135,410),FVector(NRLayout::DoorAnchor(1,1).X,20,410)};
    auto* Viewport=GetWorld()->GetGameViewport();
    Viewport->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::W,IE_Pressed,1,1,FInputDeviceId::CreateFromInternalId(0),false,Viewport->Viewport));
    GetWorld()->GetTimerManager().SetTimer(Test->Timer,[this,Test,Route]()
    {
        Test->Time+=.1f;
        const FVector Position=Player->GetActorLocation(); const FVector Target=Route[Test->Step];
        // Loose corner acceptance left the capsule against the south corridor
        // wall before the 36m eastward leg. Centre it before changing direction.
        if(FVector::Dist2D(Position,Target)<18 && FMath::Abs(Position.Z-Target.Z)<40)
        {
            UE_LOG(LogTemp,Display,TEXT("NR_MAP PASS step=%d at=(%.1f,%.1f,%.1f)"),Test->Step,Position.X,Position.Y,Position.Z);
            if(++Test->Step==Route.Num()) { UE_LOG(LogTemp,Display,TEXT("NR_MAP_COMPLETE failures=0")); FPlatformMisc::RequestExitWithStatus(false,0); return; }
        }
        if(Test->Time>130 || Dead) {
            FHitResult Hit;FCollisionQueryParams Query;Query.AddIgnoredActor(Player);Query.AddIgnoredActor(Ghost);
            GetWorld()->SweepSingleByChannel(Hit,Position,Route[Test->Step],FQuat::Identity,ECC_Pawn,FCollisionShape::MakeCapsule(28,85),Query);
            const auto* Block=Cast<ANRProp>(Hit.GetActor());
            UE_LOG(LogTemp,Error,TEXT("NR_MAP_COMPLETE failures=1 stuck step=%d at=(%.1f,%.1f,%.1f) axis=%.1f canmove=%d obstruction=%s impact=%s"),Test->Step,Position.X,Position.Y,Position.Z,Player->InputComponent->GetAxisValue(TEXT("Forward")),Player->CanMove(),Block?*Block->Id:*GetNameSafe(Hit.GetActor()),*Hit.ImpactPoint.ToString());
            FPlatformMisc::RequestExitWithStatus(false,1); return;
        }
        const FVector Direction=Route[Test->Step]-Position;
        Player->GetController()->SetControlRotation(FRotator(0,FMath::RadiansToDegrees(FMath::Atan2(Direction.Y,Direction.X)),0));
        // Focus/modal transitions can flush a held key. Restore the real input,
        // instead of assuming the one startup press remains down for two minutes.
        if(Player->CanMove() && Player->InputComponent->GetAxisValue(TEXT("Forward"))<.5f) {
            auto* V=GetWorld()->GetGameViewport();
            V->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::W,IE_Released,0,1,FInputDeviceId::CreateFromInternalId(0),false,V->Viewport));
            V->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::W,IE_Pressed,1,1,FInputDeviceId::CreateFromInternalId(0),false,V->Viewport));
        }
    },.1f,true,.5f);
}
void ANRGameMode::InspectPresentation()
{
    int32 Failures=0,Pickups=0,Displays=0; ANRProp* CCTV=nullptr;
    auto Check=[&Failures](bool OK,const FString& Name) {
        UE_LOG(LogTemp,Display,TEXT("NR_PRESENTATION %s %s"),OK?TEXT("PASS"):TEXT("FAIL"),*Name);
        if(!OK) ++Failures;
    };
    for(auto* P:Props)
    {
        if(P->Id.StartsWith(TEXT("cart_")))
        {
            ++Pickups; const FBox Bounds=P->Mesh->Bounds.GetBox();
            const FVector Center=Bounds.GetCenter(); bool Supported=true;
            for(const FVector2D Offset:{FVector2D(0,0),FVector2D(-8,-3),FVector2D(8,-3),FVector2D(-8,3),FVector2D(8,3)})
            {
                FHitResult Hit; FCollisionQueryParams Query; Query.AddIgnoredActor(P); Query.AddIgnoredActor(Player);
                const FVector At(Center.X+Offset.X,Center.Y+Offset.Y,Bounds.Min.Z);
                const bool HitBase=GetWorld()->LineTraceSingleByChannel(Hit,At+FVector(0,0,.5),At-FVector(0,0,2),ECC_Visibility,Query);
                Supported &= HitBase && FMath::Abs(Hit.ImpactPoint.Z-Bounds.Min.Z)<.3f;
            }
            Check(Supported,P->Id+TEXT(" rests on support at center and corners"));
        }
        if(P->Id==TEXT("cctv") || P->Id.StartsWith(TEXT("cctv_display_")) || P->Id==TEXT("roster"))
        {
            TArray<UStaticMeshComponent*> Components; P->GetComponents(Components);
            for(auto* Component:Components) if(Component->GetName()==TEXT("DisplaySurface"))
            {
                ++Displays;
                Check(Component->GetMaterial(0) && Component->GetMaterial(0)->IsA<UMaterialInstanceDynamic>(),P->Id+TEXT(" has a dynamic screen material"));
                Check(Component->GetComponentLocation().Y<P->GetActorLocation().Y,P->Id+TEXT(" screen faces office chair"));
            }
        }
        if(P->Id==TEXT("cctv")) CCTV=P;
    }
    Check(Pickups==3 && Displays==6,TEXT("three supported cartridges and six monitor screens"));
    Check(DocumentScroll.IsValid() && DocumentScroll->SupportsKeyboardFocus(),TEXT("document scroll panel accepts keyboard focus"));
    if(CCTV)
    {
        Elapsed=0;Use(CCTV);
        Check(CCTVView && !Page.Contains(TEXT("02:13 —")),TEXT("no incident recording before the incident"));
        Player->GetCharacterMovement()->Velocity=FVector(100,0,0);
        Player->AddMovementInput(FVector::ForwardVector,1,true);
        const float Before=Elapsed; Tick(.5f);
        Check(Elapsed>Before && ModalInput && !Player->CanMove(),TEXT("CCTV keeps the world clock running while inspecting cameras"));
        Check(Player->GetVelocity().IsNearlyZero() && Player->GetPendingMovementInputVector().IsNearlyZero(),TEXT("opening a reading panel stops existing and queued movement"));
        Escape(); Tick(0);
        Check(!CCTVView && !ModalInput && Player->CanMove(),TEXT("Esc returns control to the player"));
        Elapsed=FirstCall+1;Use(CCTV);
        Check(Page.Contains(TEXT("02:13 —")),TEXT("recording state follows incident time"));
        Escape(); ShowDocument(TEXT("physical")); Tick(0);
        const auto* SubtitleController=Player->GetController<APlayerController>();
        Check(Page.IsEmpty() && !ModalInput && Player->CanMove() && SubtitleController && !SubtitleController->bShowMouseCursor && !Notice.IsEmpty() && Evidence.Contains(TEXT("physical")),TEXT("investigation subtitles preserve evidence without a modal or cursor"));
        OpenJournal();
        Check(Page.Contains(Documents[TEXT("physical")]),TEXT("journal preserves full subtitle documents"));
        Message(TEXT("temporary"),.1f); Tick(.2f);
        Check(Notice==TEXT("temporary"),TEXT("hidden subtitles wait while reading an enlarged document"));
        Escape(); ReadRules=true; Red=true; ShowDocument(TEXT("rules"));
        Check(RulesView && Red,TEXT("red annotation uses dedicated red text"));
        Escape();
        Check(Page.IsEmpty() && !RulesView && !CCTVView,TEXT("closing rules clears panel state immediately"));
        Escape();
        Check(Paused && !Page.IsEmpty() && !RulesView && !CCTVView,TEXT("pause does not inherit document or CCTV decorations"));
        Escape(); Tick(0);
        Check(!Paused && !ModalInput && Player->CanMove(),TEXT("closing pause returns control to the player"));
        Message(TEXT("첫 줄\n다음 줄")); Tick(MessageTime+.01f);
        const bool Advanced=Notice==TEXT("다음 줄");
        ShowDocument(TEXT("missing_presentation_document"));
        const bool Replaced=SubtitleLines.Num()==1 && SubtitleIndex==0 && Notice==TEXT("특별한 점은 보이지 않는다.");
        Tick(MessageTime+.01f);
        Check(Advanced && Replaced && Notice.IsEmpty() && SubtitleLines.IsEmpty() && Page.IsEmpty() && Player->CanMove(),TEXT("subtitle lines advance in order and a new source replaces the queue"));
    } else Check(false,TEXT("CCTV interactable exists"));
    UE_LOG(LogTemp,Display,TEXT("NR_PRESENTATION_COMPLETE failures=%d"),Failures);
    FPlatformMisc::RequestExitWithStatus(false,Failures?1:0);
}

void ANRGameMode::SmokeTest()
{
    int32 Failures=0;
    const auto Check=[&Failures](bool OK,const TCHAR* Name)
    { UE_LOG(LogTemp,Display,TEXT("NR_SMOKE %s: %s"),OK?TEXT("PASS"):TEXT("FAIL"),Name); if(!OK) ++Failures; };
    Check(Player!=nullptr,TEXT("player spawned"));
    Check(Documents.Num()>=10,TEXT("story documents loaded"));
    Check(Props.Num()>30 && CCTVTargets.Num()==CCTVChannelCount,TEXT("world and cameras created"));
    if(!Player) { FPlatformMisc::RequestExitWithStatus(false,1); return; }
    Check(Player->CanMove(),TEXT("movement enabled on fresh start"));
    Check(Player->InputComponent && Player->InputComponent->GetClass()==UInputComponent::StaticClass(),TEXT("legacy pawn input fixed independently of editor settings"));
    const auto* PC=Cast<APlayerController>(Player->GetController());
    Check(PC && PC->PlayerInput && PC->PlayerInput->GetClass()==UPlayerInput::StaticClass(),TEXT("legacy controller input active"));
    Player->Forward(1); Check(!Player->GetPendingMovementInputVector().IsNearlyZero(),TEXT("movement input accepted")); Player->ConsumeMovementInputVector();
    const FVector Before=Player->GetActorLocation(); FHitResult MoveHit;
    Player->GetCharacterMovement()->MoveUpdatedComponent(FVector(0,-30,0),Player->GetActorQuat(),true,&MoveHit);
    Check(FVector::Dist(Before,Player->GetActorLocation())>25,TEXT("spawn has room for capsule movement"));
    Player->SetActorLocation(Before);
    Page.Empty(); Paused=false;
    ANRProp* Office=nullptr; ANRProp* Entrance=nullptr;
    for(auto* P:Props) { if(P->Id==TEXT("door_office")) Office=P; if(P->Id==TEXT("entrance")) Entrance=P; }
    Check(Office && Entrance,TEXT("story gate doors exist"));
    if(Office && Entrance) {
        Use(Office); Use(Entrance);
        Check(!Office->Open && !Entrance->Open && !IntroComplete,TEXT("opening office and exterior remain locked"));
        Elapsed=FirstCall+SecondCall+10; Tick(0);
        Check(PhoneStage==1,TEXT("ignoring first call cannot skip to second call"));
        const float WaitingTime=Elapsed; Tick(5);
        Check(Elapsed==WaitingTime,TEXT("mandatory-call waiting does not consume investigation time"));
        Elapsed=0; PhoneStage=0;
    }
    ANRProp* Cartridge=nullptr; ANRProp* Door=nullptr; ANRProp* Phone=nullptr;
    for(auto* P:Props)
    { if(P->Id==TEXT("cart_start")) Cartridge=P; if(P->Id==TEXT("door_202")) Door=P; if(P->Id==TEXT("phone")) Phone=P; }
    Check(Cartridge && Door && Phone,TEXT("interactable actors found"));
    if(Cartridge && Door && Phone)
    {
        for(auto* Drawer:Props) if(Drawer->StoredItem==Cartridge) { Use(Drawer); Drawer->Tick(1); }
        Use(Cartridge); Use(Cartridge); Check(Player->Cartridges==1,TEXT("pickup cannot duplicate"));
        Player->Reload(); Check(Player->UVRemaining==UVCapacity && Player->Cartridges==0,TEXT("cartridge load"));
        SaveCheckpoint(); Player->Cartridges=9; Player->UVRemaining=0; Door->SetDoor(true);
        Die(); RestoreCheckpoint();
        Check(!Dead && !Door->Open && Player->Cartridges==0 && Player->UVRemaining==UVCapacity,TEXT("death restores equipment and doors"));
        Page.Empty(); Player->SetActorLocation(NRLayout::OfficePoint(FVector(85,-395,100))); Elapsed=FirstCall+1; Tick(0);
        Check(PhoneStage==1,TEXT("first complaint time transition"));
        Use(Phone); Check(AnsweredStage==1 && Evidence.Contains(TEXT("first_call")) && Page.IsEmpty() && Player->CanMove(),TEXT("phone records evidence and uses movable subtitles"));
        if(Office) { Use(Office); Check(!Office->Open && IntroCallPending,TEXT("office stays closed throughout opening dialogue")); }
        float IntroRemaining=MessageTime;
        for(int32 I=SubtitleIndex+1;I<SubtitleLines.Num();++I) IntroRemaining+=SubtitleLines[I].Duration;
        Tick(IntroRemaining+.01f);
        Check(IntroComplete && !IntroCallPending && Office && !Office->Open && FirstComplaintRequired(),TEXT("first call completion requires the player's ledger entry"));
        OpenComplaintLog(); SelectComplaintKey(EKeys::One); SelectComplaintKey(EKeys::One); TickComplaintLog(10); Escape();
        Check(FirstComplaintWritten() && Office && Office->Open,TEXT("first handwritten line unlocks internal exploration"));
        if(Entrance) { Use(Entrance); Check(!Entrance->Open,TEXT("exterior stays closed after opening call")); }
        // Early arrival: someone slips into 202, then the door shuts. No chase.
        Player->SetActorLocation(FVector(NRLayout::DoorAnchor(1,1).X,NRLayout::CorridorY,410)); Player->GetController()->SetControlRotation(FRotator(0,90,0)); Player->Camera->SetWorldRotation(FRotator(0,90,0));
        Tick(0);
        Check(Witnessed && Door->Open && !Ghost->IsHidden() && !Threat,TEXT("early arrival witnesses a figure entering 202"));
        Tick(2);
        Check(!Door->Open && Ghost->IsHidden() && !Threat && !Dead,TEXT("witnessed figure leaves 202 closed without a chase"));
        Player->SetActorLocation(FVector(725,-153,410)); Player->GetController()->SetControlRotation(FRotator(-18,90,0)); Player->Camera->SetWorldRotation(FRotator(-18,90,0));
        Player->UV=true; Use(Door); Check(Evidence.Contains(TEXT("uv")) && Page.IsEmpty(),TEXT("UV clue available as subtitles"));
        Player->UV=false; Use(Door); Check(Evidence.Contains(TEXT("physical")) && Page.IsEmpty(),TEXT("non-UV fallback clue available as subtitles"));
        Use(Door); Check(Door->Open,TEXT("door opens after inspection"));
        Page.Empty(); StartThreat(); ThreatTime=3; Player->SetActorLocation(Ghost->GetActorLocation()); Tick(0);
        Check(Dead,TEXT("ghost contact kills")); RestoreCheckpoint();
        // End-card fixture; the complete fuse/report path is exercised by NRDemoTest.
        PowerRepaired=true; ReportFiled=true; RoundFiled=true; CCTVReset=true; Evidence.Add(TEXT("sealed_panel")); Evidence.Add(TEXT("service_ledger")); Evidence.Add(TEXT("lost_tag"));
        Page.Empty(); RoomEntered=true; Player->SetActorLocation(NRLayout::OfficePoint(FVector(85,-395,100))); Tick(0);
        Check(Red && PhoneStage==3,TEXT("return reveals writing and final call"));
        Use(Phone);
        Check(!Finished && EndingPending && Page.IsEmpty() && Player->CanMove() && Evidence.Contains(TEXT("final_call")),TEXT("final call speaks before the ending card"));
        Tick(3.1f);
        Check(FinalKnockStage==1 && !Finished,TEXT("final phone knock precedes door knock"));
        const float AudioTime=FinalKnockTime;
        Paused=true; Tick(10); Paused=false;
        Page=TEXT("reading fixture"); Tick(10); Page.Empty();
        Check(FinalKnockTime==AudioTime && FinalKnockStage==1,TEXT("pause and reading suspend final audio sequence"));
        Tick(3.1f);
        Check(FinalKnockStage==2 && !Finished,TEXT("door knock plays before ending card"));
        float Remaining=MessageTime;
        for(int32 I=SubtitleIndex+1;I<SubtitleLines.Num();++I) Remaining+=SubtitleLines[I].Duration;
        Tick(Remaining+.01f); Tick(0);
        Check(Finished && !EndingPending && !Page.IsEmpty() && ModalInput && !Player->CanMove(),TEXT("ending card opens after all final call subtitles"));
        Check(Page.Contains(TEXT("307호 전화를 받았다")),TEXT("answered 307 call is reflected in the ending"));
        // Rule 5 path: leaving the 307 call unanswered ends the shift quietly after five rings.
        Finished=false; Page.Empty(); Evidence.Remove(TEXT("final_call")); AnsweredStage=2; PhoneStage=3; FinalRings=0; RingTimer=0;
        for(int32 I=0;I<7 && !Finished;++I) Tick(6.1f);
        Check(Finished && FinalRings==6 && Evidence.Contains(TEXT("final_call_ignored")) && !Evidence.Contains(TEXT("final_call")) && Page.Contains(TEXT("받지 않았다")),TEXT("unanswered 307 call ends the demo after five rings"));
    }
    UE_LOG(LogTemp,Display,TEXT("NR_SMOKE_COMPLETE failures=%d"),Failures);
    FPlatformMisc::RequestExitWithStatus(false,Failures?1:0);
}
