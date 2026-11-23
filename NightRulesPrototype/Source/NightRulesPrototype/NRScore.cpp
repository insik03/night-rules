#include "NRGame.h"
#include "NRShakes.h"
#include "Camera/PlayerCameraManager.h"
#include "GameFramework/PlayerController.h"
#include "Camera/CameraComponent.h"
#include "Components/AudioComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Animation/AnimSequence.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"
#include "TimerManager.h"
#include "HAL/PlatformMisc.h"

// Original score from tools/create_score.py, imported by tools/import_score.py.
static USoundBase* ScoreSound(const TCHAR* Name)
{
    return LoadObject<USoundBase>(nullptr,*FString::Printf(TEXT("/Game/Audio/Score/%s.%s"),Name,Name));
}

static UAudioComponent* ScoreLoop(AActor* Owner,const TCHAR* Name,USoundAttenuation* Spatial)
{
    USoundBase* S=ScoreSound(Name); if(!S || !Owner) return nullptr;
    auto* C=NewObject<UAudioComponent>(Owner); C->SetSound(S); C->bAutoActivate=false; C->bAutoDestroy=false;
    if(Spatial) { C->AttenuationSettings=Spatial; C->SetupAttachment(Owner->GetRootComponent()); }
    else C->bAllowSpatialization=false;
    C->RegisterComponent(); C->SetVolumeMultiplier(0); return C;
}

void ANRGameMode::SetupScore()
{
    MusicNight=ScoreLoop(this,TEXT("bgm_night"),nullptr);
    MusicBlackout=ScoreLoop(this,TEXT("bgm_blackout"),nullptr);
    MusicChase=ScoreLoop(this,TEXT("bgm_chase"),nullptr);
    HeartbeatAudio=ScoreLoop(this,TEXT("heartbeat"),nullptr);
    GhostBreathAudio=ScoreLoop(Ghost,TEXT("ghost_breath"),LocalAudioAttenuation);
    CrawlClip=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/PrototypeAssets/GhostMeshy/A_CaretakerCrawl.A_CaretakerCrawl"));
}

float ANRGameMode::GhostLurch() const
{
    // An uneven gait: surge, then drag. Averages 1x so chase timing is unchanged.
    const float T=GetWorld()?GetWorld()->GetTimeSeconds():0.f;
    return 1.f+.3f*FMath::Sin(T*2.f*PI/1.7f);
}

