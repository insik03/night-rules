#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/PlayerController.h"
#include "Styling/SlateBrush.h"
#include "NRGame.generated.h"

class UCameraComponent;
class UTexture2D;
class USkeletalMeshComponent;
class UPrimitiveComponent;
class UBlendSpace;
class UAnimSequence;
class USkeletalMesh;
class USpotLightComponent;
class UStaticMeshComponent;
class UTextRenderComponent;
class SWidget;
class STextBlock;
class USceneCaptureComponent2D;
class UTextureRenderTarget2D;
class SScrollBox;
class SButton;
class UPointLightComponent;
class UAudioComponent;
class USoundBase;
class USoundAttenuation;
class UMaterialInterface;
class UMaterialInstanceDynamic;

// Shared floor-plan anchors (cm). Gosiwon rooms (~6 m2) line the north side of a 130 cm corridor.
namespace NRLayout
{
    constexpr float FloorHeight=320, RoomStartX=350, RoomPitch=230, RoomFront=-70, RoomBack=230, CorridorY=-135;
    constexpr int32 RoomsPerFloor=12;
    // 1F rear block: equal 465 x 420 cm rooms, divided at x=-35.
    // Looking inward from the entrance: storage LEFT, office RIGHT.
    constexpr float OfficeShift=270, OfficeShiftY=-280, OfficeDoorX=35, StoreDoorX=-267.5f;
    inline FVector OfficePoint(FVector At) { return At+FVector(OfficeShift,OfficeShiftY,0); }
    inline FVector OfficeWallPoint(FVector At) { return OfficePoint(At)+FVector(0,-140,0); }
    inline bool InOffice(FVector At) { return At.Z<260 && At.Z>=0 && At.X>-35 && At.X<430 && At.Y>-900 && At.Y<-480; }
    inline float StoreX(float PreviousX) { return -70-PreviousX; }
    inline bool InStore(FVector At) { return At.Z<260 && At.Z>=0 && At.X>-500 && At.X<-35 && At.Y>-900 && At.Y<-480; }
    // FBX import keeps X but mirrors Y (measured: desk handles at Blender +Y land on UE -Y),
    // so Blender's -Y front becomes local +Y in Unreal.
    constexpr float FrontSign=-1;
    inline float RoomLeft(int32 Index) { return RoomStartX+Index*RoomPitch; }
    // Floor is 0 for 1xx rooms. DoorAnchor is the doorway centre on the corridor face, at floor level.
    inline FVector DoorAnchor(int32 Floor,int32 Index) { return FVector(RoomLeft(Index)+55,RoomFront,Floor*FloorHeight); }
    inline FVector RoomCenter(int32 Floor,int32 Index) { return FVector(RoomLeft(Index)+115,(RoomFront+RoomBack)/2,Floor*FloorHeight); }
}

UCLASS()
class NIGHTRULESPROTOTYPE_API ANRController : public APlayerController
{
    GENERATED_BODY()
public:
    ANRController();
};

UCLASS()
class NIGHTRULESPROTOTYPE_API ANRProp : public AActor
{
    GENERATED_BODY()
public:
    ANRProp();
    UPROPERTY() UStaticMeshComponent* Mesh;
    UPROPERTY() UTextRenderComponent* Label;
    FString Id, Caption;
    FVector Home;
    bool Sliding=false; float Slide=0;
    UPROPERTY() ANRProp* StoredItem;
    UPROPERTY() TArray<UStaticMeshComponent*> CorePanels;
    float CorePanelAngle=0;
    void SetupCorePanels(); void ApplyCorePanelPose();
    bool Open = false;
    float ClosedYaw = 0, TargetYaw = 0;
    virtual void Tick(float Delta) override;
    void Configure(const FString& Key, const FString& Name, FVector Size);
    void SetDoor(bool Value);
};

