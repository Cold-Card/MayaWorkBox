import sys
current_version = int("{0}{1}".format(sys.version_info[0], sys.version_info[1]))
if current_version == 27:
    from .__hybrid__.filter_widget27 import *
if current_version == 37:
    from .__hybrid__.filter_widget37 import *
if current_version == 39:
    from .__hybrid__.filter_widget39 import *
if current_version == 310:
    from .__hybrid__.filter_widget310 import *
if current_version == 311:
    from .__hybrid__.filter_widget311 import *
