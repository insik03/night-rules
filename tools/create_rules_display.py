"""Generate current story paper artwork, including the three rule states."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name("create_story_props.py")), run_name="__main__")
