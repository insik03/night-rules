"""Blender: gosiwon door, frame and built-in furniture with CC0 oak veneer (Poly Haven).
Run after fetch_cc0_assets.py. Writes FBX + door_import.json into PolyHaven/Prepared,
which import_cc0_unreal.py picks up. Units: metres; every mesh has a floor-level origin.
Door leaf origin sits on the hinge edge so the game can swing it by yaw alone.
Lock, peephole and number plate face Blender -Y (the corridor side)."""
from pathlib import Path
import bpy, json, shutil

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'Art/ThirdParty/PolyHaven'
OUT = SRC / 'Prepared'
WOOD = 'oak_veneer_01'

bpy.ops.wm.read_factory_settings(use_empty=True)

def constant(name, color, rough, metal):
    # Reuse by name: a duplicate would become 'Name.001', an invalid Unreal asset name.
    if name in bpy.data.materials: return bpy.data.materials[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = rough; p.inputs['Metallic'].default_value = metal
    return m

wood = bpy.data.materials.new('M_GS_Wood')
# ponytail: colour constants for hardware; swap to scanned textures if close-ups need it.
steel = constant('M_GS_Steel', (.62, .62, .6), .35, 1)
black = constant('M_GS_BlackPlastic', (.02, .02, .022), .45, 0)
white = constant('M_GS_WhitePlastic', (.78, .78, .74), .5, 0)

textures = {}
for role, marker in [('base', 'diff'), ('rough', 'rough'), ('normal', 'nor_gl')]:
    name = f'{WOOD}_{marker}_1k.png'
    shutil.copyfile(SRC / WOOD / name, OUT / name); textures[role] = name

def box(size, at, mat, bevel=.002):
    bpy.ops.mesh.primitive_cube_add(size=1, location=at)
    o = bpy.context.object; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat)
    if bevel:
        b = o.modifiers.new('bevel', 'BEVEL'); b.width = bevel; b.segments = 2
        bpy.ops.object.modifier_apply(modifier=b.name)
    return o

def cyl(r, depth, at, mat, axis='Y'):
    rot = {'X': (0, 1.5708, 0), 'Y': (1.5708, 0, 0), 'Z': (0, 0, 0)}[axis]
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=at, rotation=rot, vertices=20)
    o = bpy.context.object; o.data.materials.append(mat); return o

def export(name, parts):
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts: p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join(); o = bpy.context.object; o.name = name
    # Wood grain: box-project UVs at 1 tile per metre, grain running vertically.
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.cube_project(cube_size=1.0); bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.export_scene.fbx(filepath=str(OUT / (name + '.fbx')), use_selection=True,
        object_types={'MESH'}, axis_forward='-Y', axis_up='Z', apply_unit_scale=True,
        bake_anim=False, add_leaf_bones=False, mesh_smooth_type='FACE')
    slots = []
    for i, s in enumerate(o.material_slots):
        m = s.material
        if m is wood: slots.append({'name': 'M_GS_Wood', 'slot': i, 'textures': textures})
        else:
            p = m.node_tree.nodes['Principled BSDF']
            slots.append({'name': m.name, 'slot': i, 'textures': {}, 'constants': {
                'base': list(p.inputs['Base Color'].default_value)[:3],
                'rough': p.inputs['Roughness'].default_value, 'metal': p.inputs['Metallic'].default_value}})
    o.hide_set(True)
    return {'slug': 'haedam_gosiwon', 'mesh': name, 'materials': slots,
            'dimensions_cm': [round(d * 100, 1) for d in o.dimensions]}

