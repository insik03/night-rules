#include "../NightRulesPrototype/Source/NightRulesPrototype/NRMechanics.h"
#include <cassert>
#include <cstdio>
int main()
{
    using namespace NRMechanics;
    assert(Drain(45,12,false)==45); // normal light must not consume cartridge
    assert(Drain(45,12,true)==33);
    assert(Drain(1,5,true)==0); // never negative
    assert(Drain(0,5,true)==0);
    assert(Drain(5,-1,true)==5);
    assert(!WitnessWindow(44,45,180));
    assert(WitnessWindow(45,45,180));
    assert(WitnessWindow(224.99f,45,180));
    assert(!WitnessWindow(225,45,180));
    assert(PickupAllowed(false)); assert(!PickupAllowed(true));
    for(int Mask=0;Mask<8;++Mask)
        assert(SecondCallAllowed(Mask&1,Mask&2,Mask&4)==(Mask==0));
    assert(ShiftClockSeconds(0,45)==7935);
    assert(ShiftClockSeconds(45,45)==7980);
    assert(ShiftClockSeconds(46,45)==7981);
    assert(ShiftClockSeconds(105,45)==8040);
    assert(ShiftClockSeconds(420,45)<3*3600+14*60); // no scripted jump to 03:14
    assert(!NeedsEuro(U'리')); // 의자 끄는 소리로
    assert(!NeedsEuro(U'가')); // 확인 불가로
    assert(!NeedsEuro(U'물')); // rieul exception
    assert(NeedsEuro(U'음'));
    assert(NeedsEuro(U'림'));
    assert(!NeedsEuro(0));
    std::puts("MECHANICS_OK: cartridge, witness, second-call, shift-clock and Korean particle tests passed");
}
