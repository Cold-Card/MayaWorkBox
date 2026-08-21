# -*- coding: utf-8 -*-
# Introduction: Fix nHair Distortion
# Author: WangRuiLong
import maya.cmds as cmds
import pymel.core as pm

Fix_nHair_Distortion_version = '1.0.0'

class MainUI():
    def __init__(self,MainPY):
        self.window = None
        self.py = MainPY
        self.modified_list = None
        self.referenced_list = None
        self.FHD_parent_node_text = None
    
    def create_window(self):
        window_name = 'fix_nHair_distortion_window'
        if pm.window(window_name,exists=True):
            pm.deleteUI(window_name,window=True)
        self.window = pm.window(window_name,title='Fix nHair Distortion '+Fix_nHair_Distortion_version,s=True)
        
        pm.formLayout('sep_formLayout_ui')
        pm.formLayout('main_formLayout_ui')
        pm.separator('main_separator_1_ui',st=u'in')
        pm.formLayout('list_formLayout_ui')
        pm.button('load_referenced_button_ui',h=30,ann=u'Load Referenced Itme',l=u'Referenced',c=lambda *args:self.py.load_sel('ref'))
        pm.button('load_modified_button_ui',h=30,ann=u'Load Modified Itme',l=u'Modified',c=lambda *args:self.py.load_sel('mod'))
        self.referenced_list = pm.textScrollList('referenced_textScrollList_ui',ams=True,sc=lambda *args:self.py.sel_list('ref'))
        pm.popupMenu('ref_list_popupMenu_ui',p='referenced_textScrollList_ui')
        pm.menuItem('ref_list_on_unique_menuItem_ui',l=u'No Unique',cb=False)
        pm.menuItem('ref_list_menuItemDivider_ui',d=True)
        pm.menuItem('ref_list_sorted_menuItem_ui',l=u'A-Z Sorted',c=lambda *args:self.py.sorted_list('ref'))
        pm.menuItem('ref_list_sorted_rev_menuItem_ui',l=u'Z-A Sorted',c=lambda *args:self.py.sorted_list('ref',rev=1))
        self.modified_list = pm.textScrollList('modified_textScrollList_ui',ams=True,sc=lambda *args:self.py.sel_list('mod'))
        pm.popupMenu('mod_list_popupMenu_ui',p='modified_textScrollList_ui')
        pm.menuItem('mod_list_on_unique_menuItem_ui',l=u'No Unique',cb=False)
        pm.menuItem('mod_list_menuItemDivider_ui',d=True)
        pm.menuItem('mod_list_sorted_menuItem_ui',l=u'A-Z Sorted',c=lambda *args:self.py.sorted_list('mod'))
        pm.menuItem('mod_list_sorted_rev_menuItem_ui',l=u'Z-A Sorted',c=lambda *args:self.py.sorted_list('mod',rev=1))
        pm.formLayout('referenced_button_formLayout_ui')
        pm.button('referenced_add_button_ui',ann=u'Add Item',l=u'＋',c=lambda *args:self.py.edit_list('add','ref'))
        pm.button('referenced_remove_button_ui',ann=u'Remove Item',l=u'－',c=lambda *args:self.py.edit_list('remove','ref'))
        pm.button('referenced_up_button_ui',ann=u'Move Up',l=u'∧',c=lambda *args:self.py.move_list('move_up','ref'))
        pm.button('referenced_down_button_ui',ann=u'Move Down',l=u'∨',c=lambda *args:self.py.move_list('move_down','ref'))
        pm.formLayout('modified_button_formLayout_ui',p='list_formLayout_ui')
        pm.button('modified_add_button_ui',ann=u'Add Item',l=u'＋',c=lambda *args:self.py.edit_list('add','mod'))
        pm.button('modified_remove_button_ui',ann=u'Remove Item',l=u'－',c=lambda *args:self.py.edit_list('remove','mod'))
        pm.button('modified_up_button_ui',ann=u'Move Up',l=u'∧',c=lambda *args:self.py.move_list('move_up','mod'))
        pm.button('modified_down_button_ui',ann=u'Move Down',l=u'∨',c=lambda *args:self.py.move_list('move_down','mod'))
        pm.separator('main_separator_2_ui',p='main_formLayout_ui',st=u'in')
        pm.formLayout('command_formLayout_ui',p='main_formLayout_ui')
        pm.frameLayout('FHD_frameLayout_ui',bgc=[0.3199999928474426, 0.3199999928474426, 0.3199999928474426],cl=False,cll=True,l=u'Fix nHair Distortion',mh=2)
        pm.formLayout('FHD_formLayout_ui')
        pm.button('FHD_create_loc_set_button_ui',ann=u'Create Loc',bgc=[0.41999998688697815, 0.5600000023841858, 0.75],l=u'Create',c=lambda *args:self.py.fix_nHair_distortion('create'))
        pm.button('FHD_sel_parent_node_button_ui',l=u'Sel',c=lambda *args:self.py.fix_nHair_distortion('sel'))
        self.FHD_parent_node_text = pm.textField('FHD_parent_node_textField_ui',ann=u'Load the parent node, if not, use the model itself',ed=False)
        pm.button('FHD_load_parent_node_button_ui',l=u'< Load',c=lambda *args:self.py.fix_nHair_distortion('load'))
        pm.button('FHD_fix_VLD_button_ui',h=30,ann=u'Fix Vertex Large-displacement Distortion',bgc=[0.41999998688697815, 0.75, 0.41999998688697815],l=u'Fix',c=lambda *args:self.py.fix_nHair_distortion('fix'))
        pm.button('FHD_break_fix_button_ui',ann=u'Break fix node',bgc=[0.75, 0.699999988079071, 0.41999998688697815],l=u'Break Fix',c=lambda *args:self.py.fix_nHair_distortion('break'))
        pm.button('FHD_del_fix_button_ui',ann=u'Delete fix node',bgc=[0.75, 0.4300000071525574, 0.41999998688697815],l=u'Del Fix',c=lambda *args:self.py.fix_nHair_distortion('del'))
        pm.separator('main_separator_3_ui',p='main_formLayout_ui',st=u'in')
        self.main_progressBar = pm.progressBar('main_progressBar_ui',p='main_formLayout_ui',h=10)
        pm.separator('mian_separator_4_ui',p='main_formLayout_ui',st=u'in')
        pm.formLayout('sep_formLayout_ui',e=1,af=[['main_formLayout_ui', 'top', 0], ['main_formLayout_ui', 'left', 2], ['main_formLayout_ui', 'right', 2], ['main_formLayout_ui', 'bottom', 0]])
        pm.formLayout('main_formLayout_ui',e=1,af=[['main_separator_1_ui', 'top', 5], ['main_separator_1_ui', 'left', 0], ['main_separator_1_ui', 'right', 0], ['list_formLayout_ui', 'left', 0], ['list_formLayout_ui', 'right', 0], ['main_separator_2_ui', 'left', 0], ['main_separator_2_ui', 'right', 0], ['command_formLayout_ui', 'left', 0], ['command_formLayout_ui', 'right', 0], ['main_separator_3_ui', 'left', 0], ['main_separator_3_ui', 'right', 0], ['main_progressBar_ui', 'left', 0], ['main_progressBar_ui', 'right', 0], ['mian_separator_4_ui', 'left', 0], ['mian_separator_4_ui', 'right', 0], ['mian_separator_4_ui', 'bottom', 5]],ac=[['list_formLayout_ui', 'top', 5, 'main_separator_1_ui'], ['list_formLayout_ui', 'bottom', 5, 'main_separator_2_ui'], ['main_separator_2_ui', 'bottom', 5, 'command_formLayout_ui'], ['command_formLayout_ui', 'bottom', 5, 'main_separator_3_ui'], ['main_separator_3_ui', 'bottom', 3, 'main_progressBar_ui'], ['main_progressBar_ui', 'bottom', 3, 'mian_separator_4_ui']])
        pm.formLayout('list_formLayout_ui',e=1,af=[['load_referenced_button_ui', 'top', 0], ['load_referenced_button_ui', 'left', 0], ['load_modified_button_ui', 'top', 0], ['load_modified_button_ui', 'right', 0], ['referenced_textScrollList_ui', 'left', 0], ['modified_textScrollList_ui', 'right', 0], ['referenced_button_formLayout_ui', 'left', 0], ['referenced_button_formLayout_ui', 'bottom', 0], ['modified_button_formLayout_ui', 'right', 0], ['modified_button_formLayout_ui', 'bottom', 0]],ac=[['referenced_textScrollList_ui', 'top', 0, 'load_referenced_button_ui'], ['referenced_textScrollList_ui', 'bottom', 0, 'referenced_button_formLayout_ui'], ['modified_textScrollList_ui', 'top', 0, 'load_modified_button_ui'], ['modified_textScrollList_ui', 'bottom', 0, 'modified_button_formLayout_ui']],ap=[['load_referenced_button_ui', 'right', 1, 50], ['load_modified_button_ui', 'left', 1, 50], ['referenced_textScrollList_ui', 'right', 1, 50], ['modified_textScrollList_ui', 'left', 1, 50], ['referenced_button_formLayout_ui', 'right', 1, 50], ['modified_button_formLayout_ui', 'left', 1, 50]])
        pm.formLayout('referenced_button_formLayout_ui',e=1,af=[['referenced_add_button_ui', 'top', 0], ['referenced_add_button_ui', 'left', 0], ['referenced_add_button_ui', 'bottom', 0], ['referenced_remove_button_ui', 'top', 0], ['referenced_remove_button_ui', 'bottom', 0], ['referenced_up_button_ui', 'top', 0], ['referenced_up_button_ui', 'bottom', 0], ['referenced_down_button_ui', 'top', 0], ['referenced_down_button_ui', 'right', 0], ['referenced_down_button_ui', 'bottom', 0]],ap=[['referenced_add_button_ui', 'right', 1, 25], ['referenced_remove_button_ui', 'left', 1, 25], ['referenced_remove_button_ui', 'right', 1, 50], ['referenced_up_button_ui', 'left', 1, 50], ['referenced_up_button_ui', 'right', 1, 75], ['referenced_down_button_ui', 'left', 1, 75]])
        pm.formLayout('modified_button_formLayout_ui',e=1,af=[['modified_add_button_ui', 'top', 0], ['modified_add_button_ui', 'left', 0], ['modified_add_button_ui', 'bottom', 0], ['modified_remove_button_ui', 'top', 0], ['modified_remove_button_ui', 'bottom', 0], ['modified_up_button_ui', 'top', 0], ['modified_up_button_ui', 'bottom', 0], ['modified_down_button_ui', 'top', 0], ['modified_down_button_ui', 'right', 0], ['modified_down_button_ui', 'bottom', 0]],ap=[['modified_add_button_ui', 'right', 1, 25], ['modified_remove_button_ui', 'left', 1, 25], ['modified_remove_button_ui', 'right', 1, 50], ['modified_up_button_ui', 'left', 1, 50], ['modified_up_button_ui', 'right', 1, 75], ['modified_down_button_ui', 'left', 1, 75]])
        pm.formLayout('command_formLayout_ui',e=1,af=[['FHD_frameLayout_ui', 'left', 0], ['FHD_frameLayout_ui', 'right', 0]],ac=[])
        pm.formLayout('FHD_formLayout_ui',e=1,af=[['FHD_create_loc_set_button_ui', 'top', 0], ['FHD_create_loc_set_button_ui', 'left', 0], ['FHD_sel_parent_node_button_ui', 'top', 0], ['FHD_parent_node_textField_ui', 'top', 0], ['FHD_load_parent_node_button_ui', 'top', 0], ['FHD_load_parent_node_button_ui', 'right', 0], ['FHD_fix_VLD_button_ui', 'left', 0], ['FHD_fix_VLD_button_ui', 'right', 0], ['FHD_break_fix_button_ui', 'left', 0], ['FHD_del_fix_button_ui', 'right', 0]],ac=[['FHD_parent_node_textField_ui', 'left', 1, 'FHD_sel_parent_node_button_ui'], ['FHD_parent_node_textField_ui', 'right', 1, 'FHD_load_parent_node_button_ui'], ['FHD_fix_VLD_button_ui', 'top', 2, 'FHD_load_parent_node_button_ui'], ['FHD_break_fix_button_ui', 'top', 2, 'FHD_fix_VLD_button_ui'], ['FHD_del_fix_button_ui', 'top', 2, 'FHD_fix_VLD_button_ui']],ap=[['FHD_create_loc_set_button_ui', 'right', 1, 15], ['FHD_sel_parent_node_button_ui', 'left', 1, 15], ['FHD_load_parent_node_button_ui', 'left', 0, 85], ['FHD_break_fix_button_ui', 'right', 1, 50], ['FHD_del_fix_button_ui', 'left', 1, 50]])
        
        self.window.show()

