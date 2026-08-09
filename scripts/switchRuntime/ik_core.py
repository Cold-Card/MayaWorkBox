# coding:utf-8

import math
from maya.api.OpenMaya import *

def pos_sub(pos1, pos2):
    return [v1-v2 for v1, v2 in zip(pos1, pos2)]


def pos_add(pos1, pos2):
    return [v1+v2 for v1, v2 in zip(pos1, pos2)]


def pos_dot(pos1, pos2):
    u"""
    点乘
    """
    return sum([v1*v2 for v1, v2 in zip(pos1, pos2)])


def pos_length(pos):
    return pos_dot(pos, pos)**0.5


def pos_distance(pos1, pos2):
    return pos_length(pos_sub(pos1, pos2))


def pos_normal(pos1):
    u"""
    归一化
    """
    length = pos_length(pos1)
    if length < 0.0000001:
        return [0, 0, 0]
    return [v/length for v in pos1]


def pos_cross(pos1, pos2):
    u"""
    叉乘
    """
    pos = []
    for i in range(3):
        j = (i + 1) % 3
        k = (i + 2) % 3
        pos.append(pos1[j] * pos2[k] - pos1[k] * pos2[j])
    return pos


def pos_mul(pos, v):
    return [v1*v for v1 in pos]


def vector_mul_matrix(vector, matrix):
    v = [0, 0, 0]
    for i in range(3):
        for j in range(3):
            v[i] += vector[j] * matrix[j][i]
    return v


def pos_angle(pos1, pos2):
    u"""
    求pos1与pos2的夹角
    @param pos1: 向量pos1
    @param pos2: 向量pos2
    @return:
    """
    cos_value = pos_dot(pos1, pos2)/(pos_length(pos1)*pos_length(pos2))
    if cos_value >= 1.0:
        return 0
    elif cos_value <= -1:
        return math.pi
    return math.acos(cos_value)


def pos_schmidt(v1, v2):
    u"""
    施密特正交，v2 减去 v1 在v2上的投影，得到一个垂直于v1的向量
    @param v1: 向量v1
    @param v2: 向量v2
    @return:
    """
    return pos_normal(pos_sub(v2, pos_mul(v1, pos_dot(v1, v2))))


def look_at(pos, aim_pos, aim_axis, up_axis, up_vector):
    u"""
    @param pos: 自身坐标
    @param aim_pos: 第一个轴朝向的坐标
    @param aim_axis: 第一个朝向轴: +x, -x
    @param up_axis: 第二个朝向轴：+y, -y, +z, -z
    @param up_vector: 第二个轴朝向的向量
    @return: 矩阵
    """
    x_vector = pos_normal(pos_sub(aim_pos, pos))
    if "-" in aim_axis:
        x_vector = pos_mul(x_vector, -1)
    if "-" in up_axis:
        up_vector = pos_mul(up_vector, -1)
    if "z" in up_axis:
        z_vector = pos_normal(up_vector)
        y_vector = pos_normal(pos_cross(z_vector, x_vector))
        z_vector = pos_normal(pos_cross(x_vector, y_vector))
    else:
        y_vector = pos_normal(up_vector)
        z_vector = pos_normal(pos_cross(x_vector, y_vector))
        y_vector = pos_normal(pos_cross(z_vector, x_vector))
    return [x_vector, y_vector, z_vector, pos]


def snap_matrix(src, dst):
    u"""
    src吸附到dst骨骼
    将src位置移动到dst位置
    src的x轴与dst的哪个轴夹角最小，则朝向哪个轴。YZ同理
    @param src: 源矩阵
    @param dst: 目标矩阵
    @return:
    """
    vectors = [pos_normal(pos_mul(dst[i][:3], j)) for i in range(3) for j in [+1, -1]]
    result = []
    for i in range(3):
        angles = [pos_angle(src[i][:3], v) for v in vectors]
        result.append(vectors.pop(angles.index(min(angles))))
    result.append(dst[3][:3])
    return result


def m43_to_m16(matrix):
    matrix_list = []
    for row, row4 in zip(matrix, [0, 0, 0, 1]):
        matrix_list += row
        matrix_list.append(row4)
    return matrix_list


def solve_ik(points, a, b, default_vector=(1.0, 0, 0)):
    v1 = pos_normal(pos_sub(points[1], points[0]))
    v2 = pos_normal(pos_sub(points[2], points[1]))
    angle = pos_angle(v1, v2)
    if angle < 1e-6:
        up_vector = default_vector
    else:
        up_vector = pos_cross(v1, v2)
    ik_matrix = look_at(points[0], points[2], "+x", "+y", up_vector)
    ik_matrix = MMatrix(m43_to_m16(ik_matrix))

    c = pos_distance(points[2], points[0])
    c = min(c, (a+b))
    cos_value = (c ** 2 + a ** 2 - b ** 2) / (2 * a * c)
    cos_value = max(-1.0, min(1.0, cos_value))
    angle = math.acos(cos_value)

    tx = math.cos(angle) * a
    tz = math.sin(angle) * a
    pole_point = list(MPoint([tx, 0, tz]) * ik_matrix)[:3]
    hand_point = list(MPoint([c, 0, 0]) * ik_matrix)[:3]
    matrix_a = m43_to_m16(look_at(points[0], pole_point, "+x", "+y", up_vector))
    matrix_b = m43_to_m16(look_at(pole_point, points[2], "+x", "+y", up_vector))
    return matrix_a, matrix_b, hand_point


def solve_pole(points, default_vector, pole_length):
    v1 = pos_normal(pos_sub(points[1], points[0]))
    v2 = pos_normal(pos_sub(points[2], points[1]))
    if pos_distance(v1, v2) > 0.00001:
        up_vector = pos_cross(v2, v1)
    else:
        up_vector = default_vector
    point_matrix = look_at(points[0], points[2], "+x", "+z", up_vector)
    pole_vector = pos_normal(point_matrix[1])
    return pos_add(points[1], pos_mul(pole_vector, pole_length))


