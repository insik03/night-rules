#include "NRGame.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Components/AudioComponent.h"
#include "Sound/SoundBase.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/World.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Engine/Texture2D.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Kismet/KismetRenderingLibrary.h"
#include "Misc/ConfigCacheIni.h"
#include "AudioDevice.h"
#include "HAL/PlatformMisc.h"
#include "TimerManager.h"
#include "GameFramework/PlayerController.h"

void ANRGameMode::LoadPreferences()
{
    GConfig->GetFloat(TEXT("NightRules.Preferences"),TEXT("MouseSensitivity"),MouseSensitivity,GGameUserSettingsIni);
    GConfig->GetFloat(TEXT("NightRules.Preferences"),TEXT("MasterVolume"),MasterVolume,GGameUserSettingsIni);
    MouseSensitivity=FMath::Clamp(MouseSensitivity,.2f,3.f); ApplyVolume(MasterVolume);
}
void ANRGameMode::SavePreferences()
{
    GConfig->SetFloat(TEXT("NightRules.Preferences"),TEXT("MouseSensitivity"),MouseSensitivity,GGameUserSettingsIni);
    GConfig->SetFloat(TEXT("NightRules.Preferences"),TEXT("MasterVolume"),MasterVolume,GGameUserSettingsIni);
    GConfig->Flush(false,GGameUserSettingsIni);
}
void ANRGameMode::ApplyVolume(float V)
{
    MasterVolume=FMath::Clamp(V,0.f,1.f);
    if(auto Device=GetWorld()->GetAudioDevice()) Device->SetTransientPrimaryVolume(MasterVolume);
}
void ANRGameMode::TickDisplays(float D)
{
    // M_RulesInk reveals each red pixel once Progress passes its stroke order (T_RulesInkOrder).
    RulesShownRed=Red; RulesShownStage=!Red?0:RuleInk>=1?2:1;
    if(RulesMaterial) RulesMaterial->SetScalarParameterValue(TEXT("Progress"),Red?RuleInk:-1.f);
    if(RulesUIMaterial) RulesUIMaterial->SetScalarParameterValue(TEXT("Progress"),Red?RuleInk:-1.f);
    // The history uses the same elapsed shift time as the complaint log.
    if(MonitorOff || (ReportFiled && !CCTVReset)) return;
    CaptureTime-=D; RecordTimer-=D;
    const bool RecordNow=RecordTimer<=0;
    if(CaptureTime<=0 || RecordNow)
    {
        TSet<int32> Visible; for(int32 Channel:CCTVChannels) Visible.Add(Channel);
        for(int32 I=0;I<CCTVCameras.Num();++I) if(RecordNow || Visible.Contains(I)) CCTVCameras[I]->CaptureScene();
        CaptureTime=(CCTVView || FVector::Dist2D(Player->GetActorLocation(),FVector(0,-300,0))<600)?.2f:.5f;
    }
    if(!RecordNow) return;
    RecordTimer=.5f;
    for(int32 I=0;I<CCTVChannelCount;++I)
    {
        const int32 Slot=HistoryHead*CCTVChannelCount+I;
        if(!CCTVHistory[Slot]) {
            auto* Frame=NewObject<UTextureRenderTarget2D>(this); Frame->InitCustomFormat(256,144,PF_B8G8R8A8,false); CCTVHistory[Slot]=Frame;
        }
        CCTVCopyMaterials[I]->SetTextureParameterValue(TEXT("Feed"),CCTVTargets[I]);
        UKismetRenderingLibrary::DrawMaterialToRenderTarget(this,CCTVHistory[Slot],CCTVCopyMaterials[I]);
    }
    CCTVFrameTimes[HistoryHead]=Elapsed;
    HistoryHead=(HistoryHead+1)%120; HistoryCount=FMath::Min(HistoryCount+1,120);
}
void ANRGameMode::ReplayCCTV(float Position)
{
    if(MonitorOff || HistoryCount==0) return;
    ReplayIndex=FMath::Clamp(FMath::RoundToInt(Position*(HistoryCount-1)),0,HistoryCount-1);
    const int32 Slot=(HistoryHead-HistoryCount+120+ReplayIndex)%120;
    ReplayTime=CCTVFrameTimes[Slot];
    // Copy the selected frame so ongoing recording cannot overwrite the viewed image.
    if(ReplayTargets.IsEmpty()) for(int32 I=0;I<CCTVChannelCount;++I) {
        auto* Target=NewObject<UTextureRenderTarget2D>(this); Target->InitCustomFormat(256,144,PF_B8G8R8A8,false); ReplayTargets.Add(Target);
    }
    for(int32 I=0;I<CCTVChannelCount;++I) {
        CCTVCopyMaterials[I]->SetTextureParameterValue(TEXT("Feed"),CCTVHistory[Slot*CCTVChannelCount+I]);
        UKismetRenderingLibrary::DrawMaterialToRenderTarget(this,ReplayTargets[I],CCTVCopyMaterials[I]);
        CCTVCopyMaterials[I]->SetTextureParameterValue(TEXT("Feed"),CCTVTargets[I]);
        CCTVUIMaterials[I]->SetTextureParameterValue(TEXT("Feed"),ReplayTargets[I]);
    }
    if(CCTVView && ReplayIndex<HistoryCount-1 && Evidence.Contains(TEXT("manager_call")) && !Evidence.Contains(TEXT("log_recording_reviewed"))) {
        Evidence.Add(TEXT("log_recording_reviewed"));
        Record(TEXT("investigation"),TEXT("reviewed_2f_recording"));SaveCheckpoint();
    }
    RefreshCCTVMonitors();
}
void ANRGameMode::LiveCCTV()
{
    ReplayIndex=-1;
    for(int32 I=0;I<CCTVTargets.Num();++I) CCTVUIMaterials[I]->SetTextureParameterValue(TEXT("Feed"),CCTVTargets[I]);
    RefreshCCTVMonitors();
}
FString ANRGameMode::CCTVStatus() const
{
    if(MonitorOff) return TEXT("전원 꺼짐");
    if(ReplayIndex>=0) return TEXT("녹화 확인 · ")+ShiftClock(ReplayTime,true)+FString::Printf(TEXT(" · %.1f초 전  |  아래 막대로 최근 녹화 탐색"),FMath::Max(0.f,Elapsed-ReplayTime));
    if(ReportFiled && !CCTVReset) return TEXT("수신 화면 정지 · ")+ShiftClock(CCTVStoppedAt,true)+TEXT("  |  이전 녹화 확인 가능");
    return TEXT("● 실시간 · ")+ShiftClock(Elapsed,true)+FString::Printf(TEXT("  |  최근 %.0f초 녹화 · 2fps  |  막대를 왼쪽으로 옮기면 되감기"),HistoryCount*.5f);
}
void ANRGameMode::ExperienceTest()
{
    int32 Failures=0;
    auto Check=[&](bool OK,const TCHAR* Name){UE_LOG(LogTemp,Display,TEXT("NR_EXPERIENCE %s %s"),OK?TEXT("PASS"):TEXT("FAIL"),Name); if(!OK) ++Failures;};
    Check(RulesMaterial && RulesMaterial->K2_GetTextureParameterValue(TEXT("Feed")),TEXT("world rules display has a readable texture before interaction"));
    const float OriginalSensitivity=MouseSensitivity,OriginalVolume=MasterVolume;
    MouseSensitivity=1.75f; ApplyVolume(.37f); SavePreferences(); MouseSensitivity=1; MasterVolume=1; LoadPreferences();
    Check(FMath::IsNearlyEqual(MouseSensitivity,1.75f) && FMath::IsNearlyEqual(MasterVolume,.37f),TEXT("settings survive save and reload"));
    Page.Empty(); Paused=false; auto* PC=Player->GetController<APlayerController>(); PC->RotationInput=FRotator::ZeroRotator;
    MouseSensitivity=1; Player->Turn(1); const float Baseline=PC->RotationInput.Yaw; PC->RotationInput=FRotator::ZeroRotator;
    MouseSensitivity=2; Player->Turn(1); Check(Baseline!=0 && FMath::IsNearlyEqual(PC->RotationInput.Yaw,Baseline*2),TEXT("sensitivity scales actual mouse rotation input")); PC->RotationInput=FRotator::ZeroRotator;
    MouseSensitivity=OriginalSensitivity; ApplyVolume(OriginalVolume); SavePreferences();
    // Exercise a short recording, replay, and return to live. Ring bounds are checked without a long wait.
    for(int32 I=0;I<3;++I) TickDisplays(.51f);
    Check(HistoryCount>=3 && CCTVHistory.Num()==120*CCTVChannelCount,TEXT("eight camera history uses a bounded 120-frame ring"));
    ReplayCCTV(0); const float Selected=ReplayTime;
    Check(ReplayIndex==0 && CCTVUIMaterials[0]->K2_GetTextureParameterValue(TEXT("Feed"))==ReplayTargets[0],TEXT("rewind selects a recorded image"));
    TickDisplays(.51f); Check(ReplayTime==Selected,TEXT("selected replay does not drift while recording"));
    LiveCCTV(); Check(ReplayIndex<0 && CCTVUIMaterials[0]->K2_GetTextureParameterValue(TEXT("Feed"))==CCTVTargets[0],TEXT("live button restores actual camera targets"));
    const int32 Before=HistoryCount; MonitorOff=true; TickDisplays(1); Check(HistoryCount==Before,TEXT("power-off does not fabricate new recordings")); MonitorOff=false;
    Red=true; TickDisplays(0); Check(RulesShownRed,TEXT("wall rules receive the red annotation"));
    TArray<FColor> Recorded,Replayed;
    const int32 FirstSlot=(HistoryHead-HistoryCount+120)%120;
    UKismetRenderingLibrary::ReadRenderTarget(this,CCTVHistory[FirstSlot*CCTVChannelCount],Recorded,false);
    ReplayCCTV(0);
    UKismetRenderingLibrary::ReadRenderTarget(this,ReplayTargets[0],Replayed,false);
    bool HasImage=false; for(const FColor& Pixel:Recorded) if(Pixel.R>12 || Pixel.G>12 || Pixel.B>12) { HasImage=true; break; }
    Check(HasImage && Recorded.Num()==256*144,TEXT("recorded camera pixels contain a rendered scene"));
    Check(Recorded==Replayed,TEXT("replay pixels match the selected recorded frame"));
    LiveCCTV();
    const float SavedElapsed=Elapsed;const bool SavedReport=ReportFiled,SavedReset=CCTVReset;
    Elapsed=FirstCall+125;CCTVStoppedAt=Elapsed;ReportFiled=true;CCTVReset=false;
    const FString Frozen=ShiftClock(CCTVStoppedAt,true);
    Check(CCTVStatus().Contains(Frozen) && ComplaintClock()==ShiftClock(Elapsed),TEXT("frozen CCTV and notebook share one shift clock"));
    Elapsed+=1;Check(CCTVStatus().Contains(Frozen) && ShiftClock(Elapsed,true)!=Frozen,TEXT("CCTV image freezes while shift clock advances one second"));
    SaveCheckpoint();Elapsed+=100;CCTVStoppedAt=0;RestoreCheckpoint();
    Check(CCTVStatus().Contains(Frozen),TEXT("checkpoint preserves actual CCTV stop timestamp"));
    Elapsed=SavedElapsed;ReportFiled=SavedReport;CCTVReset=SavedReset;
    IntroCallPending=false; ShowDocument(TEXT("first_call"));
    Check(VoiceLines.Num()==3 && VoiceLines[0] && VoiceLines[1] && VoiceLines[2] && ActiveVoice,TEXT("Korean first call loads three clips and starts playback"));
    bool Fits=VoiceLines.Num()==3; for(int32 I=0;I<VoiceLines.Num();++I) Fits &= VoiceLines[I] && SubtitleLines[I].Duration>=VoiceLines[I]->GetDuration();
    Check(Fits,TEXT("each subtitle lasts at least as long as its voice clip"));
    IntroCallPending=false; Message(TEXT("replacement")); Check(!ActiveVoice && VoiceLines.IsEmpty(),TEXT("replacing dialogue stops old speech"));
    UE_LOG(LogTemp,Display,TEXT("NR_EXPERIENCE_COMPLETE failures=%d"),Failures);
    FPlatformMisc::RequestExitWithStatus(false,Failures?1:0);
}

