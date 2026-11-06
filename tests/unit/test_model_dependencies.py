"""Optional explanation packages must not prevent importing model utilities."""
import subprocess
import sys


def test_model_interpreter_import_without_explanation_packages():
    script = '''
import builtins
original_import = builtins.__import__
def import_without_explanation(name, *args, **kwargs):
    if name.split('.')[0] in {'shap', 'lime'}:
        raise ModuleNotFoundError(name)
    return original_import(name, *args, **kwargs)
builtins.__import__ = import_without_explanation
from src.core.model.model_interpreter import ModelInterpreter
ModelInterpreter(object(), feature_names=['feature'])
'''
    result = subprocess.run([sys.executable, '-c', script], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
