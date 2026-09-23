import maya.cmds as cmds
import pymel.core as pm

def prefix_logic(prefix):
    prefix = str(prefix or '').strip()
    if not prefix:
        return ''
    return prefix if prefix.endswith('_') else prefix + '_'

def create_text_control(name,prefix,view=None,parent=None,center_pivot=False,create_border=True):
    prefix_ = prefix_logic(prefix)
    if view is None:
        view = ' '.join((name).split('_'))
    txt_grp = pm.PyNode(pm.textCurves(t=view, f='Times New Roman')[0])
    pm.xform(txt_grp, ws=True, s=(0.5, 0.5, 0.5))
    if create_border:
        pm.xform(txt_grp, ws=True, t=(0, 1.02, 0),s=(0.2, 0.2, 0.2))
    if center_pivot:
        #bbox = txt_grp.getBoundingBox(space='world')
        pm.xform(txt_grp, cpc=True)
        rp = txt_grp.getRotatePivot(space='world')
        pm.xform(txt_grp, ws=True, t=rp * -1)

    transforms = pm.ls(txt_grp, dag=True, type='transform')
    for transform in transforms:
        pm.delete(transform.inputs())
    pm.makeIdentity(txt_grp, a=True, t=1, r=1, s=1)

    curveShapes = pm.ls(txt_grp, dag=True, type='nurbsCurve')
    for curveShape in curveShapes:
        curveShape.ihi.set(0)
        curveShape.hiddenInOutliner.set(1)

    del_nodes = [txt_grp]
    if create_border:
        border_curve = pm.curve(d=1, p=[(0, 0, 0), (2, 0, 0), (2, 1, 0), (0, 1, 0), (0, 0, 0)], n=prefix_ + 'bend_AngleWeight_border')
        curveShapes.insert(0, border_curve.getShape())
        del_nodes.append(border_curve)

    if parent is None:
        parent = pm.createNode('transform',n=name)
    else:
        if parent.getShapes():
            pm.delete(parent.getShapes())
    
    for curveShape in curveShapes:
        curveShape.overrideEnabled.set(1)
        curveShape.overrideColor.set(20)
        curveShape.lineWidth.set(2)
        pm.parent(curveShape, parent, add=True, shape=True)
    if create_border:
        curveShapes[0].template.set(1)
    
    parent_name = str(parent)
    shapes = parent.getShapes()
    for shape in shapes:
        shape.rename('{}Shape'.format(parent_name))
    
    pm.delete(del_nodes)
    for attr in ['tx','ty','tz','rx','ry','rz','sx','sy','sz','v']:
        pm.setAttr(f'{parent}.{attr}', lock=True, keyable=False, channelBox=False)
    return parent

def addAttr(nodeName, attrName, prefix='', minValue=None, maxValue=None,
            keyable=True, attributeType="float", defaultValue=0, enumName=None):
    attrName = prefix_logic(prefix) + attrName

    if not pm.objExists(nodeName):
        pm.warning('{} 不存在'.format(nodeName))
        return None

    node = pm.PyNode(nodeName)
    if not node.hasAttr(attrName):
        kwargs = {
            'longName': attrName,
            'keyable': keyable,
            'attributeType': attributeType,
            'defaultValue': defaultValue,
        }
        if enumName is not None:
            kwargs['enumName'] = enumName
        if minValue is not None:
            kwargs['minValue'] = minValue
        if maxValue is not None:
            kwargs['maxValue'] = maxValue

        pm.addAttr(node, **kwargs)

        if not keyable:
            pm.setAttr('{}.{}'.format(node, attrName), e=True, channelBox=True)

    return node.attr(attrName)


def add_sep_attr(obj,sepName):
    if not sepName:
        pm.warning("Please enter a name")
        return
    if not obj or not pm.objExists(obj):
        pm.warning("请先指定有效对象")
        return

    obj = pm.PyNode(obj)
    attr_name = "sepAttr_{}".format(sepName)
    if obj.hasAttr(attr_name):
        return obj.attr(attr_name)

    pm.addAttr(obj, ln=attr_name, nn="__________", at="enum",
                en="{}:".format(sepName))
    pm.setAttr("{}.{}".format(obj, attr_name), channelBox=True, lock=True)
    return obj.attr(attr_name)


def createNode(nodeType, nodeName, editData=None):
    if not pm.objExists(nodeName):
        node = pm.createNode(nodeType, n=nodeName)
    else:
        node = pm.PyNode(nodeName)

    for attrName, value in (editData or {}).items():
        if not node.hasAttr(attrName):
            pm.warning('{} 没有属性：{}'.format(node, attrName))
            continue
        try:
            node.attr(attrName).set(value)
        except (RuntimeError, TypeError, ValueError):
            pm.warning('无法设置 {}.{} = {}'.format(node, attrName, value))

    return pm.PyNode(node)


