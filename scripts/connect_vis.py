import maya.cmds as cmds
import pymel.core as pm
def addAttr(nodeName,attrName,k=True,cb=True):
    nodeName = pm.PyNode(nodeName)
    if not nodeName.hasAttr(attrName):
        nodeName.addAttr(attrName,at='bool')
        nodeName.attr(attrName).set(k=k,channelBox=cb)
    return nodeName.attr(attrName)

sels = cmds.ls(sl=True)
vis = 'visibility_ctrl'

###
addAttr(vis,'faceSecCtrlVis')
cmds.connectAttr(vis + '.faceCtrlVis', 'facial_grp.visibility',f=True)
pairs = [
    ('{}.faceSecCtrlVis'.format(vis), 'L_UpCheek_A_ctrl.upCheekSec'),
    ('{}.faceSecCtrlVis'.format(vis), 'L_Cheek_A_ctrl.cheekSec'),
    ('{}.faceSecCtrlVis'.format(vis), 'R_UpCheek_A_ctrl.upCheekSec'),
    ('{}.faceSecCtrlVis'.format(vis), 'R_Eyeball_A_ctrl.eyelidSec'),
    ('{}.faceSecCtrlVis'.format(vis), 'R_Eyeball_A_ctrl.ringSec'),
    ('{}.faceSecCtrlVis'.format(vis), 'R_Brow_A_ctrl.browSec'),
    ('{}.faceSecCtrlVis'.format(vis), 'L_Brow_A_ctrl.browSec'),
    ('{}.faceSecCtrlVis'.format(vis), 'R_Cheek_A_ctrl.cheekSec'),
    ('{}.faceSecCtrlVis'.format(vis), 'M_Mouth_A_ctrl.mouthSec'),
    ('{}.faceSecCtrlVis'.format(vis), 'L_Eyeball_A_ctrl.eyelidSec'),
    ('{}.faceSecCtrlVis'.format(vis), 'L_Eyeball_A_ctrl.ringSec'),
]
for src, dst in pairs:
    cmds.connectAttr(src, dst, force=True)
addAttr(vis,'faceTweakCtrlVis')
cmds.connectAttr(vis + '.faceTweakCtrlVis', 'M_Head_base_secCtrl_Group.visibility',f=True)

###
addAttr(vis,'faceSecCtrlVis')
cmds.connectAttr(vis + '.faceCtrlVis', 'MD_Neck_01_Head_Ctrl_Grp.visibility',f=True)
cmds.connectAttr(vis + '.faceCtrlVis', 'Head_01_Grp.visibility',f=True)
cmds.connectAttr(vis + '.faceCtrlVis', 'Head_02_Grp.visibility',f=True)
pairs = [
    ('{}.faceSecCtrlVis'.format(vis), 'RT_Cheek_01_Master_01_Ctrl.ctrlVis'),
    ('{}.faceSecCtrlVis'.format(vis), 'LF_Brow_01_Master_Ctrl.ctrlVis'),
    ('{}.faceSecCtrlVis'.format(vis), 'RT_Brow_01_Master_Ctrl.ctrlVis'),
    ('{}.faceSecCtrlVis'.format(vis), 'RT_Cheek_01_Master_02_Ctrl.ctrlVis'),
    ('{}.faceSecCtrlVis'.format(vis), 'LF_Cheek_01_Master_02_Ctrl.ctrlVis'),
    ('{}.faceSecCtrlVis'.format(vis), 'LF_Cheek_01_Master_01_Ctrl.ctrlVis'),
    ('{}.faceSecCtrlVis'.format(vis), 'MD_Mouth_01_Master_Ctrl.tweakCtrlVis'),
    ('{}.faceSecCtrlVis'.format(vis), 'LF_Eye_01_Master_Ctrl.tweakCtrlVis'),
    ('{}.faceSecCtrlVis'.format(vis), 'RT_Eye_01_Master_Ctrl.tweakCtrlVis'),
]
for src, dst in pairs:
    cmds.connectAttr(src, dst, force=True)
    cmds.setAttr(dst,channelBox=True)




