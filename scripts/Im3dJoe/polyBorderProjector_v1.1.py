##--------------------------------------------------------------------------
##
## ScriptName : polyBorder Projector
## Author     : Joe Wu
## URL        : https://www.youtube.com/@Im3dJoe
## LastUpdate : 2022/11/03
##            : project select poly border to target mesh
## Version    : 1.0  First version for public test
##            : 1.1  Improve UI
## Other Note : test in maya 2020.2 windows
##
## Install    : copy and paste script into a python tab in maya script editor
## how to use : select some edges or vertexs + one target mesh
##--------------------------------------------------------------------------

import maya.cmds as mc
import math
import maya.OpenMaya as om

def polyBorderProjector():
    if mc.window("polyBorderAdv", exists = True):
        mc.deleteUI("polyBorderAdv")
    polyBorderAdvUI = mc.window("polyBorderAdv", title = 'polyBorder Projector v1.1', w = 200, s = 1 ,mxb = False,mnb = False)
   
    mc.columnLayout(adj=1)
    mc.text(l='',w=20)
    mc.rowColumnLayout(nc= 6 ,cw=[(1,30),(2,50),(3,182),(4,5),(5,40),(6,10),(7,10),(8,50),(9,20)])
    mc.text(l='',w=20)
    mc.text(l='Target    ',w=20)
    mc.textField('borderProjMeshList',ed=0, width=150)
    mc.text(l='',w=20)
    mc.iconTextButton(style="textOnly",  label= "Load",bgc = [0.18,0.18,0.18], rpt=1, c = 'projMeshLoad()')
    
    mc.text(l='',w=20)
    mc.setParent( '..' )
    mc.text(l='',w=20)
    mc.rowColumnLayout(nc= 9 ,cw=[(1,20),(2,50),(3,20),(4,50),(5,10),(6,50),(7,10),(8,50),(9,20)])
    mc.text(l='',w=20)
    mc.text(l='Method',w=20)
    mc.text(l='',w=20)
    mc.iconTextButton(style="textOnly", label= "Axis",bgc = [0.58,0.38,0.38], rpt=1, c = 'polyBorderOffset()')
    mc.text(l='',w=20)
    mc.iconTextButton(style="textOnly", label= "Extend",bgc = [0.38,0.38,0.58], rpt=1, c = 'polyBorderExtend()')
    mc.text(l='',w=20)
    mc.iconTextButton(style="textOnly", label= "Extrude",bgc = [0.38,0.58,0.53], rpt=1, c = 'polyBorderExtendExtrude()')
    mc.text(l='',w=20)
    mc.setParent( '..' )
    mc.separator( height=15, style='in' )
    mc.columnLayout(adj=1)
    mc.radioButtonGrp('singleAxisDir', label='Axis         ', sl=2,cw = [(1,90),(2,55),(3,55),(4,55)], labelArray3=['X', 'Y', 'Z'], numberOfRadioButtons=3 )
    mc.radioButtonGrp('singleAxisSpace', label='Space         ', sl=1,cw = [(1,90),(2,55),(3,70)], labelArray2=['World', 'Local'], numberOfRadioButtons=2)
    mc.text(l='',w=20)
    mc.showWindow(polyBorderAdvUI)

def projMeshLoad():
    targetMesh = mc.filterExpand(sm=12)
    getSelList = mc.ls(targetMesh,fl=1,l=1)
    toStr = ','.join(getSelList)
    mc.textField('borderProjMeshList', e=1 , tx = toStr)

