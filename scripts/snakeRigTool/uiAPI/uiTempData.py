# -*- coding: utf 8 -*-
class TempJoint:
    u'''
    记录骨骼信息
    '''
    head_joint = None

    body_start_joint = None
    body_end_joint = None
    body_insert_joint_list = []

    neck_start_joint = None
    head_end_joint = None
    neck_insert_joint_list = []

    path_guide_joint = None
    path_curve_length = None
    path_curve_ctrl_num = None

    path_curve = None

