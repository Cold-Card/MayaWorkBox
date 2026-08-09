from . import callback
from . import key_frame_post
from . import switch
from maya import cmds


def adv_biped():
    cmds.select(cmds.ls([u'FKShoulder_L', u'FKElbow_L', u'FKWrist_L', u'PoleArm_L', u'IKArm_L', "FKIKArm_L"]))
    switch.Arm.create_set()
    cmds.select(cmds.ls([u'FKShoulder_R', u'FKElbow_R', u'FKWrist_R', u'PoleArm_R', u'IKArm_R', "FKIKArm_R"]))
    switch.Arm.create_set()
    cmds.select([u'FKHip_L', u'FKKnee_L', u'FKAnkle_L', u'PoleLeg_L', u'IKLeg_L', "FKIKLeg_L"])
    switch.Arm.create_set()
    cmds.select([u'FKHip_R', u'FKKnee_R', u'FKAnkle_R', u'PoleLeg_R', u'IKLeg_R', "FKIKLeg_L"])
    switch.Arm.create_set()


def open_auto_switch():
    callback.PostSceneRead()
    callback.build_all_runtime_switch()


def close_auto_switch():
    callback.remove_all()
    callback.kill_all_job("switchRuntime.PostSceneRead")


def open_switch():
    callback.build_all_runtime_switch()


def close_switch():
    callback.remove_all()


def open_key_frame_post():
    key_frame_post.open_key_frame_post()

def close_key_frame_post():
    key_frame_post.close_key_frame_post()