W, H, T = .78, 2.0, .04          # door leaf; opening is 0.80 x 2.02
items = []
# Corridor face is -Y. Hardware heights follow common Korean residential doors.
items.append(export('SM_GS_Door', [
    box((W, T, H), (W / 2, 0, H / 2 + .005), wood),
    box((W - .12, .004, .5), (W / 2, -T / 2, 1.55), wood, 0),          # raised lower/upper panel lines
    box((W - .12, .004, .7), (W / 2, -T / 2, .5), wood, 0),
    box((.07, .03, .27), (W - .08, -T / 2 - .015, 1.0), black),       # digital doorlock (corridor)
    box((.05, .006, .07), (W - .08, -T / 2 - .031, 1.06), constant('M_GS_Keypad', (.05, .08, .07), .2, 0), 0),
    box((.06, .03, .2), (W - .08, T / 2 + .015, 1.0), white),         # inner lock body (room)
    *[box((.14, .02, .022), (W - .13, s * (T / 2 + .045), .9), steel) for s in (-1, 1)],  # levers
    *[cyl(.012, .045, (W - .08, s * (T / 2 + .022), .9), steel) for s in (-1, 1)],
    cyl(.009, T + .01, (W / 2, 0, 1.52), steel),                       # peephole
    box((.14, .004, .06), (W / 2, -T / 2 - .002, 1.68), steel),        # room number plate
    *[box((.012, T + .006, .1), (0, 0, z), steel) for z in (.25, 1.0, 1.75)],   # hinges
    box((.3, .045, .05), (.25, T / 2 + .025, H - .06), steel),          # door closer (room side)
]))
J, C, D = .035, .06, .12         # jamb thickness, casing width, wall depth
items.append(export('SM_GS_DoorFrame', [
    *[box((J, D, H + .02), (s * (.4 + J / 2), 0, (H + .02) / 2), wood) for s in (-1, 1)],
    box((.8 + 2 * J, D, J), (0, 0, H + .02 + J / 2), wood),
    *[box((C, .012, H + .02 + J + C), (s * (.4 + J + C / 2 - J), f * (D / 2 + .006), (H + .02 + J + C) / 2), wood)
      for s in (-1, 1) for f in (-1, 1)],
    *[box((.8 + 2 * C + 2 * J, .012, C), (0, f * (D / 2 + .006), H + .02 + J + C / 2), wood) for f in (-1, 1)],
    box((.8, D, .012), (0, 0, .006), steel),                            # threshold strip
]))
# Built-in desk with upper bookshelf (책상 + 상부장); back against -Y wall... front faces +Y.
DW, DD = 1.0, .5
items.append(export('SM_GS_Desk', [
    box((DW, DD, .03), (0, 0, .735), wood),
    *[box((.02, DD, .72), (s * (DW / 2 - .01), 0, .36), wood) for s in (-1, 1)],
    box((.4, DD - .02, .72), (DW / 2 - .22, 0, .36), wood),           # drawer pedestal
    *[box((.37, .006, .2), (DW / 2 - .22, DD / 2 - .002, z), wood) for z in (.15, .38, .6)],
    *[box((.1, .015, .015), (DW / 2 - .22, DD / 2 + .01, z + .06), steel) for z in (.15, .38, .6)],
    box((DW, .02, .55), (0, -DD / 2 + .01, 1.32), wood),               # hutch back
    *[box((.02, .3, .55), (s * (DW / 2 - .01), -DD / 2 + .15, 1.32), wood) for s in (-1, 1)],
    *[box((DW, .3, .02), (0, -DD / 2 + .15, z), wood) for z in (1.05, 1.32, 1.59)],
    box((DW - .04, .015, .02), (0, -DD / 2 + .3, 1.05), white),        # under-shelf light strip
]))
items.append(export('SM_GS_WallShelf', [
    box((.9, .25, .02), (0, 0, .01), wood),
    *[box((.02, .2, .12), (s * .4, -.02, -.06), steel) for s in (-1, 1)],
]))
items.append(export('SM_GS_AirCon', [
    box((.8, .2, .28), (0, 0, .14), white, .02),
    box((.72, .01, .03), (0, .1, .04), constant('M_GS_Vent', (.15, .15, .15), .6, 0), 0),
    box((.08, .006, .015), (.32, .102, .22), constant('M_GS_Led', (.1, .5, .2), .3, 0), 0),
]))
# Demo investigation props. Wall-mounted ones are centred (placed by centre point);
# small pickups are grounded by the game, so their origin does not matter.
grey = constant('M_GS_PaintedSteel', (.42, .44, .43), .55, .6)
paper = constant('M_GS_Paper', (.85, .82, .7), .8, 0)
tape = constant('M_GS_Tape', (.8, .72, .35), .6, 0)
yellow = constant('M_GS_Warning', (.85, .65, .05), .5, 0)
def tilt(o, deg):
    o.rotation_euler[1] = deg * 3.14159 / 180; bpy.ops.object.transform_apply(rotation=True); return o
