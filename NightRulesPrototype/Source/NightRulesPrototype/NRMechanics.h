#pragma once
#include <algorithm>

// Pure functions shared by game code and compiler-level tests.
namespace NRMechanics
{
    inline float Drain(float Remaining,float Delta,bool UVPowered)
    {
        return UVPowered ? std::max(0.f,Remaining-std::max(0.f,Delta)) : Remaining;
    }
    inline bool PickupAllowed(bool AlreadyCollected) { return !AlreadyCollected; }
    inline bool WitnessWindow(float Elapsed,float FirstCall,float Duration)
    { return Elapsed>=FirstCall && Elapsed<FirstCall+Duration; }
    inline bool SecondCallAllowed(bool Minseo,bool DreamWake,bool Avoided)
    { return !Minseo && !DreamWake && !Avoided; }
    inline int ShiftClockSeconds(float Elapsed,float FirstCall)
    { return std::max(0,7980+static_cast<int>(std::max(0.f,Elapsed))-static_cast<int>(FirstCall)); }
    // Hangul jongseong: no final consonant and rieul take 로; all others take 으로.
    inline bool NeedsEuro(unsigned Last)
    { return Last>=0xAC00 && Last<=0xD7A3 && (Last-0xAC00)%28!=0 && (Last-0xAC00)%28!=8; }
}
