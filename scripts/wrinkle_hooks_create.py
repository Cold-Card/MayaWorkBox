import pymel.core as pm
import re

parts = ['Brow','Nose','UpCheek','Mouth']
general_pose = ['General','{}_{}_Up','{}_{}_Down','{}_{}_Left','{}_{}_Right']
combo_pose = ['Combo','{}_{}_RightUp','{}_{}_RightDown','{}_{}_LeftUp','{}_{}_LeftDown']
twist_pose = ['Twist','{}_{}_TwistNeg','{}_{}_TwistPos']
IMO_pose = ['IMO','{}_Inn{}_Up','{}_Inn{}_Down','{}_Inn{}_Left','{}_Inn{}_Right']

axial_dict ={
    'UD':['Up','Down'],
    'LR':['Left','Right'],
    'RUD':['RightUp','RightDown'],
    'LUD':['LeftUp','LeftDown'],
    'Twist':['TwistPos','TwistNeg']
    }

all_pose = {
    'Brow':[general_pose,combo_pose[0:3]],
    'Nose':[general_pose],
    'UpCheek':[general_pose],
    'Mouth':[general_pose,combo_pose]
    }

driver_dict = {
    'Brow':['{}_{}1_A_jnt','{}_{}_A_ctrl'],
    'Nose':['{}_{}_A_ctrl_zero','{}_{}_A_ctrl'],
    'UpCheek':['{}_{}_A_ctrl_zero','{}_{}_A_ctrl'],
    'Mouth':['{}_{}_A_ctrl_zero','{}_{}_A_ctrl']
}

def get_driver(t_attr):
    axial = t_attr.split('_')[-1]
    for key, value in axial_dict.items():
        if axial in value:
            posNeg = value.index(axial) 
            print(axial, posNeg)  # pos = 0, neg = 1
            if posNeg == 0:
                posNeg = 1
            elif posNeg == 1:
                posNeg = -1
            return key, posNeg
        else:
            continue

def auto_createGroup(nodeName): 
    if not pm.objExists(nodeName):
        return
    for x in ['_ofs','_con','_drv']:
        if not pm.objExists(nodeName+x):
            pm.group(nodeName,n=nodeName+x)

def create_hooks():
    if not pm.objExists('wrinkle_hooks'):
        hooks = pm.createNode('transform',n='wrinkle_hooks')
    else:
        hooks = pm.PyNode('wrinkle_hooks')
    for x in ['t','r','s']:
        for i in ['x','y','z']:
            hooks.attr(x+i).set(l=True,cb=False,k=False)
    hooks.v.set(l=True,cb=False,k=False)  
    return hooks 

def auto_createNode(nodeType,nodeName,editData={}):
    if not pm.objExists(nodeName):
        if nodeType == 'locator':
            node = pm.spaceLocator(n=nodeName)
        else:
            node = pm.createNode(nodeType,n=nodeName)
    else:
        node = pm.PyNode(nodeName)
    if editData:
        for attrName, value in editData.items():
            if node.hasAttr(attrName):
                try:
                    node.attr(attrName).set(value)
                except:
                    continue
            else:
                print('{} no find attr: {}'.format(node,attrName))
    return node

def auto_addAttr(nodeName,attrName,min_val=0,max_val=1,dv_val=0): 
    if not pm.objExists(nodeName): 
        print('{} no find'.format(nodeName))
        return
    if not nodeName.hasAttr(attrName):
        nodeName.addAttr(attrName,at='double',min=min_val,max=max_val,dv=dv_val,k=1)
    return nodeName.attr(attrName)

def auto_addAttr_enum(nodeName,attrName,niceName,enumList):
    if not pm.objExists(nodeName): 
        print('{} no find'.format(nodeName))
        return
    if not nodeName.hasAttr(attrName):
        nodeName.addAttr(attrName,at='enum',en=enumList,nn=niceName)
        nodeName.attr(attrName).set(l=True,cb=True)
    return nodeName.attr(attrName)

def auto_connectAttr(t_attr,limit=True,neg=False):

    return

def auto_sdk(driver,driven,keys={}):
    keys_list = list(keys.keys())
    for driver_value, driven_value in keys.items():
        in_tangent_type = 'linear'
        out_tangent_type = 'linear'
        if driver_value == keys_list[0]:
            in_tangent_type = 'clamped'
        elif driver_value == keys_list[-1]:
            out_tangent_type = 'clamped'
        sdk_node = pm.setDrivenKeyframe(driven, cd=driver, dv=driver_value, v=driven_value, itt=in_tangent_type, ott=out_tangent_type)
        
def hooks_attrs_create(hooks,part):     
    auto_addAttr_enum(hooks,part+'Sep','__________','{}:'.format(part))
    for attrs in all_pose[part]:
        auto_addAttr_enum(hooks,part+attrs[0]+'Sep','___','{}:'.format(attrs[0]))
        for attr in attrs[1:]:
            for i in ['L','R']:
                pose_name = attr.format(i,part)
                driver_attr = auto_addAttr(hooks,pose_name,min_val=0,max_val=1,dv_val=0) 
                hooks_attrs_remap(hooks,pose_name)
                           
def hooks_attrs_remap(hooks,pose_name):
    hooks_attr = hooks.attr(pose_name)
    if not pm.objExists(hooks_attr):
        pm.warning('{} no find in hooks'.format(pose_name))
        return
    if not pm.objExists(pose_name+'_driver_remapColor'):
        driver_remap = auto_createNode('remapColor',pose_name+'_driver_remapColor')
    else:
        driver_remap = pm.PyNode(pose_name+'_driver_remapColor')
    driver_remap.attr('outColorR') >> hooks_attr
    return driver_remap
        
