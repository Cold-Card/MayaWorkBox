import sys
current_version = int("{0}{1}".format(sys.version_info[0], sys.version_info[1]))
if current_version == 27:
    from .__hybrid__.context_menu27 import *
if current_version == 37:
    from .__hybrid__.context_menu37 import *
if current_version == 39:
    from .__hybrid__.context_menu39 import *
if current_version == 310:
    from .__hybrid__.context_menu310 import *
if current_version == 311:
    from .__hybrid__.context_menu311 import *
