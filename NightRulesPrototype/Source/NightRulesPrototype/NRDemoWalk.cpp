#include "NRGame.h"
#include "Camera/CameraComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/InputComponent.h"
#include "Engine/GameViewportClient.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "InputKeyEventArgs.h"
#include "TimerManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "HAL/PlatformMisc.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

// A known-route completion test, not a human first-play estimate. No teleports,
// inventory grants, event-clock jumps, state changes, speed changes, or direct Use calls.
void ANRGameMode::DemoWalkTest()
{
    FString Raw; TSharedPtr<FJsonObject> Data;
    if(!FFileHelper::LoadFileToString(Raw,*(FPaths::ProjectContentDir()/TEXT("Data/demo-walk.json"))) ||
       !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Raw),Data))
    { UE_LOG(LogTemp,Error,TEXT("NR_WALK_COMPLETE failures=1 missing route")); FPlatformMisc::RequestExitWithStatus(false,1); return; }
    struct FRun
    {
        TArray<TSharedPtr<FJsonValue>> Steps; int32 Step=0; float Began=0, StepBegan=0, SentAt=-1, ReadUntil=-1;
        bool W=false, Sprint=false; FTimerHandle Timer;
        bool Shots=false; float LastShot=-100;    // -NRWalkShots: screenshots for visual review
    };
    auto Run=MakeShared<FRun>(); Run->Shots=FParse::Param(FCommandLine::Get(),TEXT("NRWalkShots")); Run->Steps=Data->GetArrayField(TEXT("steps")); Run->Began=Run->StepBegan=GetWorld()->GetRealTimeSeconds();
    auto Key=[this](FKey K,EInputEvent E)
    {
        auto* V=GetWorld()->GetGameViewport();
        V->InputKey(FInputKeyEventArgs::CreateSimulated(K,E,1,1,FInputDeviceId::CreateFromInternalId(0),false,V->Viewport));
    };
    Record(TEXT("test"),TEXT("known_route_walk_start"));
    GetWorld()->GetTimerManager().SetTimer(Run->Timer,[this,Run,Key]
    {
        const float Now=GetWorld()->GetRealTimeSeconds();
        auto Shot=[&](const TCHAR* Why)
        {
            if(!Run->Shots) return;
            Run->LastShot=Now; Player->GetController<APlayerController>()->ConsoleCommand(TEXT("Shot SHOWUI"));
            UE_LOG(LogTemp,Display,TEXT("NR_WALK_SHOT step=%d why=%s real=%.1f"),Run->Step,Why,Now-Run->Began);
        };
        if(Now-Run->LastShot>6) Shot(TEXT("periodic"));
        auto Stop=[&]{ if(Run->W) { Key(EKeys::W,IE_Released); Run->W=false; } };
        auto Fail=[&](const FString& Why)
        {
            FHitResult Hit; FCollisionQueryParams Query; Query.bTraceComplex=true; Query.AddIgnoredActor(Player);
            const FVector At=Player->GetActorLocation();
            GetWorld()->SweepSingleByChannel(Hit,At,At+Player->GetActorForwardVector()*100,FQuat::Identity,ECC_Pawn,FCollisionShape::MakeCapsule(28,85),Query);
            const auto* Block=Cast<ANRProp>(Hit.GetActor());
            UE_LOG(LogTemp,Display,TEXT("NR_WALK obstruction=%s impact=%s axis=%.1f canmove=%d"),Block?*Block->Id:*GetNameSafe(Hit.GetActor()),*Hit.ImpactPoint.ToString(),Player->InputComponent->GetAxisValue(TEXT("Forward")),Player->CanMove());
            Stop();Key(EKeys::LeftShift,IE_Released); UE_LOG(LogTemp,Error,TEXT("NR_WALK_COMPLETE failures=1 step=%d real=%.1f at=%s focus=%s reason=%s"),Run->Step,Now-Run->Began,*Player->GetActorLocation().ToString(),Player->Focus?*Player->Focus->Id:TEXT("none"),*Why);
            // Clearing this timer destroys its delegate captures. Keep the handle
            // on the stack and do not read captured state after ClearTimer.
            FTimerHandle CompletedTimer=Run->Timer;
            GetWorld()->GetTimerManager().ClearTimer(CompletedTimer); FPlatformMisc::RequestExitWithStatus(false,1);
        };
        if(Dead) { Fail(TEXT("player died on route")); return; }
        if(Run->Step>=Run->Steps.Num())
        {
            Stop();Key(EKeys::LeftShift,IE_Released); UE_LOG(LogTemp,Display,TEXT("NR_WALK_COMPLETE failures=%d real_seconds=%.2f steps=%d"),Finished?0:1,Now-Run->Began,Run->Step);
            const uint8 ExitStatus=Finished?0:1;
            FTimerHandle CompletedTimer=Run->Timer;
            GetWorld()->GetTimerManager().ClearTimer(CompletedTimer); FPlatformMisc::RequestExitWithStatus(false,ExitStatus); return;
        }
        const auto S=Run->Steps[Run->Step]->AsObject(); const FString Kind=S->GetStringField(TEXT("kind"));
        auto Next=[&]
        {
            if(Kind!=TEXT("move")) Shot(*Kind);
            Stop(); UE_LOG(LogTemp,Display,TEXT("NR_WALK PASS step=%d kind=%s real=%.1f at=%s"),Run->Step,*Kind,Now-Run->Began,*Player->GetActorLocation().ToString());
            ++Run->Step; Run->StepBegan=Now; Run->SentAt=-1; Run->ReadUntil=-1;
        };
        if(Now-Run->StepBegan>100 || Now-Run->Began>1800) { Fail(TEXT("timeout")); return; }
        if(Kind==TEXT("move"))
        {
            // An unsolicited reading panel (for example the blackout notice) can
            // interrupt walking and flush held keys, just as it does for a player.
            if(!Page.IsEmpty())
            {
                Stop();
                if(Run->ReadUntil<0) Run->ReadUntil=Now+FMath::Max(3.f,Page.Len()/8.f);
                if(Now>=Run->ReadUntil) { Key(EKeys::Escape,IE_Pressed); Key(EKeys::Escape,IE_Released); }
                return;
            }
            Run->ReadUntil=-1;
            const auto XYZ=S->GetArrayField(TEXT("at")); const FVector Target(XYZ[0]->AsNumber(),XYZ[1]->AsNumber(),XYZ[2]->AsNumber());
            const FVector Delta=Target-Player->GetActorLocation();
            if(Delta.Size2D()<22 && FMath::Abs(Delta.Z)<45) { Next(); return; }
            Player->GetController()->SetControlRotation(FRotator(0,Delta.Rotation().Yaw,0));
            if(Run->Sprint && !Player->SprintHeld) {Key(EKeys::LeftShift,IE_Released);Key(EKeys::LeftShift,IE_Pressed);}
            if(!Run->W || Player->InputComponent->GetAxisValue(TEXT("Forward"))<.5f) { Key(EKeys::W,IE_Released);Key(EKeys::W,IE_Pressed); Run->W=true; }
            return;
        }
        Stop();
        if(Kind==TEXT("sprint")) {
            Run->Sprint=S->GetBoolField(TEXT("held"));
            Key(EKeys::LeftShift,Run->Sprint?IE_Pressed:IE_Released);Next();return;
        }
        if(Kind==TEXT("complaint_choice"))
        {
            const int32 Stage=S->GetIntegerField(TEXT("step")), Number=S->GetIntegerField(TEXT("key"));
            if(!ComplaintView || Page.IsEmpty()) { Fail(TEXT("complaint card is not open")); return; }
            if(Number<1 || Number>3) { Fail(TEXT("invalid complaint number key")); return; }
            if(Run->SentAt>=0) {
                if(Now-Run->SentAt<.3f) return;
                if((Stage==0 && ComplaintStep!=1) || (Stage==1 && ComplaintWriting==INDEX_NONE && !FirstComplaintWritten())) { Fail(TEXT("number key did not choose complaint option")); return; }
                Next(); return;
            }
            if(ComplaintStep!=Stage) { Fail(TEXT("unexpected complaint selection stage")); return; }
            const FKey NumberKey=Number==1?EKeys::One:Number==2?EKeys::Two:EKeys::Three;
            Key(NumberKey,IE_Pressed); Key(NumberKey,IE_Released); Run->SentAt=Now; return;
        }
        if(Kind==TEXT("investigation_plan")) {
            if(ComplaintLog.Plan==S->GetIntegerField(TEXT("key"))) {Next();return;}
            if(!ComplaintView || !ComplaintPlanning){Fail(TEXT("investigation planning is not open"));return;}
            const int32 Number=S->GetIntegerField(TEXT("key"));
            const FKey NumberKey=Number==1?EKeys::One:Number==2?EKeys::Two:EKeys::Three;
            Key(NumberKey,IE_Pressed);Key(NumberKey,IE_Released);return;
        }
        if(Kind==TEXT("complaint_written"))
        {
            if(Evidence.Contains(TEXT("complaint_written_")+S->GetStringField(TEXT("source")))) Next();
            return;
        }
        if(Kind==TEXT("awakening")) { if(Evidence.Contains(TEXT("dream_wake")) && !DreamActive) Next(); return; }
        if(Kind==TEXT("call")) { if(PhoneStage>AnsweredStage) Next(); return; }
        if(Kind==TEXT("end")) { if(Finished) Next(); return; }
        if(Kind==TEXT("read"))
        {
            if(!Page.IsEmpty())
            {
                if(Run->ReadUntil<0) Run->ReadUntil=Now+FMath::Max(3.f,Page.Len()/8.f);
                if(Now>=Run->ReadUntil) { Key(EKeys::Escape,IE_Pressed); Key(EKeys::Escape,IE_Released); }
                return;
            }
            if(SubtitleLines.IsEmpty()) Next(); return;
        }
        if(Kind==TEXT("use") || Kind==TEXT("open"))
        {
            ANRProp* Target=nullptr; const FString Id=S->GetStringField(TEXT("id"));
            for(auto* P:Props) if(P->Id==Id) { Target=P; break; }
            if(!Target) { Fail(TEXT("missing target ")+Id); return; }
            if(Kind==TEXT("open") && Target->Open) { Next(); return; }
            if(Run->SentAt>=0)
            {
                if(Now-Run->SentAt<.4f) return;
                if(Id.StartsWith(TEXT("cart_")) && !Collected.Contains(Id)) { Fail(TEXT("pickup not collected ")+Id); return; }
                FString EvidenceKey;
                if(S->TryGetStringField(TEXT("evidence"),EvidenceKey) && !Evidence.Contains(EvidenceKey)) { Fail(TEXT("interaction did not produce ")+EvidenceKey); return; }
                Next(); return;
            }
            for(auto* Drawer:Props) if(Drawer->StoredItem==Target && Drawer->Slide<37) return;
            const FBox TargetBounds=Target->Mesh->Bounds.GetBox();
            const FVector Aim=Target->Sliding?FVector(TargetBounds.GetCenter().X,TargetBounds.Min.Y+.5f,TargetBounds.GetCenter().Z):Target->Mesh->Bounds.Origin;
            Player->GetController()->SetControlRotation((Aim-Player->Camera->GetComponentLocation()).Rotation());
            if(Player->Focus==Target && Player->CanMove())
            { Key(EKeys::E,IE_Pressed); Key(EKeys::E,IE_Released); Run->SentAt=Now; }
            return;
        }
        Fail(TEXT("unknown route operation ")+Kind);
    },.1f,true,.5f);
}
