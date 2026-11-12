"""Original framed entrance door authored in Blender, with separate glazing slot."""
from pathlib import Path
exec(compile((Path(__file__).parent/'create_assets.py').read_text(encoding='utf-8').split('phone=export')[0], 'mesh_helpers', 'exec'))
glass=mat('Outdoor glass',(.12,.2,.19))
parts=[box('Pane',(0,0,1.10),(1.20,.015,2.10),glass),
 *[box('Stile',(x,0,1.10),(.045,.055,2.20),metal) for x in [-.625,.625]],
 *[box('Rail',(0,0,z),(1.3,.055,.045),metal) for z in [.025,1.1,2.175]],
 box('Pull handle',(.47,-.065,1.1),(.025,.05,.36),metal)]
export('SM_EntranceDoor',parts)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'haedam_entrance.blend'))
