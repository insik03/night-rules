"""Compatibility entry point: generate the current single-corridor review plans."""
from pathlib import Path
import runpy

if __name__ == '__main__':
    runpy.run_path(str(Path(__file__).with_name('create_single_corridor_plan.py')), run_name='__main__')
