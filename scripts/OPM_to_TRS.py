import pymel.core as pm

def connect_attr(source,target,source_i=['X','Y','Z'],target_i=['X','Y','Z']):
    for a, b in list(zip(source_i,target_i)):
        pm.connectAttr(source+a, target+b, f=True)

def create_node(nodeType,name):
    if not pm.objExists(name):
        node = pm.createNode(nodeType,n=name)
    else:
        node = name
    return node
    
def connect_matrix_to_transform_attributes(joint, source_matrix_attr):
    """
    将源矩阵连接到骨骼的位移、旋转和缩放属性,同时剔除jointOrient影响
    替代原本连接到offsetParentMatrix的方式
    """
    # 获取骨骼的旋转顺序
    joint_rotate_order = pm.getAttr(joint + '.rotateOrder')
    
    # 1. 分解源矩阵，将位移和缩放连接到骨骼
    decompose_source = create_node('decomposeMatrix', name=joint + '_source_decompose')
    pm.connectAttr(source_matrix_attr, decompose_source + '.inputMatrix',f=True)
    #pm.setAttr(decompose_source + '.inputRotateOrder', joint_rotate_order)
    
    fix_jointOrient(joint)
    
    # 直接连接位移和缩放到骨骼
    connect_attr(decompose_source + '.outputTranslate', joint + '.translate')
    if pm.connectionInfo(joint + '.scaleX', isDestination=True):
        scale_mult = create_node('multiplyDivide', name=joint + '_scale_mult')
        scale_source = pm.listConnections(joint + '.scaleX', s=True,d=False)[0]
        connect_attr(scale_source+'.output',scale_mult+'.input1', source_i=['R','G','B'])
        connect_attr(decompose_source + '.outputScale',scale_mult+'.input2')
        connect_attr(scale_mult + '.output', joint + '.scale')
    else:
        connect_attr(decompose_source + '.outputScale', joint + '.scale')
    connect_attr(decompose_source + '.outputShear', joint + '.shear',target_i=['XY','XZ','YZ'])
    
    # 2. 将jointOrient转换为矩阵并求逆
    compose_orient = create_node('composeMatrix', name=joint + '_orient_compose')
    connect_attr(joint + '.jointOrient', compose_orient + '.inputRotate')
    #pm.setAttr(compose_orient + '.inputRotateOrder', joint_rotate_order)
    
    inverse_orient = create_node('inverseMatrix', name=joint + '_orient_inverse')
    pm.connectAttr(compose_orient + '.outputMatrix', inverse_orient + '.inputMatrix',f=True)
    
    # 3. 原矩阵与jointOrient逆矩阵相乘
    mult_matrix = create_node('multMatrix', name=joint + '_rotation_mult')
    pm.connectAttr(source_matrix_attr, mult_matrix + '.matrixIn[0]',f=True)
    pm.connectAttr(inverse_orient + '.outputMatrix', mult_matrix + '.matrixIn[1]',f=True)
    
    # 4. 分解新矩阵，只将旋转连接到骨骼
    decompose_rotation = create_node('decomposeMatrix', name=joint + '_rotation_decompose')
    pm.connectAttr(mult_matrix + '.matrixSum', decompose_rotation + '.inputMatrix',f=True)
    pm.connectAttr(joint + '.rotateOrder', decompose_rotation + '.inputRotateOrder',f=True)
    #pm.setAttr(decompose_rotation + '.inputRotateOrder', joint_rotate_order)
    
    # 只连接旋转到骨骼
    connect_attr(decompose_rotation + '.outputRotate', joint + '.rotate')

def fix_jointOrient(joint):
    decompose_source = joint + '_source_decompose'
    if pm.objExists(decompose_source):
        joint_orient = pm.getAttr('{}.outputRotate'.format(decompose_source))
        pm.setAttr('{}.jointOrient'.format(joint),joint_orient)
    
def cleanup_existing_connections(joint):
    """
    清理骨骼上现有的offsetParentMatrix连接
    """
    # 断开offsetParentMatrix的输入连接
    if pm.connectionInfo(joint + '.offsetParentMatrix', isDestination=True):
        source_attr = pm.connectionInfo(joint + '.offsetParentMatrix', sourceFromDestination=True)
        pm.disconnectAttr(source_attr, joint + '.offsetParentMatrix')
        
        # 确保其他变换属性没有锁定
        for attr in ['.translate', '.rotate', '.scale']:
            for axis in ['X', 'Y', 'Z']:
                full_attr = joint + attr + axis
                if not pm.getAttr(full_attr, lock=True):
                    continue
                pm.setAttr(full_attr, lock=False)
                print(f"unlock: {full_attr}")
        
        connect_matrix_to_transform_attributes(joint, source_attr)
        # 重置offsetParentMatrix为单位矩阵
        identity_matrix = pm.dt.Matrix()
        pm.setAttr(joint + '.offsetParentMatrix', identity_matrix, type='matrix')

jnts = pm.ls(sl=True,type='joint')
for jnt in jnts:
    cleanup_existing_connections(jnt)
    #fix_jointOrient(jnt)
    