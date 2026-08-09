import maya.cmds as cmds
import maya.mel as mel
import os

def process_referenced_file(file_path, custom_operation=None):
    """
    引用一个 Maya Ascii 文件，执行自定义操作，然后移除引用

    参数:
        file_path (str): 要引用的 .ma 文件路径
        custom_operation (callable, optional): 一个可调用对象，接受命名空间参数
    """
    # 检查文件是否存在
    if not cmds.file(file_path, q=True, exists=True):
        cmds.warning(f"文件不存在: {file_path}")
        return

    # 引用文件
    ref_node = cmds.file(file_path, reference=True, ignoreVersion=True,ns='jnts_template')
    if not ref_node:
        cmds.error("引用失败，未返回任何新节点")

    # 命名空间
    namespace = cmds.referenceQuery(ref_node, namespace=True, shortName=True)
    print(f"引用 '{ref_node}' 使用了命名空间: {namespace}")

    # 执行用户自定义操作
    if custom_operation is not None:
        custom_operation(namespace)

    cmds.file(file_path, removeReference=True)
    print(f"引用 '{ref_node}' 已移除")

def is_plugin_available_and_loaded(plugin_name):
    """检查插件是否存在且已加载"""
    try:
        if not cmds.pluginInfo(plugin_name, query=True, loaded=True):
            cmds.loadPlugin(plugin_name)
            print(f"插件 {plugin_name} 已加载")
        return True
    except:
        print(f"插件 {plugin_name} 不存在")
        return False

def load_jnts_template():
    version = cmds.about(version=True)
    jnts = cmds.ls(sl=True,shortNames=True)
    # 1. 检查插件
    if not is_plugin_available_and_loaded('SuperRiggingEditor' + version) and not is_plugin_available_and_loaded('SuperRiggingEditor'):
        return

    # 2. 检查骨骼选择
    if not jnts:
        cmds.warning("请选择骨骼")
        return

    # 3. 手动选择模板文件（.ma）
    file_path = cmds.fileDialog2(
        fileFilter="Maya Ascii (*.ma)",
        dialogStyle=2,      # 标准文件对话框
        fileMode=1,         # 1 = 打开文件
        caption="选择骨骼模板文件"
    )
    if not file_path:
        cmds.warning("未选择文件，操作取消")
        return
    target_file = file_path[0]  # fileDialog2 返回列表，取第一个

    # 4. 定义对引用内容的操作（闭包捕获 jnts）
    def custom_py(namespace):
        mel.eval(
            f'SGRBFDeformer -r 0.1 -np 2000 -rbf 1 '
            f'-m "{namespace}:body_geo" "body_geo" '
            f'-t "{namespace}:jnts_rivet_model";'
        )
        for jnt in jnts:
            r_jnt = f'{namespace}:{jnt}'
            cmds.matchTransform(jnt, r_jnt, pos=1, rot=1)

    # 5. 执行引用-处理-移除流程
    process_referenced_file(target_file, custom_py)

if __name__ == "__main__":
    load_jnts_template()