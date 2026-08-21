import maya.cmds as cmds
def create_slide_con(new_curve, all_joint_out_skin, all_rotate_joint, all_position_out_joint, ik_all_rotate_curve, ik_all_curve, all_move_list):
    u'''
        new_curve: IK曲线\n
        all_joint_out_skin: 所有位置骨骼（IK骨骼约束的骨骼）\n
        all_rotate_joint: 所有旋转骨骼（被 all_joint_out_skin 骨骼约束的骨骼，但rx轴被 约束+表达式 控制）\n
        all_position_out_joint: 所有控制曲线的骨骼（控制器直接控制的骨骼）\n
        ik_all_rotate_curve: 用于控制IK骨骼旋转的控制器（会与 all_position_out_joint 的rx轴相加，一起控制IK骨骼的旋转）\n
        ik_all_curve: 所有控制器\n
        all_move_list: 表达式要输出的对象列表（加减节点，输入：all_rotate_joint的约束节点rx、表达式，输出：all_rotate_joint 的rx轴）
    '''
    # print(ik_all_con_joint)
    # 添加旋转数值平滑属性
    for i in range(0,len(ik_all_curve)):
        #if i % 3 != 0:
            cmds.addAttr(ik_all_curve[i], ln='rotateSmoothA', min=0, dv=1, at='double')
            cmds.setAttr((ik_all_curve[i] + '.rotateSmoothA'), e=1, keyable=True)
            cmds.addAttr(ik_all_curve[i], ln='rotateSmoothB', min=0, dv=1, at='double')
            cmds.setAttr((ik_all_curve[i] + '.rotateSmoothB'), e=1, keyable=True)
    # 创建骨骼滑动表达式
    # 获取所有点
    #points = cmds.ls(new_curve[0] + '.cv[*]', fl=1)
    #points = points[::3]
    ## 先获取每个点的u值
    all_point_u_num = []
    for i in range(len(ik_all_rotate_curve)):
        #cmds.select(points[i])
        #cluster = cmds.cluster()
        loc = cmds.spaceLocator()
        cmds.delete(cmds.parentConstraint(all_position_out_joint[i], loc))
        #cmds.delete(cluster)
        nearestPointOnCurve = cmds.createNode('nearestPointOnCurve',name=(all_position_out_joint[i] + '_nearestPointOnCurve'))
        cmds.connectAttr(new_curve[0] + '.worldSpace[0]', nearestPointOnCurve + '.inputCurve')
        decomposeMatrix = cmds.createNode('decomposeMatrix',name=(all_position_out_joint[i] + '_decomposeMatrix'))
        cmds.connectAttr(loc[0] + '.worldMatrix[0]', decomposeMatrix + '.inputMatrix')
        # cmds.connectAttr(ik_all_con_joint[i] + '.worldMatrix[0]', decomposeMatrix + '.inputMatrix')
        cmds.connectAttr(decomposeMatrix + '.outputTranslate', nearestPointOnCurve + '.inPosition')
        num = cmds.getAttr(nearestPointOnCurve + '.result.parameter')
        # text = nearestPointOnCurve + '.result.parameter'
        # all_point_u_num.append(text)
        all_point_u_num.append(num)
        cmds.delete(loc, nearestPointOnCurve, decomposeMatrix)
    # print(all_point_u_num)

    # 创建实时获取骨骼具体位置u值的节点
    all_joint_nearestPointOnCurve = []
    for i in range(len(all_joint_out_skin)):
        nearestPointOnCurve = cmds.createNode('nearestPointOnCurve',name=(all_joint_out_skin[i] + '_nearestPointOnCurve'))
        cmds.connectAttr(new_curve[0] + '.worldSpace[0]', nearestPointOnCurve + '.inputCurve')
        decomposeMatrix = cmds.createNode('decomposeMatrix',name=(all_joint_out_skin[i] + '_decomposeMatrix'))
        cmds.connectAttr(all_joint_out_skin[i] + '.worldMatrix[0]', decomposeMatrix + '.inputMatrix')
        cmds.connectAttr(decomposeMatrix + '.outputTranslate', nearestPointOnCurve + '.inPosition')
        all_joint_nearestPointOnCurve.append(nearestPointOnCurve)
    # print(all_joint_nearestPointOnCurve)

    # 添加指针偏移属性
    # 添加表达式,统一获取控制器旋转数值，再获取当前骨骼u值在某个范围,然后计算权重乘以旋转数值
    # 按顺序获取u值
    all_point_u_num[0] = 0.0
    all_point_u_num[-1] = 1.0
    # 获取每个间隔具体u值长度
    all_point_u_num_length_text = str(all_point_u_num[1] - all_point_u_num[0])
    for i in range(1,len(all_point_u_num)-1):
        all_point_u_num_length_text = all_point_u_num_length_text + ',' + str(all_point_u_num[i + 1] - all_point_u_num[i])
    all_point_u_num_length_text = all_point_u_num_length_text + ',' + str(all_point_u_num[-1] - all_point_u_num[-2])
    # print(all_point_u_num_length_text)
    all_point_u_num_text = str(all_point_u_num[0])
    for i in range(1, len(all_point_u_num)):
        all_point_u_num_text = all_point_u_num_text + ',' + str(all_point_u_num[i])
    # print(text)
    # 按顺序获取旋转数值
    rote_text = all_position_out_joint[0] + '.rotateX'
    for i in range(1, len(all_position_out_joint)):
        rote_text = rote_text + ',' + str(all_position_out_joint[i]) + '.rotateX'

    # 按顺序获取当前指针平滑数值
    smooth_text = ''
    for i in range(0,len(ik_all_curve)-1):
        text = ik_all_curve[i] + '.rotateSmoothB,' + ik_all_curve[i+1] + '.rotateSmoothA,' + '0.0,' 
        '''if i % 3 == 0:
            text = '0.0,'
        else:
            text = ik_all_curve[i] + '.smooth,'''
        smooth_text += text
    smooth_text = '0.0,' + smooth_text[:-1]

    # 创建基础函数
    expression_txt = (
            'float $all_point_u_num[] = {' + all_point_u_num_text + '};\n'
            'float $all_point_u_num_length[] = {' + all_point_u_num_length_text + '};\n'
            'float $all_curve_rote_num[] = {' + rote_text + '};\n'
            'float $all_curve_smooth_num[] = {' + smooth_text + '};\n'
            '//二分查找\n'
            'global proc int findFloatRange(float $targetNum, float $list[]) {\n'
            '    int $left = 0;\n'
            '    int $right = size($list) - 1;\n'
            '    while ($left <= $right) {\n'
            '        int $mid = ($left + $right) / 2;\n'
            '        float $midVal = $list[$mid];\n'
            '        if (($right-$left)<=1) {\n'
            '            return($left);\n'
            '        } else if ($midVal < $targetNum) {\n'
            '            $left = $mid;\n'
            '        } else {\n'
            '            $right = $mid;\n'
            '        }\n'
            '    }\n'
            '}\n'
            # 'global proc int nearSearch(float $targetNum, float $list[], int $position) {\n'
            # '    if($list[$position]<=$targetNum && $list[$position+1]>=$targetNum){\n'
            # '        return($position);\n'
            # '    }else{\n'
            # '        for($i=0;$i<size($list);$i++){\n'
            # '            $position = $position+1;\n'
            # '            if($list[$position]<=$targetNum && $list[$position+1]>=$targetNum){\n'
            # '                return($position);\n'
            # '            }\n'
            # '        }\n'
            # '    }\n'
            # '}\n'
            '//临近查询\n'
            'global proc int nearSearch(float $targetNum, float $list[], int $position) {\n'
            '    int $size = size($list);\n'
            # '    // 边界保护：确保 position+1 不越界\n'
            # '    if ($position < 0 || $position >= $size-1) {\n'
            # '        $position = 0; // 重置为安全起点\n'
            # '    }\n'
            '    // 初始位置检查\n'
            '    if ($list[$position] <= $targetNum && $list[$position+1] >= $targetNum) {\n'
            '        return $position;\n'
            '    } \n'
            '    // 遍历后续位置\n'
            '    else {\n'
            '        for ($i = 0; $i < $size-1; $i++) { // 限制循环范围避免越界\n'
            '            $position = ($position + 1) % ($size-1); // 循环查找或重置位置\n'
            '            if ($list[$position] <= $targetNum && $list[$position+1] >= $targetNum) {\n'
            '                return $position;\n'
            '            }\n'
            '        }\n'
            '        // 所有路径必须返回 int：未找到时返回 $position 标识失败\n'
            '        return $position; \n'
            '    }\n'
            '}\n'
            '// 平滑\n'
            'global proc float smooth(float $list[], float $fn_weight, int $position) {\n'
            '    // 获取当前范围内的指针属性\n'
            '    int $f_num = $position*3+1;\n'
            '    int $e_num = $position*3+2;\n'
            '    // 获取前端权重\n'
            '    float $pow_num_f = $list[$f_num];\n'
            '    float $f_weight = `pow $fn_weight $pow_num_f`;\n'
            '    // 获取后端权重\n'
            '    float $pow_num_e = $list[$e_num];\n'
            '    float $e_weight = `pow (1-$fn_weight) $pow_num_e`;\n'
            '    //输出前权重\n'
            '    float $out_weight = $f_weight/($f_weight+$e_weight);\n'
            '    return $out_weight;\n'
            '}\n'
    )

    an_num = '$' + all_joint_out_skin[0] + '_u_num'
    an_position = '$' + all_joint_out_skin[0] + '_position'
    an_weight = '$' + all_joint_out_skin[0] + '_weight'
    an_num_distance = '$' + all_joint_out_skin[0] + '_u_num_distance'
    text = (
            'float ' + an_num + ' = ' + all_joint_nearestPointOnCurve[0] + '.result.parameter;\n'
            'int ' + an_position + ' = findFloatRange(' + an_num + ', $all_point_u_num);\n'
            'float ' + an_num_distance + ' = ' + an_num + '-$all_point_u_num[' + an_position + '];\n'
            'float ' + an_weight + ' = 0.0;\n'
            'if(' + an_num_distance + ' != 0.0){\n'
            # '    ' + an_weight + ' = smoothstep(0, 1,((' + an_num_distance + ')/($all_point_u_num_length['+an_position+'])));};\n'
            '    ' + an_weight + ' = smooth($all_curve_smooth_num, ((' + an_num_distance + ')/($all_point_u_num_length['+an_position+'])), ' + an_position + ');}\n'
            # '' + all_rotate_joint[0] + '.rotateX = $all_curve_rote_num[' + an_position + ']*(1-' + an_weight + ')+$all_curve_rote_num[' + an_position + '+1]*' + an_weight + ';\n'
            '' + all_move_list[0] + '.input1D[1] = $all_curve_rote_num[' + an_position + ']*(1-' + an_weight + ')+$all_curve_rote_num[' + an_position + '+1]*' + an_weight + ';\n'
    )
    add_text = text
    # expression_txt += add_text
    f_an_position = an_position
    for i in range(1,len(joint_chain)):
        an_num = '$' + all_joint_out_skin[i] + '_u_num'
        an_num_distance = '$' + all_joint_out_skin[i] + '_u_num_distance'
        an_position = '$' + all_joint_out_skin[i] + '_position'
        an_weight = '$' + all_joint_out_skin[i] + '_weight'
        text = (
                'float ' + an_num + ' = ' + all_joint_nearestPointOnCurve[i] + '.result.parameter;\n'
                'int ' + an_position + ' = nearSearch('+an_num+', $all_point_u_num, ' + f_an_position + ');\n'
                'float ' + an_num_distance + ' = ' + an_num + '-$all_point_u_num[' + an_position + '];\n'
                'float ' + an_weight + ' = 0.0;\n'
                'if(' + an_num_distance + ' != 0.0){\n'
                # '    ' + an_weight + ' = smoothstep(0, 1,((' + an_num_distance + ')/($all_point_u_num_length['+an_position+'])));};\n'
                '    ' + an_weight + ' = smooth($all_curve_smooth_num, ((' + an_num_distance + ')/($all_point_u_num_length['+an_position+'])), ' + an_position + ');}\n'
                # '' + all_rotate_joint[i] + '.rotateX = $all_curve_rote_num[' + an_position + ']*(1-' + an_weight + ')+$all_curve_rote_num[' + an_position + '+1]*' + an_weight + ';\n'
                '' + all_move_list[i] + '.input1D[1] = $all_curve_rote_num[' + an_position + ']*(1-' + an_weight + ')+$all_curve_rote_num[' + an_position + '+1]*' + an_weight + ';\n'
        )
        add_text += text
        f_an_position = an_position
    expression_txt += add_text
    # print(expression_txt)
    cmds.expression(s=expression_txt, ae=1, uc='all', o='', n=(expr_name + '_expression'))
    # 添加表达式开关
    '''cmds.addAttr(top_curve, ln='close_expression', at='bool')
    cmds.setAttr(top_curve + '.close_expression', e=1, keyable=1, channelBox=True)
    condition = cmds.createNode('condition')
    cmds.connectAttr((top_curve + '.close_expression'), (condition + '.firstTerm'))
    cmds.setAttr(condition + '.colorIfFalseR', 2)
    cmds.connectAttr((condition + '.outColorR'), (expr_name + '_expression.nodeState'))'''

    return all_joint_nearestPointOnCurve


