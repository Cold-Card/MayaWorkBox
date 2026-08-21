import pymel.core as pm

axis = ['L','R','M']
side = ['Up','Lo']
index = ['1','2']
fbs = ['Front','Back']
no_main = ['Main']
for i in axis:
    for x in side:
        if i == 'M':
            index = ['1']
            no_main = ['Main','']
        for z in index:
            for main in no_main:
                if main == '':
                    z = ''
                lip_ctrl = pm.PyNode(f'{i}_{x}Lip{main}{z}_A_ctrl')
                zero_grp = pm.PyNode(lip_ctrl+'_zero')
                zero_attr = pm.PyNode(zero_grp+f'.{i}_{x}Lip{main}{z}_FB')
                
                pm.addAttr(lip_ctrl, ln='volume', at='double', min=0, max=10, dv=10, k=True)
                
                unit_node = pm.createNode('unitConversion',n=lip_ctrl+'_volume_unitConversion')
                unit_node.conversionFactor.set(0.1)
                MDL_node = pm.createNode('multDoubleLinear',n=lip_ctrl+'_volume_MDL')
                
                lip_ctrl.volume >> unit_node.input
                unit_node.output >> MDL_node.input2
                zero_attr >> MDL_node.input1
                
                for fb in fbs:
                    sdk_node = pm.PyNode(f'M_Head_base_blendShape_M_Head_base_{i}_{x}Lip{main}{z}_{fb}')
                
                    MDL_node.output >> sdk_node.input
            