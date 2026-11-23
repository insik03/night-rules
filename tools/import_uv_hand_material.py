from pathlib import Path
import unreal
root=Path(__file__).resolve().parents[1]
a=unreal.AssetToolsHelpers.get_asset_tools(); lib=unreal.MaterialEditingLibrary
name='M_UVHandResidue_v2'; dest='/Game/PrototypeAssets'
m=unreal.load_asset(dest+'/'+name)
if not m:
 m=a.create_asset(name,dest,unreal.Material,unreal.MaterialFactoryNew())
 m.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT)
 m.set_editor_property('blend_mode',unreal.BlendMode.BLEND_MASKED)
 m.set_editor_property('two_sided',True)
 m.set_editor_property('opacity_mask_clip_value',.20)
 tex=lib.create_material_expression(m,unreal.MaterialExpressionTextureSampleParameter2D)
 tex.set_editor_property('parameter_name','Feed');tex.set_editor_property('texture',unreal.load_asset(dest+'/T_ClueHandprint'))
 uv=lib.create_material_expression(m,unreal.MaterialExpressionTextureCoordinate)
 scale=lib.create_material_expression(m,unreal.MaterialExpressionVectorParameter);scale.set_editor_property('parameter_name','UVScale');scale.set_editor_property('default_value',unreal.LinearColor(1,1,0,0))
 offset=lib.create_material_expression(m,unreal.MaterialExpressionVectorParameter);offset.set_editor_property('parameter_name','UVOffset');offset.set_editor_property('default_value',unreal.LinearColor(0,0,0,0))
 mul=lib.create_material_expression(m,unreal.MaterialExpressionMultiply);add=lib.create_material_expression(m,unreal.MaterialExpressionAdd)
 lib.connect_material_expressions(uv,'',mul,'A');lib.connect_material_expressions(scale,'RG',mul,'B')
 lib.connect_material_expressions(mul,'',add,'A');lib.connect_material_expressions(offset,'RG',add,'B');lib.connect_material_expressions(add,'',tex,'Coordinates')
 tint=lib.create_material_expression(m,unreal.MaterialExpressionVectorParameter);tint.set_editor_property('parameter_name','Tint');tint.set_editor_property('default_value',unreal.LinearColor(.12,.65,.35,1))
 emission=lib.create_material_expression(m,unreal.MaterialExpressionMultiply)
 lib.connect_material_expressions(tint,'',emission,'A');lib.connect_material_expressions(tex,'R',emission,'B')
 lib.connect_material_property(emission,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
 lib.connect_material_property(tex,'A',unreal.MaterialProperty.MP_OPACITY_MASK)
 lib.recompile_material(m)
 unreal.EditorAssetLibrary.save_loaded_asset(m)
if not unreal.load_asset(dest+'/T_ClueHandprint'): raise RuntimeError('Handprint texture missing')
unreal.log('UV_HAND_MATERIAL_COMPLETE')
