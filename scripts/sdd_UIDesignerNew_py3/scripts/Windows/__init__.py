__all__= ['window']
import importlib

for i in __all__:
    module = importlib.import_module('.'+i, __name__)
    globals()[i] = module