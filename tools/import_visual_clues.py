"""Import a surface handprint and immutable materials; preserve old rooted graphs."""
from pathlib import Path
import unreal

root = Path(__file__).resolve().parents[1]
dest = '/Game/PrototypeAssets'
assets = unreal.AssetToolsHelpers.get_asset_tools()
lib = unreal.MaterialEditingLibrary
for name in ('T_UVDoor', 'T_UVFragment', 'T_ClueHandprint'):
    task = unreal.AssetImportTask()
    task.filename = str(root / 'Art/Investigation' / (name + '.png'))
    task.destination_path = dest
    task.automated = True
    task.replace_existing = True
    task.save = True
    assets.import_asset_tasks([task])
    if not task.imported_object_paths:
        raise RuntimeError('Texture import failed: ' + name)

def material(name):
    existing = unreal.load_asset(dest + '/' + name)
    if existing:
        return existing, False
    return assets.create_asset(name, dest, unreal.Material, unreal.MaterialFactoryNew()), True

mat, create = material('M_ClueSurface_v1')
if create:
    mat.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
    mat.set_editor_property('two_sided', True)
    mat.set_editor_property('opacity_mask_clip_value', .15)
    sample = lib.create_material_expression(mat, unreal.MaterialExpressionTextureSampleParameter2D)
    sample.set_editor_property('parameter_name', 'Feed')
    sample.set_editor_property('texture', unreal.load_asset(dest + '/T_ClueHandprint'))
    # Use alpha as deposited grime; no baked lighting/colour fringe from the source.
    lib.connect_material_property(sample, 'A', unreal.MaterialProperty.MP_OPACITY_MASK)
    tint = lib.create_material_expression(mat, unreal.MaterialExpressionVectorParameter)
    tint.set_editor_property('parameter_name', 'Tint')
    tint.set_editor_property('default_value', unreal.LinearColor(.085, .063, .042, 1))
    lib.connect_material_property(tint, '', unreal.MaterialProperty.MP_BASE_COLOR)
    rough = lib.create_material_expression(mat, unreal.MaterialExpressionConstant)
    rough.set_editor_property('r', .95)
    lib.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    lib.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)

mat, create = material('M_ClueMetal_v1')
if create:
    tint = lib.create_material_expression(mat, unreal.MaterialExpressionVectorParameter)
    tint.set_editor_property('parameter_name', 'Tint')
    tint.set_editor_property('default_value', unreal.LinearColor(.32, .32, .29, 1))
    lib.connect_material_property(tint, '', unreal.MaterialProperty.MP_BASE_COLOR)
    rough = lib.create_material_expression(mat, unreal.MaterialExpressionConstant)
    rough.set_editor_property('r', .65)
    lib.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    lib.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
mat, create = material('M_ClueUVHand_v1')
if create:
    mat.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
    mat.set_editor_property('two_sided', True)
    mat.set_editor_property('opacity_mask_clip_value', .15)
    sample = lib.create_material_expression(mat, unreal.MaterialExpressionTextureSample)
    sample.set_editor_property('texture', unreal.load_asset(dest + '/T_ClueHandprint'))
    lib.connect_material_property(sample, 'A', unreal.MaterialProperty.MP_OPACITY_MASK)
    tint = lib.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector)
    tint.set_editor_property('constant', unreal.LinearColor(.12, .65, .35, 1))
    lib.connect_material_property(tint, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    lib.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
unreal.log('VISUAL_CLUES_IMPORT_COMPLETE')
