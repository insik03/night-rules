from pathlib import Path
exec(compile((Path(__file__).parent/'create_assets.py').read_text(encoding='utf-8').split('phone=export')[0], 'helpers', 'exec'))
white=mat('Sanitary ceramic',(.75,.75,.69));dark=mat('Bowl interior',(.09,.1,.085))
parts=[box('Tank',(0,.21,.60),(.42,.17,.44),white),box('Base',(0,0,.13),(.22,.33,.26),white),box('Flush button',(.10,.21,.83),(.05,.04,.008),metal)]
bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=(0,-.04,.32));o=bpy.context.object;o.scale=(.22,.29,.17);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(white);parts.append(o)
bpy.ops.mesh.primitive_torus_add(major_radius=.16,minor_radius=.025,major_segments=32,minor_segments=8,location=(0,-.055,.47));o=bpy.context.object;o.scale=(1,1.38,.6);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(white);parts.append(o)
parts.append(box('Seat opening',(0,-.055,.445),(.25,.34,.009),dark))
export('SM_Toilet',parts);bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'haedam_sanitary.blend'))
