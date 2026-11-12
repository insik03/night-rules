using UnrealBuildTool;
using System.Collections.Generic;
public class NightRulesPrototypeEditorTarget : TargetRules
{
    public NightRulesPrototypeEditorTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Editor;
        DefaultBuildSettings = BuildSettingsVersion.Latest;
        IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
        ExtraModuleNames.Add("NightRulesPrototype");
    }
}
