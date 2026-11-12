#include "NRGame.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/Texture2D.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Engine/World.h"
#include "Engine/GameViewportClient.h"
#include "InputKeyEventArgs.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Text/STextBlock.h"
#include "Styling/CoreStyle.h"
#include "Kismet/KismetRenderingLibrary.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "TimerManager.h"
#include "HAL/PlatformMisc.h"

FString ANRGameMode::CCTVChannelName(int32 Channel) const
{
    static const TCHAR* Names[]={TEXT("관리실"),TEXT("1층 복도"),TEXT("1층 주방"),TEXT("2층 복도"),TEXT("2층 주방"),TEXT("3층 복도"),TEXT("3층 주방"),TEXT("옥상 계단")};
    return Channel>=0 && Channel<CCTVChannelCount?FString::Printf(TEXT("CAM %02d · %s"),Channel+1,Names[Channel]):TEXT("신호 없음");
}

void ANRGameMode::SetupCCTV()
{
    const FVector Locations[]={NRLayout::OfficePoint(FVector(-115,-220,240)),FVector(420,-185,240),FVector(470,-850,240),FVector(420,-185,560),FVector(470,-850,560),FVector(420,-185,880),FVector(470,-850,880),FVector(3840,-845,1185)};
    for(int32 I=0;I<CCTVChannelCount;++I)
    {
        const FRotator Rotation=I==0?(NRLayout::OfficePoint(FVector(25,-380,100))-Locations[I]).Rotation():I==7?(FVector(3690,-380,810)-Locations[I]).Rotation():I%2==0?FRotator(-25,39,0):FRotator(-15,8,0);
        auto* Mount=GetWorld()->SpawnActor<AActor>();
        auto* Capture=NewObject<USceneCaptureComponent2D>(Mount);
        Mount->SetRootComponent(Capture); Mount->AddInstanceComponent(Capture); Capture->RegisterComponent();
        Capture->SetWorldLocation(Locations[I]); Capture->SetWorldRotation(Rotation); Capture->FOVAngle=I==0?100:90;
        Capture->PostProcessSettings.bOverride_AutoExposureBias=true; Capture->PostProcessSettings.AutoExposureBias=1.5f;
        Capture->PostProcessSettings.bOverride_ColorGamma=true; Capture->PostProcessSettings.ColorGamma=FVector4(1.5f,1.5f,1.5f,1.f);
        Capture->PostProcessSettings.bOverride_ColorGain=true; Capture->PostProcessSettings.ColorGain=FVector4(1.5f,1.5f,1.5f,1.f);
        Capture->PostProcessBlendWeight=1.f;
        auto* Target=NewObject<UTextureRenderTarget2D>(this); Target->InitCustomFormat(512,288,PF_B8G8R8A8,false);
        Capture->TextureTarget=Target; Capture->bCaptureEveryFrame=false; Capture->bCaptureOnMovement=false; Capture->CaptureSource=ESceneCaptureSource::SCS_FinalColorLDR;
        CCTVCameras.Add(Capture); CCTVTargets.Add(Target);
        auto* UI=UMaterialInstanceDynamic::Create(LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/PrototypeAssets/M_CCTVUI.M_CCTVUI")),this);
        UI->SetTextureParameterValue(TEXT("Feed"),Target); CCTVUIMaterials.Add(UI);
        CCTVBrushes[I].SetResourceObject(UI); CCTVBrushes[I].ImageSize=FVector2D(280,157.5f);
        auto* Housing=Prop(TEXT("cctvcam"),TEXT(""),Locations[I]+FVector(0,0,5),FVector(1));
        Face(Housing,FVector2D(Rotation.Vector().X,Rotation.Vector().Y));
        if(I==0) {
            // The source mesh includes a rear wall arm. Connect that arm's end plate
            // to the ceiling rather than hanging a second mount above the camera body.
            // Measured in the prepared mesh: rear plate Y=27.68cm, centre Z=4.22cm.
            Housing->AddActorWorldOffset(FVector(0,0,248.f-Housing->Mesh->Bounds.GetBox().Max.Z));
            const FVector Forward=FVector(Rotation.Vector().X,Rotation.Vector().Y,0).GetSafeNormal();
            const FVector Anchor=Housing->GetActorLocation()-Forward*27.68f+FVector(0,0,4.22f);
            for(const auto& Part:{TPair<FVector,FVector>(FVector(Anchor.X,Anchor.Y,(260+Anchor.Z)*.5f),FVector(4,4,260-Anchor.Z)),TPair<FVector,FVector>(FVector(Anchor.X,Anchor.Y,259),FVector(14,14,2))}) {
                auto* Bracket=Prop(TEXT("office_camera_mount"),TEXT(""),Part.Key,Part.Value);
                Bracket->Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
                if(auto* Metal=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/PrototypeAssets/M_Concrete.M_Concrete")))Bracket->Mesh->SetMaterial(0,Metal);
                Capture->HideActorComponents(Bracket);
            }
        }
        Capture->HideActorComponents(Housing);
        auto* Copy=UMaterialInstanceDynamic::Create(LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/PrototypeAssets/M_Display.M_Display")),this);
        Copy->SetTextureParameterValue(TEXT("Feed"),Target); CCTVCopyMaterials.Add(Copy);
    }
    CCTVMonitorMaterials.SetNumZeroed(CCTVMonitorCount);
    for(auto* P:Props) if(P->Id==TEXT("cctv") || P->Id.StartsWith(TEXT("cctv_display_")) || P->Id==TEXT("roster"))
    {
        const bool IsCCTV=P->Id!=TEXT("roster");
        const int32 Monitor=P->Id==TEXT("cctv")?0:FCString::Atoi(*P->Id.RightChop(13));
        if(IsCCTV) P->Caption=FString::Printf(TEXT("CCTV %d · %s"),Monitor+1,Monitor==0?TEXT("관리실"):Monitor==4?TEXT("옥상계단"):*FString::Printf(TEXT("%d층 복도·주방"),Monitor));
        auto* Surface=NewObject<UStaticMeshComponent>(P,TEXT("DisplaySurface")); P->AddInstanceComponent(Surface); Surface->SetupAttachment(P->Mesh);
        Surface->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Plane.Plane")));
        Surface->SetRelativeLocation(IsCCTV?FVector(0,15.1,18):FVector(0,17.7,25.5)); Surface->SetRelativeRotation(FRotator(0,0,90));
        Surface->SetRelativeScale3D(IsCCTV?FVector(.255,.195,1):FVector(.31,.225,1)); Surface->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Surface->SetCastShadow(false); Surface->RegisterComponent();
        auto* Material=UMaterialInstanceDynamic::Create(LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/PrototypeAssets/M_Display.M_Display")),P);
        Surface->SetMaterial(0,Material);
        if(IsCCTV) CCTVMonitorMaterials[Monitor]=Material;
        else Material->SetTextureParameterValue(TEXT("Feed"),LoadObject<UTexture2D>(nullptr,TEXT("/Game/PrototypeAssets/T_ResidentScreen.T_ResidentScreen")));
    }
    MonitorMaterial=CCTVMonitorMaterials[0];
    CCTVFrameTimes.Init(0,120); CCTVHistory.SetNumZeroed(120*CCTVChannelCount);
    RefreshCCTVMonitors();
}

void ANRGameMode::RefreshCCTVMonitors()
{
    for(int32 I=0;I<CCTVMonitorCount;++I)
    {
        const int32 Channel=CCTVChannels[I];
        CCTVMonitorBrushes[I].SetResourceObject(CCTVUIMaterials[Channel]); CCTVMonitorBrushes[I].ImageSize=FVector2D(280,157.5f);
        if(CCTVMonitorMaterials.IsValidIndex(I) && CCTVMonitorMaterials[I])
            CCTVMonitorMaterials[I]->SetTextureParameterValue(TEXT("Feed"),ReplayIndex>=0 && ReplayTargets.IsValidIndex(Channel)?ReplayTargets[Channel]:CCTVTargets[Channel]);
    }
}

void ANRGameMode::SwitchCCTVChannel(int32 Monitor,int32 Direction)
{
    if(Monitor<0 || Monitor>=CCTVMonitorCount || MonitorOff) return;
    const int32 First=CCTVFirstChannel(Monitor),Span=CCTVChannelSpan(Monitor);
    CCTVChannels[Monitor]=First+((CCTVChannels[Monitor]-First+(Direction<0?Span-1:1)+Span)%Span);
    RefreshCCTVMonitors();
    Record(TEXT("cctv_channel"),FString::Printf(TEXT("monitor_%d_cam_%d"),Monitor+1,CCTVChannels[Monitor]+1));
}

TSharedRef<SWidget> ANRGameMode::BuildCCTVPanel()
{
    auto Card=[this](int32 Monitor)->TSharedRef<SWidget>
    {
        return SNew(SBorder).Padding(7).BorderBackgroundColor(FLinearColor(.025f,.04f,.04f,1))
        [SNew(SVerticalBox)
         +SVerticalBox::Slot().AutoHeight()[SNew(SImage).Image(&CCTVMonitorBrushes[Monitor])]
         +SVerticalBox::Slot().AutoHeight().Padding(0,5,0,0)
         [SNew(SHorizontalBox)
          +SHorizontalBox::Slot().AutoWidth()[SNew(SButton).Text(FText::FromString(TEXT("◀"))).IsEnabled_Lambda([this,Monitor]{return !MonitorOff && CCTVChannelSpan(Monitor)>1;}).OnClicked_Lambda([this,Monitor]{SwitchCCTVChannel(Monitor,-1);return FReply::Handled();})]
          +SHorizontalBox::Slot().FillWidth(1).HAlign(HAlign_Center).VAlign(VAlign_Center)[SNew(STextBlock).Font(FCoreStyle::GetDefaultFontStyle("Regular",16)).Text_Lambda([this,Monitor]{return FText::FromString(FString::Printf(TEXT("%d번 · "),Monitor+1)+CCTVChannelName(CCTVChannels[Monitor]));})]
          +SHorizontalBox::Slot().AutoWidth()[SNew(SButton).Text(FText::FromString(TEXT("▶"))).IsEnabled_Lambda([this,Monitor]{return !MonitorOff && CCTVChannelSpan(Monitor)>1;}).OnClicked_Lambda([this,Monitor]{SwitchCCTVChannel(Monitor,1);return FReply::Handled();})]]];
    };
    auto Rows=SNew(SVerticalBox).Visibility_Lambda([this]{return CCTVView?EVisibility::SelfHitTestInvisible:EVisibility::Collapsed;});
    for(int32 Row=0;Row<2;++Row)
    {
        auto Line=SNew(SHorizontalBox);
        const int32 First=Row==0?3:0, Count=Row==0?2:3;
        for(int32 I=First;I<First+Count;++I) Line->AddSlot().AutoWidth().Padding(5,0)[Card(I)];
        Rows->AddSlot().AutoHeight().HAlign(HAlign_Center).Padding(0,0,0,8)[Line];
    }
    return Rows;
}

void ANRGameMode::CCTVStackTest()
{
    struct FRun { int32 Failures=0,Step=0; float Time=0; bool Checked=false; FTimerHandle Timer; };
    auto Run=MakeShared<FRun>();
    auto Check=[Run](bool OK,const FString& Name){UE_LOG(LogTemp,Display,TEXT("NR_CCTV_STACK %s %s"),OK?TEXT("PASS"):TEXT("FAIL"),*Name);if(!OK)++Run->Failures;};
    FirstCall=99999; IntroComplete=true; Page.Empty(); Notice.Empty();
    // Start at the existing 2F landing, then use real walking collision through both new flights.
    const TArray<FVector> Route={FVector(3610,-790,570),FVector(3790,-790,570),FVector(3790,-250,730),FVector(3790,-135,730),FVector(3610,-135,730),FVector(3610,-790,890),FVector(3790,-790,890),FVector(3790,-250,1050),FVector(3790,-135,1050)};
    GetWorld()->GetTimerManager().SetTimer(Run->Timer,[this,Run,Check,Route]
    {
        Run->Time+=.02f;
        if(!Run->Checked)
        {
            Run->Checked=true;
            Check(CCTVCameras.Num()==8 && CCTVMonitorMaterials.Num()==5,TEXT("eight cameras feed five monitors"));
            for(int32 M=0;M<CCTVMonitorCount;++M)Check(CCTVChannels[M]==CCTVFirstChannel(M),TEXT("monitor defaults to its assigned floor"));
            TArray<FBox> Bottom,Top;
            for(auto* P:Props) if(P->Id==TEXT("cctv") || P->Id.StartsWith(TEXT("cctv_display_"))) {
                const FBox B=P->Mesh->Bounds.GetBox(); (B.Min.Z<100?Bottom:Top).Add(B);
                Use(P); Check(CCTVView,TEXT("each physical monitor opens the controls")); Escape();
            }
            Check(Bottom.Num()==3 && Top.Num()==2,TEXT("three lower cabinets and two upper cabinets"));
            bool Clear=true; for(int32 I=0;I<Bottom.Num();++I) for(int32 J=I+1;J<Bottom.Num();++J) Clear &= !Bottom[I].Intersect(Bottom[J]);
            Check(Clear && Top.Num()==2 && !Top[0].Intersect(Top[1]),TEXT("monitor housings do not overlap"));
            ANRProp *Base=nullptr,*Shelf=nullptr,*Desk=nullptr;
            float BracketMin=10000,BracketMax=-10000,OfficeCameraTop=0,OfficeCameraBottom=0;
            for(auto* P:Props) {
                if(P->Id==TEXT("monitor_base"))Base=P;
                if(P->Id==TEXT("monitor_shelf"))Shelf=P;
                if(P->Id==TEXT("desk"))Desk=P;
                if(P->Id==TEXT("office_camera_mount")){BracketMin=FMath::Min(BracketMin,(float)P->Mesh->Bounds.GetBox().Min.Z);BracketMax=FMath::Max(BracketMax,(float)P->Mesh->Bounds.GetBox().Max.Z);}
                if(P->Id==TEXT("cctvcam") && NRLayout::InOffice(P->GetActorLocation())){OfficeCameraTop=P->Mesh->Bounds.GetBox().Max.Z;OfficeCameraBottom=P->Mesh->Bounds.GetBox().Min.Z;}
            }
            bool Supported=Base && Shelf && Desk;
            if(Supported) {
                Supported &= FMath::Abs(Base->Mesh->Bounds.GetBox().Min.Z-Desk->Mesh->Bounds.GetBox().Max.Z-.05f)<.3f;
                for(const auto& B:Bottom)Supported &= FMath::Abs(B.Min.Z-Base->Mesh->Bounds.GetBox().Max.Z-.05f)<.3f;
                for(const auto& B:Top)Supported &= FMath::Abs(B.Min.Z-Shelf->Mesh->Bounds.GetBox().Max.Z-.05f)<.3f;
                for(auto* P:Props)if(P->Id==TEXT("monitor_shelf_leg"))Supported &= FMath::Abs(P->Mesh->Bounds.GetBox().Min.Z-Base->Mesh->Bounds.GetBox().Max.Z)<.3f && FMath::Abs(P->Mesh->Bounds.GetBox().Max.Z-Shelf->Mesh->Bounds.GetBox().Min.Z)<.3f;
            }
            Check(Supported,TEXT("all five monitors and shelf legs contact their physical supports"));
            Check(BracketMin>OfficeCameraBottom && BracketMin<OfficeCameraTop && FMath::Abs(BracketMax-260)<.3f,TEXT("office camera bracket reaches rear arm height and ceiling"));
            TArray<float> MonitorX;MonitorX.SetNumZeroed(5);
            for(auto* P:Props)if(P->Id==TEXT("cctv") || P->Id.StartsWith(TEXT("cctv_display_")))MonitorX[P->Id==TEXT("cctv")?0:FCString::Atoi(*P->Id.RightChop(13))]=P->GetActorLocation().X;
            Check(MonitorX[0]>MonitorX[1] && MonitorX[1]>MonitorX[2] && MonitorX[3]>MonitorX[4],TEXT("physical left-to-right order matches the expanded panel when facing desk"));
            for(int32 I=0;I<CCTVChannelCount;++I) {
                TArray<FColor> Pixels; UKismetRenderingLibrary::ReadRenderTarget(this,CCTVTargets[I],Pixels,false);
                int32 Lit=0; for(const auto& Pixel:Pixels) if(FMath::Max3(Pixel.R,Pixel.G,Pixel.B)>20) ++Lit;
                Check(Lit>500,CCTVChannelName(I)+TEXT(" renders an actual scene"));
            }
            RecordTimer=0; TickDisplays(.51f); ReplayCCTV(1);
            const float Frozen=ReplayTime;
            for(int32 M=0;M<CCTVMonitorCount;++M) {
                const int32 Start=CCTVChannels[M], Other=CCTVChannels[(M+1)%CCTVMonitorCount];
                for(int32 C=0;C<CCTVChannelCount;++C) {
                    SwitchCCTVChannel(M,1);
                    Check(CCTVChannels[M]>=CCTVFirstChannel(M) && CCTVChannels[M]<CCTVFirstChannel(M)+CCTVChannelSpan(M),TEXT("forward switching stays within assigned floor"));
                    Check(CCTVMonitorMaterials[M]->K2_GetTextureParameterValue(TEXT("Feed"))==ReplayTargets[CCTVChannels[M]],TEXT("channel switching preserves the selected replay frame"));
                }
                Check(CCTVChannels[M]==Start && CCTVChannels[(M+1)%CCTVMonitorCount]==Other,TEXT("channel wrap is independent per monitor"));
                SwitchCCTVChannel(M,-1);Check(CCTVChannels[M]>=CCTVFirstChannel(M) && CCTVChannels[M]<CCTVFirstChannel(M)+CCTVChannelSpan(M),TEXT("reverse switching stays within assigned floor"));SwitchCCTVChannel(M,1);
            }
            Check(ReplayTime==Frozen,TEXT("switching channels keeps replay timestamp")); LiveCCTV();
            for(int32 M=0;M<CCTVMonitorCount;++M) Check(CCTVMonitorMaterials[M]->K2_GetTextureParameterValue(TEXT("Feed"))==CCTVTargets[CCTVChannels[M]],TEXT("live mode restores each selected camera"));
            Check(CCTVHistory.Num()==960,TEXT("all channels have bounded recording storage"));
            MonitorOff=true; const int32 Before=CCTVChannels[0]; SwitchCCTVChannel(0,1); Check(CCTVChannels[0]==Before,TEXT("power-off blocks channel switching")); MonitorOff=false;
            for(auto* P:Props) if(P->Id==TEXT("door_arch_roof"))P->SetDoor(true);
            Player->SetActorLocation(FVector(3610,-135,410)); Player->GetCharacterMovement()->StopMovementImmediately();
            auto* Viewport=GetWorld()->GetGameViewport();
            Viewport->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::W,IE_Pressed,1,1,FInputDeviceId::CreateFromInternalId(0),false,Viewport->Viewport));
        }
        const FVector Position=Player->GetActorLocation();
        if(FVector::Dist2D(Position,Route[Run->Step])<25 && FMath::Abs(Position.Z-Route[Run->Step].Z)<40) {
            Check(true,FString::Printf(TEXT("walked upper stair waypoint %d"),Run->Step));
            if(++Run->Step==Route.Num()) {
                UE_LOG(LogTemp,Display,TEXT("NR_CCTV_STACK_COMPLETE failures=%d"),Run->Failures);
                FPlatformMisc::RequestExitWithStatus(false,Run->Failures?1:0); GetWorld()->GetTimerManager().ClearTimer(Run->Timer); return;
            }
        }
        if(Run->Time>75 || Dead) {
            FHitResult Hit; FCollisionQueryParams Query; Query.bTraceComplex=true; Query.AddIgnoredActor(Player);
            FVector To=Route[Run->Step]-Position; To.Z=0;
            GetWorld()->SweepSingleByChannel(Hit,Position,Position+To.GetSafeNormal()*100,FQuat::Identity,ECC_Pawn,FCollisionShape::MakeCapsule(28,85),Query);
            if(auto* Obstacle=Cast<ANRProp>(Hit.GetActor())) UE_LOG(LogTemp,Error,TEXT("NR_CCTV_STACK obstruction=%s at=%s bounds=%s"),*Obstacle->Id,*Obstacle->GetActorLocation().ToString(),*Obstacle->Mesh->Bounds.GetBox().ToString());
            UE_LOG(LogTemp,Error,TEXT("NR_CCTV_STACK_COMPLETE failures=%d stair waypoint=%d at=%s"),Run->Failures+1,Run->Step,*Position.ToString());
            FPlatformMisc::RequestExitWithStatus(false,1); GetWorld()->GetTimerManager().ClearTimer(Run->Timer); return;
        }
        FVector Direction=Route[Run->Step]-Position; Direction.Z=0; Player->GetController()->SetControlRotation(Direction.Rotation());
    },.02f,true,2.f);
}