def build_bend_logic(source, roll, rollAix, angle, falloff, followParent, target, weight, next_weight, aixs, ctrl, prefix):
    prefix_ = prefix_logic(prefix)
    # addAttr #############################
    add_sep_attr(ctrl, prefix + 'Bend')
    on_off = addAttr(ctrl, 'bendOn', prefix, attributeType="float", keyable=True, minValue=0, maxValue=1, defaultValue=1)
    offset = addAttr(ctrl, 'bendOffset', prefix, attributeType="float", keyable=True, defaultValue=0)
    #######################################

    pm.undoInfo(openChunk=True)
    try:
        mult_RollFalloffRvs = createNode('multDL', f'{source}_bend_mult_RollFalloffRvs', {'input2': -0.1})
        mult_Roll = createNode('multDL', f'{source}_bend_mult_Roll', {'input2': 0.1})
        add_RollStart = createNode('addDL', f'{target}_{prefix_}bend_add_RollStart',{'input1': weight})
        clamp_RollStart = createNode('clamp', f'{target}_{prefix_}bend_clamp_RollStart',{'maxR':1})
        remap_RollWeight = createNode('remapValue', f'{target}_{prefix_}bend_remap_RollWeight',{'inputMax': next_weight})
        mult_RotWeight = createNode('multDL', f'{target}_{prefix_}bend_mult_RotWeight')
        mult_RotAngle = createNode('multDL', f'{target}_{prefix_}bend_mult_RotAngle')
        remap_AngleWeight = createNode('remapValue', f'{target}_{prefix_}bend_remap_AngleWeight',{'inputValue': 1-weight})
        add_weightOffset = createNode('addDL', f'{target}_{prefix_}bend_add_weightOffset')
        mult_weightOnOff = createNode('multDL', f'{target}_{prefix_}bend_mult_weightOnOff')
        mult_RotAix = createNode('multiplyDivide', f'{target}_{prefix_}bend_mult_RotAix',{'input2': (0,0,0)})

        pm.connectAttr(falloff, f'{mult_RollFalloffRvs}.input1', force=True)
        pm.connectAttr(angle, f'{mult_RotAngle}.input2', force=True)
        pm.connectAttr(roll, f'{mult_Roll}.input1', force=True)
        pm.connectAttr(f'{mult_Roll}.output', f'{remap_RollWeight}.inputValue', force=True)
        pm.connectAttr(f'{mult_RollFalloffRvs}.output', f'{add_RollStart}.input2', force=True)
        pm.connectAttr(f'{add_RollStart}.output', f'{clamp_RollStart}.inputR', force=True)
        pm.connectAttr(f'{clamp_RollStart}.outputR', f'{remap_RollWeight}.inputMin', force=True)
        pm.connectAttr(f'{remap_RollWeight}.outValue', f'{mult_RotWeight}.input1', force=True)
        pm.connectAttr(f'{mult_RotWeight}.output', f'{mult_RotAngle}.input1', force=True)
        pm.connectAttr(f'{remap_AngleWeight}.outValue', f'{add_weightOffset}.input1', force=True)
        pm.connectAttr(offset, f'{add_weightOffset}.input2', force=True)
        pm.connectAttr(f'{add_weightOffset}.output', f'{mult_weightOnOff}.input1', force=True)
        pm.connectAttr(on_off, f'{mult_weightOnOff}.input2', force=True)
        pm.connectAttr(f'{mult_weightOnOff}.output', f'{mult_RotWeight}.input2', force=True)

        for aix in aixs:
            pm.connectAttr(f'{mult_RotAngle}.output', f'{mult_RotAix}.input1{aix}', force=True)
            pm.connectAttr(f'{mult_RotAix}.output{aix}', f'{target}.rotate{aix}', force=True)
            for i in range(0,len(aixs)):
                value = 0
                if rollAix.getEnums()[i] == aix:
                    value = 1
                pm.setDrivenKeyframe(f'{mult_RotAix}.input2{aix}',
                                cd=rollAix,
                                driverValue=i,
                                value=value
                            )
                
        # followParent logic ###########################
        rev_followParent = createNode('reverse', f'{target}_{prefix_}bend_rev_followParent')
        pm.connectAttr(f'{remap_RollWeight}.outValue', f'{rev_followParent}.inputX', force=True)
        pm.connectAttr(f'{rev_followParent}.outputX', followParent, force=True)
        ################################################

        print(f'Success: Logic connected from {source} to {target}')
    finally:
        pm.undoInfo(closeChunk=True)
    return remap_AngleWeight

