"""Original residential furnishings for Haedam, Blender mesh sources."""
from pathlib import Path
exec(compile((Path(__file__).parent/'create_assets.py').read_text(encoding='utf-8').split('phone=export')[0], 'helpers', 'exec'))
white=mat('Appliance enamel',(.66,.66,.60)); dark=mat('Appliance glass',(.015,.022,.025)); linen=mat('Faded bedding',(.21,.27,.24)); cream=mat('Mattress fabric',(.57,.53,.43))
fridge=export('SM_Fridge',[
 box('Cabinet',(0,0,.9),(.68,.70,1.8),white),box('Freezer',(0,-.362,1.52),(.65,.035,.49),white),box('Door',(0,-.362,.66),(.65,.035,1.18),white),
 *[box('Handle',(.24,-.405,z),(.025,.035,.24),metal) for z in [.91,1.39]],
 box('Gasket',(0,-.383,1.25),(.65,.006,.015),dark),box('Foot grille',(0,-.37,.075),(.6,.015,.1),metal)])
microwave=export('SM_Microwave',[
 box('Body',(0,0,.16),(.52,.40,.32),white),box('Glass',(-.055,-.208,.17),(.34,.016,.22),dark),box('Control panel',(.197,-.213,.17),(.07,.01,.22),plastic),
 *[box('Button',(.20,-.225,z),(.03,.01,.025),metal) for z in [.08,.13,.18]],box('Display',(.197,-.224,.25),(.055,.008,.025),linen)])
counter=export('SM_KitchenCounter',[
 box('Worktop',(0,0,.86),(2.4,.65,.06),cream),box('Carcass',(0,0,.41),(2.35,.6,.82),white),
 *[box('Cupboard',(x,-.31,.44),(.57,.025,.7),plastic) for x in [-.9,-.3,.3,.9]],
 *[box('Pull',(x,-.34,.68),(.12,.025,.018),metal) for x in [-.9,-.3,.3,.9]]])
table=export('SM_DiningTable',[box('Top',(0,0,.735),(1.4,.8,.05),wood),*[box('Leg',(x,y,.36),(.045,.045,.72),metal) for x in [-.62,.62] for y in [-.32,.32]]])
bed=export('SM_Bed',[box('Frame',(0,0,.24),(.95,1.95,.30),wood),box('Mattress',(0,0,.44),(.90,1.90,.16),cream),box('Blanket',(0,-.25,.54),(.88,1.35,.035),linen),box('Pillow',(0,.64,.57),(.6,.4,.12),cream)])
sink=export('SM_Sink',[box('Top',(0,0,.84),(1.5,.55,.07),white),box('Cabinet',(0,0,.40),(1.45,.5,.80),plastic),box('Basin',(0,-.03,.885),(.6,.38,.025),metal),box('Tap stem',(0,.19,1),(.025,.025,.23),metal),box('Tap spout',(0,.10,1.10),(.025,.20,.025),metal)])
locker=export('SM_Locker',[box('Body',(0,0,.9),(.45,.45,1.8),plastic),box('Door',(0,-.234,.92),(.42,.02,1.74),metal),*[box('Vent',(0,-.25,1.55+i*.035),(.28,.006,.012),dark) for i in range(4)],box('Handle',(.15,-.26,.9),(.018,.03,.14),cream)])
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'haedam_furnishings.blend'))