def polyBorderOffset():
    snapingEdges = mc.filterExpand(sm=32)
    snapingCV = mc.filterExpand(sm=31)
    targetMesh = mc.textField('borderProjMeshList', q=1 , tx = 1)
    targetMesh = targetMesh.split(',')
    selState = 0
    if len(targetMesh) > 0:
        if snapingCV:
            mc.select(snapingCV)
            mc.polySelectConstraint( m=2, w=1, t=0x0001)
            snapingCV = mc.filterExpand(sm=31)
            mc.ConvertSelectionToContainedEdges()
            mc.polySelectConstraint(pp=1, m=2, w=1, t=0x8000)
            mc.polySelectConstraint(disable =True)
            snapingEdges = mc.filterExpand(sm=32)
            boraderRingCV = snapingCV
        elif len(snapingEdges)>0:
            mc.select(snapingEdges)
            mc.polySelectConstraint( m=2, w=1, t=0x8000)
            snapingEdges = mc.filterExpand(sm=32)
            mc.ConvertSelectionToVertices()
            boraderRingCV = mc.ls(sl=1,fl=1)
            mc.select(snapingEdges)
            mc.polySelectConstraint(pp=1, m=2, w=1, t=0x8000)
            mc.polySelectConstraint(disable =True)
            snapingEdges = mc.filterExpand(sm=32)
            selState = 1
        selMesh =boraderRingCV[0].split('.')[0]
        dirAxis=mc.radioButtonGrp('singleAxisDir',q=1, sl=1)
        spaceType = mc.radioButtonGrp('singleAxisSpace',q=1, sl=1)
        vectBtwPnts = om.MVector(1,0,0)
        selMesh =snapingEdges[0].split('.')[0]
        rayDirection = ''
        vc = ''
        if spaceType == 1:
            vc = ''
            if dirAxis == 1:
                vc = (1, 0, 0)
            elif dirAxis == 2:
                vc = (0, 1, 0)
            elif dirAxis == 3:
                vc = (0, 0, 1)

        elif spaceType == 2:
            tx, ty, tz = 0,0,0
            if dirAxis == 1:
                tx, ty, tz = getLocalVecToWorldSpaceAPI(selMesh,vec=om.MVector.xAxis)
            elif dirAxis == 2:
                tx, ty, tz = getLocalVecToWorldSpaceAPI(selMesh,vec=om.MVector.yAxis)
            elif dirAxis == 3:
                tx, ty, tz = getLocalVecToWorldSpaceAPI(selMesh,vec=om.MVector.zAxis)
            vc = ( tx, ty, tz)
        rayDirection = om.MVector(*vc)
        for b in boraderRingCV:
            edgeList = mc.polyListComponentConversion(b, fv=1, te=1)
            edgeX = mc.ls(edgeList,fl=1)
            getEdge = list(set(edgeX) - set(snapingEdges))
            cvList = mc.polyListComponentConversion(getEdge, fe=1, tv=1)
            cvX =  mc.ls(cvList,fl=1)
            getCV = list(set(cvX) - set(boraderRingCV))
            basePoint = mc.pointPosition(getCV[0],w=1)
            raySource = om.MFloatPoint(basePoint[0],basePoint[1],basePoint[2])
            for t in targetMesh:
                name = t
                selectionList = om.MSelectionList()
                selectionList.add( name )
                node = om.MDagPath()
                selectionList.getDagPath(0, node )
                meshFn = om.MFnMesh()
                meshFn.setObject( node )
                hitpoint = om.MFloatPoint()
                finalX = []
                finalY = []
                finalZ = []
                shortDistance = 10000000000
                distanceBetween = 1000000000
                intersection = meshFn.closestIntersection(
                    om.MFloatPoint(raySource),
                    om.MFloatVector(rayDirection),
                    None,
                    None,
                    False,
                    om.MSpace.kWorld,
                    99999,
                    True,
                    None,
                    hitpoint,
                    None,
                    None,
                    None,
                    None,
                    None)
                if intersection:
                    x = hitpoint.x
                    y = hitpoint.y
                    z = hitpoint.z
                    distanceBetween = math.sqrt( ((float(basePoint[0]) - x)**2)  + ((float(basePoint[1]) - y)**2) + ((float(basePoint[2]) - z)**2))
                    if distanceBetween < shortDistance:
                        shortDistance = distanceBetween
                        finalX = x
                        finalY = y
                        finalZ = z
                    mc.move(finalX, finalY, finalZ, b, a=1, ws=1)
        if selState == 0:
            mc.select(snapingCV)
            cmd = 'doMenuComponentSelectionExt("' + selMesh + '", "vertex", 0);'
            mel.eval(cmd)

        else:
            mc.select(snapingEdges)
            cmd = 'doMenuComponentSelectionExt("' + selMesh + '", "edge", 0);'
            mel.eval(cmd)