void ANRGameMode::TickScore(float D)
{
    if(!Player || !Ghost) return;
    const bool Exec=ExecutionActive;
    const bool Chasing=Threat && !Ghost->IsHidden();
    auto* PC=Player->GetController<APlayerController>(); APlayerCameraManager* Camera=PC?PC->PlayerCameraManager.Get():nullptr;
    const float Gate=(Finished || (Dead && !Exec))?0.f:Paused?.35f:1.f;
    auto Fade=[D](UAudioComponent* C,float Target,float Rate) {
        if(!C) return;
        const float V=FMath::FInterpConstantTo(C->VolumeMultiplier,Target,D,Rate); C->SetVolumeMultiplier(V);
        if(V>.001f && !C->IsPlaying()) C->Play(); else if(V<=.001f && Target<=0 && C->IsPlaying()) C->Stop();
    };
    // Music bed: night drone, darker bed in the blackout, driving cue in a pursuit. A catch cuts it.
    const float Cut=Exec?6.f:0.f;
    Fade(MusicChase,(Chasing && !Exec?.75f:0.f)*Gate,Cut?Cut:Chasing?2.f:.6f);
    Fade(MusicBlackout,(!Chasing && !Exec && PowerOut?.5f:0.f)*Gate,Cut?Cut:.4f);
    Fade(MusicNight,(!Chasing && !Exec && !PowerOut?.32f:0.f)*Gate,Cut?Cut:.3f);

    float Dist=MAX_flt; if(Chasing || Exec) Dist=FVector::Dist(Player->GetActorLocation(),Ghost->GetActorLocation());
    float Target=Exec?1.f:Chasing?FMath::Max(.25f,FMath::Clamp(1.f-(Dist-90.f)/1500.f,0.f,1.f)):0.f;
    Fear=FMath::FInterpTo(Fear,Target,D,Target>Fear?3.f:.8f); if(Fear<.002f && Target==0) Fear=0;

    // The pursuer is announced once it actually moves, and screams the first time it is close and in view.
    if(!Threat) { ChaseStung=false; ShriekPlayed=false; }
    if(Chasing && !ChaseStung && GhostSpeed>1) { ChaseStung=true; if(auto* S=ScoreSound(TEXT("sting_chase"))) UGameplayStatics::PlaySound2D(this,S,.9f*Gate); if(Camera) Camera->StartCameraShake(UNRJoltShake::StaticClass(),.6f); }
    if(Chasing && !ShriekPlayed && Dist<520) {
        FHitResult Hit; FCollisionQueryParams Q; Q.AddIgnoredActor(Ghost); Q.AddIgnoredActor(Player);
        if(!GetWorld()->LineTraceSingleByChannel(Hit,Player->Camera->GetComponentLocation(),Ghost->GetActorLocation()+FVector(0,0,60),ECC_Visibility,Q)) {
            ShriekPlayed=true; if(auto* S=ScoreSound(TEXT("ghost_shriek"))) UGameplayStatics::PlaySoundAtLocation(this,S,Ghost->GetActorLocation(),Gate,1.f,0,LocalAudioAttenuation);
        }
    }
    if(Exec && !ScoreExecution) if(auto* S=ScoreSound(TEXT("ghost_catch"))) UGameplayStatics::PlaySound2D(this,S,1.f);
    if(ExecutionHit && !ScoreHit) { if(auto* S=ScoreSound(TEXT("tinnitus"))) UGameplayStatics::PlaySound2D(this,S,.8f); if(Camera) Camera->StartCameraShake(UNRJoltShake::StaticClass(),1.6f); }
    ScoreExecution=Exec; ScoreHit=ExecutionHit;

    // It laughs while it runs: a giggle or a low chuckle every few seconds, from its mouth.
    if(Chasing && GhostSpeed>1 && !Paused) {
        LaughTimer-=D;
        if(LaughTimer<=0) {
            if(auto* S=ScoreSound(FMath::RandBool()?TEXT("ghost_chuckle"):TEXT("ghost_laugh")))
                UGameplayStatics::PlaySoundAtLocation(this,S,Ghost->GetActorLocation()+FVector(0,0,70),Gate,FMath::FRandRange(.92f,1.05f),0,LocalAudioAttenuation);
            LaughTimer=FMath::FRandRange(3.2f,5.5f);
        }
    } else if(!Threat) LaughTimer=2.f; // first laugh shortly after the sting
    // Escaped: one more chuckle from behind.
    if(ScoreWasThreat && !Threat && !Dead && !Exec) if(auto* S=ScoreSound(TEXT("ghost_chuckle")))
        UGameplayStatics::PlaySoundAtLocation(this,S,Ghost->GetActorLocation(),.7f*Gate,.9f,0,LocalAudioAttenuation);
    ScoreWasThreat=Threat;
    TickCrawlScare(D);

    // Heartbeat speeds from 80 to 140 bpm as the pursuer closes; silent after the strike.
    const float Pitch=1.f+.75f*Fear;
    Fade(HeartbeatAudio,(Fear>.02f && !ExecutionHit?.25f+.75f*Fear:0.f)*Gate,3.f);
    if(HeartbeatAudio) HeartbeatAudio->SetPitchMultiplier(Pitch);
    Fade(GhostBreathAudio,((Chasing || Exec) && !ExecutionHit?1.f:0.f)*Gate,4.f);
    FearPulse=FMath::Fmod(FearPulse+D*Pitch/.75f,1.f);
    const float Kick=FMath::Exp(-FearPulse*8.f)*Fear;

    // Vision narrows and smears with the heartbeat. Fully neutral when nothing is near.
    auto& PP=Player->Camera->PostProcessSettings; const bool Any=Fear>0;
    PP.bOverride_VignetteIntensity=Any; PP.VignetteIntensity=.4f+1.1f*Fear+.35f*Kick;
    PP.bOverride_FilmGrainIntensity=Any; PP.FilmGrainIntensity=.7f*Fear;
    PP.bOverride_SceneFringeIntensity=Any; PP.SceneFringeIntensity=2.5f*Fear+3.f*Kick;
    PP.bOverride_ColorSaturation=Any; PP.ColorSaturation=FVector4(1,1,1,1.f-.5f*Fear);
    // Handheld tremor (ue-gameplay-cameras: Perlin shake pattern), scaled by fear.
    if(Camera && Fear>.02f && !FearShake) FearShake=Camera->StartCameraShake(UNRFearShake::StaticClass(),Fear);
    if(FearShake) { FearShake->ShakeScale=Fear; if(Fear<=.02f && Camera) { Camera->StopCameraShake(FearShake,false); FearShake=nullptr; } }
    if(Any || FearLook) { Player->Camera->SetFieldOfView(Any?85.f-3.f*Kick:85.f); FearLook=Any; }

    // Lights stutter around the pursuer. Blackouts and the chase strobe keep ownership otherwise.
    if(!PowerOut && !LastChaseDark) {
        const float T=GetWorld()->GetTimeSeconds();
        for(int32 I=0;I<InteriorLights.Num();++I) if(auto* L=InteriorLights[I]) {
            const bool Near=Chasing && FVector::DistSquared(L->GetComponentLocation(),Ghost->GetActorLocation())<FMath::Square(420.f);
            const bool Dim=Near && FMath::PerlinNoise1D(T*11.f+I*3.7f)<-.1f;
            // Only restore what this pass dimmed; other systems may own a light's level.
            if(Dim) { L->SetIntensity(LightIntensities[I]*.12f); DimmedLights.Add(I); }
            else if(DimmedLights.Remove(I)) L->SetIntensity(LightIntensities[I]);
        }
    }
}

