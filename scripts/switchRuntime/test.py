from . import callback
from . import switch
from . import tools
from . import key_frame_post
from maya import cmds


def test_adv():
    print ("test arm")
    callback.remove_all()
    callback.kill_all_job("switchRuntime.PostSceneRead")
    cmds.delete(cmds.ls("switchRuntime*Set*"))
    tools.adv_biped()
    callback.build_all_runtime_switch()
    callback.open_key_frame_post()
    # callback.SelectedChanged()
    # callback.PostSceneRead()


def test_auto_key():
    callback.remove_all()
    callback.PostSceneRead()


def debug_arm():
    callback.remove_all()
    callback.kill_all_job("switchRuntime.PostSceneRead")
    cmds.delete(cmds.ls("switchRuntime*Set*"))
    cmds.setAttr("Main.scale", 1, 1, 1)
    cmds.select(cmds.ls([u'FKShoulder_L', u'FKElbow_L', u'FKWrist_L', u'PoleArm_L', u'IKArm_L', "FKIKArm_L"]))
    switch.Arm.create_set()
    callback.build_all_runtime_switch()
    # cmds.setAttr("FKElbow_L.rz", 0)
    # arm_ik_fk = switch.Arm(switch.Arm.create_set())
    # cmds.setAttr("FKElbow_L.rz", 30)
    # cmds.setAttr("Main.scale", 0.2, 0.2, 0.2)
    # print(arm_ik_fk(arm_ik_fk.fk_ctrls[0]))
    # print(arm_ik_fk(arm_ik_fk.ik_ctrls[0]))


def test_key():
    callback.remove_all()
    callback.kill_all_job("switchRuntime.PostSceneRead")
    cmds.delete(cmds.ls("switchRuntime*Set*"))
    tools.adv_biped()
    callback.build_all_runtime_switch()

    callback.remove_all_node_callback()
    key_frame_post.open_key_frame_post()
    cmds.select("FKShoulder_L")
    callback.update_active_ctrl()
    key_frame_post.set_key_frame_pose()



def doit():
    # debug_arm()
    test_key()
    # callback.remove_all()
    # switch.build_all_runtime_switch()

