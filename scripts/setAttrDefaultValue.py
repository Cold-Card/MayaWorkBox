import maya.cmds as cmds
objs = cmds.ls(sl=True)
defaultValue = 0
for obj in objs:
    attrNames = cmds.channelBox('mainChannelBox',q=True,sma=True)
    for attrName in attrNames:
        cmds.addAttr('{}.{}'.format(obj,attrName),e=True,dv=defaultValue)
        cmds.setAttr('{}.{}'.format(obj,attrName),defaultValue)
        print('Set {}.{} defaultValue: {}'.format(obj,attrName,defaultValue))