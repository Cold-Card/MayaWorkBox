# -*- coding: utf-8 -*-
# batch create ctrl for objects in Maya
# author: wangruilong
# date: 20250630

import pymel.core as pm

BASE_ATTR_NAMES = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'v']

def createCubeCurve(w,h,d):
    return pm.curve(
        d=1,
        p=[
            (-w, h, d),(w, h, d),
            (w, -h, d),(-w, -h, d),
            (-w, h, d),(-w, h, -d),
            (-w, -h, -d),(-w, -h, d),
            (w, -h, d),(w, -h, -d),
            (w, h, -d),(w, h, d),
            (w, h, -d),(w, -h, -d),
            (-w, -h, -d),(-w, h, -d),
            (w, h, -d)
        ]
    )

class NodeBase(object):
    def __init__(self, obj, speace='locator'):
        self.obj = obj
        self.space = speace

        self._locator = None
        self._locatorName = '{}_pivotLocator'.format(obj)
        self._ctlName = '{}_ctrl'.format(obj)
        self._ctlParentName = '{}_ctrl'.format(obj)
        self._jnt = '{}_jnt'.format(obj)
        self.ctl = None
        self.jnt = None

        self._ctlCount = 5
        self._ctlParentNames = {
            0: '{}_{:02d}_oft', self._ctlCount - 1: '{}_ctrl_grp', self._ctlCount - 2: '{}_constraint'
        }
        self._colorDatas = {0: 13, 1: 12, 2: 31}

        self._w = 1
        self._h = 1
        self._d = 1
        self._average = True
        self.constraints = []
        self.transforms = None
        self.scaled = 0.55
        self.interval = 1.2
        self.geo_vis_attr = 'geoVis'
        self._geo_vis_attr = None
        self._exCtlNum = 1
        self.exCtls = []
        self.vis_geo = True
        self.scale_lock = True

    @property
    def exctlNum(self):
        return self._exCtlNum
    
    @exctlNum.setter
    def exctlNum(self, num):
        self._exCtlNum = num
        self._ctlCount = 5 - 1 + self._exCtlNum

        self._ctlParentNames = {
            0: '{}_{:02d}_oft', self._ctlCount - 1: '{}_ctrl_grp', self._ctlCount - 2: '{}_constraint'
        }
    
    def setColor(self, node, index):
        node_shape = node.getShape()
        node_shape.ove.set(1)
        node_shape.ovc.set(index)

    def geos(self):
        return [x.getParent() for x in pm.ls(self.obj, dag=True, type='mesh', ni=True)]
    
    def createLocator(self):
        locator = self.getLocator()
        if locator is None:
            pivot = self.getPivot()
            locator = pm.spaceLocator(name=self._locatorName)
            locator.t.set(pivot)
    
    def getLocator(self):
        if self._locator is None:
            locators = pm.ls(self._locatorName)
            if len(locators) == 1:
                self._locator = locators[0]
        return self._locator
    
    def getPivot(self, space=None):
        if space is None:
            space = self.space
        if space == 'object':
            return self.obj.getScalePivot()
        elif space == 'locator':
            locator = self.getLocator()
            if locator is not None:
                return locator.getScalePivot()
            
        bbox = self.obj.getBoundingBox(space='world')
        self._d = bbox.depth()
        self._w = bbox.width()
        self._h = bbox.height()

        return bbox.center()
    
    def add_attrs(self, ctl, name):
        ctl.addAttr(name, at='bool')
        _geo_vis_attr = ctl.attr(name)
        _geo_vis_attr.set(1)
        pm.setAttr(_geo_vis_attr, e=True, keyable=True)
        return _geo_vis_attr
    
    def createCtls(self):
        pm.select(cl=True)
        w, h, d = self._w, self._h, self._d
        if self._average:
            w = h = d = sum([self._w, self._h, self._d]) / 3.0
        w, h, d = w * self.scaled, h * self.scaled, d * self.scaled
        self.ctl = createCubeCurve(w, h, d)
        self.ctl.rename(self._ctlName)
        pm.setAttr(self.ctl.v,lock=True, keyable=False,channelBox=False)
        if self.scale_lock:
            for scale_attr in ['sx', 'sy', 'sz']:
                pm.setAttr(self.ctl+'.{}'.format(scale_attr), lock=True, keyable=False, channelBox=False)
        self.setColor(self.ctl, 22)

        for i in range(self.exctlNum):
            w, h, d = w * self.interval, h * self.interval, d * self.interval
            ctl = createCubeCurve(w, h, d)
            ctl.rename('{}_{:02d}_ctrl'.format(self.obj, i + 1))
            pm.setAttr(ctl.v, lock=True, keyable=False, channelBox=False)
            if self.scale_lock:
                for scale_attr in ['sx', 'sy', 'sz']:
                    pm.setAttr(ctl+'.{}'.format(scale_attr), lock=True, keyable=False, channelBox=False)
            self.exCtls.append(ctl)
            self.setColor(ctl, self._colorDatas.get(i, 10))

        if self.vis_geo:
            if len(self.exCtls):
                geo_vis_ctl = self.exCtls[-1]
            else:
                geo_vis_ctl = self.ctl
            self._geo_vis_attr = self.add_attrs(geo_vis_ctl, self.geo_vis_attr)

        if len(self.exCtls):
            exctl_attr = self.add_attrs(self.exCtls[-1], 'secCtlVis')
            pm.setAttr(exctl_attr, keyable=True, channelBox=True)
            exctl_attr.set(1)
            exctl_attr >> self.ctl.getShape().v
            for exctl in self.exCtls[:-1]:
                exctl_attr >> exctl.getShape().v
        
        pm.select(self.ctl)

        transforms = [self.ctl]
        for i in range(self._ctlCount):
            name_pattern = self._ctlParentNames.get(i, self._ctlParentNames.get(0))
            transforms.append(pm.group(name=name_pattern.format(self.obj, i+1)))

        for i, exctl in enumerate(self.exCtls):
            pm.parent(exctl, transforms[i + 2])
            pm.parent(transforms[i + 1], exctl)
        
        return transforms
    
    def exists(self):
        return pm.objExists(self._ctlName)
    
    def create(self):
        if self.exists():
            return
        self.getPivot()
        self.transforms = self.createCtls()
        self.jnt = pm.createNode('joint', name=self._jnt)
        self.jnt.v.set(0)
        pm.parent(self.jnt, self.transforms[0])

        locator = self.getLocator()
        if locator is None:
            position = self.getPivot()
            self.transforms[-1].t.set(position)
        else:
            pm.delete(pm.parentConstraint(locator, self.transforms[-1]))

        if locator is not None:
            pm.delete(locator)

        pm.parent(self.transforms[-3], self.transforms[-1])
        return self.transforms
    
    def connect(self, mode='constraint'):
        if mode == 'constraint':
            self.constraints.append(pm.parentConstraint(self.ctl, self.obj, mo=True))
            self.constraints.append(pm.scaleConstraint(self.ctl, self.obj, mo=True))
            pm.parent(self.constraints, self.transforms[-2])
            if self._geo_vis_attr is not None:
                self._geo_vis_attr >> self.obj.v
        elif mode == 'skin':
            geos = self.geos()
            if len(geos):
                pm.select(geos,self.jnt)
                pm.mel.eval('newSkinCluster "-toSelectedBones -bindMethod 0 -normalizeWeights 1 -weightDistribution 0 -mi 1 -dr 10 -rui  false,multipleBindPose,1";')
                if self._geo_vis_attr is not None:
                    for geo in geos:
                        self._geo_vis_attr >> geo.v
            pm.delete(self.transforms[-2])
        else:
            pass

