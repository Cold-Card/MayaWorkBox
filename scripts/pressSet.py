import maya.cmds as cmds

def build_connection_logic(source_0, source_1, target):
    """
    Auto-generated logic network
    Sources: press_up_01_loc, press_ground_01
    Targets: press_01
    
    Args:
        source_0: 驱动端节点 1 (原: press_up_01_loc)
        source_1: 驱动端节点 2 (原: press_ground_01)
        target: 被驱动端节点 (原: press_01)
    """
    cmds.undoInfo(openChunk=True)
    try:
        # 1. Create Intermediate Nodes
        weight_multiplyDivide = cmds.createNode('multiplyDivide', name=f'{target}_weight_multiplyDivide')
        weight_reverse = cmds.createNode('reverse', name=f'{target}_weight_reverse')
        dis_floatMath = cmds.createNode('floatMath', name=f'{target}_dis_floatMath')
        dis_multDL = cmds.createNode('multDL', name=f'{target}_dis_multDL')
        weight_multDL = cmds.createNode('multDL', name=f'{target}_weight_multDL')
        dis_plusMinusAverage = cmds.createNode('plusMinusAverage', name=f'{target}_dis_plusMinusAverage')
        up_decomposeMatrix = cmds.createNode('decomposeMatrix', name=f'{target}_up_decomposeMatrix')
        ground_decomposeMatrix = cmds.createNode('decomposeMatrix', name=f'{target}_ground_decomposeMatrix')
        weight_addDL = cmds.createNode('addDL', name=f'{target}_weight_addDL')
        scale_clamp = cmds.createNode('clamp', name=f'{target}_scale_clamp')

        # 2. Set Attributes (Skip Default Values)
        cmds.setAttr(f'{weight_multiplyDivide}.input2Z', 1.0)
        cmds.setAttr(f'{weight_multiplyDivide}.input1Y', 0.0)
        cmds.setAttr(f'{weight_multiplyDivide}.input1Z', 0.0)
        cmds.setAttr(f'{weight_multiplyDivide}.operation', 2)
        cmds.setAttr(f'{weight_multiplyDivide}.input2X', 16.0)
        cmds.setAttr(f'{weight_multiplyDivide}.input2Y', 1.0)
        cmds.setAttr(f'{weight_reverse}.inputY', 0.0)
        cmds.setAttr(f'{weight_reverse}.inputZ', 0.0)
        cmds.setAttr(f'{dis_floatMath}.operation', 5)
        cmds.setAttr(f'{dis_multDL}.input2', -1.0)
        cmds.setAttr(f'{dis_plusMinusAverage}.operation', 2)
        cmds.setAttr(f'{up_decomposeMatrix}.inputRotateOrder', 0)
        cmds.setAttr(f'{ground_decomposeMatrix}.inputRotateOrder', 0)
        cmds.setAttr(f'{weight_addDL}.input2', 1.0)
        cmds.setAttr(f'{scale_clamp}.inputB', 0.0)
        cmds.setAttr(f'{scale_clamp}.minG', 0.0)
        cmds.setAttr(f'{scale_clamp}.renderPassMode', 1)
        cmds.setAttr(f'{scale_clamp}.maxG', 0.0)
        cmds.setAttr(f'{scale_clamp}.minB', 0.0)
        cmds.setAttr(f'{scale_clamp}.maxB', 0.0)
        cmds.setAttr(f'{scale_clamp}.inputG', 0.0)

        # 3. Connect Attributes (Including Message Type)
        cmds.connectAttr(f'{source_0}.mult', f'{weight_multDL}.input2', force=True)
        cmds.connectAttr(f'{source_0}.worldMatrix', f'{up_decomposeMatrix}.inputMatrix', force=True)
        cmds.connectAttr(f'{source_0}.min', f'{scale_clamp}.minR', force=True)
        cmds.connectAttr(f'{source_0}.max', f'{scale_clamp}.maxR', force=True)
        cmds.connectAttr(f'{source_1}.worldMatrix', f'{ground_decomposeMatrix}.inputMatrix', force=True)
        cmds.connectAttr(f'{weight_multiplyDivide}.outputX', f'{weight_reverse}.inputX', force=True)
        cmds.connectAttr(f'{weight_reverse}.outputX', f'{weight_multDL}.input1', force=True)
        cmds.connectAttr(f'{dis_floatMath}.outFloat', f'{weight_multiplyDivide}.input1X', force=True)
        cmds.connectAttr(f'{dis_multDL}.output', f'{dis_floatMath}.floatB', force=True)
        cmds.connectAttr(f'{weight_multDL}.output', f'{weight_addDL}.input1', force=True)
        cmds.connectAttr(f'{dis_plusMinusAverage}.output1D', f'{dis_multDL}.input1', force=True)
        cmds.connectAttr(f'{dis_plusMinusAverage}.output1D', f'{dis_floatMath}.floatA', force=True)
        cmds.connectAttr(f'{up_decomposeMatrix}.outputTranslateY', f'{dis_plusMinusAverage}.input1D[0]', force=True)
        cmds.connectAttr(f'{ground_decomposeMatrix}.outputTranslateY', f'{dis_plusMinusAverage}.input1D[1]', force=True)
        cmds.connectAttr(f'{weight_addDL}.output', f'{scale_clamp}.inputR', force=True)
        cmds.connectAttr(f'{scale_clamp}.outputR', f'{target}.scaleZ', force=True)

        print(f'Success: Logic connected (2 sources -> 1 targets)')
    finally:
        cmds.undoInfo(closeChunk=True)

