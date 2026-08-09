import pymel.core as pm
def addAttr(nodeName,attrName): 
        if not nodeName.hasAttr(attrName):
            nodeName.addAttr(attrName,at='double',k=1)
        return attrName
def createNode(nodeType,nodeName,editData={}):
        if not pm.objExists(nodeName):
            pm.createNode(nodeType,n=nodeName)
        nodeName = pm.PyNode(nodeName)
        for attrName, value in editData.items():
            if nodeName.hasAttr(attrName):
                try:
                    nodeName.attr(attrName).set(value)
                except:
                    continue
            else:
                print('{} 没有属性：{}'.format(nodeName,attrName))
        return nodeName
cons = pm.ls(sl=True)
for con in cons:
    jnt = pm.PyNode(con.name()[:-5])
    moveOffset_value = jnt.moveOffset.get()
    rotOffset_value = jnt.rotOffset.get()
    addAttr(con,'moveOffset')
    addAttr(con,'rotOffset')
    con.moveOffset.set(moveOffset_value)
    con.rotOffset.set(rotOffset_value)
    con.moveOffset.lock()
    con.rotOffset.lock()
    addAttr(con,'moveOffsetPlus')
    addAttr(con,'rotOffsetPlus')
    PMA = createNode('plusMinusAverage','{}_PMA'.format(con))
    con.moveOffset >> PMA.input2D[0].input2Dx
    con.rotOffset >> PMA.input2D[0].input2Dy
    con.moveOffsetPlus >> PMA.input2D[1].input2Dx
    con.rotOffsetPlus >> PMA.input2D[1].input2Dy
    PMA.output2Dx >> jnt.moveOffset
    PMA.output2Dy >> jnt.rotOffset