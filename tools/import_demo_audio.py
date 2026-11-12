import unreal, json
from pathlib import Path
root=Path(__file__).resolve().parents[1]/'Art'/'DemoAudio'
for row in json.loads((root/'manifest.json').read_text()):
    t=unreal.AssetImportTask(); t.filename=str(root/(row['name']+'.wav')); t.destination_path='/Game/Audio'
    t.automated=True; t.replace_existing=True; t.save=True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    if not t.imported_object_paths:raise RuntimeError('Audio import failed: '+row['name'])
    a=unreal.load_asset(t.imported_object_paths[0]); a.set_editor_property('looping',row['loop'])
    unreal.EditorAssetLibrary.save_loaded_asset(a,only_if_is_dirty=False)
unreal.log_warning('DEMO_AUDIO_IMPORT_COMPLETE')
