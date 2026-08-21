import pymel.core as pm

oldJnts = pm.ls(sl=True)
#newJnts = pm.ls(sl=True)
for i, oldJnt in enumerate(oldJnts):
    newJnt = oldJnt.split(':')[-1]
    if pm.objExists(newJnt):
        newJnt = pm.PyNode(newJnt)
        multMatrixs = pm.listConnections(oldJnt+'.worldMatrix[0]',s=False,d=True,p=True)
        if multMatrixs:
            for multMatrix in multMatrixs:
                newJnt.worldMatrix[0] >> multMatrix
        
        

jnts = pm.ls(sl=True)
for jnt in jnts:
    corrective_jnt = jnt.name()[:-9]
    bodyJnt = corrective_jnt.split(':')[-1]
    if pm.objExists(bodyJnt):
        print(bodyJnt)
        pm.parent(jnt,bodyJnt)
        zero_grp = pm.PyNode(corrective_jnt+'_ib_zero_grp')
        for i in ['tx','ty','tz','rx','ry','rz']:
            zero_grp.attr(i).unlock()
        pm.matchTransform(zero_grp, bodyJnt, pos=True, rot=True)
        if bodyJnt[-2:] == '_R':
            attr_val = pm.getAttr(zero_grp+'.rotate')
            zero_grp.r.set([(attr_val[0]*-1),(attr_val[1]*-1),(attr_val[2]+180)])
        for i in ['tx','ty','tz','rx','ry','rz']:
            zero_grp.attr(i).lock()
            
            

# 导出
import maya.cmds as cmds

def break_offset_parent_matrix_connections(direction="both"):
    """
    断开选中骨骼的Offset Parent Matrix属性的连接
    
    参数:
        direction: 连接方向 ("input", "output", 或 "both")
    """
    selected_bones = cmds.ls(selection=True, type='joint')
    
    if not selected_bones:
        cmds.warning("请先选择一些骨骼关节")
        return
    
    for bone in selected_bones:
        offset_attr = f"{bone}.offsetParentMatrix"
        
        if not cmds.objExists(offset_attr):
            continue
        
        # 根据方向获取连接
        if direction in ["both", "input"]:
            # 获取输入连接 (其他属性连接到offsetParentMatrix)
            inputs = cmds.listConnections(
                offset_attr, 
                source=True, 
                destination=False, 
                plugs=True
            )
            
            if inputs:
                for input_attr in inputs:
                    try:
                        # 获取连接到offsetParentMatrix的目标属性
                        dest_attrs = cmds.connectionInfo(input_attr, destinationFromSource=True)
                        for dest_attr in dest_attrs:
                            if dest_attr == offset_attr:
                                cmds.disconnectAttr(input_attr, dest_attr)
                                print(f"已断开输入连接: {input_attr} -> {dest_attr}")
                    except Exception as e:
                        cmds.warning(f"无法断开输入连接: {str(e)}")
        
        if direction in ["both", "output"]:
            # 获取输出连接 (offsetParentMatrix连接到其他属性)
            outputs = cmds.listConnections(
                offset_attr, 
                source=False, 
                destination=True, 
                plugs=True
            )
            
            if outputs:
                for output_attr in outputs:
                    try:
                        # 获取连接到offsetParentMatrix的源属性
                        src_attrs = cmds.connectionInfo(output_attr, sourceFromDestination=True)
                        for src_attr in src_attrs:
                            if src_attr == offset_attr:
                                cmds.disconnectAttr(src_attr, output_attr)
                                print(f"已断开输出连接: {src_attr} -> {output_attr}")
                    except Exception as e:
                        cmds.warning(f"无法断开输出连接: {str(e)}")

# 使用示例 - 只断开输入连接
break_offset_parent_matrix_connections(direction="input")