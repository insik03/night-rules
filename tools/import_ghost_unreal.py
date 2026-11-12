"""Import the locally authored ghost, its projected textures and walking loop."""
import unreal
from pathlib import Path
R=Path(__file__).resolve().parents[1]; DEST='/Game/PrototypeAssets/Ghost'
assets=unreal.AssetToolsHelpers.get_asset_tools()
t=unreal.AssetImportTask(); t.filename=str(R/'Art/Ghost/SK_ErasedGhost.fbx'); t.destination_path=DEST
t.automated=True; t.replace_existing=True; t.save=True
opts=unreal.FbxImportUI(); opts.automated_import_should_detect_type=False
opts.mesh_type_to_import=unreal.FBXImportType.FBXIT_SKELETAL_MESH; opts.import_as_skeletal=True
opts.import_mesh=True; opts.import_animations=True; opts.import_materials=False; opts.import_textures=False
opts.skeletal_mesh_import_data.import_uniform_scale=1.0
t.options=opts; assets.import_asset_tasks([t])
if not t.imported_object_paths:raise RuntimeError('Ghost FBX import failed')
tasks=[]
for name,file in [('T_GhostFront','01_front.png'),('T_GhostBack','02_back.png')]:
    tx=unreal.AssetImportTask(); tx.filename=str(R/'Art/GhostReferences/v2'/file); tx.destination_path=DEST
    tx.destination_name=name; tx.automated=True; tx.replace_existing=True; tx.save=True; tasks.append(tx)
assets.import_asset_tasks(tasks)
lib=unreal.MaterialEditingLibrary
materials={}
for name,texture in [('GhostFront','T_GhostFront'),('GhostBack','T_GhostBack'),('GhostSkin',None)]:
    m=unreal.load_asset(DEST+'/M_'+name) or assets.create_asset('M_'+name,DEST,unreal.Material,unreal.MaterialFactoryNew())
    lib.set_material_usage(m,unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH)
    lib.delete_all_material_expressions(m)
    if texture:
        c=lib.create_material_expression(m,unreal.MaterialExpressionTextureSample)
        c.set_editor_property('texture',unreal.load_asset(DEST+'/'+texture)); pin='RGB'
    else:
        c=lib.create_material_expression(m,unreal.MaterialExpressionConstant3Vector)
        c.set_editor_property('constant',unreal.LinearColor(.29,.30,.29,1)); pin=''
    lib.connect_material_property(c,pin,unreal.MaterialProperty.MP_BASE_COLOR)
    rough=lib.create_material_expression(m,unreal.MaterialExpressionConstant); rough.set_editor_property('r',.94)
    lib.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS)
    lib.recompile_material(m); unreal.EditorAssetLibrary.save_loaded_asset(m); materials[name]=m
mesh=unreal.load_asset(DEST+'/SK_ErasedGhost')
if not isinstance(mesh,unreal.SkeletalMesh):raise RuntimeError('Expected skeletal mesh')
slots=mesh.get_editor_property('materials')
for index,slot in enumerate(slots):
    name=str(slot.get_editor_property('material_slot_name'))
    slot.set_editor_property('material_interface',materials.get(name,materials['GhostSkin']))
    slots[index]=slot
mesh.set_editor_property('materials',slots)
animations=[]
for p in unreal.EditorAssetLibrary.list_assets(DEST):
    a=unreal.load_asset(p)
    if isinstance(a,unreal.AnimSequence):animations.append(a)
if not animations:raise RuntimeError('Walking animation missing')
walk=animations[0]
if walk.get_name()!='A_GhostWalk':
    if unreal.EditorAssetLibrary.does_asset_exist(DEST+'/A_GhostWalk'):unreal.EditorAssetLibrary.delete_asset(DEST+'/A_GhostWalk')
    unreal.EditorAssetLibrary.rename_asset(walk.get_path_name(),DEST+'/A_GhostWalk')
unreal.EditorAssetLibrary.save_directory(DEST,only_if_is_dirty=False,recursive=True)
unreal.log('GHOST_IMPORT_COMPLETE bones='+str(mesh.get_name()))
