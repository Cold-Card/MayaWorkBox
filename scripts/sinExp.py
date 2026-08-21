import maya.cmds as cmds
def sinExpContent(coned_grp_lst, same_coned_attr,
                  coned_ctrl_lst, ctrl_width_attr,
                  speed_attr, width_attr, go_attr, delay_attr, addWidth_attr):
    u'''
    正弦波浪表达式
    coned_grp_lst: 被控制的物体的组名称列表（表达式会添加在此物体上）
    same_coned_attr: 被控制物体需要被控制的属性（短名称）
    coned_ctrl_lst: 控制的控制器名称列表（ ctrl_width_attr 属性所添加的物体）
    ctrl_width_attr: 每个控制器的幅度属性（短名称）
    speed_attr: 主控制器的速度属性
    width_attr: 主控制器的整体幅度属性（振幅）
    go_attr:主控制器的手动偏移属性（偏移）
    delay_attr: 主控制器的延迟属性（频率）
    addWidth_attr: 主控制器的局部幅度属性（幅度递减/递增属性）
    '''
    exp = ""
    for obj in range(len(coned_grp_lst)):
        attr = "{}.{}".format(coned_grp_lst[obj], same_coned_attr)
        ctrl_attr = "{}.{}".format(coned_ctrl_lst[obj], ctrl_width_attr)
        exp += "{} = sin(time * {} + {} - {} * {}) * {} * (1 + {} * {}) * {};\n".format(attr, speed_attr, go_attr, obj,
                                                                                        delay_attr, width_attr, obj,
                                                                                        addWidth_attr, ctrl_attr)
    return exp
    
def createEXP(content, expName):
    u'''
    创建表达式
    '''
    exp_node = cmds.expression(s=content, ae=True, uc="all", n=expName)
    return exp_node

main_ctrl = 'locator19'
coned_grp_lst = cmds.ls(sl=True)
coned_ctrl_lst = cmds.ls(sl=True)
speed_attr = "{}.speed".format(main_ctrl)
width_attr = "{}.width".format(main_ctrl)
go_attr = "{}.go".format(main_ctrl)
delay_attr = "{}.delay".format(main_ctrl)
addWidth_attr = "{}.addWidth".format(main_ctrl)
exp = sinExpContent(coned_grp_lst, 'tz',
                coned_ctrl_lst, 'widthRG',
                speed_attr, width_attr, go_attr, delay_attr, addWidth_attr)
createEXP(exp, "sinExp")