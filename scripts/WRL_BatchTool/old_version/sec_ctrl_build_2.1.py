OERU_sec_version = '2.1'

import maya.cmds as cmds
import pymel.core as pm
from functools import partial

class OERU_sec():
    
    def connectMatrix(self, geoName, arg=None):
        skinNode = pm.PyNode(geoName).listHistory(pdo=1, type='skinCluster')
        if skinNode:
            for jnt in pm.skinCluster(skinNode[0],q=1,inf=1):
                jointIndex = [infc.name()[:-1].rsplit('[',1)[-1] for infc in jnt.obcc.listConnections(s=0, p=1) if skinNode[0].name() in infc.name()]
                if not pm.isConnected(jnt.parentInverseMatrix[0],skinNode[0].bindPreMatrix[int(jointIndex[0])]):
                    jnt.parentInverseMatrix[0] >> skinNode[0].bindPreMatrix[int(jointIndex[0])]
                    
    def replaceGeo(self, objs, arg=None):
        originalGeo = objs[0].split('.')[0]
        if not cmds.objExists(originalGeo + '_secOriginalGeo'):
            #print(originalGeo)
            newName = cmds.rename(originalGeo, originalGeo + '_secOriginalGeo')
            dupGeo = cmds.duplicate(newName, n=originalGeo, st=0)[0]
            testNum = 0
            while True:
                if cmds.pickWalk(dupGeo, d='left')[0] == newName or testNum == 100:
                    break
                testNum += 1
                cmds.reorder(dupGeo, r=-1)
            if cmds.listRelatives(newName, p=1):
                cmds.parent(newName, w=1)
            cmds.blendShape(newName,dupGeo , w=(0, 1), n='{}_secBlendShape'.format(dupGeo))
    
            return newName
        else:
            cmds.warning('{}添加过替代模型'.format(originalGeo))
            
    def CreateCtrl(self, name, arg=None):
        curve_ball = 'curve -d 1 -p 0 1 0 -p 0.5 0.866025 0 -p 0.866025 0.5 0 -p 1 0 0 -p 0.866025 -0.5 0 -p 0.5 -0.866025 0 -p 0 -1 0 -p -0.5 -0.866025 0 -p -0.866025 -0.5 0 -p -1 0 0 -p -0.866025 0.5 0 -p -0.5 0.866025 0 -p 0 1 0 -p 0 0.866025 -0.5 -p 0 0.5 -0.866025 -p 0 0 -1 -p 0 -0.5 -0.866025 -p 0 -0.866025 -0.5 -p 0 -1 0 -p 0 -0.866025 0.5 -p 0 -0.5 0.866025 -p 0 0 1 -p 0 0.5 0.866025 -p 0 0.866025 0.5 -p 0 1 0 -p 0 0.866025 -0.5 -p 0 0.5 -0.866025 -p 0 0 -1 -p 0.5 0 -0.866025 -p 0.866025 0 -0.5 -p 1 0 0 -p 0.866025 0 0.5 -p 0.5 0 0.866025 -p 0 0 1 -p -0.5 0 0.866025 -p -0.866025 0 0.5 -p -1 0 0 -p -0.866025 0 -0.5 -p -0.5 0 -0.866025 -p 0 0 -1 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 -k 13 -k 14 -k 15 -k 16 -k 17 -k 18 -k 19 -k 20 -k 21 -k 22 -k 23 -k 24 -k 25 -k 26 -k 27 -k 28 -k 29 -k 30 -k 31 -k 32 -k 33 -k 34 -k 35 -k 36 -k 37 -k 38 -k 39;'
        curveName = pm.mel.eval(curve_ball)
        conName = pm.rename(curveName, name)
        reserveGrp = pm.group(n=name + '_reserve')
        #print(reserveGrp)
        grp = [reserveGrp, pm.group(conName, name='{}_Grp_02'.format(conName)), pm.group(conName, name='{}_Grp_01'.format(conName)), conName]
        #print(grp)
        return pm.group(reserveGrp, n=name + '_zero'), grp

    def rivetFollicle(self, objsList, name, rivetGeo, arg=None):
        if type(objsList) != list:
            objsList = [objsList]
        shapeNode = pm.PyNode(rivetGeo).getShape()
        returnList = []
        
        closestNode = pm.createNode('closestPointOnMesh', n='OERU_ClosestPoint_node')
        shapeNode.worldMatrix[0] >> closestNode.inputMatrix
        shapeNode.worldMesh >> closestNode.inMesh
        
        for objEO in objsList:
            obj = pm.PyNode(objEO)
            rpPosition = obj.getRotatePivot()
            follicleShape = pm.createNode('follicle', n='{}_ParentFollicleShape'.format(obj))
            follicleParent = follicleShape.getParent()
            follicleShape.ot >> follicleParent.t
            follicleShape.outRotate >> follicleParent.r
            shapeNode.outMesh >> follicleShape.inputMesh
            shapeNode.worldMatrix[0] >> follicleShape.inputWorldMatrix
            
            returnList.append(follicleParent.name())
            closestNode.ip.set(rpPosition)
            follicleShape.pu.set(closestNode.u.get())
            follicleShape.pv.set(closestNode.v.get())
            reserveGrp = pm.group(em=1, p=follicleParent, n='{}_reserve'.format(follicleParent))
            jointName = pm.joint(reserveGrp, r=1, n='{}_Joint'.format(name))
            cmds.connectAttr(follicleParent+'.t',obj+'.t')
            cmds.connectAttr(follicleParent+'.r',obj+'.r')
            cmds.connectAttr(follicleParent+'.s',obj+'.s')
            proxy = pm.group(em=1, p=reserveGrp, n='{}_proxy'.format(name))
            pm.parentConstraint(proxy, jointName, mo=1, weight=1)
            pm.scaleConstraint(proxy, jointName, mo=1, weight=1)
            grp = [reserveGrp, pm.group(proxy,name='{}_Grp_02'.format(proxy)), pm.group(proxy,name='{}_Grp_01'.format(proxy)), proxy]
            mainExtra = 'Main'
            if pm.objExists(mainExtra):
                pm.scaleConstraint(mainExtra, follicleParent, mo=True)
                
        pm.delete(closestNode)
        return returnList, grp, jointName
        
    def UI_button(self, model, vtx, arg=None):
        
        if model == 'load':
            pm.textScrollList('OERU_sec_UI_Scroll', e=1, ra=1)
            pm.textScrollList('OERU_sec_UI_Scroll', e=1, append=cmds.ls(sl=1,fl=1))
        elif model == 'add':
            for sl in pm.ls(sl=1, fl=1):
                if not sl in pm.textScrollList('OERU_sec_UI_Scroll', q=1, ai=1):
                    pm.textScrollList('OERU_sec_UI_Scroll',e=1, append=sl)
        
        elif model == 'build':
            #vtx = pm.textScrollList('OERU_sec_UI_Scroll', q=1, ai=1)
            objsList = vtx
            #print(objsList)
            geoName = objsList[0].split('.')[0]
            #print(geoName)
            if not cmds.objExists('{}_secOriginalGeo'.format(geoName)):
                
                originalGeo = self.replaceGeo(objsList)
                
                secGrp = cmds.group(em=1, n='{}_sec_Group'.format(geoName))
                rootJoint = cmds.joint(secGrp, r=1, n='{}_sec_rootJoint'.format(geoName))
                skinNode = cmds.skinCluster(rootJoint, geoName, tsb=1, n='{}_sec_skinCluster'.format(geoName))
                
                ctrlGrp = cmds.group(em=1, n='{}_secCtrl_Group'.format(geoName))
                follicleGrp = cmds.group(em=1, n='{}_secFollicle_Group'.format(geoName))
                
                cmds.parent(originalGeo, ctrlGrp, follicleGrp, secGrp)
                cmds.hide(originalGeo, follicleGrp, rootJoint)
                
                rig_Other = 'Rig_Other'
                if pm.objExists(rig_Other):
                    pm.parent(secGrp, rig_Other)
            else:
                ctrlGrp = '{}_secCtrl_Group'.format(geoName)
                originalGeo = '{}_secOriginalGeo'.format(geoName)
                follicleGrp = '{}_secFollicle_Group'.format(geoName)
                skinNode = '{}_sec_skinCluster'.format(geoName)
             
            eAdd = 0
            while True:
                if not cmds.objExists('{}_secCtrl_{}'.format(geoName, str(eAdd).zfill(2))) or eAdd == 100:
                    #print(eAdd)
                    break
                eAdd += 1
                #print(eAdd)
                    
            for i,obj in enumerate(objsList):
                name = '{}_secCtrl_{}'.format(geoName, str(i+eAdd).zfill(2))
                print(name)
                vtxPosition = pm.xform(obj, q=1, ws=1, t=1)
                ctrlReturn = self.CreateCtrl(name)
                pm.parent(ctrlReturn[0], ctrlGrp)
                pm.move(vtxPosition[0], vtxPosition[1], vtxPosition[2], ctrlReturn[0])
                follicleList = self.rivetFollicle(ctrlReturn[0], name, rivetGeo=originalGeo)
                for x in range(4):
                    for attr in ['.t','.r','.s']:
                        pm.connectAttr(ctrlReturn[1][x]+attr, follicleList[1][x]+attr)
                        
                pm.parent(follicleList[0], follicleGrp)
                pm.skinCluster(skinNode, e=1, wt=0, ai=follicleList[2])
            self.connectMatrix(geoName)
            pm.select(cl=True)
        elif model == 'transfer':
            sel = pm.selected()
            #print(sel)
            baseOrigGeo = sel[0].name()+'_secOriginalGeo'
            if not cmds.objExists(baseOrigGeo):
                cmds.error('第一个选中物体没有替代模型')
                
            skinNode = [h for h in pm.listHistory(sel[0], pdo=0) if pm.objectType(h) == 'skinCluster'][0]
            jointList = pm.skinCluster(skinNode, q=1, inf=1)
            for sl in sel[1:]:
                sl_name = str(sl)
                oldGeoName = self.replaceGeo([sl])
                pm.skinCluster(jointList, sl_name, tsb=1)
                
                pm.copySkinWeights(sel[0], sl_name, noMirror=1, surfaceAssociation='closestPoint', influenceAssociation='closestJoint')
                self.connectMatrix(sl_name)
                
                if sl.endswith('secOriginalGeo'):
                    pm.parent(sl, '{}_sec_Group'.format(sel[0]))
                    sl.v.set(0)
            
            pm.select(cl=True)
        else:
            print('noting???')
            
            
    def UI_window(self):
        bgColor = (0.3, 0.3, 0.3)
        buttonColor = (0.13, 0.13, 0.13)
        if cmds.window('OERU_sec_UI',q=1,ex=1):
            cmds.deleteUI('OERU_sec_UI')
        cmds.window('OERU_sec_UI', title='OERU_secBuild {}'.format(OERU_sec_version), s=1, tlb=1)
        cmds.columnLayout(adj=1)
        cmds.rowColumnLayout(nc=2, cw=(100, 100), adj=1)
        cmds.button('qButton',label='加载模型点',c=partial(self.UI_button, 'load'),bgc=buttonColor)
        cmds.button(label='+',c=partial(self.UI_button, 'add'),bgc=buttonColor)
        cmds.setParent('..')
        cmds.textScrollList('OERU_sec_UI_Scroll', h=70, nr=15, ams=0)
        cmds.button(label='创建',c=partial(self.UI_button, 'build'),h=45, bgc=buttonColor)
        cmds.button(label='传递效果到新模型',c=partial(self.UI_button, 'transfer'),h=45, bgc=buttonColor)
        cmds.window('OERU_sec_UI',e=1, wh=(200, 187))
        cmds.window('OERU_sec_UI',e=1, vis=1)
        
def show():
    OERU_secInstance = OERU_sec()
    OERU_secInstance.UI_window()

if __name__ == '__main__':
    show()