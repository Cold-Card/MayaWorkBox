import maya.cmds as cmds

def add_sep_attr(sepName):
    objs = cmds.ls(sl=True)
    if not sepName:
        cmds.warning("Please enter a name")
        return
    if not objs:
        cmds.warning("Please select objects")
        return
    attrName = sepName.replace(" ", "_")
    for obj in objs:
        cmds.addAttr(obj, ln="sepAttr_{}".format(attrName), nn="__________", at="enum", en="{}:".format(sepName))
        cmds.setAttr(obj + ".sepAttr_{}".format(attrName), channelBox=True)
        cmds.setAttr(obj + ".sepAttr_{}".format(attrName), lock=True)


def show_ui():
    window_name = "sepAttrWindow"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name)

    win = cmds.window(window_name, title="Add Separator Attribute", widthHeight=(300, 150), sizeable=False)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=10)

    # Title
    cmds.text(label="Add Separator Attribute", align="center", height=30, font="boldLabelFont")

    # Separator name input
    cmds.rowLayout(numberOfColumns=2, columnWidth2=(100, 180), columnAlign=[(1, "right"), (2, "left")], columnAttach=[(1, "right", 5), (2, "left", 5)])
    cmds.text(label="Separator Name:", align="right")
    name_field = cmds.textField(text="", placeholderText="Enter name...")
    cmds.setParent("..")

    # Button row
    cmds.rowLayout(numberOfColumns=2, columnWidth2=(150, 150), columnAlign=[(1, "center"), (2, "center")], columnAttach=[(1, "both", 10), (2, "both", 10)])
    cmds.button(label="Apply", command=lambda x: add_sep_attr(cmds.textField(name_field, query=True, text=True)))
    cmds.button(label="Close", command=lambda x: cmds.deleteUI(window_name))
    cmds.setParent("..")

    cmds.showWindow(win)

if __name__ == "__main__":
    show_ui()