def polyBorderExtend():
    snapingEdges = mc.filterExpand(sm=32)
    snapingCV = mc.filterExpand(sm=31)
    targetMesh = mc.textField('borderProjMeshList', q=1 , tx = 1)
    targetMesh = targetMesh.split(',')
    selState = 0
    if len(targetMesh) > 0:
        if snapingCV:
            mc.select(snapingCV)
            mc.polySelectConstraint( m=2, w=1, t=0x0001)
            snapingCV = mc.filterExpand(sm=31)
            mc.ConvertSelectionToContainedEdges()
            mc.polySelectConstraint(pp=1, m=2, w=1, t=0x8000)
            mc.polySelectConstraint(disable =True)
            snapingEdges = mc.filterExpand(sm=32)
            boraderRingCV = snapingCV
        elif len(snapingEdges)>0:
            mc.select(snapingEdges)
            mc.polySelectConstraint( m=2, w=1, t=0x8000)
            snapingEdges = mc.filterExpand(sm=32)
            mc.ConvertSelectionToVertices()
            boraderRingCV = mc.ls(sl=1,fl=1)
            mc.select(snapingEdges)
            mc.polySelectConstraint(pp=1, m=2, w=1, t=0x8000)
            mc.polySelectConstraint(disable =True)
            snapingEdges = mc.filterExpand(sm=32)
            selState = 1
        selMesh =boraderRingCV[0].split('.')[0]
        for b in boraderRingCV:
            aimPoint = mc.pointPosition(b,w=1)
            edgeList = mc.polyListComponentConversion(b, fv=1, te=1)
            edgeX = mc.ls(edgeList,fl=1)
            mc.select(edgeX)
            getEdge = list(set(edgeX) - set(snapingEdges))
            cvList = mc.polyListComponentConversion(getEdge, fe=1, tv=1)
            cvX =  mc.ls(cvList,fl=1)
            getCV = list(set(cvX) - set(boraderRingCV))
            basePoint = mc.pointPosition(getCV[0],w=1)
            vectBtwPnts= ((basePoint [0] -aimPoint [0])*-1), ((basePoint [1] -aimPoint [1])*-1), ((basePoint [2] -aimPoint [2])*-1)
            vectorToFinish = om.MFloatVector(vectBtwPnts[0],vectBtwPnts[1],vectBtwPnts[2])
            raySource = om.MFloatPoint(basePoint[0],basePoint[1],basePoint[2])
            rayDirection = vectorToFinish
            rayDirection = rayDirection.normal()
            for t in targetMesh:
                name = t
                selectionList = om.MSelectionList()
                selectionList.add( name )
                node = om.MDagPath()
                selectionList.getDagPath( 0, node )
                meshFn = om.MFnMesh()
                meshFn.setObject( node )
                hitpoint = om.MFloatPoint()
                finalX = []
                finalY = []
                finalZ = []
                shortDistance = 10000000000
                distanceBetween = 1000000000
                intersection = meshFn.closestIntersection(
                    om.MFloatPoint(raySource),
                    om.MFloatVector(rayDirection),
                    None,
                    None,
                    False,
                    om.MSpace.kWorld,
                    99999,
                    False,
                    None,
                    hitpoint,
                    None,
                    None,
                    None,
                    None,
                    None)
                if intersection:
                    x = hitpoint.x
                    y = hitpoint.y
                    z = hitpoint.z
                    distanceBetween = math.sqrt( ((float(aimPoint[0]) - x)**2)  + ((float(aimPoint[1]) - y)**2) + ((float(aimPoint[2]) - z)**2))
                    if distanceBetween < shortDistance:
                        shortDistance = distanceBetween
                        finalX = x
                        finalY = y
                        finalZ = z
                    mc.move(finalX, finalY, finalZ, b, a=1, ws=1)
        if selState == 0:
            mc.select(snapingCV)
            cmd = 'doMenuComponentSelectionExt("' + selMesh + '", "vertex", 0);'
            mel.eval(cmd)

        else:
            mc.select(snapingEdges)
            cmd = 'doMenuComponentSelectionExt("' + selMesh + '", "edge", 0);'
            mel.eval(cmd)