items.append(export('SM_GS_Breaker', [
    box((.42, .07, .58), (0, .005, 0), grey, .006),
    box((.39, .012, .54), (0, -.036, 0), grey, .003),                    # door
    box((.03, .02, .07), (.16, -.05, 0), black),                          # latch
    box((.12, .002, .1), (0, -.043, .17), yellow, 0),                     # warning sticker
    box((.16, .002, .05), (0, -.043, -.18), paper, 0),                    # circuit card
]))
items.append(export('SM_GS_Hatch', [
    box((.48, .03, .68), (0, .01, 0), grey, .004),
    *[cyl(.008, .01, (x, -.008, z), steel) for x in (-.2, .2) for z in (-.3, .3)],
    tilt(box((.72, .004, .05), (0, -.008, 0), tape, 0), 54),             # crossed seal tape
    tilt(box((.72, .004, .05), (0, -.009, 0), tape, 0), -54),
    box((.14, .003, .05), (0, -.011, .22), paper, 0),                     # dated seal slip
]))
navy = constant('M_GS_BinderCover', (.05, .08, .16), .6, 0)
items.append(export('SM_GS_Binder', [
    *[box((.26, .006, .19), (0, y, 0), navy, .002) for y in (-.017, .017)],
    box((.255, .028, .185), (0, 0, 0), paper, 0),
    box((.012, .04, .19), (-.13, 0, 0), navy, .002),                      # spine
    box((.08, .002, .04), (.04, -.021, .04), paper, 0),                   # label
]))
items.append(export('SM_GS_Fuse', [
    cyl(.018, .1, (0, 0, 0), constant('M_GS_Ceramic', (.82, .8, .74), .4, 0), 'X'),
    *[cyl(.02, .03, (x, 0, 0), steel, 'X') for x in (-.06, .06)],
]))
items.append(export('SM_GS_KeyTag', [
    box((.12, .045, .012), (0, 0, 0), constant('M_GS_RedPlastic', (.45, .04, .03), .45, 0), .01),
    box((.04, .02, .002), (0, 0, .007), paper, 0),                        # faded number sticker
    cyl(.018, .004, (.08, 0, 0), steel, 'Z'),                             # ring
]))
# Open complaint logbook lying on the office desk: two pages either side of the spine.
green = constant('M_GS_LogCover', (.06, .12, .08), .7, 0)
rule = constant('M_GS_RuleLine', (.45, .5, .6), .8, 0)
items.append(export('SM_GS_Logbook', [
    box((.31, .225, .004), (0, 0, .002), green, .001),
    *[box((.145, .21, .008), (s * .076, 0, .008), paper, .001) for s in (-1, 1)],
    *[box((.13, .0012, .0006), (s * .076, y, .0123), rule, 0) for s in (-1, 1) for y in [-.08 + .02 * k for k in range(9)]],
    box((.006, .215, .006), (0, 0, .011), green, 0),                     # spine gutter
]))
(OUT / 'door_import.json').write_text(json.dumps(items, indent=2), encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'haedam_gosiwon.blend'))
print('GOSIWON_OK', [i['mesh'] for i in items])
