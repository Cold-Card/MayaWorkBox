# -*- coding: utf-8 -*-
from maya import cmds, mel
import os
from . import callback
import shutil


def set_key_frame_pose():
    print(">>>set_key_frame_pose", callback.CTRL)
    if callback.CTRL not in callback.SWITCHES:
        return
    ctrls = [sw.ctrls for sw in callback.SWITCHES.get(callback.CTRL, [])]
    if not ctrls:
        return
    ctrls = sum(ctrls, [])
    if not ctrls:
        return
    ctrls = cmds.ls(ctrls)
    if not ctrls:
        return
    cmds.setKeyframe(ctrls)


def open_key_frame_post():
    import maya.cmds as cmds
    version = cmds.about(version=True)
    mel_path = os.path.join(os.path.dirname(__file__), "mel", version, "PostSetKeyframeArgList.mel")
    mel_path = mel_path.replace("\\", "/")
    print("version", version)
    if not os.path.isfile(mel_path):
        raise RuntimeError(u"未找到对应Maya版本的mel文件: {}".format(mel_path))
    mel.eval('source "%s"' % mel_path)


def close_key_frame_post():
    mel.eval('source "%s"' % "performSetKeyframeArgList.mel")


def rewrite_mel_with_python_call(orig_mel, dst_file):
    # 读取原mel内容
    with open(orig_mel, 'r') as f:
        lines = f.readlines()
    # 在最后10行内寻找'return $cmd;'，插入python调用
    insert_idx = None
    for i in range(len(lines)-10, len(lines)):
        if 'return $cmd;' in lines[i]:
            insert_idx = i
            break
    if insert_idx is not None:
        # 用catch包裹python调用
        call_line = '    catch(`python \"import switchRuntime.key_frame_post; switchRuntime.key_frame_post.set_key_frame_pose()\"`);\n'
        lines.insert(insert_idx, call_line)
    # 写入新mel文件
    with open(dst_file, 'w') as f:
        f.writelines(lines)
    print(u"重写并拷贝: {} -> {}".format(orig_mel, dst_file))


def copy_all_pre_mel():
    path = r"C:/Program Files/Autodesk/Maya{}/scripts/others/performSetKeyframeArgList.mel"
    for v in range(2016, 2026):
        orig_mel = path.format(v)
        if not os.path.isfile(orig_mel):
            orig_mel = path.format(v-1)
        if not os.path.isfile(orig_mel):
            continue
        dst_dir = os.path.join(os.path.dirname(__file__), "mel", str(v))
        # 兼容Python2和3的目录创建
        try:
            os.makedirs(dst_dir)
        except OSError:
            if not os.path.isdir(dst_dir):
                raise
        dst_file = os.path.join(dst_dir, "PostSetKeyframeArgList.mel")
        rewrite_mel_with_python_call(orig_mel, dst_file)


def test():
    open_key_frame_post()
