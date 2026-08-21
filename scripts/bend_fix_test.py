import maya.cmds as cmds

def build_connection_logic(source_0, source_1, source_2, target):
    """
    Auto-generated logic network
    Sources: IK_ff_body_joint_19_pxy_fk_1_oft, IK_body_joint_19_ctl_fk_2_oft, locator1
    Targets: IK_body_joint_19_ctl_fk_3_oft
    
    Args:
        source_0: 驱动端节点 1 (原: IK_ff_body_joint_19_pxy_fk_1_oft)
        source_1: 驱动端节点 2 (原: IK_body_joint_19_ctl_fk_2_oft)
        source_2: 驱动端节点 3 (原: locator1)
        target: 被驱动端节点 (原: IK_body_joint_19_ctl_fk_3_oft)
    """
    cmds.undoInfo(openChunk=True)
    try:
        # 1. Create Intermediate Nodes
        addDL_var = cmds.createNode('addDL', name=f'{target}_addDL_gen')
        remapValue_var = cmds.createNode('remapValue', name=f'{target}_remapValue_gen')
        t_multiplyDivide_var = cmds.createNode('multiplyDivide', name=f'{target}_t_multiplyDivide_gen')
        r_multiplyDivide_var = cmds.createNode('multiplyDivide', name=f'{target}_r_multiplyDivide_gen')
        unitConversion_02_var = cmds.createNode('unitConversion', name=f'{target}_unitConversion_02_gen')
        unitConversion_01_var = cmds.createNode('unitConversion', name=f'{target}_unitConversion_01_gen')
        rz_unitConversion_var = cmds.createNode('unitConversion', name=f'{target}_rz_unitConversion_gen')
        rx_unitConversion_var = cmds.createNode('unitConversion', name=f'{target}_rx_unitConversion_gen')
        ry_unitConversion_var = cmds.createNode('unitConversion', name=f'{target}_ry_unitConversion_gen')

        # 2. Set Attributes (Skip Default Values)
        cmds.setAttr(f'{remapValue_var}.value[1].value_Position', 1.0)
        cmds.setAttr(f'{remapValue_var}.outputMin', 1.0)
        cmds.setAttr(f'{remapValue_var}.color[0].color_Interp', 1)
        cmds.setAttr(f'{remapValue_var}.outputMax', 0.0)
        cmds.setAttr(f'{remapValue_var}.value[0].value_Interp', 1)
        cmds.setAttr(f'{remapValue_var}.inputMin', 0.0)
        cmds.setAttr(f'{remapValue_var}.value[1].value_FloatValue', 1.0)
        cmds.setAttr(f'{remapValue_var}.value[1].value_Interp', 1)
        cmds.setAttr(f'{remapValue_var}.color[1].color_Position', 1.0)
        cmds.setAttr(f'{remapValue_var}.value[0].value_Position', 0.0)
        cmds.setAttr(f'{remapValue_var}.color[0].color_Position', 0.0)
        cmds.setAttr(f'{remapValue_var}.value[0].value_FloatValue', 0.0)
        cmds.setAttr(f'{remapValue_var}.color[0].color_Color', 0.0, 0.0, 0.0, type='float3')
        cmds.setAttr(f'{remapValue_var}.color[1].color_Color', 1.0, 1.0, 1.0, type='float3')
        cmds.setAttr(f'{remapValue_var}.color[1].color_Interp', 1)
        cmds.setAttr(f'{t_multiplyDivide_var}.operation', 1)
        cmds.setAttr(f'{r_multiplyDivide_var}.operation', 1)
        cmds.setAttr(f'{unitConversion_02_var}.conversionFactor', 57.29577951308232)
        cmds.setAttr(f'{unitConversion_01_var}.conversionFactor', 57.29577951308232)
        cmds.setAttr(f'{rz_unitConversion_var}.conversionFactor', 0.017453292519943295)
        cmds.setAttr(f'{rx_unitConversion_var}.conversionFactor', 0.017453292519943295)
        cmds.setAttr(f'{ry_unitConversion_var}.conversionFactor', 0.017453292519943295)

        # 3. Connect Attributes (Including Message Type)
        cmds.connectAttr(f'{source_0}.translate', f'{t_multiplyDivide_var}.input1', force=True)
        cmds.connectAttr(f'{source_0}.rotate', f'{unitConversion_02_var}.input', force=True)
        cmds.connectAttr(f'{source_1}.rotateZ', f'{unitConversion_01_var}.input', force=True)
        cmds.connectAttr(f'{source_2}.angle', f'{addDL_var}.input1', force=True)
        cmds.connectAttr(f'{source_2}.fix', f'{addDL_var}.input2', force=True)
        cmds.connectAttr(f'{addDL_var}.output', f'{remapValue_var}.inputMax', force=True)
        cmds.connectAttr(f'{remapValue_var}.outValue', f'{t_multiplyDivide_var}.input2Y', force=True)
        cmds.connectAttr(f'{remapValue_var}.outValue', f'{t_multiplyDivide_var}.input2X', force=True)
        cmds.connectAttr(f'{remapValue_var}.outValue', f'{t_multiplyDivide_var}.input2Z', force=True)
        cmds.connectAttr(f'{remapValue_var}.outValue', f'{r_multiplyDivide_var}.input2X', force=True)
        cmds.connectAttr(f'{remapValue_var}.outValue', f'{r_multiplyDivide_var}.input2Y', force=True)
        cmds.connectAttr(f'{remapValue_var}.outValue', f'{r_multiplyDivide_var}.input2Z', force=True)
        cmds.connectAttr(f'{t_multiplyDivide_var}.outputY', f'{target}.translateY', force=True)
        cmds.connectAttr(f'{t_multiplyDivide_var}.outputZ', f'{target}.translateZ', force=True)
        cmds.connectAttr(f'{t_multiplyDivide_var}.outputX', f'{target}.translateX', force=True)
        cmds.connectAttr(f'{r_multiplyDivide_var}.outputY', f'{ry_unitConversion_var}.input', force=True)
        cmds.connectAttr(f'{r_multiplyDivide_var}.outputZ', f'{rz_unitConversion_var}.input', force=True)
        cmds.connectAttr(f'{r_multiplyDivide_var}.outputX', f'{rx_unitConversion_var}.input', force=True)
        cmds.connectAttr(f'{unitConversion_02_var}.output', f'{r_multiplyDivide_var}.input1', force=True)
        cmds.connectAttr(f'{unitConversion_01_var}.output', f'{remapValue_var}.inputValue', force=True)
        cmds.connectAttr(f'{rz_unitConversion_var}.output', f'{target}.rotateZ', force=True)
        cmds.connectAttr(f'{rx_unitConversion_var}.output', f'{target}.rotateX', force=True)
        cmds.connectAttr(f'{ry_unitConversion_var}.output', f'{target}.rotateY', force=True)

        print(f'Success: Logic connected (3 sources -> 1 targets)')
    finally:
        cmds.undoInfo(closeChunk=True)
        
loc = 'locator1'
drivers=cmds.ls(sl=True)
drivens=cmds.ls(sl=True)
bends=cmds.ls(sl=True)
for i,driver in enumerate(drivers):
    build_connection_logic(driver,bends[i],loc,drivens[i])