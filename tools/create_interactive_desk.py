"""Split the existing CC0 desk into its original body and six functional drawers."""
import bpy
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Art/ThirdParty/PolyHaven/Prepared'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Art/ThirdParty/PolyHaven/metal_office_desk/metal_office_desk_2k.blend'))
objects=[o for o in bpy.context.view_layer.objects if o.type=='MESH']
points=[o.matrix_world@Vector(v) for o in objects for v in o.bound_box]
lo=Vector([min(p[i] for p in points) for i in range(3)]);hi=Vector([max(p[i] for p in points) for i in range(3)])
center=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z)); scale=Vector([(1.4,.65,.76)[i]/(hi[i]-lo[i]) for i in range(3)])
for o in objects:
 matrix=o.matrix_world.copy()
 for v in o.data.vertices:
  point=matrix@v.co-center;v.co=Vector([point[i]*scale[i] for i in range(3)])
 o.matrix_world.identity()
 for slot in o.material_slots:
  if slot.material: slot.material.name='M_PH_metal_office_desk_0'
groups=[('SM_PH_DeskBody',[o for o in objects if '_drawer_' not in o.name])]
groups += [('SM_PH_Drawer'+str(i),[o for o in objects if o.name.endswith('_drawer_%02d'%i)]) for i in range(1,7)]
for name,parts in groups:
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0]
 bpy.ops.object.convert(target='MESH');bpy.ops.object.join()
 o=bpy.context.object;o.name=name
 bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,bake_anim=False,add_leaf_bones=False,mesh_smooth_type='FACE')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'haedam_interactive_desk.blend'))
print('DRAWER_EXPORT_COMPLETE')
