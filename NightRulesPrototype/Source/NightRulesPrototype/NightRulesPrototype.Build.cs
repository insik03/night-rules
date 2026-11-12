using UnrealBuildTool;
public class NightRulesPrototype : ModuleRules
{
    public NightRulesPrototype(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new [] { "Core", "CoreUObject", "Engine", "InputCore", "Slate", "SlateCore", "Json", "AudioMixer", "EngineCameras" });
    }
}
