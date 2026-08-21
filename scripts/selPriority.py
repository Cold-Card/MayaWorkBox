import maya.cmds as cmds

WIN_NAME = "SelectionPriorityTool"

COLOR_ACTIVE = (0.3, 0.6, 0.3)
COLOR_DEFAULT = (0.2, 0.2, 0.2)

buttons = {}

# ===== 提示 =====
def show_msg(text):
    cmds.inViewMessage(
        amg=f'<hl>{text}</hl>',
        pos='topRight',
        fade=True,
        fadeStayTime=800,
        fadeOutTime=400
    )

# ===== 高亮 =====
def set_active(btn_key):
    for k, b in buttons.items():
        cmds.button(b, e=True, bgc=COLOR_DEFAULT)

    cmds.button(buttons[btn_key], e=True, bgc=COLOR_ACTIVE)

# ===== 模式 =====
def curve_mode(*args):
    cmds.selectPriority(nurbsCurve=10, joint=2, polymesh=1)
    #cmds.selectType(nurbsCurve=True, joint=True, polymesh=True)
    set_active("curve")
    show_msg("Curve")

def joint_mode(*args):
    cmds.selectPriority(nurbsCurve=2, joint=10, polymesh=1)
    #cmds.selectType(nurbsCurve=True, joint=True, polymesh=True)
    set_active("joint")
    show_msg("Joint")

def mesh_mode(*args):
    cmds.selectPriority(nurbsCurve=1, joint=2, polymesh=10)
    #cmds.selectType(nurbsCurve=True, joint=True, polymesh=True)
    set_active("mesh")
    show_msg("Mesh")

def curve_only(*args):
    cmds.selectType(nurbsCurve=True, joint=False, polymesh=False)
    set_active("curve_only")
    show_msg("Curve Only")

def reset_mode(*args):
    cmds.selectPriority(nurbsCurve=2, joint=9, polymesh=2)
    #cmds.selectType(nurbsCurve=True, joint=True, polymesh=True)
    set_active("reset")
    show_msg("Default")

# ===== UI =====
def create_ui():
    global buttons

    if cmds.window(WIN_NAME, exists=True):
        cmds.deleteUI(WIN_NAME)

    cmds.window(
        WIN_NAME,
        title="Sel Tool",
        sizeable=False,
        widthHeight=(200, 190),
        toolbox=True
    )

    main = cmds.columnLayout(adj=True, rs=6)

    # ===== Priority =====
    cmds.frameLayout(label="Priority", collapsable=False, mw=4, mh=4)
    cmds.rowLayout(nc=3, cw3=(60, 60, 60), ct3=("both", "both", "both"), co3=(2,2,2))

    buttons["curve"] = cmds.button(label="Curve", h=30, bgc=COLOR_DEFAULT, c=curve_mode)
    buttons["joint"] = cmds.button(label="Joint", h=30, bgc=COLOR_DEFAULT, c=joint_mode)
    buttons["mesh"]  = cmds.button(label="Mesh",  h=30, bgc=COLOR_DEFAULT, c=mesh_mode)

    cmds.setParent(main)

    # ===== Curve Only =====
    cmds.frameLayout(label="Curve Only", collapsable=False, mw=4, mh=4)
    buttons["curve_only"] = cmds.button(label="Enable", h=30, bgc=COLOR_DEFAULT, c=curve_only)

    cmds.setParent(main)

    # ===== Reset =====
    cmds.frameLayout(label="Reset", collapsable=False, mw=4, mh=4)
    buttons["reset"] = cmds.button(label="Default", h=30, bgc=COLOR_DEFAULT, c=reset_mode)

    cmds.setParent(main)

    cmds.showWindow(WIN_NAME)

    # 默认状态
    set_active("reset")
    show_msg("Default")

def show():
    # 运行
    create_ui()