import maya.cmds as cmds
objs = cmds.ls(sl=True)
attr_date = {}
for obj in objs:
    attrNames = cmds.channelBox('mainChannelBox',q=True,sma=True)
    value = cmds.getAttr('{}.{}'.format(obj,attrNames[0]))
    attr_date[obj] = value

Bs = cmds.ls(sl=True)
for obj in attr_date.keys():
    attrNames = cmds.channelBox('mainChannelBox',q=True,sma=True)
    cmds.setAttr('{}.{}'.format(Bs[0],attrNames[0]),attr_date[obj])