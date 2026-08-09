from maya import cmds
from . import callback
from .ik_core import *


def link_message(switch_set, ctrl, name):
    if not cmds.objExists(switch_set + "." + name):
        cmds.addAttr(switch_set, ln=name, at="message", k=1)
    cmds.connectAttr(ctrl + ".message", switch_set + "." + name, f=1)


def save_data(node, **kwargs):
    for attr, value in kwargs.items():
        if isinstance(value, float):
            cmds.addAttr(node, ln=attr, dv=value, at="double", k=1)
        elif isinstance(value, list):
            if len(value) == 16:
                cmds.addAttr(node, ln=attr, dt="matrix")
                cmds.setAttr(node+"."+attr, value, type="matrix")
            elif len(value) == 3:
                cmds.addAttr(node, ln=attr, dt="double3")
                cmds.setAttr(node + "." + attr, *value, type="double3")


def load_data(node):
    data = {}
    for attr in cmds.listAttr(node, ud=1):
        node_attr = node+"."+attr
        typ = cmds.getAttr(node_attr, typ=1)
        if typ == "message":
            value = cmds.listConnections(node_attr, s=1, d=0)[0]
            value = cmds.ls(value, l=1)[0]
        elif typ == "double3":
            value = cmds.getAttr(node_attr)[0]
        else:
            value = cmds.getAttr(node_attr)
        data[attr] = value
    return data


def scale_matrix16(matrix, scale):
    matrix = list(matrix)
    for i in [0, 1, 2, 4, 5, 6, 8, 9, 10]:
        matrix[i] *= scale
    return matrix