class MainPY():
    def __init__(self):
        self.ui = MainUI(self)
        self.CopySkinWeightsMel = 'copySkinWeights -noMirror -surfaceAssociation closestPoint -influenceAssociation closestJoint -influenceAssociation oneToOne;'
        self.WrapMel = 'CreateWrap;'
    
    # load sel
    def load_sel(self,button):
        if button == 'ref':
            stuff = self.ui.referenced_list
        elif button == 'mod':
            stuff = self.ui.modified_list
        sel = cmds.ls(sl=True,fl=True)
        stuff.removeAll()
        for item in sel:
            stuff.append(item)
    
    # sel list
    def sel_list(self,project):
        if project == 'ref':
            stuff = self.ui.referenced_list
        elif project == 'mod':
            stuff = self.ui.modified_list
        sel_item = stuff.getSelectItem()
        pm.select(sel_item,r=True)
        
    # edit list
    def edit_list(self,button,project):
        sel = cmds.ls(sl=True,fl=True)
        if project == 'ref':
            stuff = self.ui.referenced_list
            unique_check = pm.menuItem('ref_list_on_unique_menuItem_ui', q=True, cb=True)
        elif project == 'mod':
            stuff = self.ui.modified_list
            unique_check = pm.menuItem('mod_list_on_unique_menuItem_ui', q=True, cb=True)
        items = stuff.getAllItems()
        if button == 'add':
            for item in sel:
                if item in items and unique_check == 0:
                    continue
                stuff.append(item)
        elif button == 'remove':
            if unique_check == 0:
                for item in sel:
                    if item not in items:
                        continue
                    stuff.removeItem(item)
            if unique_check == 1:
                indexs = stuff.getSelectIndexedItem()
                for index in sorted(indexs,reverse=True):
                    stuff.removeIndexedItem(index)
    
    # move list
    def move_list(self,button,project):
        if project == 'ref':
            stuff = self.ui.referenced_list
        elif project == 'mod':
            stuff = self.ui.modified_list
        sel_items = stuff.getSelectItem()
        sel_items_index = stuff.getSelectIndexedItem()
        if button == 'move_up':
            if sel_items:
                for item, index in list(zip(sel_items,sel_items_index)):
                    if index > 1:
                        stuff.removeIndexedItem(index)
                        stuff.appendPosition([index-1,item])
                        stuff.setSelectIndexedItem(index-1)
        elif button == 'move_down':
            if sel_items:
                number_index = stuff.getNumberOfItems()
                for item, index in reversed(list(zip(sel_items,sel_items_index))):
                    if index < number_index:
                        stuff.removeIndexedItem(index)
                        stuff.appendPosition([index+1,item])
                        stuff.setSelectIndexedItem(index+1)

    # Sorted list
    def sorted_list(self,project,rev=0):
        if project == 'ref':
            stuff = self.ui.referenced_list
        elif project == 'mod':
            stuff = self.ui.modified_list
        item_list = stuff.getAllItems()
        sorted_item = sorted(item_list)
        stuff.removeAll()
        if rev:
            sorted_item = sorted(sorted_item,reverse=True)
        for item in sorted_item:
            stuff.append(item)
                        
    # print
    def print_command_out(self,outM,outWarning=False,outSep=True):
        if outSep:
            outSepnum = 10
        else:
            outSepnum = 0
        if not outWarning:
            print('='*outSepnum + ' {} '.format(outM) + '='*outSepnum)
        else:
            pm.warning(' {} '.format(outM))
        # pm.scrollField(self.ui.command_print,edit=True,it='='*outSepnum + ' {} '.format(outM) + '='*outSepnum + '\n')
    
    # progressBar
    def progressBar_set(self,i,num):
        pm.progressBar(self.ui.main_progressBar,edit=True,maxValue=num)
        pm.progressBar(self.ui.main_progressBar,edit=True,progress=i)

    # Fix nHair Distortion
    def fix_nHair_distortion(self,button):
        if button == 'create':
            if not pm.objExists('VLD_Loc'):
                VLD_loc = pm.spaceLocator(n='VLD_Loc')
                VLD_loc.useOutlinerColor.set(1)
                VLD_loc.outlinerColor.set(0.85,0.70,1.70)
                VLD_loc.getShape().overrideEnabled.set(1)
                VLD_loc.getShape().overrideRGBColors.set(1)
                VLD_loc.getShape().overrideColorRGB.set(0.85,0.70,1.70)
                pm.group(VLD_loc,n='VLD_Set_Grp')
                pm.setAttr('VLD_Set_Grp.useOutlinerColor',1)
                pm.setAttr('VLD_Set_Grp.outlinerColor',0.85,0.70,1.70)
                pm.setAttr('VLD_Set_Grp.v',0)
            pm.textField(self.ui.FHD_parent_node_text,e=True,tx='VLD_Loc')
            if pm.objExists('MainExtra2'):
                pm.pointConstraint('MainExtra2','VLD_Loc',mo=True)
            elif pm.objExists('Main'):
                pm.pointConstraint('Main','VLD_Loc',mo=True)
            if pm.objExists('RIG_Other'):
                pm.parent('VLD_Set_Grp','RIG_Other')
            pm.select(cl=True)
            return
        
        elif button == 'load':
            sel = pm.ls(sl=True,type='transform')
            if sel:
                pm.textField(self.ui.FHD_parent_node_text,e=True,tx=sel[0])
            else:
                pm.textField(self.ui.FHD_parent_node_text,e=True,tx='')
            return
            
        FHD_parent_node = pm.textField(self.ui.FHD_parent_node_text,q=True,tx=True)
        
        if button == 'sel':
            if FHD_parent_node:
                pm.select(FHD_parent_node,r=True)
            return
        
        self.print_command_out('Fix nHair Distortion')
        modified_models = self.ui.modified_list.getAllItems()
        for i, modified_model in enumerate(modified_models):
            modified_shape = pm.listRelatives(modified_model, shapes=True, fullPath=True)[0]
            follicle_shape = pm.listConnections(modified_shape+'.create',s=True,d=False,sh=True)[0]
            if follicle_shape and follicle_shape.type() == 'follicle':
                tempCurve = pm.listConnections(follicle_shape+'.startPositionMatrix',s=True,d=False)[0]
            else:
                self.print_command_out('{} 未查询到 follicle 节点，已跳过'.format(modified_model),outWarning=True,outSep=False)
                continue
            multMat_name = modified_model
            if FHD_parent_node:
                multMat_name = FHD_parent_node
            if button == 'fix':
                if tempCurve.type() == 'multMatrix':
                    self.print_command_out('{} 已存在修复节点，已跳过'.format(modified_model),outWarning=True,outSep=False)
                    continue
                multMat = '{}_multMatrix_{}'.format(multMat_name,tempCurve)
                while not pm.objExists(multMat):
                    multMat = pm.createNode('multMatrix',n=multMat)
                    pm.connectAttr(tempCurve+'.worldMatrix[0]',multMat+'.matrixIn[0]',f=True)
                    pm.connectAttr(multMat_name+'.worldInverseMatrix[0]',multMat+'.matrixIn[1]',f=True)
                conn_nodes = pm.listConnections(tempCurve+'.worldMatrix[0]',s=False,p=True,t='follicle')
                conn_attrs = [conn_attr for conn_attr in conn_nodes if conn_attr.node() == follicle_shape]
                if conn_attrs:
                    for conn_li in conn_attrs:
                        pm.connectAttr(multMat+'.matrixSum',conn_li,f=True)
                self.print_command_out('{} 已创建修复节点并连接'.format(modified_model),outWarning=False,outSep=False)
            else:
                multMats = pm.listConnections(follicle_shape+'.startPositionMatrix',d=False,t='multMatrix')
                if not multMats and button == 'break':
                    self.print_command_out('{} 未查询到修复节点，已跳过'.format(modified_model),outWarning=True,outSep=False)
                    continue
                for multMat in multMats:
                    tempCurve = pm.listConnections(multMat+'.matrixIn[0]',d=False,p=True,t='transform')
                    conn_nodes = pm.listConnections(multMat+'.matrixSum',s=False,p=True,t='follicle')
                    conn_attrs = [conn_attr for conn_attr in conn_nodes if conn_attr.node() == follicle_shape]
                    for conn_li in conn_attrs:
                        pm.connectAttr(tempCurve[0],conn_li,f=True)
            if button == 'break':
                self.print_command_out('{} 已断开修复节点连接'.format(modified_model),outWarning=False,outSep=False)
                if i == len(modified_models)-1:
                    pm.inViewMessage(amg='Fix nHair Distortion: <hl>Break Fianl</hl>',pos='midCenterTop',fade=False,dk=True)
            if button == 'del':
                tempCurve = pm.listConnections(follicle_shape+'.startPositionMatrix',s=True,d=False,t='transform')[0]
                if tempCurve:
                    multMats = pm.listConnections(tempCurve+'.worldMatrix[0]',s=False,t='multMatrix')
                    for multMat in multMats:
                        conn_nodes = pm.listConnections(multMat+'.matrixSum',s=False,p=True,t='follicle')
                        if not conn_nodes:
                            pm.delete(multMat)
                self.print_command_out('{} 已删除修复节点'.format(modified_model),outWarning=False,outSep=False)
                if i == len(modified_models)-1:
                    pm.inViewMessage(amg='Fix nHair Distortion: <hl>Delete Fianl</hl>',pos='midCenterTop',fade=False,dk=True)
            self.progressBar_set(i+1,len(modified_models))
                    
if __name__ == '__main__':
    MainPY().ui.create_window()