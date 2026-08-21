import maya.cmds as cmds
import pymel.core as pm

def addAttr(nodeName,attrName,min_val=0,max_val=10,dv_val=0): 
        if not nodeName.hasAttr(attrName):
            nodeName.addAttr(attrName,at='double',min=min_val,max=max_val,dv=dv_val,k=1)
        return attrName

def createNode(nodeType,nodeName,editData={}):
    if not pm.objExists(nodeName):
        pm.createNode(nodeType,n=nodeName)
    nodeName = pm.PyNode(nodeName)
    for attrName, value in editData.items():
        if nodeName.hasAttr(attrName):
            try:
                nodeName.attr(attrName).set(value)
            except:
                continue
        else:
            print('{} 没有属性：{}'.format(nodeName,attrName))
    return nodeName

def build_connection_logic(target, index, same_coned_attr, speed_attr, width_attr, go_attr, delay_attr, addWidth_attr, widthRG_attr):
    """
    Args:
        target: 被驱动端节点
        index: 被驱动端节点索引
        same_coned_attr: 被控制物体需要被控制的属性（短名称）
        widthRG_attr: 每个控制器的幅度属性
        speed_attr: 主控制器的速度属性
        width_attr: 主控制器的整体幅度属性（振幅）
        go_attr: 主控制器的手动偏移属性（偏移）
        delay_attr: 主控制器的延迟属性（频率）
        addWidth_attr: 主控制器的局部幅度属性（幅度递减/递增属性）
    """

    # 1. Create Intermediate Nodes
    sin_PMA_01_var = createNode('plusMinusAverage', nodeName=f'{target}_sin_PMA_01')
    sin_MDL_01_var = createNode('multDL', nodeName=f'{target}_sin_MDL_01')
    sin_PMA_03_var = createNode('plusMinusAverage', nodeName=f'{target}_sin_PMA_03')
    sin_PMA_02_var = createNode('plusMinusAverage', nodeName=f'{target}_sin_PMA_02')
    sin_MDL_03_var = createNode('multDL', nodeName=f'{target}_sin_MDL_03')
    sin_multiplyDL_01_var = createNode('multiplyDL', nodeName=f'{target}_sin_multiplyDL_01')
    sin_MDL_02_var = createNode('multDL', nodeName=f'{target}_sin_MDL_02')
    sin_var = createNode('sin', nodeName=f'{target}_sin')

    # 2. Set Attributes (Skip Default Values)
    cmds.setAttr(f'{sin_MDL_03_var}.input1', index)
    cmds.setAttr(f'{sin_MDL_02_var}.input1', index)
    cmds.setAttr(f'{sin_PMA_03_var}.operation', 1)
    cmds.setAttr(f'{sin_PMA_03_var}.input1D[0]', 1.0)
    cmds.setAttr(f'{sin_PMA_02_var}.operation', 2)
    cmds.setAttr(f'{sin_PMA_01_var}.operation', 1)

    # 3. Connect Attributes (Including Message Type)
    cmds.connectAttr(f'time1.outTime', f'{sin_MDL_01_var}.input1', force=True)
    cmds.connectAttr(f'{sin_PMA_02_var}.output1D', f'{sin_var}.input', force=True)
    cmds.connectAttr(speed_attr, f'{sin_MDL_01_var}.input2', force=True)
    cmds.connectAttr(width_attr, f'{sin_multiplyDL_01_var}.input[1]', force=True)
    cmds.connectAttr(go_attr, f'{sin_PMA_01_var}.input1D[1]', force=True)
    cmds.connectAttr(delay_attr, f'{sin_MDL_02_var}.input2', force=True)
    cmds.connectAttr(addWidth_attr, f'{sin_MDL_03_var}.input2', force=True)
    cmds.connectAttr(f'{sin_PMA_03_var}.output1D', f'{sin_multiplyDL_01_var}.input[2]', force=True)
    cmds.connectAttr(f'{sin_MDL_03_var}.output', f'{sin_PMA_03_var}.input1D[1]', force=True)
    cmds.connectAttr(f'{sin_PMA_01_var}.output1D', f'{sin_PMA_02_var}.input1D[0]', force=True)
    cmds.connectAttr(f'{sin_MDL_02_var}.output', f'{sin_PMA_02_var}.input1D[1]', force=True)
    cmds.connectAttr(f'{sin_var}.output', f'{sin_multiplyDL_01_var}.input[0]', force=True)
    cmds.connectAttr(f'{sin_MDL_01_var}.output', f'{sin_PMA_01_var}.input1D[0]', force=True)
    cmds.connectAttr(widthRG_attr, f'{sin_multiplyDL_01_var}.input[3]', force=True)
    cmds.connectAttr(f'{sin_multiplyDL_01_var}.output', f'{target}.{same_coned_attr}', force=True)


def createSin(main_ctrl,coned_grp_lst,coned_ctrl_lst,same_coned_attr):
    speed_attr = f"{main_ctrl}.speed"
    go_attr = f"{main_ctrl}.go"
    width_attr = f"{main_ctrl}.width"
    delay_attr = f"{main_ctrl}.delay"
    addWidth_attr = f"{main_ctrl}.addWidth"
    for index in range(len(coned_grp_lst)):
        widthRG_attr = f'{coned_ctrl_lst[index]}.widthRG'
        build_connection_logic(coned_grp_lst[index], index, same_coned_attr, speed_attr, width_attr, go_attr, delay_attr, addWidth_attr, widthRG_attr)


if __name__ == '__main__':
    main_ctrl = 'Visibility_ctrl'
    same_coned_attr = 'tz'
    coned_grp_lst = cmds.ls(sl=True)
    coned_ctrl_lst = cmds.ls(sl=True)
    createSin(main_ctrl,coned_grp_lst,coned_ctrl_lst)