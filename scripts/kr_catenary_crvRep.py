import pymel.core as pm

crv = pm.ls(sl=True)[0]
crv_shape = crv.getShape()

mms = pm.ls(sl=True)
l = 0
for i, mm in enumerate(mms):
    mm.outputTranslate >> crv_shape.controlPoints[i+9*l]