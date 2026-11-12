"""Import typography artwork and physically lit paper overlays, then shared animated rule materials."""
from pathlib import Path
import runpy, unreal
R=Path(__file__).resolve().parents[1]; A=unreal.AssetToolsHelpers.get_asset_tools();L=unreal.MaterialEditingLibrary
for name in ('T_RulesPage','T_RulesRed','T_RulesReply','T_PredecessorNote','T_ServiceLedgerCover','T_UVGuide'):
 dest='/Game/PrototypeAssets' if name.startswith('T_Rules') else '/Game/PrototypeAssets/StoryProps'
 t=unreal.AssetImportTask();t.filename=str(R/'Art/StoryProps'/(name+'.png'));t.destination_path=dest;t.automated=True;t.replace_existing=True;t.save=True;A.import_asset_tasks([t])
 if not t.imported_object_paths:raise RuntimeError('Story texture failed: '+name)
 tex=unreal.load_asset(dest+'/'+name);tex.set_editor_property('lod_group',unreal.TextureGroup.TEXTUREGROUP_UI);tex.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_EDITOR_ICON);unreal.EditorAssetLibrary.save_loaded_asset(tex)
name='M_StoryPaper';dest='/Game/PrototypeAssets/StoryProps'
m=unreal.load_asset(dest+'/'+name) or A.create_asset(name,dest,unreal.Material,unreal.MaterialFactoryNew());m.set_editor_property('two_sided',True);L.delete_all_material_expressions(m)
t=L.create_material_expression(m,unreal.MaterialExpressionTextureSampleParameter2D);t.set_editor_property('parameter_name','Feed');t.set_editor_property('texture',unreal.load_asset(dest+'/T_PredecessorNote'));L.connect_material_property(t,'RGB',unreal.MaterialProperty.MP_BASE_COLOR)
r=L.create_material_expression(m,unreal.MaterialExpressionConstant);r.set_editor_property('r',.94);L.connect_material_property(r,'',unreal.MaterialProperty.MP_ROUGHNESS)
e=L.create_material_expression(m,unreal.MaterialExpressionMultiply);e.set_editor_property('const_b',.035);L.connect_material_expressions(t,'RGB',e,'A');L.connect_material_property(e,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
L.recompile_material(m);unreal.EditorAssetLibrary.save_loaded_asset(m)
runpy.run_path(str(R/'tools/import_rules_ink.py'),run_name='__main__')
unreal.log('STORY_PROPS_IMPORT_COMPLETE')
