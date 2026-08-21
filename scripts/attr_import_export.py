import json
import os
import maya.cmds as cmds

# 预设属性列表
CORRJNT_ATTRIBUTES = [
    "angleMin", "angleMax", "reactionMove", "reactionRotate", "reactionScale",
    "inverseBehaviour", "reactionMoveRev", "reactionRotateRev", "reactionScaleRev",
    "moveOffset", "rotOffset"
]

AI_ATTRIBUTES = [
    'aiOpaque','aiMatte',
    'primaryVisibility','castsShadows','aiVisibleInDiffuseReflection','aiVisibleInSpecularReflection',
    'aiVisibleInDiffuseTransmission','aiVisibleInSpecularTransmission','aiVisibleInVolume','aiSelfShadows',
    'aiSubdivType','aiSubdivIterations','aiSubdivAdaptiveMetric','aiSubdivPixelError',
    'aiSubdivAdaptiveSpace','aiSubdivUvSmoothing','aiSubdivSmoothDerivs','aiSubdivFrustumIgnore',
    'aiDispHeight','aiDispPadding','aiDispZeroValue'
]

def export_attributes(file_path, attributes):
    """
    导出选中对象的自定义属性到JSON文件
    """
    # 获取选中的对象
    selected_objects = cmds.ls(selection=True)
    if not selected_objects:
        cmds.warning("请先选择一些对象")
        return False
    
    # 收集数据
    data = {}
    for obj in selected_objects:
        data[obj] = {}
        
        for attr in attributes:
            full_attr_name = "{}.{}".format(obj, attr)
            if cmds.objExists(full_attr_name):
                try:
                    # 获取属性值
                    attr_value = cmds.getAttr(full_attr_name)
                    # 获取属性类型
                    attr_type = cmds.getAttr(full_attr_name, type=True)
                    
                    data[obj][attr] = {
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

def import_attributes(file_path, skip_missing, use_filter, filter_attributes):
    """
    从JSON文件导入自定义属性到对象
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
    imported_count = 0
    skipped_count = 0
    
    aiDispData = {}

    for obj, attr_data in data.items():
        # 检查对象是否存在
        if not cmds.objExists(obj):
            cmds.warning("对象不存在: {}".format(obj))
            skipped_count += len(attr_data)
            continue
        
        for attr, attr_info in attr_data.items():
            # 如果启用过滤且当前属性不在过滤列表中，则跳过
            if use_filter and attr not in filter_attributes:
                skipped_count += 1
                continue
                
            full_attr_name = "{}.{}".format(obj, attr)
            
            # 检查属性是否存在
            if not cmds.objExists(full_attr_name):
                if skip_missing:
                    cmds.warning("属性 {} 不存在于对象 {} 上，已跳过".format(attr, obj))
                    skipped_count += 1
                    continue
                try:
                    # 根据保存的类型创建属性
                    attr_type = attr_info.get("type", "float")
                    if attr_type == "float":
                        cmds.addAttr(obj, longName=attr, attributeType=attr_type, defaultValue=0)
                    elif attr_type == "bool":
                        cmds.addAttr(obj, longName=attr, attributeType="bool")
                    elif attr_type == "long":
                        cmds.addAttr(obj, longName=attr, attributeType="long", defaultValue=0)
                    elif attr_type == "double":
                        cmds.addAttr(obj, longName=attr, attributeType="double", defaultValue=0)
                    elif attr_type == "string":
                        cmds.addAttr(obj, longName=attr, dataType="string")
                    # 可以添加更多类型的处理
                    else:
                        cmds.addAttr(obj, longName=attr, attributeType="float", defaultValue=0)
                    
                    # 确保属性可键控
                    cmds.setAttr(full_attr_name, keyable=True)
                except Exception as e:
                    cmds.warning("无法创建属性 {} 在对象 {}: {}".format(attr, obj, str(e)))
                    skipped_count += 1
                    continue
            
            # 设置属性值
            try:
                value = attr_info["value"]
                attr_type = attr_info.get("type", "float")

                origValue = cmds.getAttr(full_attr_name)
                if attr_type == "string":
                    cmds.setAttr(full_attr_name, value, type="string")
                else:
                    cmds.setAttr(full_attr_name, value)
                if value != origValue:
                    cmds.warning("属性 {} : {} -> {}".format(full_attr_name, origValue, value))
                if (attr in ['aiDispZeroValue','aiDispPadding'] and value != 0.0) or (attr == 'aiDispHeight' and value != 1.0):
                    aiDispData[full_attr_name] = [value, origValue]

                imported_count += 1
            except Exception as e:
                cmds.warning("无法设置属性 {} 的值: {}".format(full_attr_name, str(e)))
                skipped_count += 1

    for attr_name, values in aiDispData.items():
        cmds.warning("{} 的值为 {} (导入前值为 {})，可能会导致渲染问题".format(attr_name, values[0], values[1]))
        
    # 显示导入结果
    message = "导入完成!\n成功导入: {} 个属性\n跳过: {} 个属性".format(imported_count, skipped_count)
    if use_filter:
        message += "\n(已启用属性过滤)"
    cmds.confirmDialog(title="导入完成", message=message)
    return True

def export_dialog():
    """
    导出文件选择对话框
    """

    mesh_aiAttrs = cmds.checkBox('mesh_aiAttrs_ui', query=True, value=True)
    corrJnt_attrs = cmds.checkBox('corrJnt_attrs_ui', query=True, value=True)

    # 获取属性列表
    attributes = []
    attr_text = cmds.textField('attr_ui', query=True, text=True)
    if attr_text:
        attributes += [attr.strip() for attr in attr_text.split(",") if attr.strip()]
    if mesh_aiAttrs:
        attributes += AI_ATTRIBUTES
    if corrJnt_attrs:
        attributes += CORRJNT_ATTRIBUTES
    #print(attributes)
    if not attributes:
        cmds.warning("请输入至少一个属性名称")
        return
    
    file_path = cmds.fileDialog2(
        fileMode=0, 
        fileFilter="JSON Files (*.json)", 
        dialogStyle=2,
        caption="导出属性"
    )
    
    if file_path:
        export_attributes(file_path[0], attributes)

def import_dialog():
    """
    导入文件选择对话框
    """
    # 获取跳过选项
    skip_missing = cmds.checkBox('skip_missing_ui', query=True, value=True)
    
    # 获取过滤选项
    use_filter = cmds.checkBox('use_filter_ui', query=True, value=True)
    
    # 获取属性列表（用于过滤）
    attr_text = cmds.textField('attr_ui', query=True, text=True)
    filter_attributes = [attr.strip() for attr in attr_text.split(",") if attr.strip()]
    
    file_path = cmds.fileDialog2(
        fileMode=1, 
        fileFilter="JSON Files (*.json)", 
        dialogStyle=2,
        caption="导入属性"
    )
    
    if file_path:
        import_attributes(file_path[0], skip_missing, use_filter, filter_attributes)

def show_ui():
    """
    UI 界面
    """
    # 检查窗口是否已经存在
    if cmds.window('attrImportExportWin_ui', q=True, ex=True):
        cmds.deleteUI('attrImportExportWin_ui')
    
    # 创建窗口和布局
    cmds.window('attrImportExportWin_ui', t=u'属性导入导出')
    cmds.formLayout('formLayout_layout_ui')
    cmds.formLayout('formLayout1_ui')
    cmds.text('attr_text_ui', w=300, l=u'载入属性（逗号分隔）', fn=u'boldLabelFont')
    cmds.textField('attr_ui', tx=u'')
    cmds.formLayout('formLayout2_ui', p='formLayout_layout_ui')
    cmds.text('export_text_ui', l=u'导出选项：', fn=u'boldLabelFont')
    cmds.checkBox('mesh_aiAttrs_ui', l=u'Arnold 属性', v=False)
    cmds.checkBox('corrJnt_attrs_ui', l=u'矫正骨骼属性', v=False)
    cmds.formLayout('formLayout3_ui', p='formLayout_layout_ui')
    cmds.text('import_text_ui', l=u'导入选项：', fn=u'boldLabelFont')
    cmds.checkBox('skip_missing_ui', l=u'跳过不存在的属性', v=True)
    cmds.checkBox('use_filter_ui', l=u'使用属性过滤', v=False)
    cmds.separator('separator1_ui', p='formLayout_layout_ui', st=u'in')
    cmds.formLayout('formLayout4_ui', p='formLayout_layout_ui')
    cmds.button('export_ui', h=30, l=u'导出属性', c=lambda x: export_dialog())
    cmds.button('import_ui', h=30, l=u'导入属性', c=lambda x: import_dialog())
    
    # 布局设置
    cmds.formLayout('formLayout_layout_ui', e=1, 
                   af=[
                       ['formLayout1_ui', 'top', 10], 
                       ['formLayout1_ui', 'left', 5], 
                       ['formLayout1_ui', 'right', 5], 
                       ['formLayout2_ui', 'left', 5], 
                       ['formLayout2_ui', 'right', 5], 
                       ['formLayout3_ui', 'left', 5], 
                       ['formLayout3_ui', 'right', 5], 
                       ['separator1_ui', 'left', 5], 
                       ['separator1_ui', 'right', 5], 
                       ['formLayout4_ui', 'left', 5], 
                       ['formLayout4_ui', 'right', 5], 
                       ['formLayout4_ui', 'bottom', 10]
                   ],
                   ac=[
                       ['formLayout2_ui', 'top', 5, 'formLayout1_ui'], 
                       ['formLayout3_ui', 'top', 5, 'formLayout2_ui'], 
                       ['separator1_ui', 'top', 5, 'formLayout3_ui'], 
                       ['formLayout4_ui', 'top', 5, 'separator1_ui']
                   ])
    
    cmds.formLayout('formLayout1_ui', e=1, 
                   af=[
                       ['attr_text_ui', 'top', 0], 
                       ['attr_text_ui', 'left', 0], 
                       ['attr_text_ui', 'right', 0], 
                       ['attr_ui', 'left', 0], 
                       ['attr_ui', 'right', 0]
                   ],
                   ac=[['attr_ui', 'top', 5, 'attr_text_ui']])
    
    cmds.formLayout('formLayout2_ui', e=1, 
                   af=[
                       ['export_text_ui', 'top', 0], 
                       ['export_text_ui', 'left', 0], 
                       ['export_text_ui', 'bottom', 0], 
                       ['mesh_aiAttrs_ui', 'top', 0], 
                       ['mesh_aiAttrs_ui', 'bottom', 0], 
                       ['corrJnt_attrs_ui', 'top', 0], 
                       ['corrJnt_attrs_ui', 'right', 0], 
                       ['corrJnt_attrs_ui', 'bottom', 0]
                   ],
                   ac=[
                       ['mesh_aiAttrs_ui', 'left', 5, 'export_text_ui'], 
                       ['corrJnt_attrs_ui', 'left', 5, 'mesh_aiAttrs_ui']
                   ],
                   ap=[['export_text_ui', 'right', 0, 25]])
    
    cmds.formLayout('formLayout3_ui', e=1, 
                   af=[
                       ['import_text_ui', 'top', 0], 
                       ['import_text_ui', 'left', 0], 
                       ['import_text_ui', 'bottom', 0], 
                       ['skip_missing_ui', 'top', 0], 
                       ['skip_missing_ui', 'bottom', 0], 
                       ['use_filter_ui', 'top', 0], 
                       ['use_filter_ui', 'right', 0], 
                       ['use_filter_ui', 'bottom', 0]
                   ],
                   ac=[
                       ['skip_missing_ui', 'left', 5, 'import_text_ui'], 
                       ['use_filter_ui', 'left', 5, 'skip_missing_ui']
                   ],
                   ap=[['import_text_ui', 'right', 0, 25]])
    
    cmds.formLayout('formLayout4_ui', e=1, 
                   af=[
                       ['export_ui', 'top', 0], 
                       ['export_ui', 'left', 0], 
                       ['export_ui', 'bottom', 0], 
                       ['import_ui', 'top', 0], 
                       ['import_ui', 'right', 0], 
                       ['import_ui', 'bottom', 0]
                   ],
                   ap=[
                       ['export_ui', 'right', 1, 50], 
                       ['import_ui', 'left', 1, 50]
                   ])
    
    cmds.showWindow('attrImportExportWin_ui')

# 运行UI
if __name__ == "__main__":
    show_ui()