def auto_override(node,color,disType=0):
    node.overrideEnabled.set(1)
    node.overrideColor.set(color)
    node.overrideDisplayType.set(disType)

def brow_driver_node_create(pose_name,suf):
    suf_shape = suf.getShape()
    loc = auto_createNode('locator','{}_loc'.format(pose_name))
    loc_shape = loc.getShape()
    auto_override(loc_shape,10,1)
    loc_shape.localScale.set([0.01,0.01,0.01])
    auto_createGroup(loc)
    cps = auto_createNode('closestPointOnSurface','{}_closestPointOnSurface'.format(loc))
    if not pm.objExists('{}_paramDimension'.format(loc)):  
        pd = pm.paramDimension(suf.uv[0,0])
        pd.getParent().rename('{}_paramDimension'.format(loc))
        auto_override(pd,20)
        print(pd)
    else:
        pd = pm.PyNode('{}_paramDimension'.format(loc))
    suf_shape.worldSpace[0] >> cps.inputSurface
    loc.getShape().worldPosition[0] >> cps.inPosition
    cps.parameterU >> pd.uParamValue
    cps.parameterV >> pd.vParamValue
    return cps

def brow_driver_general(hooks,part,i,suf,ud,lr):
    for attr in ['{}_{}','{}_{}_local']:
        pose_name = attr.format(i,part)
        brow_driver_node_create(pose_name,suf)
    driver_loc_cps = pm.PyNode('{}_{}_loc_closestPointOnSurface'.format(i,part))
    local_loc_cps = pm.PyNode('{}_{}_local_loc_closestPointOnSurface'.format(i,part))
    for attr in general_pose[1:]:
        pose_name = attr.format(i,part)
        cps = brow_driver_node_create(pose_name,suf)
        driver_remap = hooks_attrs_remap(hooks,pose_name)
        if any(item in attr for item in ['Up','Down']):
            cps.attr('parameter'+ud) >> driver_remap.inputMax
            local_loc_cps.attr('parameter'+ud) >> driver_remap.inputMin
            driver_loc_cps.attr('parameter'+ud) >> driver_remap.colorR
        elif any(item in attr for item in ['Left','Right']):
            cps.attr('parameter'+lr) >> driver_remap.inputMax
            local_loc_cps.attr('parameter'+lr) >> driver_remap.inputMin
            driver_loc_cps.attr('parameter'+lr) >> driver_remap.colorR

def brow_driver_init(part,i):
    jnt = driver_dict[part][0].format(i,part)
    for attr in ['{}_{}_loc_ofs','{}_{}_local_loc_ofs']:
        pose_name = attr.format(i,part)
        pm.matchTransform(pose_name, jnt, pos=True)
    pm.pointConstraint(jnt, '{}_{}_loc_con'.format(i,part), mo=True)
    pm.parent('{}_{}_local_loc_ofs'.format(i,part),'{}_{}_loc_ofs'.format(i,part))

    ctrl = driver_dict[part][1].format(i,part)
    for pose_index,attr in list(zip([[0,1,0],[0,-1,0],[1,0,0],[-1,0,0]],general_pose[1:])):
        pm.xform(ctrl,translation=pose_index,rotation=(0,0,0),scale=(1,1,1))
        pose_name = attr.format(i,part)
        pm.matchTransform(pose_name+'_loc_ofs', '{}_{}_loc'.format(i,part), pos=True)

    pm.xform(ctrl,translation=(0,0,0),rotation=(0,0,0),scale=(1,1,1))

def driver_general(hooks,part,i):
    for attr in all_pose[part][0][1:]:
        pose_name = attr.format(i,part)
        driver_axial, driver_posNeg = get_driver(pose_name)
        driver_attr = '{}_{}_{}'.format(i,part,driver_axial)
        driver_remap = hooks_attrs_remap(hooks,pose_name)
        driver_remap.inputMax.set(driver_posNeg)
        driver = pm.PyNode(driver_dict[part][0].format(i,part))
        driver.attr(driver_attr) >> driver_remap.colorR

def driver_combo(hooks,part,i):
    if len(all_pose[part]) > 1:
        combo_pose = all_pose[part][1][1:]
    else:
        return
    if combo_pose:
        for attr in combo_pose:
            pose_name = attr.format(i,part)
            combin = auto_createNode('combinationShape','{}_combinationShape'.format(pose_name),{'combinationMethod':2})
            drivers = re.findall('[A-Z][a-z]*', pose_name.split('_')[-1])
            driver1 = '_'.join(pose_name.split('_')[:-1] + [drivers[0]])
            driver2 = '_'.join(pose_name.split('_')[:-1] + [drivers[1]])
            driver_remap = hooks_attrs_remap(hooks,pose_name)
            hooks.attr(driver1) >> combin.inputWeight[0]
            hooks.attr(driver2) >> combin.inputWeight[1]
            combin.outputWeight >> driver_remap.colorR
            
def driver_set():
    suf = pm.ls(sl=True)[0]
    for part in parts:
        hooks = create_hooks()
        hooks_attrs_create(hooks,part)
        for i in ['L','R']:
            if part == 'Brow':
                if suf.getShape().nodeType() != 'nurbsSurface':
                    pm.warning('Please select a nurbsSurface')
                    return
                ud = 'U'
                lr = 'V'
                brow_driver_general(hooks,part,i,suf,ud,lr)
                brow_driver_init(part,i)
            else:
                driver_general(hooks,part,i)
            driver_combo(hooks,part,i)

if __name__ == '__main__':
    driver_set()



        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        