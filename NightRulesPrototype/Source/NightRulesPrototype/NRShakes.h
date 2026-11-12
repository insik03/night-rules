#pragma once
#include "CoreMinimal.h"
#include "Camera/CameraShakeBase.h"
#include "Shakes/PerlinNoiseCameraShakePattern.h"
#include "NRShakes.generated.h"

inline FPerlinNoiseShaker NRShaker(float Amplitude,float Frequency){FPerlinNoiseShaker S;S.Amplitude=Amplitude;S.Frequency=Frequency;return S;}

// Handheld tremor while something is close. Infinite; NRScore scales it by Fear each frame.
UCLASS()
class UNRFearShake : public UCameraShakeBase
{
    GENERATED_BODY()
public:
    UNRFearShake(const FObjectInitializer& Init) : Super(Init)
    {
        bSingleInstance=true;
        auto* P=Init.CreateDefaultSubobject<UPerlinNoiseCameraShakePattern>(this,TEXT("RootShakePattern")); SetRootShakePattern(P);
        P->Duration=0; P->BlendInTime=.4f; P->BlendOutTime=.6f;
        P->LocationAmplitudeMultiplier=.6f; P->X=NRShaker(.4f,2.f); P->Y=NRShaker(.6f,2.4f); P->Z=NRShaker(.8f,3.f);
        P->Pitch=NRShaker(.55f,3.2f); P->Yaw=NRShaker(.45f,2.6f); P->Roll=NRShaker(.35f,1.8f); P->FOV=NRShaker(0,0);
    }
};

// A short jolt: the pursuer appearing, or the strike.
UCLASS()
class UNRJoltShake : public UCameraShakeBase
{
    GENERATED_BODY()
public:
    UNRJoltShake(const FObjectInitializer& Init) : Super(Init)
    {
        auto* P=Init.CreateDefaultSubobject<UPerlinNoiseCameraShakePattern>(this,TEXT("RootShakePattern")); SetRootShakePattern(P);
        P->Duration=.45f; P->BlendInTime=.02f; P->BlendOutTime=.3f;
        P->X=NRShaker(1.f,18.f); P->Y=NRShaker(1.5f,22.f); P->Z=NRShaker(2.f,25.f);
        P->Pitch=NRShaker(2.2f,20.f); P->Yaw=NRShaker(1.4f,17.f); P->Roll=NRShaker(1.8f,14.f); P->FOV=NRShaker(0,0);
    }
};
