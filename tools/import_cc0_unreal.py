"""Import the prepared Poly Haven meshes and explicitly connect their PBR maps."""
from pathlib import Path
import json, unreal
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Art/ThirdParty/PolyHaven/Prepared'
DEST='/Game/ThirdParty/PolyHaven'
# create_door.py writes door_import.json next to prepare_cc0_assets.py's import.json.
items=[i for f in sorted(OUT.glob('*import.json')) for i in json.loads(f.read_text(encoding='utf-8'))]
# NR_IMPORT_ONLY=SM_A,SM_B limits the run to those meshes and their textures. Prepared/ also
# holds FBX owned by other importers (import_drawers.py sets their collision); never re-import
# those blindly.
import os
ONLY=[x for x in os.environ.get('NR_IMPORT_ONLY','').split(',') if x]
if ONLY: items=[i for i in items if i['mesh'] in ONLY]
OWNED={i['mesh']+'.fbx' for i in items}|{t for i in items for m in i['materials'] for t in m['textures'].values()}
lib=unreal.MaterialEditingLibrary
asset_tools=unreal.AssetToolsHelpers.get_asset_tools()
tasks=[]
for path in sorted(OUT.glob('*')):
    if path.suffix not in ('.fbx','.png') or path.name not in OWNED: continue
    t=unreal.AssetImportTask();t.filename=str(path);t.destination_path=DEST
    t.automated=True;t.replace_existing=True;t.save=True
    if path.suffix=='.fbx':
        options=unreal.FbxImportUI();options.import_mesh=True;options.import_as_skeletal=False
        options.import_materials=False;options.import_textures=False;options.import_animations=False
        options.static_mesh_import_data.combine_meshes=True
        options.static_mesh_import_data.auto_generate_collision=True
        t.options=options
    tasks.append(t)
asset_tools.import_asset_tasks(tasks)
for task in tasks:
    if not task.imported_object_paths: raise RuntimeError('Failed import: '+task.filename)
for item in items:
    mesh=unreal.load_asset(DEST+'/'+item['mesh'])
    if not mesh: raise RuntimeError('Missing mesh '+item['mesh'])
    for entry in item['materials']:
        path=DEST+'/'+entry['name']
        mat=unreal.load_asset(path) or asset_tools.create_asset(entry['name'],DEST,unreal.Material,unreal.MaterialFactoryNew())
        lib.delete_all_material_expressions(mat)
        roles=entry['textures']
        # opacity map = cut-out label edges, alpha map = see-through glass.
        mat.set_editor_property('blend_mode',unreal.BlendMode.BLEND_TRANSLUCENT if 'alpha' in roles else unreal.BlendMode.BLEND_MASKED if 'mask' in roles else unreal.BlendMode.BLEND_OPAQUE)
        for role, filename in entry['textures'].items():
            texture=unreal.load_asset(DEST+'/'+Path(filename).stem)
            if not texture: raise RuntimeError('Missing texture '+filename)
            texture.set_editor_property('srgb',role=='base')
            if role=='normal':
                texture.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_NORMALMAP)
                texture.set_editor_property('flip_green_channel',True)
            elif role!='base': texture.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_MASKS)
            unreal.EditorAssetLibrary.save_loaded_asset(texture)
            sample=lib.create_material_expression(mat,unreal.MaterialExpressionTextureSample)
            sample.set_editor_property('texture',texture)
            sample.set_editor_property('sampler_type',unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL if role=='normal' else unreal.MaterialSamplerType.SAMPLERTYPE_COLOR if role=='base' else unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
            prop={'base':unreal.MaterialProperty.MP_BASE_COLOR,'rough':unreal.MaterialProperty.MP_ROUGHNESS,
                  'metal':unreal.MaterialProperty.MP_METALLIC,'normal':unreal.MaterialProperty.MP_NORMAL,
                  'mask':unreal.MaterialProperty.MP_OPACITY_MASK,'alpha':unreal.MaterialProperty.MP_OPACITY}[role]
            lib.connect_material_property(sample,'RGB' if role in ('base','normal') else 'R',prop)
        for role, value in entry.get('constants',{}).items():
            if role in roles: continue
            if role=='base':
                node=lib.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector)
                node.set_editor_property('constant',unreal.LinearColor(*value,1))
            else:
                node=lib.create_material_expression(mat,unreal.MaterialExpressionConstant)
                node.set_editor_property('r',value)
            lib.connect_material_property(node,'',{'base':unreal.MaterialProperty.MP_BASE_COLOR,
                'rough':unreal.MaterialProperty.MP_ROUGHNESS,'metal':unreal.MaterialProperty.MP_METALLIC}[role])
        lib.recompile_material(mat);unreal.EditorAssetLibrary.save_loaded_asset(mat)
        mesh.set_material(entry['slot'],mat)
    # Small hand-sized props: interaction traces passed straight through their auto-generated
    # collision (measured in NRDemoTest). A box hull matches these shapes; traces use it.
    if item['mesh'] in ('SM_GS_Fuse','SM_GS_KeyTag','SM_GS_Binder','SM_GS_Breaker','SM_GS_Hatch','SM_GS_Logbook'):
        unreal.EditorStaticMeshLibrary.remove_collisions(mesh)
        unreal.EditorStaticMeshLibrary.add_simple_collisions(mesh,unreal.ScriptCollisionShapeType.BOX)
        mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    unreal.log('PH_IMPORTED '+item['mesh'])
unreal.EditorAssetLibrary.save_directory(DEST,only_if_is_dirty=True,recursive=True)
unreal.log('PH_IMPORT_FINISHED')