def polyBorderExtendExtrude():# partial ring may not be stable
    snapingEdges = mc.filterExpand(sm=32)
    snapingCV = mc.filterExpand(sm=31)
    targetMesh = mc.textField('borderProjMeshList', q=1 , tx = 1)
    targetMesh = targetMesh.split(',')
    selState = 0
    if len(targetMesh) > 0:
        if snapingCV:
            mc.select(snapingCV)
            mc.polySelectConstraint( m=2, w=1, t=0x0001)
            snapingCV = mc.filterExpand(sm=31)
            mc.ConvertSelectionToContainedEdges()
            mc.polySelectConstraint(pp=1, m=2, w=1, t=0x8000)
            mc.polySelectConstraint(disable =True)
            snapingEdges = mc.filterExpand(sm=32)
            boraderRingCV = snapingCV
        elif len(snapingEdges)>0:
            mc.select(snapingEdges)
            mc.polySelectConstraint( m=2, w=1, t=0x8000)
            snapingEdges = mc.filterExpand(sm=32)
            mc.ConvertSelectionToVertices()
            boraderRingCV = mc.ls(sl=1,fl=1)
            mc.select(snapingEdges)
            mc.polySelectConstraint(pp=1, m=2, w=1, t=0x8000)
            mc.polySelectConstraint(disable =True)
            snapingEdges = mc.filterExpand(sm=32)
            selState = 1
        selMesh =boraderRingCV[0].split('.')[0]
        #extrude edge
        mc.select(snapingEdges)
        mc.polyExtrudeEdge(constructionHistory=1, keepFacesTogether=1, divisions=1, twist=0, taper=1, offset=0.01, thickness=0, smoothingAngle =30)
        mc.ConvertSelectionToVertices()
        boraderRingCV = mc.ls(sl=1,fl=1)
        mc.ConvertSelectionToContainedEdges()
        mc.polySelectConstraint(pp=1, m=2, w=1, t=0x8000)
        mc.polySelectConstraint(pp=1, m=2, w=1, t=0x8000)
        mc.polySelectConstraint(disable =True)
        mc.ConvertSelectionToVertices()
        removeBorderList = mc.ls(sl=1,fl=1)
        for b in boraderRingCV:
            snapPoint = b
            growEdge = mc.polyListComponentConversion(b, fv=1, te=1)
            growCV = mc.polyListComponentConversion(growEdge, fe=1, tv=1)
            growCV = mc.ls(growCV,fl=1)
            aimCV = list(set(growCV) - set(boraderRingCV))
            growFace = mc.polyListComponentConversion(snapPoint, fv=1, tf=1)
            unwantCV = mc.polyListComponentConversion(growFace, ff=1, tv=1)
            unwantCV = mc.ls(unwantCV,fl=1)
            aimPoint = mc.pointPosition(b,w=1)
            edgeList = mc.polyListComponentConversion(aimCV, fv=1, te=1)
            edgeX = mc.ls(edgeList,fl=1)
            crossCV = mc.polyListComponentConversion(edgeX, fe=1, tv=1)
            crossCV = mc.ls(crossCV,fl=1)
            getCV = list(set(crossCV) - set(boraderRingCV)-set(unwantCV)-set(removeBorderList))
            basePoint = mc.pointPosition(getCV[0],w=1)
            vectBtwPnts= ((basePoint [0] -aimPoint [0])*-1), ((basePoint [1] -aimPoint [1])*-1), ((basePoint [2] -aimPoint [2])*-1)
            vectorToFinish = om.MFloatVector(vectBtwPnts[0],vectBtwPnts[1],vectBtwPnts[2])
            raySource = om.MFloatPoint(basePoint[0],basePoint[1],basePoint[2])
            rayDirection = vectorToFinish
            rayDirection = rayDirection.normal()
            for t in targetMesh:
                name = t
                selectionList = om.MSelectionList()
                selectionList.add( name )
                node = om.MDagPath()
                selectionList.getDagPath( 0, node )
                meshFn = om.MFnMesh()
                meshFn.setObject( node )
                hitpoint = om.MFloatPoint()
                finalX = []
                finalY = []
                finalZ = []
                shortDistance = 10000000000
                distanceBetween = 1000000000
                intersection = meshFn.closestIntersection(
                    om.MFloatPoint(raySource),
                    om.MFloatVector(rayDirection),
                    None,
                    None,
                    False,
                    om.MSpace.kWorld,
                    99999,
                    False,
                    None,
                    hitpoint,
                    None,
                    None,
                    None,
                    None,
                    None)
                if intersection:
                    x = hitpoint.x
                    y = hitpoint.y
                    z = hitpoint.z
                    distanceBetween = math.sqrt( ((float(aimPoint[0]) - x)**2)  + ((float(aimPoint[1]) - y)**2) + ((float(aimPoint[2]) - z)**2))
                    if distanceBetween < shortDistance:
                        shortDistance = distanceBetween
                        finalX = x
                        finalY = y
                        finalZ = z
                    mc.move(finalX, finalY, finalZ, b, a=1, ws=1)
        if selState == 0:
            mc.select(boraderRingCV)
            cmd = 'doMenuComponentSelectionExt("' + selMesh + '", "vertex", 0);'
            mel.eval(cmd)

        else:
            mc.select(boraderRingCV)
            mc.ConvertSelectionToContainedEdges()
            cmd = 'doMenuComponentSelectionExt("' + selMesh + '", "edge", 0);'
            mel.eval(cmd)


def getLocalVecToWorldSpaceAPI(obj, vec=om.MVector.xAxis):
    selList = om.MSelectionList()
    selList.add(obj)
    nodeDagPath = om.MDagPath()
    selList.getDagPath(0, nodeDagPath)
    matrix = nodeDagPath.inclusiveMatrix()
    vec = (vec * matrix).normal()
    return vec.x, vec.y, vec.z

polyBorderProjector()