"""Import A_CaretakerCrawl (tools/prepare_meshy_crawl.py) onto the existing caretaker skeleton."""
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parents[1]
DEST = '/Game/PrototypeAssets/GhostMeshy'
mesh = unreal.load_asset(DEST + '/SK_SmilingCaretaker')
if not mesh: raise RuntimeError('Import the caretaker mesh first (import_meshy_ghost_unreal.py)')
o = unreal.FbxImportUI()
o.automated_import_should_detect_type = False; o.mesh_type_to_import = unreal.FBXImportType.FBXIT_ANIMATION
o.import_mesh = False; o.import_animations = True; o.import_materials = False; o.import_textures = False
o.skeleton = mesh.get_editor_property('skeleton'); o.override_animation_name = 'A_CaretakerCrawl'
t = unreal.AssetImportTask()
t.filename = str(ROOT / 'Art/GhostMeshy/Approved/Unreal/A_CaretakerCrawl.fbx'); t.destination_path = DEST
t.destination_name = 'A_CaretakerCrawl'; t.automated = True; t.replace_existing = True; t.save = True; t.options = o
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
clip = unreal.load_asset(DEST + '/A_CaretakerCrawl')
if not isinstance(clip, unreal.AnimSequence) or clip.get_editor_property('sequence_length') < 5:
    raise RuntimeError('Crawl clip import failed')
unreal.log_warning('CRAWL_IMPORT_COMPLETE length=%.2f' % clip.get_editor_property('sequence_length'))
