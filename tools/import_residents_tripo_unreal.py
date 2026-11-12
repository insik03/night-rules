"""Import the six approved Studio residents without compiling the game."""
import json
from pathlib import Path
import unreal
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'Art/Characters/Residents-Tripo-v1'
MANIFEST=json.loads((BASE/'manifest.json').read_text(encoding='utf-8'))
TOOLS=unreal.AssetToolsHelpers.get_asset_tools();LIB=unreal.MaterialEditingLibrary
REPORT=[]

def load_file(folder, dest, name, ext, options=None):
    task=unreal.AssetImportTask();task.filename=str(folder/(name+ext))
    task.destination_path=dest;task.destination_name=name;task.automated=True
    task.replace_existing=True;task.save=True
    if options:task.options=options
    TOOLS.import_asset_tasks([task])
    obj=unreal.load_asset(dest+'/'+name)
    if not task.imported_object_paths or not obj:raise RuntimeError('Import failed '+name)
    return obj

for entry in MANIFEST['residents']:
    slug=entry['id'];name=slug.title();folder=BASE/'models'/slug/'Unreal'
    dest='/Game/PrototypeAssets/ResidentsV1/'+name
    report=json.loads((folder.parent/'prepared.json').read_text(encoding='utf-8'))
    opts=unreal.FbxImportUI();opts.automated_import_should_detect_type=False
    opts.mesh_type_to_import=unreal.FBXImportType.FBXIT_SKELETAL_MESH
    opts.import_as_skeletal=True;opts.import_mesh=True;opts.import_animations=False
    opts.import_materials=False;opts.import_textures=False
    mesh=load_file(folder,dest,'SK_'+name,'.fbx',opts)
    if not isinstance(mesh,unreal.SkeletalMesh):raise RuntimeError('Not skeletal '+name)
    skeleton=mesh.get_editor_property('skeleton')
    opts=unreal.FbxImportUI();opts.automated_import_should_detect_type=False
    opts.mesh_type_to_import=unreal.FBXImportType.FBXIT_ANIMATION
    opts.import_mesh=False;opts.import_animations=True;opts.import_materials=False;opts.import_textures=False
    opts.skeleton=skeleton;opts.override_animation_name='A_'+name+'_Idle'
    clip=load_file(folder,dest,'A_'+name+'_Idle','.fbx',opts)
    if not isinstance(clip,unreal.AnimSequence):raise RuntimeError('No idle '+name)
    duration=clip.get_editor_property('sequence_length')
    if abs(duration-report['animation_seconds'])>.15:raise RuntimeError('Animation duration mismatch '+name)
    textures={}
    for kind,texname in report['texture_maps'].items():
        tex=load_file(folder,dest,texname,'.png');tex.set_editor_property('srgb',kind=='BaseColor')
        if kind=='Normal':
            tex.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_NORMALMAP)
            tex.set_editor_property('flip_green_channel',True)
        elif kind=='ORM':tex.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_MASKS)
        tex.set_editor_property('max_texture_size',2048);unreal.EditorAssetLibrary.save_loaded_asset(tex)
        textures[kind]=tex
    matname='M_'+name+'_V1';mat=unreal.load_asset(dest+'/'+matname)
    if not mat:
        mat=TOOLS.create_asset(matname,dest,unreal.Material,unreal.MaterialFactoryNew())
        LIB.set_material_usage(mat,unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH)
        for kind,tex in textures.items():
            node=LIB.create_material_expression(mat,unreal.MaterialExpressionTextureSample)
            node.set_editor_property('texture',tex)
            node.set_editor_property('sampler_type',unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL if kind=='Normal' else unreal.MaterialSamplerType.SAMPLERTYPE_MASKS if kind=='ORM' else unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
            if kind=='ORM':
                LIB.connect_material_property(node,'G',unreal.MaterialProperty.MP_ROUGHNESS)
                LIB.connect_material_property(node,'B',unreal.MaterialProperty.MP_METALLIC)
            else:LIB.connect_material_property(node,'RGB',unreal.MaterialProperty.MP_NORMAL if kind=='Normal' else unreal.MaterialProperty.MP_BASE_COLOR)
        LIB.recompile_material(mat);unreal.EditorAssetLibrary.save_loaded_asset(mat)
    slots=mesh.get_editor_property('materials')
    if len(slots)!=1:raise RuntimeError('Unexpected atlas slot count '+name)
    slot=slots[0];slot.set_editor_property('material_interface',mat);slots[0]=slot;mesh.set_editor_property('materials',slots)
    # Imported bounds are in cm. Fail rather than hide a hundredfold unit error.
    bounds=mesh.get_imported_bounds();height=bounds.box_extent.z*2
    if abs(height-entry['height_cm'])>1:raise RuntimeError('Unexpected height '+name+': '+str(height))
    subsystem=unreal.get_editor_subsystem(unreal.SkeletalMeshEditorSubsystem)
    lods_ok=subsystem.regenerate_lod(mesh,3,True)
    if not lods_ok:raise RuntimeError('Resident LOD generation failed '+name)
    unreal.EditorAssetLibrary.save_directory(dest,only_if_is_dirty=False,recursive=True)
    REPORT.append({'id':slug,'mesh':mesh.get_path_name(),'idle':clip.get_path_name(),'height_cm':height,'idle_seconds':duration,'lod_levels':3,'source_triangles':report['triangles'],'materials_assigned':len(slots)})
    (BASE/'unreal-import.json').write_text(json.dumps(REPORT,indent=2),encoding='utf-8')
    unreal.log('RESIDENT_IMPORTED '+slug+' height_cm='+str(height))
unreal.log('RESIDENTS_IMPORT_COMPLETE count='+str(len(REPORT)))