void ANRGameMode::StopVoice()
{
    if(ActiveVoice) { ActiveVoice->Stop(); ActiveVoice=nullptr; }
    VoiceLines.Reset();
}
void ANRGameMode::PlayVoiceLine()
{
    if(ActiveVoice) { ActiveVoice->Stop(); ActiveVoice=nullptr; }
    if(VoiceLines.IsValidIndex(SubtitleIndex) && VoiceLines[SubtitleIndex])
        ActiveVoice=UGameplayStatics::SpawnSound2D(this,VoiceLines[SubtitleIndex],1.f);
}
void ANRGameMode::StartFirstCallVoice()
{
    StopVoice();
    // Only these three authored lines are voiced; other dialogue remains subtitled.
    if(SubtitleLines.Num()!=3) return;
    for(int32 I=0;I<3;++I) {
        auto* Clip=LoadObject<USoundBase>(nullptr,*FString::Printf(TEXT("/Game/Audio/Voice/minseo_first_%02d.minseo_first_%02d"),I+1,I+1));
        VoiceLines.Add(Clip);
        if(Clip) SubtitleLines[I].Duration=FMath::Max(SubtitleLines[I].Duration,Clip->GetDuration()+.25f);
    }
    MessageTime=SubtitleLines[0].Duration; PlayVoiceLine();
}