def create_group(obj, name, prefix=''):
    prefix_ = prefix_logic(prefix)
    name = prefix_ + name
    if not pm.objExists(name):
        group = pm.createNode('transform',n=name)
    group = pm.PyNode(name)
    pm.parent(obj, group)
    return group

def create_curve_ctrl(objs):
    ctrl_group_list = []
    for obj in objs:
        ctrl_curve = pm.curve(d=1, p=[(-0.05, -0.05, 0), (0.05, -0.05, 0), (0.05, 0.05, 0), (-0.05, 0.05, 0), (-0.05, -0.05, 0)], n=obj + '_ctrl')
        ctrl_curve.getShape().overrideEnabled.set(1)
        ctrl_curve.getShape().overrideColor.set(20)
        ctrl_group = create_group(ctrl_curve, obj + '_ctrl_offset_grp')
        pm.connectAttr(f'{obj}.lpx', f'{ctrl_group}.tx', force=True)
        pm.connectAttr(f'{obj}.lpy', f'{ctrl_group}.ty', force=True)
        pm.connectAttr(f'{ctrl_curve}.tx', f'{obj}.tx', force=True)
        pm.connectAttr(f'{ctrl_curve}.ty', f'{obj}.ty', force=True)
        ctrl_group_list.append(ctrl_group)
        for attr in ['tz','rx','ry','rz','sx','sy','sz','v']:
            pm.setAttr(f'{ctrl_curve}.{attr}', lock=True, keyable=False, channelBox=False)
    return ctrl_group_list

# create AngleWeight ctrl #############################################
def create_AngleWeight_ctrl(bend_ctrl, ctrl_num, remap_AngleWeight_list, prefix):
    prefix_ = prefix_logic(prefix)
    angleWeightCtrlVis = addAttr(bend_ctrl, 'weightVis', prefix, attributeType="bool", keyable=False, defaultValue=0)
    loc_list = []
    for i in range(0,ctrl_num):
        loc = prefix_ + f'bend_AngleWeight_{i:02d}'
        if not pm.objExists(loc):
            loc = pm.spaceLocator(n = loc)
        else:
            loc = pm.PyNode(loc)
        loc_list.append(loc)
        loc_plusMinusAverage = createNode('plusMinusAverage', f'{loc}_plusMinusAverage')
        pm.connectAttr(f'{loc}.tx', f'{loc_plusMinusAverage}.input2D[0].input2Dx', force=True)
        pm.connectAttr(f'{loc}.ty', f'{loc_plusMinusAverage}.input2D[0].input2Dy', force=True)
        pm.connectAttr(f'{loc}.localPositionX', f'{loc_plusMinusAverage}.input2D[1].input2Dx', force=True)
        pm.connectAttr(f'{loc}.localPositionY', f'{loc_plusMinusAverage}.input2D[1].input2Dy', force=True)
        for remap_AngleWeight in remap_AngleWeight_list:
            pm.connectAttr(f'{loc_plusMinusAverage}.output2Dx', f'{remap_AngleWeight}.value[{i}].value_Position')
            pm.connectAttr(f'{loc_plusMinusAverage}.output2Dy', f'{remap_AngleWeight}.value[{i}].value_FloatValue')
            pm.setAttr(f'{remap_AngleWeight}.value[{i}].value_Interp', 1)

            # fix remap #################################
            if i == ctrl_num-1:
                pm.setAttr(f'{remap_AngleWeight}.value[{ctrl_num}].value_Position', 10)
                pm.connectAttr(f'{loc_plusMinusAverage}.output2Dy', f'{remap_AngleWeight}.value[{ctrl_num}].value_FloatValue')
                pm.setAttr(f'{remap_AngleWeight}.value[{ctrl_num}].value_Interp', 1)
                pm.setAttr(f'{remap_AngleWeight}.value[{ctrl_num+1}].value_Position', 11)
                pm.setAttr(f'{remap_AngleWeight}.value[{ctrl_num+1}].value_FloatValue', 1)
                pm.setAttr(f'{remap_AngleWeight}.value[{ctrl_num+1}].value_Interp', 1)
            ################################################
                       
        pm.setAttr(f'{loc}.localPositionX', i / (ctrl_num-1))
        pm.setAttr(f'{loc}.localPositionY', i / (ctrl_num-1))
        pm.setAttr(f'{loc}.localPositionX', lock=True, keyable=False, channelBox=True)
        pm.setAttr(f'{loc}.localPositionY', lock=True, keyable=False, channelBox=True)
        loc.localScaleX.set(0.1)
        loc.localScaleY.set(0.1)
        loc.localScaleZ.set(0.1)
        loc.getShape().v.set(0)
    AngleWeight_loc_grp = create_group(loc_list, 'bend_AngleWeight_loc_grp', prefix)

    border_curve = pm.curve(d=1, p=[(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 0)], n=prefix_ + 'bend_AngleWeight_border')
    border_curve.template.set(1)
    border_curve.getShape().template.set(1)
    border_curve.getShape().lineWidth.set(2)
    border_group = create_group(border_curve, border_curve + '_offset_grp')

    line_list = []
    for i in range(0,len(loc_list)-1):
        line = pm.curve(d=1,p=[(1,0,0),(2,0,0)],n='{}_and_{}_line'.format(loc_list[i],loc_list[i+1]))
        line.template.set(1)
        line.getShape().template.set(1)
        line.getShape().lineWidth.set(2)
        line.inheritsTransform.set(0)
        loc_list[i].getShape().worldPosition[0] >> line.getShape().controlPoints[0]
        loc_list[i+1].getShape().worldPosition[0] >> line.getShape().controlPoints[1]
        line_list.append(line)
    line_grp = create_group(line_list, 'bend_AngleWeight_line_grp', prefix)

    loc_ctrl_grp = create_group(create_curve_ctrl(loc_list), 'bend_loc_ctrl_grp', prefix)
    #AngleWeight_loc_grp_scale_mdl = createNode('multDL', f'{AngleWeight_loc_grp}_scale_multDL', {'input2': 0.5})
    #pm.connectAttr(f'{AngleWeight_loc_grp}.sx', f'{AngleWeight_loc_grp_scale_mdl}.input1', force=True)
    #pm.connectAttr(f'{AngleWeight_loc_grp_scale_mdl}.output', f'{AngleWeight_loc_grp}.sy', force=True)
    #pm.connectAttr(f'{AngleWeight_loc_grp_scale_mdl}.output', f'{AngleWeight_loc_grp}.sz', force=True)
    #pm.setAttr(f'{AngleWeight_loc_grp}.sx', 2)
    #pm.setAttr(f'{AngleWeight_loc_grp}.sy', lock=True, keyable=False, channelBox=False)
    #pm.setAttr(f'{AngleWeight_loc_grp}.sz', lock=True, keyable=False, channelBox=False)

    AngleWeight_grp = create_group([loc_ctrl_grp,AngleWeight_loc_grp,line_grp,border_group], 'bend_AngleWeight_grp', prefix)
    pm.connectAttr(angleWeightCtrlVis, f'{AngleWeight_grp}.v', force=True)
    bend_ctrl_grp = create_group(AngleWeight_grp, 'bend_ctrl_grp', prefix)

    return bend_ctrl_grp
