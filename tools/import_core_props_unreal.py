"""Import Blender-prepared Meshy props and explicit PBR materials into Unreal."""
from pathlib import Path
import json, hashlib, os, unreal
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Art/CoreProps/v1/Unreal'
DEST='/Game/PrototypeAssets/CoreProps'
items=json.loads((OUT/'import.json').read_text(encoding='utf-8'))
only=set(os.environ.get('NR_CORE_ONLY','').split(','))-{''}
if only:items=[item for item in items if item['id'] in only]
lib=unreal.MaterialEditingLibrary;tools=unreal.AssetToolsHelpers.get_asset_tools()
owned={i['mesh']+'.fbx' for i in items}|{p for i in items for m in i['materials'] for p in m['textures'].values()}
tasks=[]
for name in sorted(owned):
 t=unreal.AssetImportTask();t.filename=str(OUT/name);t.destination_path=DEST;t.automated=True;t.replace_existing=True;t.save=True
 if name.endswith('.fbx'):
  opt=unreal.FbxImportUI();opt.import_mesh=True;opt.import_as_skeletal=False;opt.import_materials=False;opt.import_textures=False;opt.import_animations=False
  opt.static_mesh_import_data.combine_meshes=True;opt.static_mesh_import_data.auto_generate_collision=False;t.options=opt
 tasks.append(t)
tools.import_asset_tasks(tasks)
for t in tasks:
 if not t.imported_object_paths:raise RuntimeError('Import failed: '+t.filename)
materials={}
for item in items:
 mesh=unreal.load_asset(DEST+'/'+item['mesh'])
 if not mesh:raise RuntimeError('Missing mesh '+item['mesh'])
 for entry in item['materials']:
  if item['id']=='B01':
   # Tiny Meshy UV islands bleed across faces in coarse streamed mips. All door
   # instances share this atlas; keep it resident even when the material is cached.
   for filename in entry['textures'].values():
    texture=unreal.load_asset(DEST+'/'+Path(filename).stem)
    texture.set_editor_property('never_stream',True)
    texture.set_editor_property('lod_bias',0);texture.set_editor_property('max_texture_size',0)
    unreal.EditorAssetLibrary.save_loaded_asset(texture)
  name=entry['name']
  if name not in materials:
   # Versioned immutable graphs avoid UE 5.8's rooted-expression deletion crash
   # when constructors already reference a material during commandlet startup.
   signature=hashlib.sha256(json.dumps({'entry':entry,'coating_revision':2},sort_keys=True).encode()).hexdigest()[:8]
   asset_name=name+'_'+signature
   mat=unreal.load_asset(DEST+'/'+asset_name)
   if mat:
    materials[name]=mat;mesh.set_material(entry['slot'],mat);continue
   mat=tools.create_asset(asset_name,DEST,unreal.Material,unreal.MaterialFactoryNew())
   for role,filename in entry['textures'].items():
    texture=unreal.load_asset(DEST+'/'+Path(filename).stem)
    texture.set_editor_property('srgb',role=='base')
    if role=='normal':
     texture.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_NORMALMAP);texture.set_editor_property('flip_green_channel',True)
    elif role=='orm':texture.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_MASKS)
    unreal.EditorAssetLibrary.save_loaded_asset(texture)
    node=lib.create_material_expression(mat,unreal.MaterialExpressionTextureSample)
    node.set_editor_property('texture',texture)
    node.set_editor_property('sampler_type',unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL if role=='normal' else unreal.MaterialSamplerType.SAMPLERTYPE_MASKS if role=='orm' else unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
    # AI PBR overstates worn plastic as polished metal and engraves broad surfaces.
    # Keep source files intact; calibrate the coating only in the game material.
    coated=item['id'] in ('I01','I02','O03','O05')
    if role=='orm' and coated:
     rough=lib.create_material_expression(mat,unreal.MaterialExpressionMax);rough.set_editor_property('const_b',.55)
     lib.connect_material_expressions(node,'G',rough,'A');lib.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS)
     metal=lib.create_material_expression(mat,unreal.MaterialExpressionMultiply);metal.set_editor_property('const_b',.15)
     lib.connect_material_expressions(node,'B',metal,'A');lib.connect_material_property(metal,'',unreal.MaterialProperty.MP_METALLIC)
    elif role=='orm':
     lib.connect_material_property(node,'G',unreal.MaterialProperty.MP_ROUGHNESS);lib.connect_material_property(node,'B',unreal.MaterialProperty.MP_METALLIC)
    elif role=='normal' and coated:
     strength=lib.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector);strength.set_editor_property('constant',unreal.LinearColor(.25,.25,1,1))
     normal=lib.create_material_expression(mat,unreal.MaterialExpressionMultiply)
     lib.connect_material_expressions(node,'RGB',normal,'A');lib.connect_material_expressions(strength,'',normal,'B')
     lib.connect_material_property(normal,'',unreal.MaterialProperty.MP_NORMAL)
    else:lib.connect_material_property(node,'RGB',unreal.MaterialProperty.MP_NORMAL if role=='normal' else unreal.MaterialProperty.MP_BASE_COLOR)
   for role,value in entry['constants'].items():
    if role=='base' and 'base' in entry['textures']:continue
    if role in ('rough','metal') and 'orm' in entry['textures']:continue
    if role=='base':
     node=lib.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector);node.set_editor_property('constant',unreal.LinearColor(*value,1))
    else:
     node=lib.create_material_expression(mat,unreal.MaterialExpressionConstant);node.set_editor_property('r',value)
    lib.connect_material_property(node,'',{'base':unreal.MaterialProperty.MP_BASE_COLOR,'rough':unreal.MaterialProperty.MP_ROUGHNESS,'metal':unreal.MaterialProperty.MP_METALLIC}[role])
   lib.recompile_material(mat);unreal.EditorAssetLibrary.save_loaded_asset(mat);materials[name]=mat
  mesh.set_material(entry['slot'],materials[name])
 # Generated bodies have open interiors; convex hulls would seal the drawers/cabinets.
 mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
 if item['id']=='B01':
  # Blender edits vertex positions/mirrors the leaf after glTF import. Discard
  # stale imported custom normals and rebuild the tangent basis on final geometry.
  subsystem=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
  build=subsystem.get_lod_build_settings(mesh,0)
  build.recompute_normals=True;build.recompute_tangents=True;build.compute_weighted_normals=False
  build.use_full_precision_u_vs=True
  subsystem.set_lod_build_settings(mesh,0,build)
 unreal.EditorAssetLibrary.save_loaded_asset(mesh)
 unreal.log('CORE_PROP_IMPORTED '+item['mesh'])
unreal.EditorAssetLibrary.save_directory(DEST,only_if_is_dirty=True,recursive=True)
unreal.log('CORE_PROPS_IMPORT_COMPLETE')