void ANRGameMode::StartDocumentVoice(const FString& Key)
{
    FString Json; TSharedPtr<FJsonObject> Root;
    if(!FFileHelper::LoadFileToString(Json,*(FPaths::ProjectContentDir()/TEXT("Data/voices.json"))) || !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Json),Root)) return;
    const TArray<TSharedPtr<FJsonValue>>* Rows=nullptr;
    if(!Root->TryGetArrayField(Key,Rows) || Rows->IsEmpty()) return;
    // Until regenerated audio is imported, never restore obsolete story text from voices.json.
    TArray<FString> Authored; Documents.FindRef(Key).ParseIntoArrayLines(Authored,true);
    const FString Speaker=Authored.IsEmpty()?SubtitleSource:Authored[0].TrimStartAndEnd();
    if(!Authored.IsEmpty()) Authored.RemoveAt(0);
    if(Authored.Num()!=Rows->Num()) return;
    for(int32 I=0;I<Authored.Num();++I) if(Authored[I].TrimStartAndEnd()!=(*Rows)[I]->AsObject()->GetStringField(TEXT("subtitle"))) return;
    StopVoice(); SubtitleLines.Reset(); SubtitleIndex=0;
    for(const auto& Value:*Rows) {
        const auto Row=Value->AsObject(); const FString Name=Row->GetStringField(TEXT("asset"));
        auto* Clip=Name.IsEmpty()?nullptr:LoadObject<USoundBase>(nullptr,*(TEXT("/Game/Audio/Voice/Day1/")+Name+TEXT(".")+Name));
        const FString Text=Row->GetStringField(TEXT("subtitle"));
        VoiceLines.Add(Clip); SubtitleLines.Add({Text,FMath::Max(2.f,Clip?Clip->GetDuration()+.3f:Text.Len()*.09f+1.2f),Text.StartsWith(TEXT("‘")) || Text.StartsWith(TEXT("“"))?Speaker:TEXT("나 · 독백")});
    }
    Notice=SubtitleLines[0].Text; SubtitleSource=SubtitleLines[0].Speaker; MessageTime=SubtitleLines[0].Duration; PlayVoiceLine();
}
