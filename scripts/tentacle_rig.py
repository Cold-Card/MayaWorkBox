#!/usr/bin/python
#encoding:utf-8
import maya.cmds as cmds
import pymel.core as pm
from functools import partial
"{:03d}".format(1)

def create_controls_window():
    window_name = "ControlsWindow"

    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title=u"触手绑定", widthHeight=(300, 200))

    cmds.columnLayout(adjustableColumn=True)
    
    cmds.text(label=u" ", h=5)
    cmds.text(label=u"============= 创建骨骼可选 =============")
    cmds.text(label=u" ", h=5)

    cmds.rowLayout(numberOfColumns=2, columnWidth2=(120, 60), columnAlign2=("right", "left"), adjustableColumn=2)
    cmds.text(label=u"创建定位器:")
    cmds.button(label=u"创建", command=partial(create_locators))
    cmds.setParent("..")

    cmds.rowLayout(numberOfColumns=2, columnWidth2=(120, 60), columnAlign2=("right", "left"), adjustableColumn=2)
    cmds.text(label=u"关节数量:")
    jnts_num_field = cmds.intField(minValue=0, value=0)
    cmds.setParent("..")

    cmds.text(label=u"==================================")
    cmds.text(label=u" ")

    cmds.rowLayout(numberOfColumns=2, columnWidth2=(120, 60), columnAlign2=("right", "left"), adjustableColumn=2)
    cmds.text(label=u"次级控制器间隔:")
    sec_ctrl_num_field = cmds.intField(minValue=0, value=0)
    cmds.setParent("..")
    
    cmds.rowLayout(numberOfColumns=2, columnWidth2=(120, 60), columnAlign2=("right", "left"), adjustableColumn=2)
    cmds.text(label=u"触手名称:")
    ctrl_text_field = cmds.textField(text="chuShou")
    cmds.setParent("..")

    cmds.rowLayout(numberOfColumns=2, columnWidth2=(120, 60), columnAlign2=("right", "left"), adjustableColumn=2)
    cmds.text(label=u"选择触手关节:")
    cmds.button(label=u"创建", command=partial(create_controls, sec_ctrl_num_field, ctrl_text_field, jnts_num_field))
    cmds.setParent("..")

    cmds.showWindow(window_name)

def create_locators(*args):
    pm.spaceLocator(n="start")
    pm.spaceLocator(n="end")

