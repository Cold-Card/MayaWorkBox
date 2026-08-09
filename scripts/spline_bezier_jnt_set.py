import pymel.core as pm

def addAttr(nodeName,attrName,proxy=False,proxyAttr=None):
    if not nodeName.hasAttr(attrName):
        if proxy:
            nodeName.addAttr(attrName,proxy=proxyAttr,k=0)
        else:
            nodeName.addAttr(attrName,at='bool',k=0)
        nodeName.attr(attrName).set(channelBox=True)
    return nodeName.attr(attrName)
        
def edit_list(lst):
    n = len(lst)
    if n == 0:
        return []
    groups = [[lst[0]]]
    if n == 1:
        return groups
    middle = lst[1:-1]
    middle_groups = []
    for i in range(0, len(middle), 2):
        pair = middle[i:i+2]
        middle_groups.append(pair)
    groups.extend(middle_groups)
    groups.append([lst[-1]])
    return groups
    
jnts = pm.ls(sl=True)
crv = pm.PyNode('duplicatedCurve10')
cvs_num = crv.numCVs()
cvs = []
for i in range(cvs_num):
    if i % 3 != 0:
        cvs.append(i)
#print(cvs)
edited_list = edit_list(cvs)
#print(edited_list)
for x, jnt_cv in enumerate(edited_list):
    print(x)
    
    handleCtrl_grp = pm.group(jnts[x],n='{}_{}'.format(jnts[x].name(),'handleCtrl_grp'))
    addAttr(jnts[x],'handleCtrlVis')
    jnts[x].handleCtrlVis >> handleCtrl_grp.v
    fkCtrl = pm.PyNode(jnts[x].name()[:-8]+'_ctl_fk_1_oft')
    ikCtrl = pm.PyNode(jnts[x].name()[:-8]+'_ctl_ik_1_oft')
    addAttr(fkCtrl,'handleCtrlVis',proxy=True,proxyAttr=jnts[x].handleCtrlVis)
    addAttr(ikCtrl,'handleCtrlVis',proxy=True,proxyAttr=jnts[x].handleCtrlVis)
    
    loc_org = pm.spaceLocator(n='{}_{}'.format(jnts[x],'loc'))
    pm.parent(loc_org,jnts[x])
    pm.xform(loc_org,translation=(0,0,0),rotation=(0,0,0),scale=(1,1,1))
    loc_org.v.set(0)
    for z, cv in enumerate(jnt_cv):
        if z == 1 or x == 0:
            index = 'downstream'
        elif z == 0:
            index = 'upstream'
        loc_poi = pm.xform(crv.cv[cv],q=True,t=True)
        #print(loc_poi)
        jnt = pm.duplicate(jnts[x],n='{}_{}'.format(jnts[x],index),po=True)[0]
        #print(jnt)
        pm.xform(jnt,t=loc_poi,ws=True)
        line = pm.curve(d=1,p=[(1,0,0),(2,0,0)],n='{}_{}'.format(jnt,'line'))
        line.getShape().template.set(1)
        line.getShape().lineWidth.set(2)
        line.inheritsTransform.set(0)
        loc_handle = pm.spaceLocator(n='{}_{}'.format(jnt,'loc'))
        loc_handle.v.set(0)
        pm.parent(loc_handle,line,jnt)
        pm.xform(loc_handle,translation=(0,0,0),rotation=(0,0,0),scale=(1,1,1))
        pm.xform(line,translation=(0,0,0),rotation=(0,0,0),scale=(1,1,1))
        loc_org.getShape().worldPosition[0] >> line.getShape().controlPoints[0]
        loc_handle.getShape().worldPosition[0] >> line.getShape().controlPoints[1]
        
        
        
        