void ANRGameMode::TickCrawlScare(float D)
{
    if(!GhostVisual || !CrawlClip) return;
    const FVector At=Player->GetActorLocation();
    auto Restore=[this]{
        Ghost->SetActorHiddenInGame(true);
        GhostVisual->PlayAnimation(LoadObject<UAnimSequence>(nullptr,TEXT("/Game/PrototypeAssets/GhostMeshy/A_CaretakerWalk.A_CaretakerWalk")),true); GhostVisual->SetPlayRate(.8f);
    };
    if(CrawlTime<0) {
        // Once per night, in the blackout, ahead of where the player is looking down a corridor.
        if(!PowerOut || Threat || ThreatPending || DreamActive || Dead || Paused || !Page.IsEmpty() || !Ghost->IsHidden() || ScareEvents.Contains(TEXT("blackout_crawl"))) return;
        const FVector Fwd=Player->Camera->GetForwardVector();
        if(FMath::Abs(At.Y-NRLayout::CorridorY)>110 || FMath::Abs(Fwd.X)<.8f) return;
        const float Dir=FMath::Sign(Fwd.X);
        const FVector Spawn(At.X+Dir*650.f,NRLayout::CorridorY,At.Z), Far=Spawn+FVector(Dir*420.f,0,0);
        FHitResult Hit; FCollisionQueryParams Q; Q.AddIgnoredActor(Ghost); Q.AddIgnoredActor(Player);
        // Clear sightline over the whole 3.7 m crawl, and floor under both ends (not a stairwell).
        if(GetWorld()->LineTraceSingleByChannel(Hit,Player->Camera->GetComponentLocation(),Far,ECC_Visibility,Q)) return;
        for(const FVector& P:{Spawn,Far}) if(!GetWorld()->LineTraceSingleByChannel(Hit,P,P-FVector(0,0,160),ECC_Visibility,Q)) return;
        ScareEvents.Add(TEXT("blackout_crawl")); Record(TEXT("scare"),TEXT("blackout_crawl"));
        CrawlTime=0; CrawlChuckled=false;
        Ghost->SetActorLocation(Spawn); Ghost->SetActorRotation(FRotator(0,Dir>0?0.f:180.f,0)); Ghost->SetActorHiddenInGame(false);
        GhostVisual->PlayAnimation(CrawlClip,false); GhostVisual->SetPlayRate(1);
        // A dying tube over the crawl is the only light: it sputters on and off above it.
        CrawlLight=-1; float Best=MAX_flt; const FVector Mid=(Spawn+Far)*.5f;
        for(int32 I=0;I<InteriorLights.Num();++I) if(InteriorLights[I]) {
            const FVector L=InteriorLights[I]->GetComponentLocation(); const float Dz=L.Z-At.Z;
            if(Dz>0 && Dz<300 && FVector::Dist2D(L,Mid)<Best) { Best=FVector::Dist2D(L,Mid); CrawlLight=I; }
        }
        return;
    }
    if(Paused || (!Page.IsEmpty() && !CCTVView)) return;
    CrawlTime+=D;
    if(InteriorLights.IsValidIndex(CrawlLight) && InteriorLights[CrawlLight]) {
        const bool On=FMath::PerlinNoise1D(CrawlTime*7.f)>-.05f || FMath::Fmod(CrawlTime,1.3f)<.08f;
        InteriorLights[CrawlLight]->SetIntensity(LightIntensities[CrawlLight]*(On?1.f:.12f));
    }    // Around frame 55 of 166 its head turns back over the shoulder.
    if(!CrawlChuckled && CrawlTime>=2.3f) {
        CrawlChuckled=true;
        if(auto* S=ScoreSound(TEXT("ghost_chuckle"))) UGameplayStatics::PlaySoundAtLocation(this,S,GhostVisual->GetBoneLocation(TEXT("Head")),.8f,.85f,0,LocalAudioAttenuation);
    }
    const bool Close=FVector::Dist2D(At,GhostVisual->GetBoneLocation(TEXT("Hips")))<300;
    if(CrawlTime>=CrawlClip->GetPlayLength() || Close || Threat || Dead || !PowerOut) {
        if(InteriorLights.IsValidIndex(CrawlLight) && InteriorLights[CrawlLight]) InteriorLights[CrawlLight]->SetIntensity(PowerOut?0.f:LightIntensities[CrawlLight]);
        CrawlTime=-1; CrawlLight=-1; Restore(); Record(TEXT("scare"),Close?TEXT("blackout_crawl_vanished"):TEXT("blackout_crawl_done"));
    }
}

