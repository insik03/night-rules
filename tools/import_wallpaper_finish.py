"""Restore existing wallpaper artwork at a stable real-world scale. No new AI assets."""
from pathlib import Path
import unreal
ROOT=Path(__file__).resolve().parents[1]
lib=unreal.MaterialEditingLibrary; assets=unreal.AssetToolsHelpers.get_asset_tools()
dest='/Game/PrototypeAssets/Architecture'
texture=unreal.load_asset('/Game/PrototypeAssets/T_Wallpaper')
if not texture:raise RuntimeError('Existing wallpaper texture missing')
for name,tint in [('M_AM_WallpaperV3',(.70,.66,.59)),('M_AM_CleanWallpaperV3',(.98,.97,.93))]:
    if unreal.load_asset(dest+'/'+name):continue
    mat=assets.create_asset(name,dest,unreal.Material,unreal.MaterialFactoryNew())
    def node(cls):return lib.create_material_expression(mat,cls)
    pos=node(unreal.MaterialExpressionWorldPosition)
    normal=node(unreal.MaterialExpressionVertexNormalWS)
    uv=node(unreal.MaterialExpressionCustom)
    args=[]
    for key in ['Pos','Normal']:
        arg=unreal.CustomInput();arg.set_editor_property('input_name',key);args.append(arg)
    uv.set_editor_property('inputs',args)
    uv.set_editor_property('code','return float2(lerp(Pos.x,Pos.y,abs(Normal.x)),-Pos.z)/100.0;')
    uv.set_editor_property('output_type',unreal.CustomMaterialOutputType.CMOT_FLOAT2)
    lib.connect_material_expressions(pos,'XYZ',uv,'Pos');lib.connect_material_expressions(normal,'',uv,'Normal')
    sample=node(unreal.MaterialExpressionTextureSample);sample.set_editor_property('texture',texture)
    lib.connect_material_expressions(uv,'',sample,'Coordinates')
    color=node(unreal.MaterialExpressionConstant3Vector);color.set_editor_property('constant',unreal.LinearColor(*tint,1))
    mix=node(unreal.MaterialExpressionMultiply)
    lib.connect_material_expressions(sample,'RGB',mix,'A');lib.connect_material_expressions(color,'',mix,'B')
    lib.connect_material_property(mix,'',unreal.MaterialProperty.MP_BASE_COLOR)
    for prop,value in [(unreal.MaterialProperty.MP_ROUGHNESS,.94),(unreal.MaterialProperty.MP_SPECULAR,.15)]:
        scalar=node(unreal.MaterialExpressionConstant);scalar.set_editor_property('r',value)
        lib.connect_material_property(scalar,'',prop)
    lib.recompile_material(mat);unreal.EditorAssetLibrary.save_loaded_asset(mat)
unreal.log('WALLPAPER_FINISH_COMPLETE')