class Arm(object):
    def __call__(self, ctrl):
        if ctrl not in self.ctrls:
            if not cmds.objExists(self.switch_set + ".FKIKBlend"):
                return
            blend = cmds.getAttr(self.switch_set + ".FKIKBlend")
            if blend < 5.0:
                ctrl = self.fk_ctrls[-1]
            else:
                ctrl = self.ik_ctrls[-1]
        if ctrl in self.ik_ctrls:
            self.solve_fk()
        elif ctrl in self.fk_ctrls:
            self.solve_ik()

    def __init__(self, switch_set):
        self.switch_set = switch_set
        self.data = load_data(switch_set)
        self.ik_ctrls = [self.data[attr] for attr in ["ikPole", "ikHand"]]
        self.fk_ctrls = [self.data[attr] for attr in ["fkA", "fkB", "fkC"]]
        self.ctrls = [self.data[attr] for attr in ["fkA", "fkB", "fkC", "ikPole", "ikHand"]]
        callback.register_ctrls(self.ctrls, self)

    def __eq__(self, other):
        return self.switch_set == other.switch_set

    def solve_ik(self):
        callback.remove_nodes_callback(self.ik_ctrls)
        scale = cmds.xform(self.data["fkGroup"], q=1, ws=1, s=1)[0]
        hand_matrix = list(MMatrix(self.data["fk_hand_offset"]) * MMatrix(cmds.xform(self.data["fkC"], q=1, ws=1, m=1)))
        cmds.xform(self.data["ikHand"], ws=1, m=hand_matrix)
        up_vector = self.get_up_vector()
        points = [cmds.xform(self.data[name], q=1, ws=1, t=1) for name in ["fkA", "fkB", "fkC"]]
        pole_point = solve_pole(points,  up_vector, self.data["length_pole"]*scale)
        cmds.xform(self.data["ikPole"], ws=1, t=pole_point)

    def get_up_vector(self):
        return list(MVector(self.data["up_vector"]) * MMatrix(cmds.xform(self.data["fkGroup"], q=1, ws=1, m=1)))[:3]

    def solve_fk(self):
        callback.remove_nodes_callback(self.fk_ctrls)
        scale = cmds.xform(self.data["fkGroup"], q=1, ws=1, s=1)[0]
        points = [cmds.xform(self.data[name], q=1, ws=1, t=1) for name in ["fkA", "ikPole", "ikHand"]]
        up_vector = self.get_up_vector()
        matrix_a, matrix_b, hand_point = solve_ik(
            points,
            self.data["length_a"]*scale,
            self.data["length_b"]*scale,
            up_vector
        )

        fk_matrix_a = list(MMatrix(self.data["matrix_offset_a"]) * MMatrix(matrix_a))

        cmds.xform(self.data["fkA"], ws=1, m=scale_matrix16(fk_matrix_a, scale))
        fk_matrix_b = list(MMatrix(self.data["matrix_offset_b"]) * MMatrix(matrix_b))
        cmds.xform(self.data["fkB"], ws=1, m=scale_matrix16(fk_matrix_b, scale))
        hand_matrix = list(MMatrix(self.data["ik_hand_offset"]) * MMatrix(cmds.xform(self.data["ikHand"], q=1, ws=1, m=1)))
        hand_matrix[12:15] = hand_point
        cmds.xform(self.data["fkC"], ws=1, m=hand_matrix)

    @classmethod
    def create_set(cls):
        ctrls = cmds.ls(sl=1, o=1, type="transform")
        if len(ctrls) not in [5, 6]:
            return
        switch_set = cmds.sets(ctrls, n="switchRuntime%s" % cls.__name__ + "Set1")
        print("create set")
        names = ["fkA", "fkB", "fkC", "ikPole", "ikHand"]
        for name, ctrl in zip(names, ctrls):
            link_message(switch_set, ctrl, name)
        fk_group = cmds.listRelatives(ctrls[0], p=1)[0]
        link_message(switch_set, fk_group, "fkGroup")
        points = [cmds.xform(ctrls[i], q=1, ws=1, t=1) for i in range(4)]
        matrices = [cmds.xform(ctrls[i], q=1, ws=1, m=1) for i in range(5)]
        length_a = pos_length(pos_sub(points[0], points[1]))
        length_b = pos_length(pos_sub(points[1], points[2]))
        length_pole = pos_length(pos_sub(points[1], points[3]))
        ik_hand_offset = list(MMatrix(matrices[2]) * MMatrix(matrices[4]).inverse())
        fk_hand_offset = list(MMatrix(matrices[4]) * MMatrix(matrices[2]).inverse())
        v1 = pos_normal(pos_sub(points[1], points[0]))
        v2 = pos_normal(pos_sub(points[2], points[1]))
        up_vector = pos_normal(pos_cross(v1, v2))
        up_vector = list(MVector(up_vector) * MMatrix(cmds.xform(fk_group, q=1, ws=1, m=1)).inverse())[:3]
        matrix_a, matrix_b, _ = solve_ik(points, length_a, length_b, up_vector)
        matrix_offset_a = list(MMatrix(matrices[0]) * MMatrix(matrix_a).inverse())
        matrix_offset_b = list(MMatrix(matrices[1]) * MMatrix(matrix_b).inverse())
        matrix_offset_a = [float(int(round(v))) for v in matrix_offset_a]
        matrix_offset_b = [float(int(round(v))) for v in matrix_offset_b]
        up_vector = [float(int(round(v))) for v in up_vector]
        save_data(switch_set, length_a=length_a, length_b=length_b, length_pole=length_pole, up_vector=up_vector,
                  matrix_offset_a=matrix_offset_a, matrix_offset_b=matrix_offset_b,
                  ik_hand_offset=ik_hand_offset, fk_hand_offset=fk_hand_offset)
        cmds.addAttr(switch_set, ln="FKIKBlend", dv=0, at="double", k=1, min=0, max=10)
        if len(ctrls) == 6:
            if cmds.objExists(ctrls[-1]+".FKIKBlend"):
                cmds.connectAttr(ctrls[-1]+".FKIKBlend", switch_set+".FKIKBlend")
        return switch_set


callback.SWITCH_CLASS["Arm"] = Arm