UCLASS()
class NIGHTRULESPROTOTYPE_API ANRPlayer : public ACharacter
{
    GENERATED_BODY()
public:
    ANRPlayer();
    virtual void SetupPlayerInputComponent(UInputComponent* Input) override;
    virtual void Tick(float Delta) override;
    UPROPERTY() UCameraComponent* Camera;
    UPROPERTY() USpotLightComponent* Lamp;
    UPROPERTY() UStaticMeshComponent* FlashlightVisual;
    UPROPERTY() ANRProp* Focus;
    bool LightOn = true, UV = false;
    bool SprintHeld=false;
    float UVRemaining = 0;
    float StepTime = 0;
    UPROPERTY() TArray<UPrimitiveComponent*> CCTVBody;
    UPROPERTY() USkeletalMeshComponent* PlayerVisual;
    float BodyCrouch=0;
    UFUNCTION(BlueprintCallable, Category="Prototype")
    static bool ConfigureLocomotion(UBlendSpace* Blend, const TArray<UAnimSequence*>& Clips);
    UFUNCTION(BlueprintCallable, Category="Prototype")
    static bool ConfigurePlayerLODs(USkeletalMesh* PlayerMesh);
    float BodyPhase=0;
    void BuildCCTVBody(); void TickCCTVBody(float Delta);
    int32 Cartridges = 0;
    bool CanMove() const;
    void Forward(float Value); void Right(float Value);
    void Turn(float Value); void Look(float Value);
    void Interact(); void ToggleLight(); void ToggleUV(); void Reload();
    void Journal(); void Escape(); void Restart();
    void SprintStart(); void SprintStop(); void CrouchStart(); void CrouchStop();
};

UCLASS()
class NIGHTRULESPROTOTYPE_API ANRGameMode : public AGameModeBase
{
    GENERATED_BODY()
public:
    ANRGameMode();
    virtual void BeginPlay() override;
    virtual void Tick(float Delta) override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    UPROPERTY() ANRPlayer* Player;
    UPROPERTY() ANRProp* Ghost;
    UPROPERTY() USkeletalMeshComponent* GhostVisual;
    UPROPERTY() ANRProp* UVMarker;
    UPROPERTY() ANRProp* UVWakeMarker;
    UPROPERTY() ANRProp* UVHandMarker;
    void SetupInvestigation(); void TickUV();
    bool UVVisible(ANRProp* Marker, AActor* Surface=nullptr) const;
    FString UVClue() const; bool ReadUVClue();
    void InvestigationTest(); void OfficeCCTVTest(); void ProtagonistTest();
    UPROPERTY() TArray<ANRProp*> Props;
    UPROPERTY() TArray<USceneCaptureComponent2D*> CCTVCameras;
    UPROPERTY() TArray<UTextureRenderTarget2D*> CCTVTargets;
    UPROPERTY() TArray<UPointLightComponent*> InteriorLights;
    UPROPERTY() TArray<UAudioComponent*> AmbientLoops;
    UPROPERTY() USoundAttenuation* LocalAudioAttenuation;
    TArray<float> LightIntensities;
    TArray<ANRProp*> OfficeAssembly;
    void RelocateOffice();
    TMap<UStaticMeshComponent*,TArray<UMaterialInterface*>> FixtureMaterials;
    TSet<FString> ScareEvents;
    bool LastAppliedOut=false, LastChaseDark=false;
    bool PowerOut=false, PowerRepaired=false, HasFuse=false, ReportFiled=false;
    bool MonitorOff=false, CCTVReset=false, RoundFiled=false;
    float MonitorOffAt=0;
    float DemoSeconds=0, FlickerTime=0, AmbientTimer=18;
    void SetupDemo(); void TickDemo(float Delta); void SetPower(bool Out);
    void ApplyLightState(bool Out);
    bool UseDemo(ANRProp* Item); bool DemoReady() const;
    void DemoSound(const FString& Name,FVector Location,float Volume=.5f);
    void DemoTest();
    void DemoWalkTest();
    UPROPERTY() TArray<UMaterialInstanceDynamic*> CCTVUIMaterials;
    static constexpr int32 CCTVChannelCount=8;
    static constexpr int32 CCTVMonitorCount=5;
    FSlateBrush CCTVBrushes[CCTVChannelCount], CCTVMonitorBrushes[CCTVMonitorCount];
    int32 CCTVChannels[CCTVMonitorCount]={0,1,3,5,7};
    UPROPERTY() TArray<UMaterialInstanceDynamic*> CCTVMonitorMaterials;
    void SetupCCTV(); void RefreshCCTVMonitors(); void SwitchCCTVChannel(int32 Monitor,int32 Direction);
    FString CCTVChannelName(int32 Channel) const;
    static int32 CCTVFirstChannel(int32 Monitor) { return Monitor==0?0:Monitor==4?7:Monitor*2-1; }
    static int32 CCTVChannelSpan(int32 Monitor) { return Monitor>0 && Monitor<4?2:1; }
    TSharedRef<SWidget> BuildCCTVPanel();
    void CCTVStackTest();
    float CaptureTime=0;
    float MouseSensitivity=1, MasterVolume=1; bool SettingsOpen=false;
    void LoadPreferences(); void SavePreferences(); void ApplyVolume(float Value);
    UPROPERTY() UMaterialInstanceDynamic* RulesMaterial;
    UPROPERTY() UMaterialInstanceDynamic* RulesUIMaterial;
    UPROPERTY() TMap<FString,UTexture2D*> StoryTextures;
    FSlateBrush StoryDocumentBrush;
    bool PaperView=false;
    void SetupStoryProps(); void StoryPropsTest(); void StoryPreview(const FString& Kind);
    bool RulesShownRed=false; int32 RulesShownStage=-1, AnnotatedRule=2;
    FString RuleDenial, RuleReply; float RuleReplyDelay=0;
    // Red note is written stroke by stroke: 0..ReplyStart = denial, then the reply up to 1.
    float RuleInk=0, RuleScratchTime=0; static constexpr float ReplyStart=.55f;
    FString RuleInkText(bool Reply) const;
    void TickRuleAnnotations(float Delta);
    UPROPERTY() TArray<UTextureRenderTarget2D*> CCTVHistory;
    UPROPERTY() TArray<UMaterialInstanceDynamic*> CCTVCopyMaterials;
    UPROPERTY() UMaterialInstanceDynamic* MonitorMaterial;
    UPROPERTY() TArray<UTextureRenderTarget2D*> ReplayTargets;
    float ReplayTime=0;
    TArray<float> CCTVFrameTimes;
    int32 HistoryHead=0, HistoryCount=0, ReplayIndex=-1;
    float RecordTimer=0;
    float CCTVStoppedAt=0;
    void TickDisplays(float Delta); void ReplayCCTV(float Position); void LiveCCTV();
    FString CCTVStatus() const;
    void ExperienceTest();

