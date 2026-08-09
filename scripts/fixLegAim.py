import pymel.core as pm

ik_names = ['Leg']
jnt_names = ['LegAim']
for x, ik_name in enumerate(ik_names):
    for i in ['L','R']:
        LegAim_fix_MD = pm.createNode('multiplyDivide',n='IK{}LegAimMultiplyDivide_{}'.format(ik_name,i))
        pm.connectAttr('IK{}LegAimUnitConversion_{}.output'.format(ik_name,i),LegAim_fix_MD+'.input1X',f=True)
        pm.connectAttr('FKIKBlend{}UnitConversion_{}.output'.format(ik_name,i),LegAim_fix_MD+'.input2X',f=True)
        pm.connectAttr(LegAim_fix_MD+'.outputX','Aim{}BM_{}.target[0].weight'.format(jnt_names[x],i),f=True)
        
        pm.sets('AllSet',add=LegAim_fix_MD)