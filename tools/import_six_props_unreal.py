"""Rejected six-prop import, retained for audit only."""
raise SystemExit('DISABLED: these prepared assets were rejected and must not be imported.')
from pathlib import Path
import os,runpy,unreal
root=Path(__file__).resolve().parents[1]
os.environ['NR_PROP_IMPORT_DIR']=str(root/'Art/GeneratedProps/six-v1/Unreal')
os.environ['NR_PROP_IMPORT_DEST']='/Game/PrototypeAssets/GeneratedProps'
os.environ.pop('NR_CORE_ONLY',None)
runpy.run_path(str(root/'tools/import_core_props_unreal.py'),run_name='__main__')
unreal.log('SIX_PROPS_IMPORT_COMPLETE')
