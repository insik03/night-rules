"""Import only the new foley and chair animations; leave voices and existing meshes intact."""
from pathlib import Path
import unreal
R=Path(__file__).resolve().parents[1]; assets=unreal.AssetToolsHelpers.get_asset_tools()
for p in sorted((R/'Art/Footsteps/Processed').glob('*.wav')):
    t=unreal.AssetImportTask();t.filename=str(p);t.destination_path='/Game/Audio/Footsteps';t.automated=True;t.replace_existing=True;t.save=True
    assets.import_asset_tasks([t]);a=unreal.load_asset('/Game/Audio/Footsteps/'+p.stem)
    if not a:raise RuntimeError('Missing sound '+p.stem)
    a.set_editor_property('looping',False);unreal.EditorAssetLibrary.save_loaded_asset(a)
dest='/Game/PrototypeAssets/GhostMeshy';mesh=unreal.load_asset(dest+'/SK_SmilingCaretaker')
for name in ('A_CaretakerChairRun','A_CaretakerChairKill'):
    t=unreal.AssetImportTask();t.filename=str(R/'Art/GhostMeshy/Approved/Unreal'/(name+'.fbx'));t.destination_path=dest;t.destination_name=name;t.automated=True;t.replace_existing=True;t.save=True
    o=unreal.FbxImportUI();o.automated_import_should_detect_type=False;o.mesh_type_to_import=unreal.FBXImportType.FBXIT_ANIMATION;o.import_mesh=False;o.import_animations=True;o.import_materials=False;o.import_textures=False;o.skeleton=mesh.get_editor_property('skeleton');o.override_animation_name=name;t.options=o
    assets.import_asset_tasks([t]);a=unreal.load_asset(dest+'/'+name)
    if not isinstance(a,unreal.AnimSequence):raise RuntimeError('Missing animation '+name)
unreal.log('FOOTSTEP_IMPORT_COMPLETE clips=11 animations=2')