def create_controls(sec_ctrl_num_field, ctrl_text_field, jnts_num_field, *args):
    pm.select(cl=True)
    
    sec_ctrl_num = cmds.intField(sec_ctrl_num_field, query=True, value=True)
    jnts_num = cmds.intField(jnts_num_field, query=True, value=True)
    ctrl_text = cmds.textField(ctrl_text_field, query=True, text=True)
    jnts = []
    if pm.objExists("start"):
        startPos = pm.xform("start",q=True,t=True,ws=True)
        endPos = pm.xform("end",q=True,t=True,ws=True)
        posx = (endPos[0] - startPos[0])/(jnts_num - 1)
        posy = (endPos[1] - startPos[1])/(jnts_num - 1)
        posz = (endPos[2] - startPos[2])/(jnts_num - 1)
        for num in range(jnts_num):
            jnts.append(pm.joint(p=(startPos[0]+posx*num,
                                    startPos[1]+posy*num,
                                    startPos[2]+posz*num)))
    
    if jnts:
        pass
    else:    
        jnts = pm.selected()
        
    jntsNum = len(jnts)
    for jnt,jntId in zip(jnts, range(int(jntsNum))):
        jntC = pm.circle(n="ctrl_" + ctrl_text + "_" + str(jntId),nr=(1,0,0))[0]
        jntCC = pm.group(n="connect_" + ctrl_text + "_" + str(jntId))
        jntCD = pm.group(n="drive_" + ctrl_text + "_" + str(jntId))
        jntZ = pm.group(n="zero_" + ctrl_text + "_" + str(jntId))
        pm.select(jntZ, jnt)
        pm.matchTransform()
        pm.select(jntC, jnt)
        pm.parentConstraint(mo=1, w=1)
        
        if pm.objExists("ctrl_" + ctrl_text + "_" + str(jntId-1)):
            pm.parent(jntZ, "ctrl_" + ctrl_text + "_" + str(jntId-1))
    
    if jntsNum%sec_ctrl_num !=0:
        secN = jntsNum/sec_ctrl_num+1
    else:
        secN = jntsNum/sec_ctrl_num          
    for secCtrl in range(int(secN)):
        curve = pm.curve(n="sec_ctrl_" + ctrl_text + "_" + str(secCtrl),
                         degree=1, 
                         point=[(0, 1.5, 1.5),(0,-1.5, 1.5),(0,-1.5,-1.5),(0, 1.5,-1.5),(0, 1.5, 1.5)])
        curveC = pm.group(n="sec_connect_" + ctrl_text + "_" + str(secCtrl))
        curveZ = pm.group(n="sec_zero_" + ctrl_text + "_" + str(secCtrl))
        pm.select(curveZ, jnts[secCtrl*sec_ctrl_num])
        pm.matchTransform()
        
        divide_node = pm.createNode('multiplyDivide')
        
        pm.setAttr(divide_node + ".input2X", sec_ctrl_num)
        pm.setAttr(divide_node + ".input2Y", sec_ctrl_num)    
        pm.setAttr(divide_node + ".input2Z", sec_ctrl_num)
        
        curve.rotate >> divide_node.input1
        
        for ctrNum in range(sec_ctrl_num):
            if pm.objExists("drive_" + ctrl_text + "_" + str(secCtrl*sec_ctrl_num+ctrNum)):
                pm.connectAttr(divide_node.output, 
                               "drive_" + ctrl_text + "_" + str(secCtrl*sec_ctrl_num+ctrNum) + ".rotate")
        
        if secCtrl == 0:
            pm.parent("zero_" + ctrl_text + "_0", curve)
        else:
            pm.parent(curveZ, "ctrl_" + ctrl_text + "_" + str(secCtrl*sec_ctrl_num-1))
    
    # 卷曲功能 ------------------------------------ 
           
    ctrl = "sec_ctrl_" + ctrl_text + "_0"
    
    # add attrs
    cmds.addAttr(ctrl, longName='roll', attributeType='float', minValue=0, maxValue=1, keyable=True)
    cmds.addAttr(ctrl, longName='angle', attributeType='float', keyable=True, defaultValue=70)
    cmds.addAttr(ctrl, longName='falloff', attributeType='float', keyable=True, minValue=0, maxValue=1, defaultValue=0.1)

    roll_attr = ctrl + '.roll'
    angle_attr = ctrl + '.angle'
    falloff_attr = ctrl + '.falloff'

    # mult node to reverse falloff value, because we are using this value to subtract
    mult = cmds.createNode('multDoubleLinear', name='mult_m_tentacleRollFalloffRvs_001')
    cmds.connectAttr(falloff_attr, mult + '.input1')
    cmds.setAttr(mult + '.input2', -1)
    falloff_attr = mult + '.output'
    
    # list controls
    ctrls = cmds.ls("ctrl_" + ctrl_text + "_*", type='transform')
    
    # get control number
    ctrl_num = len(ctrls)
    
    # create mash distribute node
    distr = cmds.createNode('MASH_Distribute', name='distribute_m_tentacleRoll_001')
    cmds.setAttr(distr + '.pointCount', ctrl_num)
    
    # set rotate X to 1 to gather weight value from 0-1
    cmds.setAttr(distr + '.rotateX', 1)
    
    # create breakout node
    breakout = cmds.createNode('MASH_Breakout', name='breakout_m_tentacleRoll_001')
    cmds.connectAttr(distr + '.outputPoints', breakout + '.inputPoints')
    
    # loop in each control to do the roll setup
    for i, ctrl in enumerate(ctrls):
        # get connect group
        connect = ctrl.replace('ctrl_', 'connect_')
    
        # create remap node to roll will only happen in the given section
        remap = cmds.createNode('remapValue', name='remap_m_tentacleRollWeight_{:03d}'.format(i+1))
    
        # connect tentacle roll to remap
        cmds.connectAttr(roll_attr, remap + '.inputValue')
        # get max value by weight
        weight_max = 1 - float(i) / ctrl_num
        cmds.setAttr(remap + '.inputMax', weight_max)
        # get min value
        weight_min = 1 - float(i+1)/ctrl_num
        # add node to subtract falloff so the joint can roll before the previous finished
        add = cmds.createNode('addDoubleLinear', name='add_m_tentacleRollStart_{:03d}'.format(i+1))
        cmds.setAttr(add + '.input1', weight_min)
        cmds.connectAttr(falloff_attr, add + '.input2')
        # clamp value so it won't go below 0
        clamp = cmds.createNode('clamp', name='clamp_m_tentacleRollStart_{:03d}'.format(i+1))
        cmds.setAttr(clamp + '.maxR', 1)
        cmds.connectAttr(add + '.output', clamp + '.inputR')
        # connect with min value
        cmds.connectAttr(clamp + '.outputR', remap + '.inputMin')
    
        # multiply divide node to mult remap weight with distribute weight to get the final roll weight for each joint
        # because MASH doesn't work with single axis, we need to use multiply divide to breakout single axis rotation
        mult_weight = cmds.createNode('multiplyDivide', name='mult_m_tentacleRotWeight_{:03d}'.format(i+1))
        cmds.connectAttr(remap + '.outValue', mult_weight + '.input1X')
        cmds.connectAttr('{}.outputs[{}].rotate'.format(breakout, i), mult_weight + '.input2')
    
        # mult with roll angle to get output
        mult_angle = cmds.createNode('multDoubleLinear', name='mult_m_tentacleRotAngle_{:03d}'.format(i+1))
        cmds.connectAttr(mult_weight + '.outputX', mult_angle + '.input1')
        cmds.connectAttr(angle_attr, mult_angle + '.input2')
    
        # connect with connect group
        cmds.connectAttr(mult_angle + '.output', connect + '.rotateZ')
        
        
    ctrl = "sec_ctrl_" + ctrl_text + "_0"
    # add attrs
    
    cmds.addAttr(ctrl, longName='ripple', attributeType='float', keyable=True)
    cmds.addAttr(ctrl, longName='rippleOut', attributeType='float', keyable=False)
    cmds.addAttr(ctrl, longName='rippleFrequency', attributeType='float', keyable=True, minValue=0, defaultValue=5)
    cmds.addAttr(ctrl, longName='rippleAmplitude', attributeType='float', keyable=True, minValue=1, defaultValue=1.5)
    cmds.addAttr(ctrl, longName='rippleOffset', attributeType='float', keyable=True)
    cmds.addAttr(ctrl, longName='rippleFalloff', attributeType='float', keyable=True, minValue=0, maxValue=1,
                 defaultValue=0.05)
    
    # create modulo expression to connect ripple out
    cmds.expression(string='{}.rippleOut = ({}.ripple + {}.rippleOffset) % {}.rippleFrequency'.format(ctrl, ctrl, ctrl,
                                                                                                      ctrl),
                    name='expr_m_rippleOut_001')
    
    ripple_attr = ctrl + '.rippleOut'
    freq_attr = ctrl + '.rippleFrequency'
    amp_attr = ctrl + '.rippleAmplitude'
    offset_attr = ctrl + '.rippleOffset'
    fall_attr = ctrl + '.rippleFalloff'
    
    # remap ripple out to 0-1
    remap = cmds.createNode('remapValue', name='remap_m_tentacleRippleVal_001')
    cmds.connectAttr(ripple_attr, remap + '.inputValue')
    cmds.connectAttr(freq_attr, remap + '.inputMax')
    
    ripple_attr = remap + '.outValue'
    
    # falloff attr reverse
    mult_rvs = cmds.createNode('multDoubleLinear', name='mult_m_tentacleRippleNeg_001')
    cmds.connectAttr(fall_attr, mult_rvs + '.input1')
    cmds.setAttr(mult_rvs + '.input2', -1)
    falloff_rvs_attr = mult_rvs + '.output'
    
    # get joints and joints number
    jnts_num = len(jnts)
    
    # create MASH Distribute node
    distr = cmds.createNode('MASH_Distribute', name='distribute_m_tentacleRipple_001')
    cmds.setAttr(distr + '.pointCount', jnts_num)
    
    # connect scale with amplitude
    cmds.connectAttr(amp_attr, distr + '.scaleY')
    cmds.connectAttr(amp_attr, distr + '.scaleZ')
    
    # create breakout node
    breakout = cmds.createNode('MASH_Breakout', name='breakout_m_tentacleRipple_001')
    cmds.connectAttr(distr + '.outputPoints', breakout + '.inputPoints')
    
    # loop in each joint
    unit_val = 1/float(jnts_num + 1)
    for i, j in enumerate(jnts):
        # create remap node to do wave effect
        remap_jnt = cmds.createNode('remapValue', name='remap_m_tentacleRipple_{:03d}'.format(i+1))
    
        # connect ripple value to input value
        cmds.connectAttr(ripple_attr, remap_jnt + '.inputValue')
    
        # set ramp position
        cmds.setAttr(remap_jnt + '.value[1].value_Position', (i + 0.5)*unit_val)
        cmds.setAttr(remap_jnt + '.value[1].value_FloatValue', 1)
        cmds.setAttr(remap_jnt + '.value[1].value_Interp', 2)
    
        # set in and out point, default should be half unit
        add_in = cmds.createNode('addDoubleLinear', name='add_m_tentacleRippleIn_{:03d}'.format(i+1))
        add_out = cmds.createNode('addDoubleLinear', name='add_m_tentacleRippleOut_{:03d}'.format(i + 1))
    
        cmds.setAttr(add_in + '.input1', i*unit_val)
        cmds.setAttr(add_out + '.input1', (i+1)*unit_val)
    
        cmds.connectAttr(falloff_rvs_attr, add_in + '.input2')
        cmds.connectAttr(fall_attr, add_out + '.input2')
    
        # clamp the output in 0-1
        clamp = cmds.createNode('clamp', name='clamp_m_tentacleRipple_{:03d}'.format(i + 1))
        cmds.connectAttr(add_in + '.output', clamp + '.inputR')
        cmds.connectAttr(add_out + '.output', clamp + '.inputG')
        cmds.setAttr(clamp + '.maxR', 1)
        cmds.setAttr(clamp + '.maxG', 1)
    
        # connect clamp output to point position
        cmds.connectAttr(clamp + '.outputR', remap_jnt + '.value[0].value_Position')
        cmds.setAttr(remap_jnt + '.value[0].value_FloatValue', 0)
        cmds.setAttr(remap_jnt + '.value[0].value_Interp', 2)
        cmds.connectAttr(clamp + '.outputG', remap_jnt + '.value[2].value_Position')
        cmds.setAttr(remap_jnt + '.value[2].value_FloatValue', 0)
        cmds.setAttr(remap_jnt + '.value[2].value_Interp', 2)
    
        # connect output ripple wight with MASH Distribute node
        blend_ripple = cmds.createNode('blendColors', name='blend_m_tentacleRippleScale_{:03d}'.format(i + 1))
        cmds.connectAttr(remap_jnt + '.outValue', blend_ripple + '.blender')
        cmds.connectAttr('{}.outputs[{}].scale'.format(breakout, i), blend_ripple + '.color1')
        cmds.setAttr(blend_ripple + '.color2', 1, 1, 1)
    
        # connect to joint's scale
        cmds.connectAttr(blend_ripple + '.outputG', j + '.scaleY')
        cmds.connectAttr(blend_ripple + '.outputB', j + '.scaleZ')

    ctrl = "sec_ctrl_" + ctrl_text + "_0"

    # add attrs
    cmds.addAttr(ctrl, longName='offset', attributeType='float', keyable=True)
    cmds.addAttr(ctrl, longName='longth', attributeType='float', keyable=True)
    cmds.addAttr(ctrl, longName='strength', attributeType='float', keyable=True)
    cmds.addAttr(ctrl, longName='speed', attributeType='float', keyable=True)
    
    cons = pm.ls("connect_chuShou_*")
    # add expression
    expressions = ''' '''
    print (expressions)
    for i, id in zip(cons, range(len(cons))):
        if id <= len(cons)/3:
            expressions += '''{}.translateY = (sin({}.offset * {}.speed - {}.longth * {}) * {}.strength) * {};
'''.format(i, ctrl, ctrl, ctrl, id, ctrl, float(id*3)/len(cons))
        else:
            expressions += '''{}.translateY = sin({}.offset * {}.speed - {}.longth * {}) * {}.strength;
'''.format(i, ctrl, ctrl, ctrl, id, ctrl)
    exp = pm.expression(string = expressions, name = "expr_m_baidong_001")
    
create_controls_window()