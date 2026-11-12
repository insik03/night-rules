using UnrealBuildTool;
using System.Collections.Generic;
public class NightRulesPrototypeTarget : TargetRules
{
    public NightRulesPrototypeTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Game;
        DefaultBuildSettings = BuildSettingsVersion.Latest;
        IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
        ExtraModuleNames.Add("NightRulesPrototype");
    }
}
