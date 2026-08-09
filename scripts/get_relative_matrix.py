import maya.cmds as cmds
import maya.api.OpenMaya as om2
def get_relative_matrix(objA, objB):
    """
    计算 objA 在 objB 坐标系下的变换矩阵（行主序 4x4）
    返回 om2.MMatrix 对象，可直接用于点转换
    """
    # 获取世界矩阵（16个浮点数，行主序）
    matA_list = cmds.xform(objA, q=True, ws=True, matrix=True)
    matB_list = cmds.xform(objB, q=True, ws=True, matrix=True)

    # 转换为 MMatrix
    matA = om2.MMatrix(matA_list)
    matB = om2.MMatrix(matB_list)

    # 计算相对矩阵：M_rel = M_A * inv(M_B)
    matB_inv = matB.inverse()
    rel_mat = matA * matB_inv
    return rel_mat


objA = "Main"
objB = "Chest_M"
rel_matrix = get_relative_matrix(objA, objB)


cmds.setAttr("{}.matrixIn[0]".format('GlobalFollowMainMM_GlobalFollowMain2'), rel_matrix, type="matrix")