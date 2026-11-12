"""Import silent UV markings and neutral material for a temporary CCTV player proxy."""
from pathlib import Path
import unreal
R=Path(__file__).resolve().parents[1]; A=unreal.AssetToolsHelpers.get_asset_tools(); L=unreal.MaterialEditingLibrary
for name in ('T_UVDoor','T_UVFragment','T_RulesPage','T_RulesRed','T_RulesReply'):
 t=unreal.AssetImportTask();t.filename=str(R/('Art/Generated' if name.startswith('T_Rules') else 'Art/Investigation')/(name+'.png'));t.destination_path='/Game/PrototypeAssets';t.automated=True;t.replace_existing=True;t.save=True
 A.import_asset_tasks([t])
 if not t.imported_object_paths:raise RuntimeError('Missing texture '+name)
m=unreal.load_asset('/Game/PrototypeAssets/M_UVMark') or A.create_asset('M_UVMark','/Game/PrototypeAssets',unreal.Material,unreal.MaterialFactoryNew())
m.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT);m.set_editor_property('blend_mode',unreal.BlendMode.BLEND_MASKED);m.set_editor_property('two_sided',True);L.delete_all_material_expressions(m)
t=L.create_material_expression(m,unreal.MaterialExpressionTextureSampleParameter2D);t.set_editor_property('parameter_name','Feed');t.set_editor_property('texture',unreal.load_asset('/Game/PrototypeAssets/T_UVDoor'))
L.connect_material_property(t,'RGB',unreal.MaterialProperty.MP_EMISSIVE_COLOR);L.connect_material_property(t,'A',unreal.MaterialProperty.MP_OPACITY_MASK);L.recompile_material(m);unreal.EditorAssetLibrary.save_loaded_asset(m)
m=unreal.load_asset('/Game/PrototypeAssets/M_Manager') or A.create_asset('M_Manager','/Game/PrototypeAssets',unreal.Material,unreal.MaterialFactoryNew());L.delete_all_material_expressions(m)
c=L.create_material_expression(m,unreal.MaterialExpressionVectorParameter);c.set_editor_property('parameter_name','Tint');c.set_editor_property('default_value',unreal.LinearColor(.15,.19,.23,1));L.connect_material_property(c,'',unreal.MaterialProperty.MP_BASE_COLOR)
r=L.create_material_expression(m,unreal.MaterialExpressionConstant);r.set_editor_property('r',.85);L.connect_material_property(r,'',unreal.MaterialProperty.MP_ROUGHNESS);L.recompile_material(m);unreal.EditorAssetLibrary.save_loaded_asset(m)
unreal.log('INVESTIGATION_IMPORT_COMPLETE')