class Window(object):
    def __init__(self):
        self._win = None
        self._winName = 'batchCreateCtrlWin'
        self._title = 'Batch Create Ctrl'
        self.uis = {}
        self.nodes = {}
        self.baseNodes = []
        self._connect_method = {1: 'skin', 2: 'constraint'}
        self.rig_grp_name = 'batch_rig_grp'

    def close(self):
        try:
            pm.deleteUI(self._winName)
        except:
            pass
    
    def show(self):
        self.close()
        self._win = pm.window(self._winName, title=self._title)
        with self._win:
            with pm.columnLayout(adj=True):
                self.uis['method_rbg'] = pm.radioButtonGrp(label='Method:', la2=['Skin', 'Constraint'], nrb=2)
                self.uis['ctl_count_isg'] = pm.intSliderGrp(field=True, label='Count:', minValue=1, maxValue=2, fieldMinValue=1, fieldMaxValue=10, value=1)
                self.uis['scaled_fsg'] = pm.floatSliderGrp(label='Scaled:', field=True, minValue=0.1, maxValue=2.0, fieldMinValue=0.1, fieldMaxValue=10.0, value=1.1)
                self.uis['interval_fsg'] = pm.floatSliderGrp(label='Interval:', field=True, minValue=1.0, maxValue=2.0, fieldMinValue=1.0, fieldMaxValue=10.0, value=1.2)
                self.uis['vis_cbg'] = pm.checkBoxGrp(numberOfCheckBoxes=2, label='',label1='Connect Visibility', v1=True, label2='Lock Scale', v2=True)
                pm.separator(height=10, style='in')
                with pm.rowLayout(nc=3, adj=2):
                    self.uis['create_loc_btn'] = pm.button(label='Create Locator',c=lambda *args: self.createLocator())
                    self.uis['create_btn'] = pm.button(label='Create Ctrl', c=lambda *args: self.create())
                pm.separator(height=10, style='none')

        self.updateUI()

    def updateUI(self):
        self.uis['method_rbg'].setSelect(2)

    def createLocator(self):
        objs = pm.ls(sl=True)
        del self.baseNodes[:]
        
        for obj in objs:
            nodeBase = NodeBase(obj)
            nodeBase.createLocator()
            self.baseNodes.append(nodeBase)

    def create(self):
        connect_method = self.uis['method_rbg'].getSelect()
        ctl_scaled = self.uis['scaled_fsg'].getValue()* 0.5
        ctl_count = self.uis['ctl_count_isg'].getValue()
        ctl_interval = self.uis['interval_fsg'].getValue()
        vis_cbg = self.uis['vis_cbg'].getValue1()
        scale_cbg = self.uis['vis_cbg'].getValue2()

        if not len(self.baseNodes):
            objs = pm.ls(sl=True)
            for obj in objs:
                self.baseNodes.append(NodeBase(obj))
        
        if len(self.baseNodes):
            rig_grp = self.getRigGrp()
            for nodeBase in self.baseNodes:
                if not nodeBase.exists():
                    nodeBase._average = False
                    nodeBase.scaled = ctl_scaled
                    nodeBase.interval = ctl_interval
                    nodeBase.exctlNum = ctl_count - 1
                    nodeBase.vis_geo = vis_cbg
                    nodeBase.scale_lock = scale_cbg
                    nodeBase.create()
                    nodeBase.connect(mode=self._connect_method.get(connect_method))

                    pm.parent(nodeBase.transforms[-1], rig_grp)

        del self.baseNodes[:]

    def lock_attrs(self, node, endIndex=20):
        for attr in BASE_ATTR_NAMES[:endIndex]:
            attr_ = node.attr(attr)
            attr_.setLock(True)
    
    def getRigGrp(self):
        if not pm.objExists(self.rig_grp_name):
            node = pm.createNode('transform', name=self.rig_grp_name)
        return pm.ls(self.rig_grp_name)[0]
    
def show():
    win = Window()
    win.show()

if __name__ == '__main__':
    show()
                    
                