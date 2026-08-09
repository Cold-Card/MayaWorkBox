import json
import os
import maya.cmds as cmds

# 要处理的属性列表
ATTRIBUTES = [
    "angleMin", "angleMax", "reactionMove", "reactionRotate", "reactionScale",
    "inverseBehaviour", "reactionMoveRev", "reactionRotateRev", "reactionScaleRev",
    "moveOffset", "rotOffset"
]

def export_bone_attributes(file_path):
    """
    导出选中骨骼的自定义属性到JSON文件
    """
    # 获取选中的骨骼
    selected_bones = cmds.ls(selection=True, type="joint")
    if not selected_bones:
        cmds.warning("请先选择一些骨骼")
        return False
    
    # 收集数据
    data = {}
    for bone in selected_bones:
        data[bone] = {}
        
        for attr in ATTRIBUTES:
            full_attr_name = "{}.{}".format(bone, attr)
            if cmds.objExists(full_attr_name):
                try:
                    # 获取属性值
                    attr_value = cmds.getAttr(full_attr_name)
                    # 获取属性类型
                    attr_type = cmds.getAttr(full_attr_name, type=True)
                    
                    data[bone][attr] = {
                        "value": attr_value,
                        "type": attr_type
                    }
                except:
                    cmds.warning("无法获取属性 {} 的值".format(full_attr_name))
    
    # 写入JSON文件
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
        cmds.confirmDialog(title="导出成功", message="属性已成功导出到:\n{}".format(file_path))
        return True
    except Exception as e:
        cmds.warning("导出失败: {}".format(str(e)))
        return False

def import_bone_attributes(file_path):
    """
    从JSON文件导入自定义属性到骨骼
    """
    # 检查文件是否存在
    if not os.path.exists(file_path):
        cmds.warning("文件不存在: {}".format(file_path))
        return False
    
    # 读取JSON文件
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        cmds.warning("读取JSON文件失败: {}".format(str(e)))
        return False
    
    # 应用数据
    for bone, attributes in data.items():
        # 检查骨骼是否存在
        if not cmds.objExists(bone):
            cmds.warning("骨骼不存在: {}".format(bone))
            continue
        
        for attr, attr_data in attributes.items():
            full_attr_name = "{}.{}".format(bone, attr)
            
            # 检查属性是否存在，如果不存在则创建
            if not cmds.objExists(full_attr_name):
                try:
                    # 根据保存的类型创建属性
                    attr_type = attr_data.get("type", "float")
                    if attr_type == "float":
                        cmds.addAttr(bone, longName=attr, attributeType=attr_type, defaultValue=0)
                    elif attr_type == "bool":
                        cmds.addAttr(bone, longName=attr, attributeType="bool")
                    elif attr_type == "long":
                        cmds.addAttr(bone, longName=attr, attributeType="long", defaultValue=0)
                    # 可以添加更多类型的处理
                    else:
                        cmds.addAttr(bone, longName=attr, attributeType="float", defaultValue=0)
                    
                    # 确保属性可键控
                    cmds.setAttr(full_attr_name, keyable=True)
                except:
                    cmds.warning("无法创建属性 {} 在骨骼 {}".format(attr, bone))
                    continue
            
            # 设置属性值
            try:
                cmds.setAttr(full_attr_name, attr_data["value"])
            except:
                cmds.warning("无法设置属性 {} 的值".format(full_attr_name))
    
    cmds.confirmDialog(title="导入成功", message="属性已成功从文件导入:\n{}".format(file_path))
    return True

def show_ui():
    """
    显示导出导入UI界面
    """
    # 检查窗口是否已经存在
    if cmds.window("boneAttrTool", exists=True):
        cmds.deleteUI("boneAttrTool")
    
    # 创建窗口
    window = cmds.window("boneAttrTool", title="骨骼属性工具", widthHeight=(300, 150))
    
    # 创建布局
    cmds.columnLayout(adjustableColumn=True)
    
    # 添加说明
    cmds.text(label="导出/导入骨骼自定义属性", align="center")
    cmds.separator(height=20)
    
    # 导出按钮
    cmds.button(label="导出属性到JSON", command=lambda x: export_dialog())
    cmds.separator(height=10)
    
    # 导入按钮
    cmds.button(label="从JSON导入属性", command=lambda x: import_dialog())
    cmds.separator(height=10)
    
    # 显示窗口
    cmds.showWindow(window)

def export_dialog():
    """
    导出文件选择对话框
    """
    file_path = cmds.fileDialog2(
        fileMode=0, 
        fileFilter="JSON Files (*.json)", 
        dialogStyle=2,
        caption="导出骨骼属性"
    )
    
    if file_path:
        export_bone_attributes(file_path[0])

def import_dialog():
    """
    导入文件选择对话框
    """
    file_path = cmds.fileDialog2(
        fileMode=1, 
        fileFilter="JSON Files (*.json)", 
        dialogStyle=2,
        caption="导入骨骼属性"
    )
    
    if file_path:
        import_bone_attributes(file_path[0])

# 运行UI
show_ui()