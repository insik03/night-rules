"""Blender: normalize CC0 models, preserve UVs, export FBX and PNG PBR maps."""
from pathlib import Path
import bpy, json
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'Art/ThirdParty/PolyHaven'
OUT = SOURCE / 'Prepared'
OUT.mkdir(parents=True, exist_ok=True)
# Full dimensions in meters (None keeps Poly Haven's real-world scale), centered with a floor-level origin.
SPECS = {
 'metal_office_desk': ('SM_PH_Desk', (1.4, .65, .76)),
 'plastic_monobloc_chair_01': ('SM_PH_Chair', (.48, .52, .88)),
 'steel_frame_shelves_03': ('SM_PH_Shelves', (.8, .35, 1.55)),
 'vintage_microwave': ('SM_PH_Microwave', (.52, .40, .32)),
 'vintage_electric_kettle': ('SM_PH_Kettle', (.22, .20, .28)),
 'pot_enamel_01': ('SM_PH_Pot', (.30, .24, .18)),
 'television_02': ('SM_PH_CRT', None),
 'security_camera_01': ('SM_PH_SecurityCamera', None),
 'korean_fire_extinguisher_01': ('SM_PH_Extinguisher', None),
 'wall_clock': ('SM_PH_WallClock', None),
 'old_bed_frame': ('SM_PH_Bed', None),
}
manifest = []
for slug, (name, dimensions) in SPECS.items():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE / slug / (slug + '_2k.blend')))
    # Rigged assets carry bone-widget meshes outside the view layer; skip them.
    meshes = [o for o in bpy.context.view_layer.objects if o.type == 'MESH' and not o.name.lower().startswith('wdg')]
    if not meshes: raise RuntimeError('No meshes: ' + slug)
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes:
        o.hide_set(False); o.hide_viewport=False; o.select_set(True)
    bpy.context.view_layer.objects.active=meshes[0]
    # Evaluate modifiers and retain the original UVs and material slots.
    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.join()
    obj=bpy.context.object
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    points=[obj.matrix_world @ Vector(p) for p in obj.bound_box]
    lo=Vector([min(p[i] for p in points) for i in range(3)])
    hi=Vector([max(p[i] for p in points) for i in range(3)])
    center=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z))
    for v in obj.data.vertices: v.co = obj.matrix_world @ v.co - center
    obj.matrix_world.identity()
    if dimensions: obj.dimensions=dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.name=name
    materials=[]
    for index, slot in enumerate(obj.material_slots):
        mat=slot.material
        if not mat: continue
        material_name=f'M_PH_{slug}_{index}'
        mat.name=material_name
        textures={}
        for node in mat.node_tree.nodes:
            if node.type != 'TEX_IMAGE' or not node.image: continue
            img=node.image
            # Blend files reference textures using //textures/... paths.
            original=Path(bpy.path.abspath(img.filepath))
            if not original.exists():
                original=SOURCE/slug/'textures'/Path(img.filepath).name
            if not original.exists(): raise RuntimeError('Missing texture: '+str(original))
            img=bpy.data.images.load(str(original),check_existing=False)
            node.image=img
            # Force lazy image decoding before changing its source filename.
            _ = img.pixels[0]
            stem=original.stem
            target=OUT/(stem+'.png')
            img.filepath_raw=str(target); img.file_format='PNG'; img.save()
            for role, marker in [('base','_diff_'),('rough','_rough_'),('metal','_metal_'),('normal','_nor_gl_'),('mask','_opacity_'),('alpha','_alpha_')]:
                if marker in stem: textures[role]=target.name
        entry={'name':material_name,'slot':index,'textures':textures}
        if 'base' not in textures:
            # Untextured slots (e.g. clock glass) keep their Principled constants.
            bsdf=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
            if not bsdf: raise RuntimeError('No base texture or BSDF: '+material_name)
            entry['constants']={'base':list(bsdf.inputs['Base Color'].default_value)[:3],
                'rough':bsdf.inputs['Roughness'].default_value,'metal':bsdf.inputs['Metallic'].default_value}
        materials.append(entry)
    bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,
        object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,
        bake_anim=False,add_leaf_bones=False,mesh_smooth_type='FACE')
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(name+'.blend')))
    manifest.append({'slug':slug,'mesh':name,'dimensions_cm':[round(d*100,1) for d in obj.dimensions],
                     'materials':materials,'vertices':len(obj.data.vertices)})
    print('PREPARED',name,materials,flush=True)
(OUT/'import.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
