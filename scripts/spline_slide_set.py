import pymel.core as pm
import maya.cmds as cmds

class createSlideSystem():
    def __init__(self, prefix, ctrl, uValueNodePath, uValueAttr, stretch=True, slide=True, spread=True, separate=False):
        self.objs = pm.ls(sl=True)
        self.prefix = prefix
        self.ctrl = pm.PyNode(ctrl) if isinstance(ctrl, str) else ctrl
        self.uValueNodePath = uValueNodePath.split(',') if isinstance(uValueNodePath, str) else uValueNodePath
        self.uValueAttr = uValueAttr
        self.enable_stretch = stretch
        self.enable_slide = slide
        self.enable_spread = spread
        self.enable_separate = separate
        
    def getUValueNode(self,node,attrChain):
        uValueNode = node
        for i, attr in enumerate(attrChain):
            try:
                inputs = uValueNode.attr(attr).inputs()
                if not inputs:
                    print(f"警告: 属性 {uValueNode}.{attr} 没有输入连接")
                    return None
                uValueNode = inputs[0]
                if i == 0:
                    self.loc_pointOnSurfaceInfo = inputs[0]
                elif i == 1:
                    self.loc_closestPointOnSurface = inputs[0]
                elif i == 3:
                    self.loc_blendColors = inputs[0]
            except Exception as e:
                print(f"错误: 在访问 {uValueNode}.{attr} 时出错: {str(e)}")
                return None 
        return uValueNode
        
    def addAttr(self,nodeName,attrName,min_val=0,max_val=10,dv_val=0): 
        if not nodeName.hasAttr(self.prefix+attrName):
            nodeName.addAttr(self.prefix+attrName,at='double',min=min_val,max=max_val,dv=dv_val,k=1)
        return self.prefix+attrName

    def createNode(self,nodeType,nodeName,editData={}):
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
    
    ### slide
    def createSlide(self,node,uValue):
        self.slideADL = self.createNode('addDoubleLinear',node+'_slide_add_ADL',editData={'input1':uValue})
        self.slideADL.output >> self.stretchMDL.input1
        
        self.slide_unit.output >> self.slideADL.input2
        
    ### stretch    
    def createStretch(self,node,uValue):
        stretchClamp = self.createNode('clamp',node+'_stretch_Clamp',editData={'maxR':1})
        stretchRev = self.createNode('reverse',node+'_stretch_Rev')
        stretchClamp.outputR >> self.stretchMDL.input2
        stretchRev.outputX >> stretchClamp.inputR
        if pm.objExists(node+'_slide_add_ADL'):
            self.slideADL = pm.PyNode(node+'_slide_add_ADL')
            stretchADL = self.createNode('addDoubleLinear',node+'_stretch_ADL',editData={'input2':-1})
            stretchRange = self.createNode('setRange',node+'_stretch_Range',editData={'minX':uValue,'oldMaxX':1,'maxX':1})
            stretchRange.outValueX >> self.slideADL.input1
            stretchADL.output >> stretchRange.valueX
            stretchRev.outputX >> stretchADL.input1

        self.stretch_unit.output >> stretchRev.inputX
        
    ### spread
    def createSpread(self,node,uValue):
        
        COND = self.createNode('condition',node+'_spread_COND',
            editData={
                'operation':3,
                'colorIfTrueR':uValue,
                'colorIfFalseR':uValue
            })
        minMath = self.createNode('floatMath',node+'_spread_min_Math',editData={'operation':4,'floatB':uValue})
        maxMath = self.createNode('floatMath',node+'_spread_max_Math',editData={'operation':5,'floatB':uValue})
        spreadADL = self.createNode('addDoubleLinear',node+'_spread_add_ADL',editData={'input1':1})
        COND.outColorR >> self.doublePMA.input1D[1]
        minMath.outFloat >> COND.colorIfFalseR
        maxMath.outFloat >> COND.colorIfTrueR
        spreadADL.output >> minMath.floatA
        
        self.spread_unit.output >> spreadADL.input2
        self.spread_unit.output >> maxMath.floatA
        self.spread_unit.output >> COND.firstTerm

    ### separate
    def createSeparate(self,node):
        loc_separate = self.createNode('blendColors',node+'_loc_out_separate',editData={'blender':0})
        self.loc_blendColors.outputR >> loc_separate.color1R
        self.loc_closestPointOnSurface.parameterU >> loc_separate.color2R
        loc_separate.outputR >> self.loc_pointOnSurfaceInfo.parameterU

        self.separate_unit.output >> loc_separate.blender

    def create(self):
        if self.enable_separate:
            separate = self.addAttr(self.ctrl,'separate',min_val=0,max_val=10,dv_val=0)
            self.separate_unit = self.createNode('multDoubleLinear','{}_{}_unit_MDL'.format(self.ctrl,separate),editData={'input2':0.1})
            self.ctrl.attr(separate) >> self.separate_unit.input1
        if self.enable_stretch:
            stretch = self.addAttr(self.ctrl,'stretch',min_val=-10,max_val=10,dv_val=0)
            self.stretch_unit = self.createNode('multDoubleLinear','{}_{}_unit_MDL'.format(self.ctrl,stretch),editData={'input2':0.1})
            self.ctrl.attr(stretch) >> self.stretch_unit.input1
        if self.enable_spread:
            spread = self.addAttr(self.ctrl,'spread',min_val=-10,max_val=10,dv_val=0)
            self.spread_unit = self.createNode('multDoubleLinear','{}_{}_unit_MDL'.format(self.ctrl,spread),editData={'input2':0.1})
            self.ctrl.attr(spread) >> self.spread_unit.input1
        if self.enable_slide:
            slide = self.addAttr(self.ctrl,'slide',min_val=-10,max_val=10,dv_val=0)
            self.slide_unit = self.createNode('multDoubleLinear','{}_{}_unit_MDL'.format(self.ctrl,slide),editData={'input2':0.1})
            self.ctrl.attr(slide) >> self.slide_unit.input1
        
        for node in self.objs:
            uValueNode = self.getUValueNode(node,attrChain=self.uValueNodePath)
            if not uValueNode:
                return
            uValue = uValueNode.attr(self.uValueAttr).get()
            print('{} : {}'.format(uValueNode, uValue))
            
            if self.enable_stretch or self.enable_slide or self.enable_spread:
                outClamp = self.createNode('clamp',node+'_uValue_out_Clamp',editData={'maxR':1})
                self.doublePMA = self.createNode('plusMinusAverage',node+'_uValue_double_PMA',
                    editData={
                        'input1D[0]':uValue,
                        'input1D[1]':uValue,
                        'input1D[2]':-uValue
                    })
                self.doublePMA.output1D >> outClamp.inputR
                outClamp.outputR >> uValueNode.attr(self.uValueAttr)
                
            if self.enable_stretch or self.enable_slide:
                Clamp = self.createNode('clamp',node+'_slide_stretch_Clamp',editData={'maxR':1})
                self.stretchMDL = self.createNode('multDoubleLinear',node+'_slide_stretch_MDL',editData={'input1':uValue,'input2':1})
                self.stretchMDL.output >> Clamp.inputR
                Clamp.outputR >> self.doublePMA.input1D[0]

            if self.enable_slide:
                self.createSlide(node, uValue)
            
            if self.enable_stretch:
                self.createStretch(node, uValue)
            
            if self.enable_spread:
                self.createSpread(node, uValue)
            
            if self.enable_separate:
                self.createSeparate(node)
            
