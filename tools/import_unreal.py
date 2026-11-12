"""Run via UnrealEditor -ExecutePythonScript=<absolute path> after C++ build.
Import generated FBX/WAV and create a persistent map; runtime builds its greybox.
"""
import unreal
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT.parent/'Art'/'Generated'
tasks=[]
for path in sorted(OUT.glob('*')):
    if path.suffix.lower() not in ['.fbx','.wav']: continue
    task=unreal.AssetImportTask()
    task.filename=str(path)
    task.destination_path='/Game/Audio' if path.suffix=='.wav' else '/Game/PrototypeAssets'
    task.automated=True; task.replace_existing=True; task.save=True
    if path.suffix=='.fbx':
        opts=unreal.FbxImportUI()
        opts.import_mesh=True; opts.import_as_skeletal=False
        opts.import_materials=True; opts.import_textures=False; opts.import_animations=False
        opts.static_mesh_import_data.combine_meshes=True
        opts.static_mesh_import_data.auto_generate_collision=True
        task.options=opts
    tasks.append(task)
if len(tasks)<9: raise RuntimeError('Run create_audio.py and create_assets.py first; expected 6 meshes and 3 sounds.')
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
for task in tasks:
    if not task.imported_object_paths: raise RuntimeError('Import failed: '+task.filename)
    if task.filename.endswith('.wav'):
        asset=unreal.load_asset(task.imported_object_paths[0])
        asset.set_editor_property('attenuation_settings',None)
        unreal.EditorAssetLibrary.save_loaded_asset(asset)
unreal.EditorAssetLibrary.save_directory('/Game',only_if_is_dirty=True,recursive=True)
unreal.log('Haedam asset import completed. Play /Engine/Maps/Entry to run DAY 1.')

# AI-generated albedo textures; material graphs use world-space projection.
tex_tasks=[]
for path in sorted((ROOT.parent/'Art'/'Textures').glob('*.png')):
    t=unreal.AssetImportTask();t.filename=str(path);t.destination_path='/Game/PrototypeAssets';t.automated=True;t.replace_existing=True;t.save=True;tex_tasks.append(t)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tex_tasks)
lib=unreal.MaterialEditingLibrary
assets=unreal.AssetToolsHelpers.get_asset_tools()
for name,texture_name,axes in [('M_Wallpaper','T_Wallpaper','wall'),('M_Linoleum','T_Linoleum','floor')]:
    path='/Game/PrototypeAssets/'+name
    m=unreal.load_asset(path)
    if not m:m=assets.create_asset(name,'/Game/PrototypeAssets',unreal.Material,unreal.MaterialFactoryNew())
    lib.delete_all_material_expressions(m)
    pos=lib.create_material_expression(m,unreal.MaterialExpressionWorldPosition)
    if axes=='floor':
        mask=lib.create_material_expression(m,unreal.MaterialExpressionComponentMask);mask.set_editor_property('r',True);mask.set_editor_property('g',True)
    else:
        # X/Z projection on front walls; Y/Z on side walls selected by normal.
        normal=lib.create_material_expression(m,unreal.MaterialExpressionVertexNormalWS)
        nx=lib.create_material_expression(m,unreal.MaterialExpressionComponentMask);nx.set_editor_property('r',True)
        lib.connect_material_expressions(normal,'',nx,'Input')
        ab=lib.create_material_expression(m,unreal.MaterialExpressionAbs);lib.connect_material_expressions(nx,'',ab,'Input')
        xz=lib.create_material_expression(m,unreal.MaterialExpressionComponentMask);xz.set_editor_property('r',True);xz.set_editor_property('b',True);xz.set_editor_property('g',False)
        yz=lib.create_material_expression(m,unreal.MaterialExpressionComponentMask);yz.set_editor_property('g',True);yz.set_editor_property('b',True);yz.set_editor_property('r',False)
        lib.connect_material_expressions(pos,'',xz,'Input');lib.connect_material_expressions(pos,'',yz,'Input')
        mask=lib.create_material_expression(m,unreal.MaterialExpressionLinearInterpolate)
        lib.connect_material_expressions(xz,'',mask,'A');lib.connect_material_expressions(yz,'',mask,'B');lib.connect_material_expressions(ab,'',mask,'Alpha')
    if axes=='floor':lib.connect_material_expressions(pos,'',mask,'Input')
    scale=lib.create_material_expression(m,unreal.MaterialExpressionMultiply);scale.set_editor_property('const_b',.01)
    lib.connect_material_expressions(mask,'',scale,'A')
    sample=lib.create_material_expression(m,unreal.MaterialExpressionTextureSample);sample.set_editor_property('texture',unreal.load_asset('/Game/PrototypeAssets/'+texture_name))
    lib.connect_material_expressions(scale,'',sample,'Coordinates');lib.connect_material_property(sample,'RGB',unreal.MaterialProperty.MP_BASE_COLOR)
    rough=lib.create_material_expression(m,unreal.MaterialExpressionConstant);rough.set_editor_property('r',.85);lib.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS)
    lib.recompile_material(m);unreal.EditorAssetLibrary.save_loaded_asset(m)