# IK骨骼链
joint_chain = cmds.ls(sl=True)
# 表达式控制开关
#top_curve = 'Visibility_ctrl'
# 表达式名字
expr_name = 'S_rotateOffset'

new_curve = ['S_crv'] #IK曲线\n
all_joint_out_skin = cmds.ls(sl=True) #所有位置骨骼（IK骨骼约束的骨骼）\n
all_rotate_joint = cmds.ls(sl=True) #所有旋转骨骼（被 all_joint_out_skin 骨骼约束的骨骼，但rx轴被 约束+表达式 控制）\n
all_position_out_joint = cmds.ls(sl=True) #所有控制曲线的骨骼（控制器直接控制的骨骼）\n
ik_all_rotate_curve = cmds.ls(sl=True) #用于控制IK骨骼旋转的控制器（会与 all_position_out_joint 的rx轴相加，一起控制IK骨骼的旋转）\n
ik_all_curve = cmds.ls(sl=True) #所有控制器\n
#all_move_list = cmds.ls(sl=True) #表达式要输出的对象列表（加减节点，输入：all_rotate_joint的约束节点rx、表达式，输出：all_rotate_joint 的rx轴）
all_move_list = []
for i in range(len(all_joint_out_skin)):
    joint = cmds.listRelatives(all_joint_out_skin[i], c=1,type='joint')     # 就是 all_rotate_joint ，放在 all_joint_out_skin 层级下
    parentConstraint = cmds.parentConstraint(all_joint_out_skin[i], joint, mo=1)
    an = cmds.listConnections(parentConstraint[0] + '.constraintRotateX', p=1, d=1)
    # print(an)
    cmds.disconnectAttr(parentConstraint[0] + '.constraintRotateX', an[0])
    plusMinusAverage = cmds.createNode('plusMinusAverage', n=(all_joint_out_skin[i] + '_plusMinusAverage'))
    all_move_list.append(plusMinusAverage)
    # print(an)
    cmds.connectAttr(parentConstraint[0]+'.constraintRotateX', plusMinusAverage+'.input1D[0]')
    cmds.connectAttr(plusMinusAverage+'.output1D', joint[0]+'.rotateX')

cmds.select(cl=True)
create_slide_con(new_curve, all_joint_out_skin, all_rotate_joint, all_position_out_joint, ik_all_rotate_curve, ik_all_curve, all_move_list)