def createSlideWin():
    # 删除现有窗口
    if cmds.window('createSlideWin_ui', q=True, ex=True):
        cmds.deleteUI('createSlideWin_ui')
    
    # 创建窗口
    window = cmds.window('createSlideWin_ui', title="创建滑动系统",s=True)
    main_layout = cmds.formLayout('formLayout_layout_ui')
    
    form0 = cmds.formLayout('formLayout0_ui')
    prefix_text = cmds.text('prefix_text_ui',l=u'0.载入属性前缀，用于区分多个属性')
    prefix_field = cmds.textField('prefix_ui',h=23)

    # 控制器选择部分
    form1 = cmds.formLayout('formLayout2_ui', p=main_layout)
    ctrl_text = cmds.text('ctrl_text_ui', l=u'1.载入要创建控制属性的物体', fn='smallFixedWidthFont', p=form1)
    ctrl_field = cmds.textField('ctrl_ui', p=form1,h=23)
    ctrl_btn = cmds.button('ctrl_load_ui', ann=u'载入选择物体', l=u'<<', p=form1, c=load_selected_controller)
    
    # 属性路径部分
    form2 = cmds.formLayout('formLayout3_ui', p=main_layout)
    path_text = cmds.text('uValueNodePath_text_ui', l=u'2.载入查询比例的属性路径链（逗号分隔）', fn='smallFixedWidthFont', p=form2,h=23)
    path_field = cmds.textField('uValueNodePath_ui', tx='t,parameterV,inPosition,uValue,color2R', p=form2)
    path_btn = cmds.button('uValueNodePath_load_ui', ann=u'载入默认值', l=u'<<', p=form2, c=load_default_path)
    
    # 输出属性部分
    form3 = cmds.formLayout('formLayout4_ui', p=main_layout)
    attr_text = cmds.text('outAttr_text_ui', l=u'3.载入用于存储比例的节点属性', fn='smallFixedWidthFont', p=form3,h=23)
    attr_field = cmds.textField('outAttr_ui', tx='input1X', p=form3)
    
    # 功能选择部分
    form4 = cmds.formLayout('formLayout5_ui', p=main_layout)
    type_text = cmds.text('slideType_text_ui', l=u'4.选择要创建的设置', fn='smallFixedWidthFont', p=form4)
    stretch_cb = cmds.checkBox('Stretch_ui', l=u'Stretch', v=True, p=form4)
    slide_cb = cmds.checkBox('Slide_ui', l=u'Slide', v=True, p=form4)
    spread_cb = cmds.checkBox('Spread_ui', l=u'Spread', v=True, p=form4)
    separate_cb = cmds.checkBox('separate_ui',l=u'Separate', p=form4)
    
    # 分隔线
    separator = cmds.separator('separator1_ui', p=main_layout, st='in')
    
    # 运行按钮部分
    form5 = cmds.formLayout('formLayout6_ui', p=main_layout)
    run_text = cmds.text('Run_text_ui', l=u'5.选择所有查询比例的起始节点', fn='smallFixedWidthFont', p=form5)
    run_btn = cmds.button('Run_ui', h=40, bgc=[0.42, 0.75, 0.42], l=u'Run', p=form5, c=run_system)
    
    # 布局设置
    cmds.formLayout(main_layout, e=True,
                   af=[[form0, 'top', 5], [form0, 'left', 5], [form0, 'right', 5],
                       (form1, 'left', 5), (form1, 'right', 5),
                       (form2, 'left', 5), (form2, 'right', 5),
                       (form3, 'left', 5), (form3, 'right', 5),
                       (form4, 'left', 5), (form4, 'right', 5),
                       (separator, 'left', 5), (separator, 'right', 5),
                       (form5, 'left', 5), (form5, 'right', 5), (form5, 'bottom', 5)],
                   ac=[[form1, 'top', 10, form0],
                       (form2, 'top', 10, form1),
                       (form3, 'top', 10, form2),
                       (form4, 'top', 10, form3),
                       (separator, 'top', 10, form4),
                       (form5, 'top', 5, separator)])
    
    cmds.formLayout(form0,e=True,
                    af=[[prefix_text, 'top', 0], [prefix_text, 'left', 0], 
                        [prefix_field, 'left', 0], [prefix_field, 'right', 0], [prefix_field, 'bottom', 0]],
                    ac=[[prefix_field, 'top', 5, prefix_text]])

    cmds.formLayout(form1, e=True,
                   af=[(ctrl_text, 'top', 0), (ctrl_text, 'left', 0),
                       (ctrl_field, 'left', 0), (ctrl_field, 'bottom', 0),
                       (ctrl_btn, 'right', 0), (ctrl_btn, 'bottom', 0)],
                   ac=[(ctrl_field, 'top', 5, ctrl_text),
                       (ctrl_btn, 'top', 5, ctrl_text),
                       (ctrl_btn, 'left', 3, ctrl_field)],
                   ap=[(ctrl_field, 'right', 0, 80)])
    
    cmds.formLayout(form2, e=True,
                   af=[(path_text, 'top', 0), (path_text, 'left', 0),
                       (path_field, 'left', 0), (path_field, 'bottom', 0),
                       (path_btn, 'right', 0), (path_btn, 'bottom', 0)],
                   ac=[(path_field, 'top', 5, path_text),
                       (path_btn, 'top', 5, path_text),
                       (path_btn, 'left', 3, path_field)],
                   ap=[(path_field, 'right', 0, 80)])
    
    cmds.formLayout(form3, e=True,
                   af=[(attr_text, 'top', 0), (attr_text, 'left', 0),
                       (attr_field, 'left', 0), (attr_field, 'right', 0), (attr_field, 'bottom', 0)],
                   ac=[(attr_field, 'top', 5, attr_text)])
    
    cmds.formLayout(form4, e=True,
                   af=[(type_text, 'top', 0), (type_text, 'left', 0),
                       (stretch_cb, 'left', 0), (stretch_cb, 'bottom', 0),
                       (slide_cb, 'bottom', 0), (separate_cb, 'right', 0), (spread_cb, 'bottom', 0)],
                   ac=[(stretch_cb, 'top', 5, type_text),
                       (slide_cb, 'top', 5, type_text),
                       (slide_cb, 'left', 10, stretch_cb),
                       (spread_cb, 'top', 5, type_text),
                       (spread_cb, 'left', 10, slide_cb),
                       (separate_cb, 'top', 5, type_text),
                       (separate_cb, 'left', 10, spread_cb)])
    
    cmds.formLayout(form5, e=True,
                   af=[(run_text, 'top', 0), (run_text, 'left', 0),
                       (run_btn, 'left', 0), (run_btn, 'right', 0), (run_btn, 'bottom', 0)],
                   ac=[(run_btn, 'top', 5, run_text)])
    
    cmds.showWindow(window)

