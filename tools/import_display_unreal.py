"""Create an unlit screen material with a runtime texture parameter."""
from pathlib import Path
import unreal
ROOT=Path(__file__).resolve().parents[1]
assets=unreal.AssetToolsHelpers.get_asset_tools()
task=unreal.AssetImportTask();task.filename=str(ROOT/'Art/Generated/T_ResidentScreen.png')
task.destination_path='/Game/PrototypeAssets';task.automated=True;task.replace_existing=True;task.save=True
assets.import_asset_tasks([task])
if not task.imported_object_paths: raise RuntimeError('Roster screen texture import failed')
texture=unreal.load_asset('/Game/PrototypeAssets/T_ResidentScreen')
mat=unreal.load_asset('/Game/PrototypeAssets/M_Display') or assets.create_asset('M_Display','/Game/PrototypeAssets',unreal.Material,unreal.MaterialFactoryNew())
mat.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT)
mat.set_editor_property('two_sided',True)
lib=unreal.MaterialEditingLibrary;lib.delete_all_material_expressions(mat)
sample=lib.create_material_expression(mat,unreal.MaterialExpressionTextureSampleParameter2D)
sample.set_editor_property('parameter_name','Feed');sample.set_editor_property('texture',texture)
lib.connect_material_property(sample,'RGB',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
lib.recompile_material(mat);unreal.EditorAssetLibrary.save_loaded_asset(mat)
for name in ['T_RulesPage','T_RulesRed','T_RulesReply']:
    t=unreal.AssetImportTask();t.filename=str(ROOT/'Art/Generated'/(name+'.png'));t.destination_path='/Game/PrototypeAssets';t.automated=True;t.replace_existing=True;t.save=True
    assets.import_asset_tasks([t])
    if not t.imported_object_paths: raise RuntimeError('Rules texture import failed')
for name in ['minseo_first_01','minseo_first_02','minseo_first_03']:
    t=unreal.AssetImportTask();t.filename=str(ROOT/'Art/Voice'/(name+'.wav'));t.destination_path='/Game/Audio/Voice';t.automated=True;t.replace_existing=True;t.save=True
    assets.import_asset_tasks([t])
    if not t.imported_object_paths: raise RuntimeError('Voice import failed: '+name)
ui=unreal.load_asset('/Game/PrototypeAssets/M_CCTVUI') or assets.create_asset('M_CCTVUI','/Game/PrototypeAssets',unreal.Material,unreal.MaterialFactoryNew())
ui.set_editor_property('material_domain',unreal.MaterialDomain.MD_UI)
ui.set_editor_property('blend_mode',unreal.BlendMode.BLEND_OPAQUE)
lib.delete_all_material_expressions(ui)
sample=lib.create_material_expression(ui,unreal.MaterialExpressionTextureSampleParameter2D)
sample.set_editor_property('parameter_name','Feed');sample.set_editor_property('texture',texture)
lib.connect_material_property(sample,'RGB',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
lib.recompile_material(ui);unreal.EditorAssetLibrary.save_loaded_asset(ui)
unreal.log('DISPLAY_IMPORT_FINISHED')