void ANRGameMode::ScoreTest()
{
    int32 Failures=0;
    auto Check=[&](bool OK,const TCHAR* What){if(!OK)++Failures;UE_LOG(LogTemp,Display,TEXT("NR_SCORE %s %s"),OK?TEXT("PASS"):TEXT("FAIL"),What);};
    for(const TCHAR* N:{TEXT("bgm_night"),TEXT("bgm_blackout"),TEXT("bgm_chase"),TEXT("sting_chase"),TEXT("heartbeat"),TEXT("ghost_breath"),TEXT("ghost_shriek"),TEXT("ghost_catch"),TEXT("ghost_laugh"),TEXT("ghost_chuckle"),TEXT("tinnitus")}) {
        USoundBase* S=ScoreSound(N); Check(S && S->GetDuration()>1.f,N);
    }
    Check(MusicNight && MusicBlackout && MusicChase && HeartbeatAudio && GhostBreathAudio,TEXT("score components created"));
    FirstCall=99999; IntroComplete=true; Page.Empty(); StopVoice(); SubtitleLines.Reset(); Notice.Empty();
    auto Run=[&](float Seconds){for(float T=0;T<Seconds;T+=.05f)TickScore(.05f);};
    Run(5); Check(MusicNight->IsPlaying() && MusicNight->VolumeMultiplier>.3f && !MusicChase->IsPlaying() && Fear==0,TEXT("calm night plays the night bed only"));
    Check(!Player->Camera->PostProcessSettings.bOverride_VignetteIntensity,TEXT("calm view keeps default post-processing"));
    PowerOut=true; Run(5); Check(MusicBlackout->VolumeMultiplier>.45f && !MusicNight->IsPlaying(),TEXT("blackout crossfades to the darker bed"));
    PowerOut=false;
    Player->SetActorLocation(FVector(900,NRLayout::CorridorY,410)); StartThreat(); Ghost->SetActorLocation(FVector(2300,NRLayout::CorridorY,410));
    GhostSpeed=100; Run(2); Check(ChaseStung && MusicChase->VolumeMultiplier>.7f && HeartbeatAudio->IsPlaying() && GhostBreathAudio->IsPlaying(),TEXT("pursuit brings sting, chase cue, heartbeat and breath"));
    const float FarFear=Fear, FarPitch=HeartbeatAudio->PitchMultiplier;
    Ghost->SetActorLocation(Player->GetActorLocation()+FVector(300,0,0)); Run(2);
    Check(Fear>FarFear+.3f && HeartbeatAudio->PitchMultiplier>FarPitch && ShriekPlayed,TEXT("closing in raises fear, heart rate and the scream"));
    Check(Player->Camera->PostProcessSettings.bOverride_VignetteIntensity && Player->Camera->PostProcessSettings.VignetteIntensity>.9f && FearShake && FearShake->ShakeScale>.5f,TEXT("fear narrows and shakes the view"));
    Check(GhostLurch()>.69f && GhostLurch()<1.31f,TEXT("lurching gait stays within 0.7x..1.3x"));
    Threat=false; Ghost->SetActorHiddenInGame(true); Run(8);
    Check(Fear==0 && !MusicChase->IsPlaying() && !HeartbeatAudio->IsPlaying() && !Player->Camera->PostProcessSettings.bOverride_VignetteIntensity && FMath::IsNearlyEqual(Player->Camera->FieldOfView,85.f) && !FearShake,TEXT("escape restores calm audio and view"));
    Check(DimmedLights.IsEmpty(),TEXT("stuttering lights recover after the pursuit"));
    // Blackout crawl: appears ahead in the corridor, chuckles when it looks back, then is gone.
    Check(CrawlClip && CrawlClip->GetPlayLength()>5,TEXT("Meshy crawl clip loaded"));
    PowerOut=true; Player->SetActorLocation(FVector(500,NRLayout::CorridorY,410)); Player->GetController()->SetControlRotation(FRotator(0,0,0));
    ScareEvents.Remove(TEXT("blackout_crawl")); Run(.2f);
    Check(CrawlTime>=0 && !Ghost->IsHidden() && Ghost->GetActorLocation().X>1000 && CrawlLight>=0,TEXT("crawler appears ahead down the dark corridor"));
    Run(3); Check(CrawlChuckled,TEXT("it chuckles as it looks back"));
    Run(5); Check(CrawlTime<0 && Ghost->IsHidden() && ScareEvents.Contains(TEXT("blackout_crawl")) && CrawlLight<0,TEXT("crawler vanishes and never repeats"));
    Run(2); Check(CrawlTime<0 && Ghost->IsHidden(),TEXT("crawl scare is once per night"));
    PowerOut=false;    UE_LOG(LogTemp,Display,TEXT("NR_SCORE_COMPLETE failures=%d"),Failures); FPlatformMisc::RequestExitWithStatus(false,Failures?1:0);
}

void ANRGameMode::CrawlPreview()
{
    // Real game render of the blackout crawl: three shots, then exit.
    FirstCall=99999; IntroComplete=true; Page.Empty(); StopVoice(); SubtitleLines.Reset(); Notice.Empty();
    SetPower(true); Player->SetActorLocation(FVector(500,NRLayout::CorridorY,410)); Player->GetController()->SetControlRotation(FRotator(-4,0,0));
    Player->DisableInput(Player->GetController<APlayerController>());
    Player->GetController()->SetIgnoreLookInput(true);Player->GetController()->SetIgnoreMoveInput(true);
    for(float At:{1.f,2.6f,4.6f}) { FTimerHandle H; GetWorld()->GetTimerManager().SetTimer(H,[this]{Player->GetController<APlayerController>()->ConsoleCommand(TEXT("Shot SHOWUI"));},At,false); }
    FTimerHandle End; GetWorld()->GetTimerManager().SetTimer(End,[this]{UE_LOG(LogTemp,Display,TEXT("NR_CRAWL_PREVIEW_COMPLETE seen=%d"),ScareEvents.Contains(TEXT("blackout_crawl")));FPlatformMisc::RequestExit(false);},8.f,false);
}