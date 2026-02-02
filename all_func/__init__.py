import importlib
import inspect
import os

__all__ = []
func_dict = {}

module_dir = os.path.dirname(__file__)

for filename in os.listdir(module_dir):
    if filename.endswith(".py") and filename not in ("__init__.py", "rotation.py"):
        module_name = filename[:-3]
        module = importlib.import_module(f".{module_name}", __name__)
        
        funcs = [obj for name, obj in inspect.getmembers(module, inspect.isfunction)
                 if inspect.getmodule(obj) == module]
        
        if len(funcs) == 1:
            func = funcs[0]
            globals()[func.__name__] = func
            __all__.append(func.__name__)
            func_dict[len(func_dict) + 1] = func