unreal.log('HAEDAM_VISUAL_MATERIALS_COMPLETE')
# Neutral painted ceiling, kept distinct from the vinyl floor.
m=unreal.load_asset('/Game/PrototypeAssets/M_Ceiling')
if not m:m=assets.create_asset('M_Ceiling','/Game/PrototypeAssets',unreal.Material,unreal.MaterialFactoryNew())
lib.delete_all_material_expressions(m)
c=lib.create_material_expression(m,unreal.MaterialExpressionConstant3Vector);c.set_editor_property('constant',unreal.LinearColor(.42,.43,.39,1))
lib.connect_material_property(c,'',unreal.MaterialProperty.MP_BASE_COLOR)
r=lib.create_material_expression(m,unreal.MaterialExpressionConstant);r.set_editor_property('r',.95);lib.connect_material_property(r,'',unreal.MaterialProperty.MP_ROUGHNESS)
lib.recompile_material(m);unreal.EditorAssetLibrary.save_loaded_asset(m)
# Full-height office glazing; visibly transparent, still physically solid.
m=unreal.load_asset('/Game/PrototypeAssets/M_Glass')
if not m:m=assets.create_asset('M_Glass','/Game/PrototypeAssets',unreal.Material,unreal.MaterialFactoryNew())
lib.delete_all_material_expressions(m);m.set_editor_property('blend_mode',unreal.BlendMode.BLEND_TRANSLUCENT);m.set_editor_property('two_sided',True)
c=lib.create_material_expression(m,unreal.MaterialExpressionConstant3Vector);c.set_editor_property('constant',unreal.LinearColor(.12,.2,.18,1));lib.connect_material_property(c,'',unreal.MaterialProperty.MP_BASE_COLOR)
o=lib.create_material_expression(m,unreal.MaterialExpressionConstant);o.set_editor_property('r',.12);lib.connect_material_property(o,'',unreal.MaterialProperty.MP_OPACITY)
lib.recompile_material(m);unreal.EditorAssetLibrary.save_loaded_asset(m)
# Exterior material palette, procedural materials without external textures.
for name,color,rough,emission in [('M_Asphalt',(.025,.032,.035),.45,0),('M_Concrete',(.18,.19,.18),.9,0),('M_NightSky',(.004,.007,.018),1,1),('M_LitWindow',(.25,.21,.12),.7,2)]:
    m=unreal.load_asset('/Game/PrototypeAssets/'+name)
    if not m:m=assets.create_asset(name,'/Game/PrototypeAssets',unreal.Material,unreal.MaterialFactoryNew())
    lib.delete_all_material_expressions(m);m.set_editor_property('two_sided',True)
    c=lib.create_material_expression(m,unreal.MaterialExpressionConstant3Vector);c.set_editor_property('constant',unreal.LinearColor(*color,1));lib.connect_material_property(c,'',unreal.MaterialProperty.MP_BASE_COLOR)
    r=lib.create_material_expression(m,unreal.MaterialExpressionConstant);r.set_editor_property('r',rough);lib.connect_material_property(r,'',unreal.MaterialProperty.MP_ROUGHNESS)
    if emission:
        mul=lib.create_material_expression(m,unreal.MaterialExpressionMultiply);mul.set_editor_property('const_b',emission);lib.connect_material_expressions(c,'',mul,'A');lib.connect_material_property(mul,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    lib.recompile_material(m);unreal.EditorAssetLibrary.save_loaded_asset(m)
mesh=unreal.load_asset('/Game/PrototypeAssets/SM_EntranceDoor')
if not mesh:raise RuntimeError('Entrance door mesh missing')
for index,slot in enumerate(mesh.get_editor_property('static_materials')):
    if 'Outdoor_glass' in slot.material_interface.get_name():
        mesh.set_material(index,unreal.load_asset('/Game/PrototypeAssets/M_Glass'))
unreal.EditorAssetLibrary.save_loaded_asset(mesh)
unreal.log('HAEDAM_IMPORT_FINISHED')
