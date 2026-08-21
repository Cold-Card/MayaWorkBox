import maya.cmds as cmds

def spaceSwitch(value=0):
    ctrl = cmds.ls(sl=True)
    if not ctrl:
        cmds.warning('请先选择一个控制器')
        return
    else:
        ctrl = list(ctrl)[0]
    attrName = cmds.channelBox('mainChannelBox',q=True,sma=True)
    if not attrName:
        cmds.warning('请在通道盒中选中要空间切换的属性')
        return
    else:
        attrName = list(attrName)[0]
    spaceAttr = '{}.{}'.format(ctrl, attrName)
    pos = cmds.xform(ctrl, q=True, t=True, ws=True)
    ori = cmds.xform(ctrl, q=True, ro=True, ws=True)
    
    if value not in ['min', 'max']:
        if isinstance(value, (int, float)):
            cmds.setAttr(spaceAttr, value)
        else:
            cmds.warning('请输入有效的数值或 "min"/"max"')
            return
    else:
        if value == 'min':
            has_min = cmds.attributeQuery(attrName, node=ctrl, minExists=True)
            if has_min:
                min_val = cmds.attributeQuery(attrName, node=ctrl, min=True)[0]
                print(f'最小值: {min_val}')
                cmds.setAttr(spaceAttr, min_val)
            else:
                cmds.warning('未设置最小值')
        elif value == 'max':
            has_max = cmds.attributeQuery(attrName, node=ctrl, maxExists=True)
            if has_max:
                max_val = cmds.attributeQuery(attrName, node=ctrl, max=True)[0]
                print(f'最大值: {max_val}')
                cmds.setAttr(spaceAttr, max_val)
            else:
                cmds.warning('未设置最大值')
    
    cmds.xform(ctrl, t=pos, ro=ori, ws=True)

if __name__ == "__main__":
    spaceSwitch(value='min')