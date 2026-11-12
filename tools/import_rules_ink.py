"""Unreal: import rule-ink textures, pen_scratch, and build M_RulesInk.
Mix = lerp(Feed, Ink.rgb, Ink.a * saturate((Progress - Order) * 80)).
The wall copy is matte paper; the UI copy preserves the same ink progress without scene lighting."""
from pathlib import Path
import unreal
ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / 'Art/Generated'
tools = unreal.AssetToolsHelpers.get_asset_tools(); lib = unreal.MaterialEditingLibrary
tasks = []
for name, dest in [('T_RulesInk.png', '/Game/PrototypeAssets'), ('T_RulesInkOrder.png', '/Game/PrototypeAssets'), ('pen_scratch.wav', '/Game/Audio')]:
    t = unreal.AssetImportTask(); t.filename = str(GEN / name); t.destination_path = dest
    t.automated = True; t.replace_existing = True; t.save = True; tasks.append(t)
tools.import_asset_tasks(tasks)
for t in tasks:
    if not t.imported_object_paths: raise RuntimeError('Import failed ' + t.filename)
order = unreal.load_asset('/Game/PrototypeAssets/T_RulesInkOrder')
order.set_editor_property('srgb', False)
order.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_GRAYSCALE)
order.set_editor_property('filter', unreal.TextureFilter.TF_NEAREST)   # no blending across stroke order
unreal.EditorAssetLibrary.save_loaded_asset(order)
ink = unreal.load_asset('/Game/PrototypeAssets/T_RulesInk')
page = unreal.load_asset('/Game/PrototypeAssets/T_RulesPage')

for material_name in ('M_RulesInk','M_RulesInkUI'):
    mat = unreal.load_asset('/Game/PrototypeAssets/'+material_name) or tools.create_asset(material_name, '/Game/PrototypeAssets', unreal.Material, unreal.MaterialFactoryNew())
    if material_name.endswith('UI'): mat.set_editor_property('material_domain', unreal.MaterialDomain.MD_UI)
    is_ui = material_name.endswith('UI')
    mat.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT if is_ui else unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    mat.set_editor_property('two_sided', True)
    lib.delete_all_material_expressions(mat)
    E = lambda cls: lib.create_material_expression(mat, cls)
    feed = E(unreal.MaterialExpressionTextureSampleParameter2D); feed.set_editor_property('parameter_name', 'Feed'); feed.set_editor_property('texture', page)
    inks = E(unreal.MaterialExpressionTextureSample); inks.set_editor_property('texture', ink)
    ords = E(unreal.MaterialExpressionTextureSample); ords.set_editor_property('texture', order)
    ords.set_editor_property('sampler_type', unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE)
    prog = E(unreal.MaterialExpressionScalarParameter); prog.set_editor_property('parameter_name', 'Progress'); prog.set_editor_property('default_value', -1.0)
    sub = E(unreal.MaterialExpressionSubtract)
    lib.connect_material_expressions(prog, '', sub, 'A'); lib.connect_material_expressions(ords, 'R', sub, 'B')
    edge = E(unreal.MaterialExpressionMultiply); edge.set_editor_property('const_b', 80.0)
    lib.connect_material_expressions(sub, '', edge, 'A')
    sat = E(unreal.MaterialExpressionSaturate); lib.connect_material_expressions(edge, '', sat, '')
    alpha = E(unreal.MaterialExpressionMultiply)
    lib.connect_material_expressions(sat, '', alpha, 'A'); lib.connect_material_expressions(inks, 'A', alpha, 'B')
    mix = E(unreal.MaterialExpressionLinearInterpolate)
    lib.connect_material_expressions(feed, 'RGB', mix, 'A'); lib.connect_material_expressions(inks, 'RGB', mix, 'B'); lib.connect_material_expressions(alpha, '', mix, 'Alpha')
    if is_ui:
        lib.connect_material_property(mix, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    else:
        lib.connect_material_property(mix, '', unreal.MaterialProperty.MP_BASE_COLOR)
        rough = E(unreal.MaterialExpressionConstant); rough.set_editor_property('r', .94)
        lib.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
        glow = E(unreal.MaterialExpressionMultiply); glow.set_editor_property('const_b', .035)
        lib.connect_material_expressions(mix, '', glow, 'A')
        lib.connect_material_property(glow, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    lib.recompile_material(mat); unreal.EditorAssetLibrary.save_loaded_asset(mat)
unreal.log('RULES_INK_IMPORT_FINISHED')