up_list = cmds.ls(sl=True)
ground_list = cmds.ls(sl=True)
press_list = cmds.ls(sl=True)
for up, ground, press in zip(up_list, ground_list, press_list):
    build_connection_logic(up, ground, press)


######################################

import maya.cmds as cmds

def build_connection_logic(source, target):
    """
    Auto-generated logic network
    Sources: press_05_weight_reverse
    Targets: press_fix_05
    
    Args:
        source: 驱动端节点 (原: press_05_weight_reverse)
        target: 被驱动端节点 (原: press_fix_05)
    """
    cmds.undoInfo(openChunk=True)
    try:
        # 1. Create Intermediate Nodes
        fix_multDL = cmds.createNode('multDL', name=f'{target}_multDL')
        fix_clamp = cmds.createNode('clamp', name=f'{target}_clamp')

        # 2. Set Attributes (Skip Default Values)
        cmds.setAttr(f'{fix_multDL}.input2', -15.0)
        cmds.setAttr(f'{fix_clamp}.maxB', 0.0)
        cmds.setAttr(f'{fix_clamp}.renderPassMode', 1)
        cmds.setAttr(f'{fix_clamp}.minB', 0.0)
        cmds.setAttr(f'{fix_clamp}.minG', 0.0)
        cmds.setAttr(f'{fix_clamp}.maxG', 0.0)
        cmds.setAttr(f'{fix_clamp}.inputB', 0.0)
        cmds.setAttr(f'{fix_clamp}.minR', -5.0)
        cmds.setAttr(f'{fix_clamp}.maxR', 0.0)
        cmds.setAttr(f'{fix_clamp}.inputG', 0.0)

        # 3. Connect Attributes (Including Message Type)
        cmds.connectAttr(f'{source}.outputX', f'{fix_multDL}.input1', force=True)
        cmds.connectAttr(f'{fix_multDL}.output', f'{fix_clamp}.inputR', force=True)
        cmds.connectAttr(f'{fix_clamp}.outputR', f'{target}.translateY', force=True)

        print(f'Success: Logic connected from {source} to {target}')
    finally:
        cmds.undoInfo(closeChunk=True)

weight_reverse_list = cmds.ls(sl=True)
fix_jnt_list = cmds.ls(sl=True)
for weight_reverse, fix_jnt in zip(weight_reverse_list, fix_jnt_list):
    build_connection_logic(weight_reverse, fix_jnt)