    TMap<FString,FString> Documents;
    TSet<FString> Evidence, Collected;
    TSharedPtr<SWidget> Screen;
    TSharedPtr<SScrollBox> DocumentScroll;
    TSharedPtr<SButton> PauseResume;
    bool CCTVView=false, ModalInput=false, RulesView=false;
    float Elapsed=0, FirstCall=45, WitnessWindow=180, SecondCall=420, UVCapacity=45;
    // Player walk/sprint: 220/350 cm/s. Sprint barely gains distance on this pursuer.
    static constexpr float GhostChaseSpeed=430.f;
    static constexpr float GhostRunCycle=19.f/30.f;
    float GhostRouteTime=0, GhostStepTime=0, GhostSpeed=0; FVector GhostDestination;
    UPROPERTY() TArray<USoundBase*> PlayerFootsteps;
    UPROPERTY() TArray<USoundBase*> GhostFootsteps;
    UPROPERTY() UAudioComponent* ChairDragAudio;
    UPROPERTY() UStaticMeshComponent* PursuitChair;
    UPROPERTY() UAnimSequence* ChairRunClip;
    UPROPERTY() UAnimSequence* ChairKillClip;
    int32 LastPlayerFootstep=-1, LastGhostFootstep=-1;
    bool ExecutionActive=false, ExecutionHit=false;
    float ExecutionTime=0;
    FVector ExecutionCameraHome, ChairGripLocal;
    FRotator ExecutionLookHome;
    void SetupPursuitFoley(); void PlayFootstep(bool GhostStep,FVector At,float Strength=1.f);
    void TickPursuitChair(float Delta); void TickExecution(float Delta); void ResetExecution();
    void PursuitPresentationTest();
    // Score and fear presentation (NRScore.cpp). Fear 0..1 follows ghost proximity.
    UPROPERTY() UAudioComponent* MusicNight;
    UPROPERTY() UAudioComponent* MusicBlackout;
    UPROPERTY() UAudioComponent* MusicChase;
    UPROPERTY() UAudioComponent* HeartbeatAudio;
    UPROPERTY() UAudioComponent* GhostBreathAudio;
    UPROPERTY() class UCameraShakeBase* FearShake;
    float Fear=0, FearPulse=0; bool ChaseStung=false, ShriekPlayed=false, ScoreExecution=false, ScoreHit=false, FearLook=false; TSet<int32> DimmedLights;
    // Blackout scare: the caretaker crawls away down the corridor, then looks back (Meshy action 340).
    UPROPERTY() UAnimSequence* CrawlClip;
    float CrawlTime=-1, LaughTimer=0; int32 CrawlLight=-1; bool CrawlChuckled=false, ScoreWasThreat=false;
    void SetupScore(); void TickScore(float Delta); void TickCrawlScare(float Delta); float GhostLurch() const; void ScoreTest(); void CrawlPreview();
    FVector NextGhostWaypoint() const;
    float ThreatTime=0, MessageTime=0, RingTimer=0, KnockTimer=0, WitnessUntil=0;
    int32 PhoneStage=0, AnsweredStage=0, FinalRings=0;
    bool ReadRules=false, Red=false, Dead=false, Finished=false, Paused=false;
    bool Threat=false, EncounterDone=false, Witnessed=false, RoomEntered=false;
    bool ThreatPending=false, PreludeCue=false;
    bool DreamActive=false; float DreamTime=0; int32 DreamBeat=0;
    UPROPERTY() ANRProp* WakeTrace;
    void StartDream(); void TickDream(float Delta);
    void Tick202Choice(); void Choice202Test(); void WithdrawalWalkTest();
    float PreludeTime=0;
    void QueueThreat(bool AfterResident=false); void TickPrelude(float Delta);
    FString Page, Notice;
    struct FSubtitleLine { FString Text; float Duration=0; FString Speaker; };
    TArray<FSubtitleLine> SubtitleLines;
    UPROPERTY() UAudioComponent* ActiveVoice;
    UPROPERTY() TArray<USoundBase*> VoiceLines;
    void StartFirstCallVoice(); void StartDocumentVoice(const FString& Key); void PlayVoiceLine(); void StopVoice();
    void PolishTest();
    FString SubtitleSource;
    int32 SubtitleIndex=0;
    bool EndingPending=false, IntroCallPending=false, IntroComplete=false, ExitUnlocked=false;
    float FinalKnockTime=0;
    uint8 FinalKnockStage=0;
    // Checkpoint is captured at the corridor entrance before danger, not inside a trap.
    struct FCheckpoint
    {
        float Time=0, UV=0; int32 Carts=0, Phone=0, Answered=0;
        bool Rules=false, RedText=false, Witness=false, Room=false, Intro=false;
        bool Out=false, Repaired=false, Fuse=false, Report=false;
        bool Monitor=false, Reset=false, Round=false;
        float MonitorTime=0;
        float CCTVStopTime=0;
        float DemoTime=0;
        TSet<FString> Scares;
        TSet<FString> Found, Pickups;
        TMap<FString,bool> Doors;
        FVector Position; FRotator Rotation;
    } Checkpoint;
    bool HasCheckpoint=false;
    // Six imported residents; world actors own components, weak references never extend lifetimes.
    TMap<int32,TWeakObjectPtr<AActor>> ResidentActors;
    TWeakObjectPtr<ANRProp> ResidentConversationDoor;
    TArray<TWeakObjectPtr<UStaticMeshComponent>> ResidentDoorChain;
    float ResidentConversationRemaining=0;
    void BuildResidentVisuals(); void TickResidentVisuals(float Delta);
    void BuildRecentAssets(); void RecentAssetsTest();
    void BeginResidentConversation(const FString& Key); void EndResidentConversation();
    void BuildWorld(); void BuildArchitecture(); void BuildScreen(); void LoadData();
    void UpdatePointerInput(bool Force=false);
    void PointerInputTest();
    ANRProp* ArchitecturePanel(const TCHAR* Asset,FVector At,FVector Size,float Yaw=0);
    void ArchitectureTest(); void ArchitecturePreview(int32 Floor);
    void Use(ANRProp* Prop); void ShowDocument(const FString& Key,const FString& Extra=FString());
    void Record(const FString& Kind,const FString& Detail);
    void SaveCheckpoint(); void RestoreCheckpoint(); void Die();
    void Sound(const FString& Name,FVector Position);
    void Message(const FString& Text,float Duration=0,const FString& Source=TEXT("안내"),const TArray<FString>* Speakers=nullptr);
    void OpenJournal(); void Escape(); void StartThreat();
    void SmokeTest(); void MapTest();
    void InspectPresentation();
    // DAY 1 ending card; the 307 call may be answered or left ringing (rule 5).
    void EndDemo();
    void PlaceOn(ANRProp* Item, ANRProp* Support, FVector2D XY);
    ANRProp* Prop(const FString& Id,const FString& Name,FVector At,FVector Size);
    void Box(FVector At,FVector Size); void Room(int32 Floor,int32 Index);
    // Yaw so a mesh's front (Blender -Y) points along Dir.
    static void Face(AActor* Actor,FVector2D Dir);
    ANRProp* Door(const FString& Id,const FString& Name,FVector Center,float WallYaw);
    FString StatusText() const; FString PromptText() const;
    FString ObjectiveText() const;
    void FeedbackTest();
    // Complaint log
    struct FComplaintRow
    {
        FString Source, Time, Room, Content;
        TArray<FString> Rooms, Contents;
        bool Written=false, Unauthored=false;
        int32 InkChars=0;
    };
    struct FComplaintState
    {
        TArray<FComplaintRow> Rows;
        TSet<FString> Sources;
        TMap<FString,FString> Reports;
        FString PendingSource, PendingTime;
        FString LedgerLine;
        bool AnomalyReady=false, AnomalySeen=false, Entered=false;
        int32 Plan=0; // 1 testimony, 2 recordings/fixtures, 3 both; saved with the notebook.
    };
    // UHT cannot parse a struct body followed by several declarators.
    FComplaintState ComplaintLog;
    FComplaintState ComplaintCheckpoint;
    bool ComplaintView=false;
    bool ComplaintPlanning=false;
    int32 ComplaintEditing=INDEX_NONE, ComplaintStep=0, ComplaintWriting=INDEX_NONE;
    float ComplaintInkTime=0, ComplaintPenTime=0;
    UPROPERTY() UAudioComponent* ComplaintPen;
    UPROPERTY() USoundBase* ComplaintPenSound;
    void SetupComplaintLog(); void OpenComplaintLog(); void CloseComplaintLog();
    void BeginComplaintDialogue(const FString& Key); void FinishComplaintDialogue();
    void SelectComplaint(int32 Choice); void TickComplaintLog(float Delta);
    void SelectComplaintKey(FKey Key);
    void ArmComplaintAnomaly(bool Entered);
    bool FirstComplaintWritten() const; bool FirstComplaintRequired() const;
    FString ComplaintClock() const; FString ComplaintLogText(bool Choices=false) const;
    FString ShiftClock(float At,bool Seconds=false) const;
    FString ServiceLedgerText();
    FString ComplaintReportText(const FString& Template) const;
    bool IsComplaintReport(const FString& Key) const;
    void ComplaintLogTest();
    void SelectInvestigationPlan(int32 Plan); FString InvestigationPlanName() const;
    bool InvestigationPlanComplete() const; void InvestigationPlanTest();
    // Playable final-night slice. Intermediate nights are explicitly not simulated.
    struct FFinaleState {
        bool Active=false, Contacted=false, LineEnabled=true, KeyHeld=false, ReturnPortKnown=false;
        bool BoxUnlocked=false, LureConnected=false, Tools=false, ExitOpen=false, Sealed=true;
        bool MinseoLocated=false, MinseoRescued=false, MinseoEvacuated=false;
        bool Evacuating=false, ReportSubmitted=false, ChaseSpent=false;
        int32 CheckedFloors=0, EvacuatedFloors=0, SceneBeat=0;
        float EvacTime=0, PursuitTime=0, SceneTime=0;
        FString Outcome;
    };
    FFinaleState Finale;
    FFinaleState FinaleCheckpoint;
    UPROPERTY() TArray<ANRProp*> FinaleProps;
    int32 FinaleConfirm=0; // 1 manager report, 2 leave with unresolved residents
    void SetupFinale(); void StartFinale(); void ConfirmFinale(); void ApplyFinaleWorld();
    bool UseFinale(ANRProp* P); void TickFinale(float Delta); void FinishFinale(const FString& Outcome);
    FString FinaleObjective() const; FString FinaleReport() const; int32 EvacuatedCount() const;
    void FinaleTest(); void FinaleWalkTest(); void FinalePreview(const FString& Name);
};
