"""Import Blender-prepared Meshy props and explicit PBR materials into Unreal."""
from pathlib import Path
import json, hashlib, os, unreal
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Art/EnvironmentMeshy/v1/Unreal'
DEST='/Game/PrototypeAssets/Architecture'
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
 unreal.EditorAssetLibrary.save_loaded_asset(mesh)
 unreal.log('ARCHITECTURE_IMPORTED '+item['mesh'])
unreal.EditorAssetLibrary.save_directory(DEST,only_if_is_dirty=True,recursive=True)
# Renovated third-floor coating variants use the same geometry and cost no credits.
for name,color in [('M_AM_CleanWall',(.72,.70,.63)),('M_AM_CleanFloor',(.39,.40,.36)),('M_AM_CleanTile',(.55,.55,.49)),('M_AM_RoofFloor',(.08,.18,.13))]:
 mat=unreal.load_asset(DEST+'/'+name)
 if not mat:
  mat=tools.create_asset(name,DEST,unreal.Material,unreal.MaterialFactoryNew())
  node=lib.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector);node.set_editor_property('constant',unreal.LinearColor(*color,1))
  lib.connect_material_property(node,'',unreal.MaterialProperty.MP_BASE_COLOR)
  rough=lib.create_material_expression(mat,unreal.MaterialExpressionConstant);rough.set_editor_property('r',.82)
  lib.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS);lib.recompile_material(mat)
  unreal.EditorAssetLibrary.save_loaded_asset(mat)
unreal.log('ARCHITECTURE_IMPORT_COMPLETE')

# Versioned architectural finishes follow the approved palette, without floral
# wallpaper. World-space shaders keep the scale identical on every floor.
for name,code in {
 'M_AM_PlasterV2': '''float n=.5+.25*sin(Pos.x*.043+sin(Pos.z*.031)*2)+.15*sin(Pos.y*.09+Pos.z*.055); return lerp(float3(.34,.30,.24),float3(.49,.43,.34),saturate(n));''',
 'M_AM_CleanWallV2': '''float n=.5+.5*sin(Pos.x*.12+Pos.y*.11+Pos.z*.15);return lerp(float3(.50,.48,.42),float3(.53,.51,.46),n);''',
 'M_AM_LinoleumV2a': '''float2 p=Pos.xy/70;float2 d=float2(p.x+p.y,p.x-p.y);float2 e=abs(frac(d)-.5);float patternMask=1-smoothstep(.012,.030,min(e.x,e.y));float wear=.96+.04*sin(Pos.x*.023+sin(Pos.y*.055));return lerp(float3(.105,.155,.133),float3(.23,.26,.19),patternMask*.55)*wear;'''
}.items():
 mat=unreal.load_asset(DEST+'/'+name)
 if mat:continue
 mat=tools.create_asset(name,DEST,unreal.Material,unreal.MaterialFactoryNew())
 pos=lib.create_material_expression(mat,unreal.MaterialExpressionWorldPosition)
 custom=lib.create_material_expression(mat,unreal.MaterialExpressionCustom)
 inp=unreal.CustomInput();inp.set_editor_property('input_name','Pos')
 custom.set_editor_property('inputs',[inp]);custom.set_editor_property('code',code)
 custom.set_editor_property('output_type',unreal.CustomMaterialOutputType.CMOT_FLOAT3)
 lib.connect_material_expressions(pos,'XYZ',custom,'Pos')
 lib.connect_material_property(custom,'',unreal.MaterialProperty.MP_BASE_COLOR)
 rough=lib.create_material_expression(mat,unreal.MaterialExpressionConstant);rough.set_editor_property('r',.9)
 lib.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS)
 lib.recompile_material(mat);unreal.EditorAssetLibrary.save_loaded_asset(mat)
unreal.log('ARCHITECTURE_V2_FINISHES_COMPLETE')
