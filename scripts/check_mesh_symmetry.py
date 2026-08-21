import maya.api.OpenMaya as om2
import maya.cmds as cmds
import math
import time

def check_mesh_symmetry(tolerance=0.001):
    """
    :param tolerance: 对称容差值
    """
    # 获取当前选择的物体
    sel_list = om2.MGlobal.getActiveSelectionList()
    if sel_list.length() != 1:
        return cmds.warning("请选择一个模型！")
    elif sel_list.getDagPath(0).extendToShape().apiType() != 296:
        return cmds.warning("请选择模型！")
    dag_path = sel_list.getDagPath(0)
    mesh_fn = om2.MFnMesh(dag_path)

    mesh_name = dag_path.partialPathName()
    
    # 计时
    start_time = time.time()
    print("-" * 40)
    print("开始检测模型: {}".format(mesh_name))
    
    # 一次性获取所有顶点坐标
    points = mesh_fn.getPoints(om2.MSpace.kObject)
    num_vertices = len(points)
    print("总顶点数: {}".format(num_vertices))
    
    # 空间哈希参数设置
    cell_size = tolerance * 2.0  # 确保网格大于容差
    grid = {}
    left_points = []
    center_points = []
    
    # 遍历顶点，分类并构建右半部分的哈希表
    for i in range(num_vertices):
        p = points[i]
        x, y, z = p.x, p.y, p.z
        
        if x > tolerance:
            # 右侧点：存入哈希网格
            cx = int(math.floor(x / cell_size))
            cy = int(math.floor(y / cell_size))
            cz = int(math.floor(z / cell_size))
            key = (cx, cy, cz)
            
            if key not in grid:
                grid[key] = []
            grid[key].append((i, x, y, z))
        elif x < -tolerance:
            # 左侧点：存入列表等待检测
            left_points.append((i, x, y, z))
        else:
            # 中心点
            center_points.append((i, x, y, z))
            
    right_count = sum(len(v) for v in grid.values())
    print("分布统计 -> 右侧: {}, 左侧: {}, 中轴: {}".format(right_count, len(left_points), len(center_points)))
    
    if right_count != len(left_points):
        print("【警告】左右侧顶点数量不一致，模型绝对不对称！")
    
    # 校验左侧点是否存在对称的右侧点
    asymmetrical_vertices = []
    offsets = [(dx, dy, dz) for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1)]
    tol_sq = tolerance ** 2
    
    for idx, lx, ly, lz in left_points:
        mx = -lx  # 镜像X坐标
        
        cx = int(math.floor(mx / cell_size))
        cy = int(math.floor(ly / cell_size))
        cz = int(math.floor(lz / cell_size))
        
        found = False
        # 查找当前网格及其周围 26 个相邻网格 (共 27 个)
        for dx, dy, dz in offsets:
            neighbor_key = (cx + dx, cy + dy, cz + dz)
            if neighbor_key in grid:
                for ridx, rx, ry, rz in grid[neighbor_key]:
                    # 计算距离平方
                    dist_sq = (rx - mx)**2 + (ry - ly)**2 + (rz - lz)**2
                    if dist_sq <= tol_sq:
                        found = True
                        break
            if found:
                break
                
        if not found:
            asymmetrical_vertices.append(idx)
            
    # 输出结果
    end_time = time.time()
    print("检测完成，耗时: {:.3f} 秒".format(end_time - start_time))
    
    if not asymmetrical_vertices and right_count == len(left_points):
        print("模型在容差 {} 内是完美对称的。".format(tolerance))
    else:
        print("模型不对称！找到 {} 个无法匹配的左侧顶点。".format(len(asymmetrical_vertices)))
        
        # 选中不对称的点
        if asymmetrical_vertices:
            cmds.select(clear=True)
            sel_list_str = ["{}.vtx[{}]".format(mesh_name, i) for i in asymmetrical_vertices]
            cmds.select(sel_list_str)

if __name__ == "__main__":
    check_mesh_symmetry(tolerance=0.001)