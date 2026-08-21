def lockAttr(attr_name):
    u'''
    锁定属性, 该属性参数需要带上物体名称，即完整的属性名
    '''
    obj = attr_name.split(".")[0]
    attr = attr_name.split(".")[-1]
    if not isEx(obj):
        return
    if hasAttr(obj, attr):
        cmds.setAttr(attr_name, lock=True)

def hasAttr(obj, attr_name):
    u'''
    判断属性是否存在于物体上, 只需给出属性本名即可，无需带上物体名
    '''
    if attr_name in cmds.listAttr(obj):
        return True
    else:
        return False

def subExpContent(attr_lst, mode=0):
    u'''
    生成一个连续的表达式内容
    '''
    exp = ""
    if mode == 0:
        for attr in attr_lst:
            exp += "-{}".format(attr)
    elif mode == 1:
        for attr in attr_lst:
            exp += "+{}".format(attr)
    return exp

def bendExpContent(bendJointList, splineIkJointList, bendJntRotatedAttr, localBendAttr_lst, main_ctrl_bend_attr, main_ctrl_bendAgle_attr, main_ctrl_fallOff_attr, prefix):
    u'''
    尾巴/身体 卷曲表达式文本创建
    bendJointList：尾巴：需要卷曲的骨骼列表，列表内的骨骼顺序是从尾部末端骨骼到身体部分的开始骨骼  （其实就是一个反向的列表），身体：反之
    splineIkJointList: 尾巴：线性ik骨骼列表， 列表内的骨骼顺序是从尾部末端骨骼到身体部分的开始骨骼 （其实就是一个反向的列表），身体：反之
    bendJntRotatedAttr： 骨骼被控制的旋转轴属性 （rx/ry/rz）
    localBendAttr_lst: 局部弯曲控制属性的列表
    main_ctrl_bend_attr: 控制弯曲的主控制器属性
    main_ctrl_bendAgle_attr：主控制器的控制弯曲旋转数值范围的属性
    main_ctrl_fallOff_attr: 主控制器的弯曲衰减属性
    '''
    exp_node_lst = []
    bj_attr_lst = ["{}.{}".format(bj, bendJntRotatedAttr) for bj in bendJointList]
    spline_attr_lst = ["{}.{}".format(sj, bendJntRotatedAttr) for sj in splineIkJointList]
    for bj in bendJointList:
        index = bendJointList.index(bj)
        min_agle = "float $min = (-{}+({}*{}))*{} - {};\n".format(main_ctrl_bendAgle_attr, index, main_ctrl_fallOff_attr, localBendAttr_lst[index], spline_attr_lst[index])
        if_min = "if($min>0)$min=0;\n"
        max_agle = "float $max = ({}-({}*{}))*{} - {};\n".format(main_ctrl_bendAgle_attr, index, main_ctrl_fallOff_attr, localBendAttr_lst[index], spline_attr_lst[index])
        if_max = "if($max<0)$max=0;\n"
        tailExpContent = min_agle + max_agle + if_min + if_max
        if index == 0:
            tailExpContent += "{} = clamp($min, $max, {}*10);\n".format(bj_attr_lst[index],
                                                                   main_ctrl_bend_attr)
        else:
            attr_lst = bj_attr_lst[:index]
            temp_content = subExpContent(attr_lst)
            tailExpContent += "{} = clamp($min, $max, {}*10 {});\n".format(bj_attr_lst[index],
                                                                        main_ctrl_bend_attr, temp_content)
        exp_node = createEXP(tailExpContent, "{}_{}_{}_bendExp".format(prefix, bj, index))
        exp_node_lst.append(exp_node)
    return exp_node_lst
    
def createEXP(content, expName):
    u'''
    创建表达式
    '''
    exp_node = cmds.expression(s=content, ae=True, uc="all", n=expName)
    return exp_node

def addTailBendAttr(main_ctrl):
        u'''
        添加尾部卷曲绑定属性
        '''
        tailBendAttrLst = [u"tailBendAttr", "tailBend", "tailBendAngle", "tailFallOff"]

        for tail_attr in tailBendAttrLst:
            if tail_attr == u"tailBendAttr":
                if not hasAttr(main_ctrl, tail_attr):
                    cmds.addAttr(main_ctrl, ln=tail_attr, at="bool", k=True)
                    lockAttr("{}.{}".format(main_ctrl, tail_attr))
            else:
                if not hasAttr(main_ctrl, tail_attr):
                    cmds.addAttr(main_ctrl, ln=tail_attr, at=u"double", dv=0, k=True)
        cmds.setAttr("{}.tailBendAngle".format(main_ctrl), 45)
        cmds.setAttr("{}.tailFallOff".format(main_ctrl), 1)
        
main_ctrl = 'locator19'
bendJointList = cmds.ls(sl=True)
splineIkJointList = cmds.ls(sl=True)

localBendAttr_lst: 局部弯曲控制属性的列表
main_ctrl_bend_attr: 控制弯曲的主控制器属性
main_ctrl_bendAgle_attr：主控制器的控制弯曲旋转数值范围的属性
main_ctrl_fallOff_attr: 主控制器的弯曲衰减属性
speed_attr = "{}.speed".format(main_ctrl)
width_attr = "{}.width".format(main_ctrl)
go_attr = "{}.go".format(main_ctrl)
delay_attr = "{}.delay".format(main_ctrl)
addWidth_attr = "{}.addWidth".format(main_ctrl)
core.bendExpContent(bendJointList, splineIkJointList, "ry", tailBendLocalAttrLst,
                            main_ctrl_bend_attr, main_ctrl_bendAgle_attr, main_ctrl_fallOff_attr, self.system_name)