#######################################################################
        
# connection one followParent ######################
def connection_one_followParent(bend_list, driver_list, driven_list, attr, aixs=None):
    aixs = list(aixs or ['t', 'r'])
    if not (len(bend_list) == len(driver_list) == len(driven_list)):
        raise ValueError("Bend、Driver、Driven 列表数量必须一致")
    for obj, driver, driven in zip(bend_list, driver_list, driven_list):
        followParent = f'{obj}.{attr}'
        for aix in aixs:
            mult_followParent = createNode('multiplyDivide', f'{driven}_{aix}_followParent_multDL')
            for i in ['x','y','z']:
                pm.connectAttr(followParent, f'{mult_followParent}.i2{i}', force=True)
                pm.connectAttr(f'{driver}.{aix}{i}', f'{mult_followParent}.i1{i}', force=True)
                pm.connectAttr(f'{mult_followParent}.o{i}', f'{driven}.{aix}{i}', force=True)
####################################################

# connection two followParent ######################
def connection_two_followParent(a_bend_list, b_bend_list, driver_list, driven_list,
                                 a_attr, b_attr, aixs=None):
    aixs = list(aixs or ['t', 'r'])
    if not (len(a_bend_list) == len(b_bend_list) == len(driver_list) == len(driven_list)):
        raise ValueError("A-Bend、B-Bend、Driver、Driven 列表数量必须一致")
    for a_obj, b_obj, driver, driven in zip(a_bend_list, b_bend_list, driver_list, driven_list):
        a_followParent = f'{a_obj}.{a_attr}'
        b_followParent = f'{b_obj}.{b_attr}'
        mult_followParent = createNode('multDL', f'{driven}_followParent_multDL')
        pm.connectAttr(a_followParent, f'{mult_followParent}.i1', force=True)
        pm.connectAttr(b_followParent, f'{mult_followParent}.i2', force=True)
        for aix in aixs:
            mult_aixFollowParent = createNode('multiplyDivide', f'{driven}_{aix}_followParent_multDL')
            for i in ['x','y','z']:
                pm.connectAttr(f'{mult_followParent}.output', f'{mult_aixFollowParent}.i2{i}', force=True)
                pm.connectAttr(f'{driver}.{aix}{i}', f'{mult_aixFollowParent}.i1{i}', force=True)
                pm.connectAttr(f'{mult_aixFollowParent}.o{i}', f'{driven}.{aix}{i}', force=True)
