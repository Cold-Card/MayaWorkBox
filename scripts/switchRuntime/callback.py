import os.path

from maya.api.OpenMaya import *
from maya import cmds, mel
import re


SWITCHES = {}
SWITCH_CLASS = {}
SWITCH_INSTANCE = []
CTRL = None


def api_ls(*arg):
    sel = MSelectionList()
    for arg in arg:
        sel.add(arg)
    return sel


def kill_all_job(name):
    for job in cmds.scriptJob(listJobs=True):
        if name in job:
            cmds.scriptJob(kill=int(job.split(":")[0]))
            print (">>>kill", job)


def remove_nodes_callback(ctrls):
    for node in ctrls:
        ids = MNodeMessage.nodeCallbacks(api_ls(node).getDependNode(0))
        MNodeMessage.removeCallbacks(ids)
        if ids:
            print(">>>remove callback", node.split("|")[-1])


def remove_all_node_callback():
    print(">>>remove_all_node_callback")
    switch_sets = cmds.ls("switchRuntime*Set*", "*:switchRuntime*Set*", "*:*:switchRuntime*Set*", type="objectSet") or []
    for switch_set in switch_sets:
        ctrls = cmds.sets(switch_set, q=1) or []
        remove_nodes_callback(ctrls)
    global CTRL
    if not CTRL:
        return
    if not cmds.objExists(CTRL):
        return
    remove_nodes_callback([CTRL])


def remove_all():
    kill_all_job("switchRuntime.SelectedChanged")
    remove_all_node_callback()
    global SWITCHES, SWITCH_INSTANCE
    SWITCHES.clear()
    for i in range(len(SWITCH_INSTANCE)):
        SWITCH_INSTANCE.pop(0)


def callback(*args, **kwargs):
    global CTRL
    if not CTRL:
        return
    if not cmds.objExists(CTRL):
        return
    for fun in SWITCHES.get(CTRL, SWITCH_INSTANCE):
        fun(CTRL)


def update_active_ctrl():
    remove_all_node_callback()
    global CTRL
    CTRL = (cmds.ls(sl=1, type="transform", l=1) or [None])[0]
    if not CTRL:
        return
    if not cmds.objExists(CTRL):
        return
    MNodeMessage.addAttributeChangedCallback(api_ls(CTRL).getDependNode(0), callback)
    print(">>>addAttributeChangedCallback ", CTRL)


class SelectedChanged(object):

    def __init__(self):
        kill_all_job(str(self))
        cmds.scriptJob(event=["SelectionChanged", self], kws=True)
        print(">>>scriptJob SelectedChanged start")

    def __repr__(self):
        return "switchRuntime.%s()" % self.__class__.__name__

    def __call__(self):
        update_active_ctrl()


def register_ctrls(ctrls, switch):
    for ctrl in ctrls:
        SWITCHES.setdefault(ctrl, []).append(switch)


def build_all_runtime_switch():
    remove_all()
    switch_sets = cmds.ls("switchRuntime*Set*", "*:switchRuntime*Set*", "*:*:switchRuntime*Set*", type="objectSet") or []
    for switch_set in switch_sets:
        match = re.search(r'switchRuntime([A-Za-z]+)Set', switch_set)
        if not match:
            continue
        cls = match.group(1)
        if cls not in SWITCH_CLASS:
            continue
        switch = SWITCH_CLASS[cls](switch_set)
        SWITCH_INSTANCE.append(switch)
    SelectedChanged()
    update_active_ctrl()


class PostSceneRead(object):

    def __init__(self):
        kill_all_job(str(self))
        cmds.scriptJob(event=["PostSceneRead", self])
        print(">>>scriptJob PostSceneRead start")

    def __repr__(self):
        return "switchRuntime.%s()" % self.__class__.__name__

    def __call__(self):
        build_all_runtime_switch()
        print(">>>build_all_runtime_switch finish")
