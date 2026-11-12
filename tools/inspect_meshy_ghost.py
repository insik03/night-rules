"""Inspect a downloaded GLB with Blender; no network or source-file edits."""
import bpy
import json
import sys
from pathlib import Path

args = sys.argv[sys.argv.index('--') + 1:]
source, destination = map(Path, args[:2])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(source))
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
rigs = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE']
report = {
    'source': source.name,
    'triangles': sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes),
    'meshes': [{'name': o.name, 'vertices': len(o.data.vertices), 'faces': len(o.data.polygons),
                'dimensions': list(o.dimensions), 'location': list(o.location),
                'rotation': list(o.rotation_euler), 'scale': list(o.scale),
                'materials': [m.name if m else None for m in o.data.materials]} for o in meshes],
    'rigs': [{'name': r.name, 'scale': list(r.scale), 'rotation': list(r.rotation_euler),
              'bones': [{'name': b.name, 'parent': b.parent.name if b.parent else None,
                         'head': list(b.head_local), 'tail': list(b.tail_local)} for b in r.data.bones]}
             for r in rigs],
    'actions': [{'name': a.name, 'frames': list(a.frame_range)} for a in bpy.data.actions],
    'fps': bpy.context.scene.render.fps,
    'images': [{'name': i.name, 'size': list(i.size), 'packed': bool(i.packed_file)} for i in bpy.data.images],
    'materials': [{'name': m.name, 'nodes': [{'type': n.type, 'name': n.name,
                    'image': n.image.name if n.type == 'TEX_IMAGE' and n.image else None}
                    for n in m.node_tree.nodes]} for m in bpy.data.materials if m.use_nodes],
}
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(json.dumps(report, indent=2), encoding='utf-8')
print('MESHY_INSPECTION', source.name, 'triangles=', report['triangles'],
      'rigs=', len(rigs), 'actions=', report['actions'], flush=True)