####################################################

def get_bend_ctrl(bend_ctrl_name='', prefix=''):
    prefix_ = prefix_logic(prefix)
    name = '_'.join((prefix_ + bend_ctrl_name).split(' '))
    if not pm.objExists(name):
        bend_ctrl = create_text_control(name,prefix,view='Bend',center_pivot=True,create_border=False)
        bend_ctrl_grp = create_group(bend_ctrl, 'bend_ctrl_grp', prefix)
    else:
        bend_ctrl = name
    return bend_ctrl

def create_bend_system(bend_list, ctrl_list, bend_ctrl, prefix='', aixs=None, remap_AngleWeight_list=None):
    aixs = list(aixs or ['Z', 'Y', 'X'])
    if len(bend_list) != len(ctrl_list):
        raise ValueError("Bend列表与控制列表数量必须一致")
    if not bend_list:
        raise ValueError("Bend列表不能为空")
    if remap_AngleWeight_list is None:
        remap_AngleWeight_list = []
    add_sep_attr(bend_ctrl, prefix + 'Bend')
    roll = addAttr(bend_ctrl, 'roll', prefix, attributeType="float", minValue=0, maxValue=10, keyable=True)
    rollAix = addAttr(bend_ctrl, 'rollAix', prefix, attributeType="enum", enumName=f"{':'.join(aixs)}", defaultValue=0, keyable=True)
    angle = addAttr(bend_ctrl, 'angle', prefix, attributeType="float", keyable=True, defaultValue=70)
    falloff = addAttr(bend_ctrl, 'falloff', prefix, attributeType="float", keyable=True, minValue=0, maxValue=10, defaultValue=1)
    for i, obj in enumerate(bend_list):
        followParent = addAttr(obj, 'followParent', prefix, attributeType="float", keyable=True, minValue=0, maxValue=1, defaultValue=0)
        weight = i / len(bend_list)
        next_weight = (i + 1) / len(bend_list)
        remap_AngleWeight = build_bend_logic(bend_ctrl, roll, rollAix, angle, falloff, followParent, obj, weight, next_weight, aixs, ctrl_list[i], prefix)
        remap_AngleWeight_list.append(remap_AngleWeight)
    return remap_AngleWeight_list

def main(bend_list, ctrl_list, prefix='', bend_ctrl_name='', aixs=None,
         create_bend_system_def=False, create_AngleWeight_ctrl_def=False,
         ctrl_num=5, remap_AngleWeight_list=None):
    aixs = list(aixs or ['Z', 'Y', 'X'])
    remap_AngleWeight_list = list(remap_AngleWeight_list or [])
    bend_ctrl = get_bend_ctrl(bend_ctrl_name, prefix)
    if create_bend_system_def:
        create_bend_system(bend_list, ctrl_list, bend_ctrl, prefix, aixs)
    elif create_AngleWeight_ctrl_def:
        create_AngleWeight_ctrl(bend_ctrl, ctrl_num, remap_AngleWeight_list, prefix)


if __name__ == '__main__':

    bend_list = pm.ls(sl=True)
    ctrl_list = pm.ls(sl=True)
    prefix = ''
    bend_ctrl_name = ''
    aixs = ['Z','Y','X']
    remap_AngleWeight_list = []


    # create AngleWeight ctrl ------------------------
    ctrl_num = 5

    # connection followParent ------------------------
    driver_list = pm.ls(sl=True)
    driven_list = pm.ls(sl=True)
    followParent_aixs=['t','r']

    # connection one followParent
    followParent_attr = 'followParent'
    connection_one_followParent(bend_list, driver_list, driven_list, followParent_attr, followParent_aixs)

    # connection two followParent
    a_bend_list = pm.ls(sl=True)
    b_bend_list = pm.ls(sl=True)
    a_followParent_attr = 'body_followParent'
    b_followParent_attr = 'tail_followParent'
    connection_two_followParent(a_bend_list, b_bend_list, driver_list, driven_list, a_followParent_attr, b_followParent_attr, followParent_aixs)