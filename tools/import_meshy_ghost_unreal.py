"""Import the approved Meshy caretaker with its own skeleton, PBR maps and clips."""
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'Art/GhostMeshy/Approved/Unreal'
DEST = '/Game/PrototypeAssets/GhostMeshy'
assets = unreal.AssetToolsHelpers.get_asset_tools()

def import_task(filename, name, options=None):
    task = unreal.AssetImportTask()
    task.filename = str(SOURCE / filename)
    task.destination_path = DEST
    task.destination_name = name
    task.automated = True
    task.replace_existing = True
    task.save = True
    if options:
        task.options = options
    assets.import_asset_tasks([task])
    if not task.imported_object_paths:
        raise RuntimeError('Import failed: ' + filename)
    return unreal.load_asset(DEST + '/' + name)

opts = unreal.FbxImportUI()
opts.automated_import_should_detect_type = False
opts.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
opts.import_as_skeletal = True
opts.import_mesh = True
opts.import_animations = False
opts.import_materials = False
opts.import_textures = False
mesh = import_task('SK_SmilingCaretaker.fbx', 'SK_SmilingCaretaker', opts)
if not isinstance(mesh, unreal.SkeletalMesh):
    raise RuntimeError('Missing caretaker skeletal mesh')
skeleton = mesh.get_editor_property('skeleton')
for name in ('A_CaretakerWalk', 'A_CaretakerRun'):
    options = unreal.FbxImportUI()
    options.automated_import_should_detect_type = False
    options.mesh_type_to_import = unreal.FBXImportType.FBXIT_ANIMATION
    options.import_mesh = False
    options.import_animations = True
    options.import_materials = False
    options.import_textures = False
    options.skeleton = skeleton
    options.override_animation_name = name
    clip = import_task(name + '.fbx', name, options)
    if not isinstance(clip, unreal.AnimSequence) or clip.get_editor_property('sequence_length') <= .1:
        raise RuntimeError('Missing animation: ' + name)

textures = {}
for kind in ('BaseColor', 'Normal', 'ORM'):
    texture = import_task('T_Caretaker_' + kind + '.png', 'T_Caretaker_' + kind)
    texture.set_editor_property('srgb', kind == 'BaseColor')
    if kind == 'Normal':
        texture.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP)
        # glTF/Blender tangent normals are OpenGL; Unreal expects DirectX green.
        texture.set_editor_property('flip_green_channel', True)
    elif kind == 'ORM':
        texture.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_MASKS)
    unreal.EditorAssetLibrary.save_loaded_asset(texture)
    textures[kind] = texture

lib = unreal.MaterialEditingLibrary
mat = unreal.load_asset(DEST + '/M_Caretaker') or assets.create_asset(
    'M_Caretaker', DEST, unreal.Material, unreal.MaterialFactoryNew())
lib.delete_all_material_expressions(mat)
lib.set_material_usage(mat, unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH)
nodes = {}
for kind in textures:
    node = lib.create_material_expression(mat, unreal.MaterialExpressionTextureSample)
    node.set_editor_property('texture', textures[kind])
    if kind == 'Normal':
        node.set_editor_property('sampler_type', unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    elif kind == 'ORM':
        node.set_editor_property('sampler_type', unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    nodes[kind] = node
lib.connect_material_property(nodes['BaseColor'], 'RGB', unreal.MaterialProperty.MP_BASE_COLOR)
lib.connect_material_property(nodes['Normal'], 'RGB', unreal.MaterialProperty.MP_NORMAL)
lib.connect_material_property(nodes['ORM'], 'G', unreal.MaterialProperty.MP_ROUGHNESS)
lib.connect_material_property(nodes['ORM'], 'B', unreal.MaterialProperty.MP_METALLIC)
lib.recompile_material(mat)
unreal.EditorAssetLibrary.save_loaded_asset(mat)
slots = mesh.get_editor_property('materials')
if len(slots) != 1:
    raise RuntimeError('Expected one UV atlas material, got ' + str(len(slots)))
slot = slots[0]
slot.set_editor_property('material_interface', mat)
slots[0] = slot
mesh.set_editor_property('materials', slots)
assigned = mesh.get_editor_property('materials')[0].get_editor_property('material_interface')
if assigned != mat:
    raise RuntimeError('Caretaker PBR material was not assigned to the mesh slot')
unreal.EditorAssetLibrary.save_directory(DEST, only_if_is_dirty=False, recursive=True)
unreal.log('MESHY_GHOST_IMPORT_COMPLETE mesh=' + mesh.get_path_name())
