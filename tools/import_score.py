"""Import the score into /Game/Audio/Score.

Default source is Art/Score (tools/create_score.py). Tracks listed in Art/ScoreSA3/selected.json
(user-picked Stable Audio 3 candidates, tools/generate_score_sa3.py) replace those files.
"""
import unreal, json
from pathlib import Path
art = Path(__file__).resolve().parents[1] / 'Art'
picked = json.loads((art / 'ScoreSA3' / 'selected.json').read_text(encoding='utf-8-sig')) if (art / 'ScoreSA3' / 'selected.json').exists() else {}
tools = unreal.AssetToolsHelpers.get_asset_tools()
for row in json.loads((art / 'Score' / 'manifest.json').read_text(encoding='utf-8')):
    name = row['name']
    t = unreal.AssetImportTask()
    t.filename = str(art / 'ScoreSA3' / picked[name]) if name in picked else str(art / 'Score' / (name + '.wav'))
    t.destination_path = '/Game/Audio/Score'; t.destination_name = name
    t.automated = True; t.replace_existing = True; t.save = True
    tools.import_asset_tasks([t])
    if not t.imported_object_paths: raise RuntimeError('Score import failed: ' + name)
    a = unreal.load_asset(t.imported_object_paths[0]); a.set_editor_property('looping', row['loop'])
    unreal.EditorAssetLibrary.save_loaded_asset(a, only_if_is_dirty=False)
    unreal.log_warning('SCORE_TRACK %s <- %s' % (name, Path(t.filename).name))
unreal.log_warning('SCORE_IMPORT_COMPLETE')
