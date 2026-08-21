import maya.cmds as cmds
import maya.mel as mel
import datetime

def rename_skinClusters_simple():
    
    # 获取当前日期
    current_date = datetime.datetime.now().strftime("%Y%m%d")
    
    # 获取当前选择
    selection = cmds.ls(selection=True)
    
    if selection:
        for obj in selection:
            try:
                # 找到与物体相关的skinCluster
                skin_cluster = mel.eval(f'findRelatedSkinCluster("{obj}")')
                
                if skin_cluster:
                    # 检查skinCluster是否已经是当前日期格式
                    if is_current_date_skincluster(skin_cluster, current_date):
                        print(f"{skin_cluster} 已经是当前日期格式，跳过重命名")
                        continue
                    
                    # 获取物体的短名称
                    obj_short_name = get_short_name(obj)
                    
                    # 新名称
                    new_name = f"{obj_short_name}_skinCluster_{current_date}"
                    final_name = get_unique_name(new_name, skin_cluster)
                    
                    # 重命名skinCluster
                    cmds.rename(skin_cluster, final_name)
                    print(f"已重命名: {skin_cluster} -> {final_name}")
                else:
                    print(f"{obj} 没有找到skinCluster")
            except Exception as e:
                print(f"处理 {obj} 时出错: {str(e)}")
    else:
        # 直接获取所有skinCluster节点
        all_skin_clusters = cmds.ls(type='skinCluster') or []
        
        for skin_cluster in all_skin_clusters:
            try:
                # 检查skinCluster是否已经是当前日期格式
                if is_current_date_skincluster(skin_cluster, current_date):
                    print(f"{skin_cluster} 已经是当前日期格式，跳过重命名")
                    continue
                
                # 获取skinCluster影响的几何体
                geometries = cmds.skinCluster(skin_cluster, query=True, geometry=True) or []
                
                if geometries:
                    # 获取几何体的变换节点
                    geometry = geometries[0]
                    transform = cmds.listRelatives(geometry, parent=True, fullPath=True)[0]
                    
                    # 获取物体的短名称（不含路径）
                    obj_short_name = get_short_name(transform)
                    
                    # 新名称
                    new_name = f"{obj_short_name}_skinCluster_{current_date}"
                    final_name = get_unique_name(new_name, skin_cluster)
                    
                    # 重命名skinCluster
                    cmds.rename(skin_cluster, final_name)
                    print(f"已重命名: {skin_cluster} -> {final_name}")
            except Exception as e:
                print(f"处理 {skin_cluster} 时出错: {str(e)}")
    
    print("skinCluster重命名完成！")

def get_short_name(full_name):
    return full_name.split('|')[-1]

def is_current_date_skincluster(skin_cluster, current_date):
    # 检查名称是否以当前日期结尾
    if skin_cluster.endswith(f"_skinCluster_{current_date}"):
        return True
    
    # 检查名称是否包含当前日期格式（带序号的情况）
    parts = skin_cluster.split('_')
    if len(parts) >= 3:
        # 检查最后一部分是否是日期
        last_part = parts[-1]
        if last_part == current_date:
            return True
        # 检查是否是带序号的情况，如 "skinCluster_01_20251114"
        if last_part == current_date and len(parts) >= 4 and parts[-2].isdigit():
            return True
    
    return False

def get_unique_name(base_name, skin_cluster):
    # 从基础名称中提取物体名和skinCluster部分
    base_parts = base_name.split('_')
    if len(base_parts) < 3:
        # 如果格式不对，使用原来的方法
        return get_unique_name_fallback(base_name,skin_cluster)
    
    # 提取物体名和skinCluster部分
    obj_skin_part = '_'.join(base_parts[:-1])  # 物体名_skinCluster
    date_part = base_parts[-1]  # 当前日期
    
    # 检查基础名称是否已存在
    if not cmds.objExists(base_name):
        return base_name
    
    # 如果名称已存在，在skinCluster和日期之间添加序号
    counter = 1
    while True:
        new_name = f"{obj_skin_part}_{counter:02d}_{date_part}"
        if new_name == skin_cluster:
            return new_name
        if not cmds.objExists(new_name):
            return new_name
        counter += 1

def get_unique_name_fallback(base_name, skin_cluster):
    """备用方法，如果上面的方法失败，使用原来的方法"""
    if not cmds.objExists(base_name):
        return base_name
    
    counter = 1
    while True:
        new_name = f"{base_name}_{counter:02d}"
        if new_name == skin_cluster:
            return new_name
        if not cmds.objExists(new_name):
            return new_name
        counter += 1

# 执行函数
rename_skinClusters_simple()

# 清理数据结构
cmds.dataStructure( removeAll=True )