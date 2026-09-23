import maya.cmds as cmds

def ui():
    if cmds.window('setAttrDefaultWin', exists=True):
        cmds.deleteUI('setAttrDefaultWin')
    window = cmds.window('setAttrDefaultWin', title='设置属性默认值')
    cmds.columnLayout(adj=True)
    cmds.text(label='请先选择物体，并在通道盒中选中属性', align='center')
    cmds.separator(height=5)
    cmds.rowColumnLayout(nc=3, cw=[(1, 60), (2, 80), (3, 80)], columnAttach=[(1, 'both', 5), (2, 'both', 5), (3, 'both', 0)])
    cmds.text(label='默认值:')
    default_field = cmds.floatField('defaultField', value=0.0, precision=4)
    use_current_check = cmds.checkBox('使用当前值', value=False, 
                                       changeCommand=lambda v: cmds.floatField(default_field, e=True, enable=not v))
    cmds.setParent('..')
    cmds.separator(height=10)
    cmds.button(label='应用', command=lambda x: apply_defaults(default_field, use_current_check))
    cmds.showWindow(window)

def apply_defaults(default_field, use_current_check):
    use_current = cmds.checkBox(use_current_check, q=True, value=True)
    if not use_current:
        default_value = cmds.floatField(default_field, q=True, value=True)
    else:
        default_value = None  # 不使用固定值
    
    # 获取选中物体
    objs = cmds.ls(sl=True)
    if not objs:
        cmds.warning("未选中任何物体，请先选择物体")
        return
    
    # 获取通道盒中选中的属性
    attr_names = cmds.channelBox('mainChannelBox', q=True, sma=True)
    if not attr_names:
        cmds.warning("请在通道盒中选中至少一个属性")
        return
    
    # 遍历处理
    for obj in objs:
        for attr_name in attr_names:
            full_attr = f"{obj}.{attr_name}"
            
            if use_current:
                try:
                    current_val = cmds.getAttr(full_attr)
                except:
                    cmds.warning(f"无法获取属性 {full_attr} 的值，跳过")
                    continue
                final_default = current_val
            else:
                final_default = default_value
            
            try:
                # 编辑属性的默认值
                cmds.addAttr(full_attr, e=True, dv=final_default)
                # 同时将当前值设为该默认值
                cmds.setAttr(full_attr, final_default)
                print(f'已设置 "{full_attr}" 默认值为 {final_default}')
            except Exception as e:
                cmds.warning(f"设置属性 {full_attr} 失败: {e}")

# 运行UI
if __name__ == "__main__":
    ui()