def load_selected_controller(*args):
    selection = pm.ls(sl=True)
    if selection:
        cmds.textField('ctrl_ui', e=True, tx=selection[0].name())
    else:
        cmds.warning(u'请先选择一个控制器')

def load_default_path(*args):
    cmds.textField('uValueNodePath_ui', e=True, tx='t,parameterV,inPosition,uValue,color2R')

def run_system(*args):
    # 获取UI中的参数
    prefix = cmds.textField('prefix_ui', q=True, tx=True)
    ctrl = cmds.textField('ctrl_ui', q=True, tx=True)
    uValueNodePath = cmds.textField('uValueNodePath_ui', q=True, tx=True)
    uValueAttr = cmds.textField('outAttr_ui', q=True, tx=True)
    stretch = cmds.checkBox('Stretch_ui', q=True, v=True)
    slide = cmds.checkBox('Slide_ui', q=True, v=True)
    spread = cmds.checkBox('Spread_ui', q=True, v=True)
    separate = cmds.checkBox('separate_ui', q=True, v=True)
    
    # 检查是否有选中的对象
    selected_objs = pm.ls(sl=True)
    if not selected_objs:
        cmds.warning(u'请先选择要应用滑动系统的对象')
        return
    
    # 检查控制器是否存在
    if not pm.objExists(ctrl):
        cmds.warning(u'控制器不存在: {}'.format(ctrl))
        return
    
    # 创建滑动系统
    try:
        slide_system = createSlideSystem(prefix, ctrl, uValueNodePath, uValueAttr, stretch, slide, spread, separate)
        slide_system.create()
        cmds.confirmDialog(title=u'成功', message=u'滑动系统创建完成!')
    except Exception as e:
        cmds.warning(u'创建滑动系统时出错: {}'.format(str(e)))

if __name__ == '__main__':
    createSlideWin()