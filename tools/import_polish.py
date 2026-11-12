"""Import the final DAY1 voice set, calibrated SFX and a separate run clip."""
from pathlib import Path
import json,unreal
R=Path(__file__).resolve().parents[1];assets=unreal.AssetToolsHelpers.get_asset_tools()
sequences=json.loads((R/'NightRulesPrototype/Content/Data/voices.json').read_text(encoding='utf-8'))
approved={row['asset'] for rows in sequences.values() for row in rows if row['asset']}
# Compare physical packages too: startup registry discovery may be incomplete.
voice_folder=R/'NightRulesPrototype/Content/Audio/Voice/Day1'
for package in voice_folder.glob('vo_*.uasset'):
 if package.stem not in approved:
  asset_path='/Game/Audio/Voice/Day1/'+package.stem
  if not unreal.EditorAssetLibrary.delete_asset(asset_path) or package.exists():
   raise RuntimeError('Unused narration package needs removal before import: '+str(package))

tasks=[]
for p in sorted((R/'Art/Voice/Day1').glob('*.wav')):
 t=unreal.AssetImportTask();t.filename=str(p);t.destination_path='/Game/Audio/Voice/Day1';t.automated=True;t.replace_existing=True;t.save=True;tasks.append(t)
for row in json.loads((R/'Art/AudioBalanced/manifest.json').read_text()):
 t=unreal.AssetImportTask();t.filename=str(R/'Art/AudioBalanced'/(row['name']+'.wav'));t.destination_path='/Game/Audio';t.automated=True;t.replace_existing=True;t.save=True;tasks.append(t)
assets.import_asset_tasks(tasks)
for t in tasks:
 if not t.imported_object_paths:raise RuntimeError('Audio import failed '+t.filename)
for row in json.loads((R/'Art/AudioBalanced/manifest.json').read_text()):
 a=unreal.load_asset('/Game/Audio/'+row['name']);a.set_editor_property('looping',row['loop']);unreal.EditorAssetLibrary.save_loaded_asset(a)
dest='/Game/PrototypeAssets/Ghost'
mesh=unreal.load_asset(dest+'/SK_ErasedGhost')
t=unreal.AssetImportTask();t.filename=str(R/'Art/Ghost/A_GhostRun.fbx');t.destination_path=dest;t.destination_name='A_GhostRun';t.automated=True;t.replace_existing=True;t.save=True
opts=unreal.FbxImportUI();opts.automated_import_should_detect_type=False;opts.mesh_type_to_import=unreal.FBXImportType.FBXIT_ANIMATION;opts.import_mesh=False;opts.import_animations=True;opts.skeleton=mesh.get_editor_property('skeleton');opts.override_animation_name='A_GhostRun'
t.options=opts;assets.import_asset_tasks([t])
if not unreal.EditorAssetLibrary.does_asset_exist(dest+'/A_GhostRun'):raise RuntimeError('Run clip missing: '+str(t.imported_object_paths))
remaining={p.stem for p in (R/'NightRulesPrototype/Content/Audio/Voice/Day1').glob('*.uasset')}
if remaining!=approved:raise RuntimeError('Unused voice assets remain: '+str(remaining-approved))
unreal.log('POLISH_IMPORT_COMPLETE clips='+str(len(tasks)))
