# -*- coding: utf-8 -*-
# Introduction: WRL BatchTool
# Author: WangRuiLong
WRL_BatchTool_version = '2.5.2'
'''
Update Log:
    v2.5.2:
        列表添加 Flatten 选项，用于切换列表载入对象是否扁平化
    v2.5.1:
        添加 transferUVs 功能
    v2.5.0:
        代码重新编写（完成）
        优化 FSD 模块代码
        优化 Add BlendShape Target 模块代码
    v2.5.0_a:
        代码重新编写（原部分功能未完成）
        重新编写 UI ，部分模块名称更改
        将原有 FSD (Fix Skin Distortion) 模块中的 Loc 更名为 VLD (Vertex Large-displacement Distortion) 
        Skin Copy Weight 模块添加 Remove Unused Influences 选项
    v2.4.0:
        添加 Copy Constraint 模块
    v2.3.1:
        Create Cloth Set 模块添加 Wrap Exclusive Bind 选项
        Fix Skin Distortion 模块添加 Import Loc 功能
    v2.3.0:
        添加 Sec Build 模块
    v2.2.1:
        删除 print command out 模块，更换为 progressBar 模块
        优化部分代码
    v2.2.0:
        整理代码，将 UI 整理为单独 Class
        添加 Create Cloth Set 模块
    v2.1.2:
        优化 Fix Skin Distortion 模块的 Del Fix 功能，支持同时删除 Parent Node 与 No Parent Node 模式创建的修复节点
    v2.1.1:
        优化 Fix Skin Distortion 模块，支持载入指定父对象节点
    v2.1.0:
        添加 Fix Skin Distortion 模块
        增加列表排序功能
    v2.0.2:
        添加 Match T、R、S、P 功能
    v2.0.1:
        优化并添加 print command out 模块
    v2.0.0:
        重写 UI 部分（更换为 formLayout 布局）
        优化编辑列表中的 remove 功能
    ...
'''
import maya.cmds as cmds
import pymel.core as pm
if __name__ != '__main__':
    from . import sec_ctrl_build
    from . import fx_cloth_build

class MainUI():
    def __init__(self,MainPY):
        self.window = None
        self.py = MainPY
        self.modified_list = None
        self.referenced_list = None
        self.prefix_text = None
        self.suffix_text = None
        self.FSD_parent_node_text = None
    
    def create_window(self):
        window_name = 'WRL_BatchTool_window'
        if pm.window(window_name,exists=True):
            pm.deleteUI(window_name,window=True)
        self.window = pm.window(window_name,title='BatchTool '+WRL_BatchTool_version,s=True)
        
        pm.formLayout('sep_formLayout_ui')

        pm.formLayout('main_formLayout_ui')

        pm.separator('main_separator_1_ui',st=u'in')

        pm.formLayout('list_formLayout_ui')
        pm.button('load_referenced_button_ui',h=30,ann=u'Load Referenced Itme',l=u'Referenced',c=lambda *args:self.py.load_sel('ref'))
        pm.button('load_modified_button_ui',h=30,ann=u'Load Modified Itme',l=u'Modified',c=lambda *args:self.py.load_sel('mod'))
        self.referenced_list = pm.textScrollList('referenced_textScrollList_ui',ams=True,sc=lambda *args:self.py.sel_list('ref'))
        pm.popupMenu('ref_list_popupMenu_ui',p='referenced_textScrollList_ui')
        pm.menuItem('ref_list_on_unique_menuItem_ui',l=u'No Unique',cb=False)
        pm.menuItem('ref_list_flatten_menuItem_ui',l=u'Flatten',cb=True)
        pm.menuItem('ref_list_menuItemDivider_ui',d=True)
        pm.menuItem('ref_list_sorted_menuItem_ui',l=u'A-Z Sorted',c=lambda *args:self.py.sorted_list('ref'))
        pm.menuItem('ref_list_sorted_rev_menuItem_ui',l=u'Z-A Sorted', c=lambda *args:self.py.sorted_list('ref',rev=1))
        self.modified_list = pm.textScrollList('modified_textScrollList_ui',ams=True,sc=lambda *args:self.py.sel_list('mod'))
        pm.popupMenu('mod_list_popupMenu_ui',p='modified_textScrollList_ui')
        pm.menuItem('mod_list_on_unique_menuItem_ui',l=u'No Unique',cb=False)
        pm.menuItem('mod_list_flatten_menuItem_ui',l=u'Flatten',cb=True)
        pm.menuItem('mod_list_menuItemDivider_ui',d=True)
        pm.menuItem('mod_list_sorted_menuItem_ui',l=u'A-Z Sorted', c=lambda *args:self.py.sorted_list('mod'))
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

        pm.formLayout('Rename_formLayout_ui',p='main_formLayout_ui')
        pm.button('Rename_del_prefix_button_ui',l=u'Del',c=lambda *args:self.py.rename_item('del_prefix'))
        self.prefix_text = pm.textField('Rename_prefix_textField_ui')
        pm.popupMenu('Rename_prefix_popupMenu_ui',p='Rename_prefix_textField_ui')
        pm.menuItem('prefix_none_menuItem_ui',l=u'',c=lambda *args:pm.textField(self.prefix_text,e=True,tx=''))
        pm.menuItem('prefix_wrap_menuItem_ui',l=u'Wrap_',c=lambda *args:pm.textField(self.prefix_text,e=True,tx='Wrap_'))
        pm.menuItem('prefix_ncloth_menuItem_ui',l=u'nCloth_',c=lambda *args:pm.textField(self.prefix_text,e=True,tx='nCloth_'))
        pm.button('Rename_rename_button_ui',l=u'Rename',c=lambda *args:self.py.rename_item('rename'))
        pm.popupMenu('Rename_rename_button_popupMenu_ui',p='Rename_rename_button_ui')
        pm.menuItem('Raname_Ignore_Referenced_menuItem_ui',l=u'Ignore Referenced',cb=True)
        self.suffix_text = pm.textField('Rename_suffix_textField_ui')
        pm.popupMenu('Rename_suffix_popupMenu_ui',p='Rename_suffix_textField_ui')
        pm.menuItem('suffix_none_menuItem_ui',l=u'',c=lambda *args:pm.textField(self.suffix_text,e=True,tx=''))
        pm.menuItem('suffix_cfx_menuItem_ui',l=u'_cfx',c=lambda *args:pm.textField(self.suffix_text,e=True,tx='_cfx'))
        pm.menuItem('suffix_lw_menuItem_ui',l=u'_lw',c=lambda *args:pm.textField(self.suffix_text,e=True,tx='_lw'))
        pm.menuItem('suffix_grp_menuItem_ui',l=u'_Grp',c=lambda *args:pm.textField(self.suffix_text,e=True,tx='_Grp'))
        pm.menuItem('suffix_geo_menuItem_ui',l=u'_Geo',c=lambda *args:pm.textField(self.suffix_text,e=True,tx='_Geo'))
        pm.menuItem('suffix_offset_grp_menuItem_ui',l=u'_offset_Grp',c=lambda *args:pm.textField(self.suffix_text,e=True,tx='_offset_Grp'))
        pm.menuItem('suffix_extra_grp_menuItem_ui',l=u'_extra_Grp',c=lambda *args:pm.textField(self.suffix_text,e=True,tx='_extra_Grp'))
        pm.menuItem('suffix_follicle_menuItem_ui',l=u'_follicle',c=lambda *args:pm.textField(self.suffix_text,e=True,tx='_follicle'))
        pm.button('Rename_del_suffix_button_ui',l=u'Del',c=lambda *args:self.py.rename_item('del_suffix'))
	
        pm.separator('main_separator_3_ui',p='main_formLayout_ui',st=u'in')

        pm.formLayout('command_formLayout_ui',p='main_formLayout_ui')

        pm.frameLayout('RM_frameLayout_ui',bgc=[0.3199999928474426, 0.3199999928474426, 0.3199999928474426],cll=True,l=u'R <> M',mh=5)
        pm.formLayout('RM_formLayout_ui')
        pm.formLayout('RM_radio_formLayout_ui')
        self.radio_collection = pm.radioCollection('RM_radio_collection_ui')
        pm.radioButton('RM_one_to_one_radioButton_ui',l=u'One to One',sl=True)
        pm.radioButton('RM_all_to_all_radioButton_ui',l=u'All to All')

        pm.separator('RM_separator_1_ui',p='RM_formLayout_ui',st=u'none')

        pm.button('RM_skin_copy_button_ui',p='RM_formLayout_ui',h=40,l=u'Skin + Copy Weight\nR > M',c=lambda *args:self.py.skin_copy_weight())
        pm.popupMenu('RM_skin_copy_popupMenu_ui',p='RM_skin_copy_button_ui')
        pm.menuItem('remove_unused_influences_menuItem_ui',l=u'Remove Unused Influences',cb=True)
        pm.button('RM_add_targets_button_ui',p='RM_formLayout_ui',h=30,l=u'Add BlendShape Target\nR > M',c=lambda *args:self.py.add_targets())
        pm.button('RM_transferUVs_button_ui',p='RM_formLayout_ui',h=30,l=u'transferUVs\nR > M',c=lambda *args:self.py.transferUVs())
        pm.popupMenu('RM_transferUVs_button_popupMenu_ui',p='RM_transferUVs_button_ui')
        pm.radioMenuItemCollection('RM_transferUVs_radioMenuItemCollection_ui')
        pm.menuItem('RM_transferUVs_world_ui',l=u'World',rb=False)
        pm.menuItem('RM_transferUVs_local_ui',l=u'Local',rb=False)
        pm.menuItem('RM_transferUVs_component_ui',l=u'Component',rb=False)
        pm.menuItem('RM_transferUVs_topology_ui',l=u'Topology',rb=True)
        pm.button('RM_copy_constraint_button_ui',p='RM_formLayout_ui',h=30,l=u'Copy Constraint\nR > M',c=lambda *args:self.py.copy_constraint())
        pm.separator('RM_separator_2_ui',p='RM_formLayout_ui',st=u'in')
        pm.button('RM_match_button_ui',p='RM_formLayout_ui',h=47,ann=u'Match All  Transformations',l=u'Match Transformations\nR < M',c=lambda *args:self.py.match_transformations(1,1,1,0))
        pm.button('RM_match_T_button_ui',p='RM_formLayout_ui',ann=u'Match Translation',l=u'Match T',c=lambda *args:self.py.match_transformations(1,0,0,0))
        pm.button('RM_match_R_button_ui',p='RM_formLayout_ui',ann=u'Match Rotation',l=u'Match R',c=lambda *args:self.py.match_transformations(0,1,0,0))
        pm.button('RM_match_S_button_ui',p='RM_formLayout_ui',ann=u'Match Scaling',l=u'Match S',c=lambda *args:self.py.match_transformations(0,0,1,0))
        pm.button('RM_match_P_button_ui',p='RM_formLayout_ui',ann=u'Match Pivots',l=u'Match P',c=lambda *args:self.py.match_transformations(0,0,0,1))
        

        pm.frameLayout('Sec_Ctrl_frameLayout_ui',p='command_formLayout_ui',bgc=[0.3199999928474426, 0.3199999928474426, 0.3199999928474426],cl=True,cll=True,l=u'Sec Ctrl Build',mh=2)
        pm.formLayout('Sec_Ctrl_formLayout_ui')
        pm.button('Sec_Ctrl_add_button_ui',h=40,l=u'Transmission',c=lambda *args:self.py.sec_ctrl_build('transfer'))
        pm.button('Sec_Ctrl_build_button_ui',ann=u'Create Sec Ctrl',bgc=[0.41999998688697815, 0.75, 0.41999998688697815],l=u'Create',c=lambda *args:self.py.sec_ctrl_build('build'))

        pm.frameLayout('FX_Cloth_frameLayout_ui',p='command_formLayout_ui',bgc=[0.3199999928474426, 0.3199999928474426, 0.3199999928474426],cl=True,cll=True,l=u'FX Cloth Build',mh=2)
        pm.formLayout('FX_Cloth_formLayout_ui')
        pm.button('FX_Cloth_cfx_follow_button_ui',h=40,l=u'CFX Follow',c=lambda *args:self.py.cfx_follow())
        pm.button('FX_Cloth_build_button_ui',ann=u'Create FX Cloth Build',bgc=[0.41999998688697815, 0.75, 0.41999998688697815],l=u'Create',c=lambda *args:self.py.fx_cloth_build())
        pm.popupMenu('FX_Cloth_build_popupMenu_ui',p='FX_Cloth_build_button_ui')
        pm.menuItem('FX_Cloth_build_wrap_exclusive_bind_check_menuItem_ui',l=u'Wrap Exclusive Bind',cb=True)

        pm.frameLayout('FSD_frameLayout_ui',p='command_formLayout_ui',bgc=[0.3199999928474426, 0.3199999928474426, 0.3199999928474426],cl=True,cll=True,l=u'Fix Skin Distortion',mh=2)
        pm.formLayout('FSD_formLayout_ui')
        pm.button('FSD_create_loc_set_button_ui',ann=u'Create Loc',bgc=[0.41999998688697815, 0.5600000023841858, 0.75],l=u'Create',c=lambda *args:self.py.fix_skin_distortion('create'))
        pm.button('FSD_sel_parent_node_button_ui',l=u'Sel',c=lambda *args:self.py.fix_skin_distortion('sel'))
        self.FSD_parent_node_text = pm.textField('FSD_parent_node_textField_ui',ann=u'Load the parent node, if not, use the model itself',ed=False)
        pm.button('FSD_load_parent_node_button_ui',l=u'< Load',c=lambda *args:self.py.fix_skin_distortion('load'))
        pm.button('FSD_fix_VLD_button_ui',h=30,ann=u'Fix Vertex Large-displacement Distortion',bgc=[0.41999998688697815, 0.75, 0.41999998688697815],l=u'Fix',c=lambda *args:self.py.fix_skin_distortion('fix'))
        pm.button('FSD_break_fix_button_ui',ann=u'Break fix node',bgc=[0.75, 0.699999988079071, 0.41999998688697815],l=u'Break Fix',c=lambda *args:self.py.fix_skin_distortion('break'))
        pm.button('FSD_del_fix_button_ui',ann=u'Delete fix node',bgc=[0.75, 0.4300000071525574, 0.41999998688697815],l=u'Del Fix',c=lambda *args:self.py.fix_skin_distortion('del'))
	
        pm.separator('main_separator_4_ui',p='main_formLayout_ui',st=u'in')

        self.main_progressBar = pm.progressBar('main_progressBar_ui',p='main_formLayout_ui',h=10)

        pm.separator('mian_separator_5_ui',p='main_formLayout_ui',st=u'in')
        
        pm.formLayout('sep_formLayout_ui',e=1,af=[['main_formLayout_ui', 'top', 0], ['main_formLayout_ui', 'left', 2], ['main_formLayout_ui', 'right', 2], ['main_formLayout_ui', 'bottom', 0]])
        pm.formLayout('main_formLayout_ui',e=1,af=[['main_separator_1_ui', 'top', 5], ['main_separator_1_ui', 'left', 0], ['main_separator_1_ui', 'right', 0], ['list_formLayout_ui', 'left', 0], ['list_formLayout_ui', 'right', 0], ['main_separator_2_ui', 'left', 0], ['main_separator_2_ui', 'right', 0], ['Rename_formLayout_ui', 'left', 0], ['Rename_formLayout_ui', 'right', 0], ['main_separator_3_ui', 'left', 0], ['main_separator_3_ui', 'right', 0], ['command_formLayout_ui', 'left', 0], ['command_formLayout_ui', 'right', 0], ['main_separator_4_ui', 'left', 0], ['main_separator_4_ui', 'right', 0], ['main_progressBar_ui', 'left', 0], ['main_progressBar_ui', 'right', 0], ['mian_separator_5_ui', 'left', 0], ['mian_separator_5_ui', 'right', 0], ['mian_separator_5_ui', 'bottom', 5]],ac=[['list_formLayout_ui', 'top', 5, 'main_separator_1_ui'], ['list_formLayout_ui', 'bottom', 5, 'main_separator_2_ui'], ['main_separator_2_ui', 'bottom', 5, 'Rename_formLayout_ui'], ['Rename_formLayout_ui', 'bottom', 5, 'main_separator_3_ui'], ['main_separator_3_ui', 'bottom', 5, 'command_formLayout_ui'], ['command_formLayout_ui', 'bottom', 5, 'main_separator_4_ui'], ['main_separator_4_ui', 'bottom', 3, 'main_progressBar_ui'], ['main_progressBar_ui', 'bottom', 3, 'mian_separator_5_ui']])
        pm.formLayout('list_formLayout_ui',e=1,af=[['load_referenced_button_ui', 'top', 0], ['load_referenced_button_ui', 'left', 0], ['load_modified_button_ui', 'top', 0], ['load_modified_button_ui', 'right', 0], ['referenced_textScrollList_ui', 'left', 0], ['modified_textScrollList_ui', 'right', 0], ['referenced_button_formLayout_ui', 'left', 0], ['referenced_button_formLayout_ui', 'bottom', 0], ['modified_button_formLayout_ui', 'right', 0], ['modified_button_formLayout_ui', 'bottom', 0]],ac=[['referenced_textScrollList_ui', 'top', 0, 'load_referenced_button_ui'], ['referenced_textScrollList_ui', 'bottom', 0, 'referenced_button_formLayout_ui'], ['modified_textScrollList_ui', 'top', 0, 'load_modified_button_ui'], ['modified_textScrollList_ui', 'bottom', 0, 'modified_button_formLayout_ui']],ap=[['load_referenced_button_ui', 'right', 1, 50], ['load_modified_button_ui', 'left', 1, 50], ['referenced_textScrollList_ui', 'right', 1, 50], ['modified_textScrollList_ui', 'left', 1, 50], ['referenced_button_formLayout_ui', 'right', 1, 50], ['modified_button_formLayout_ui', 'left', 1, 50]])
        pm.formLayout('referenced_button_formLayout_ui',e=1,af=[['referenced_add_button_ui', 'top', 0], ['referenced_add_button_ui', 'left', 0], ['referenced_add_button_ui', 'bottom', 0], ['referenced_remove_button_ui', 'top', 0], ['referenced_remove_button_ui', 'bottom', 0], ['referenced_up_button_ui', 'top', 0], ['referenced_up_button_ui', 'bottom', 0], ['referenced_down_button_ui', 'top', 0], ['referenced_down_button_ui', 'right', 0], ['referenced_down_button_ui', 'bottom', 0]],ap=[['referenced_add_button_ui', 'right', 1, 25], ['referenced_remove_button_ui', 'left', 1, 25], ['referenced_remove_button_ui', 'right', 1, 50], ['referenced_up_button_ui', 'left', 1, 50], ['referenced_up_button_ui', 'right', 1, 75], ['referenced_down_button_ui', 'left', 1, 75]])
        pm.formLayout('modified_button_formLayout_ui',e=1,af=[['modified_add_button_ui', 'top', 0], ['modified_add_button_ui', 'left', 0], ['modified_add_button_ui', 'bottom', 0], ['modified_remove_button_ui', 'top', 0], ['modified_remove_button_ui', 'bottom', 0], ['modified_up_button_ui', 'top', 0], ['modified_up_button_ui', 'bottom', 0], ['modified_down_button_ui', 'top', 0], ['modified_down_button_ui', 'right', 0], ['modified_down_button_ui', 'bottom', 0]],ap=[['modified_add_button_ui', 'right', 1, 25], ['modified_remove_button_ui', 'left', 1, 25], ['modified_remove_button_ui', 'right', 1, 50], ['modified_up_button_ui', 'left', 1, 50], ['modified_up_button_ui', 'right', 1, 75], ['modified_down_button_ui', 'left', 1, 75]])
        pm.formLayout('Rename_formLayout_ui',e=1,af=[['Rename_del_prefix_button_ui', 'top', 0], ['Rename_del_prefix_button_ui', 'left', 0], ['Rename_del_prefix_button_ui', 'bottom', 0], ['Rename_prefix_textField_ui', 'top', 0], ['Rename_prefix_textField_ui', 'bottom', 0], ['Rename_rename_button_ui', 'top', 0], ['Rename_rename_button_ui', 'bottom', 0], ['Rename_suffix_textField_ui', 'top', 0], ['Rename_suffix_textField_ui', 'bottom', 0], ['Rename_del_suffix_button_ui', 'top', 0], ['Rename_del_suffix_button_ui', 'right', 0], ['Rename_del_suffix_button_ui', 'bottom', 0]],ac=[['Rename_prefix_textField_ui', 'left', 1, 'Rename_del_prefix_button_ui'], ['Rename_prefix_textField_ui', 'right', 1, 'Rename_rename_button_ui'], ['Rename_suffix_textField_ui', 'left', 1, 'Rename_rename_button_ui'], ['Rename_suffix_textField_ui', 'right', 1, 'Rename_del_suffix_button_ui']],ap=[['Rename_rename_button_ui', 'left', 0, 40], ['Rename_rename_button_ui', 'right', 0, 60]])
        pm.formLayout('command_formLayout_ui',e=1,af=[['RM_frameLayout_ui', 'top', 0], ['RM_frameLayout_ui', 'left', 0], ['RM_frameLayout_ui', 'right', 0], ['Sec_Ctrl_frameLayout_ui', 'left', 0], ['Sec_Ctrl_frameLayout_ui', 'right', 0], ['FX_Cloth_frameLayout_ui', 'left', 0], ['FX_Cloth_frameLayout_ui', 'right', 0], ['FSD_frameLayout_ui', 'left', 0], ['FSD_frameLayout_ui', 'right', 0]],ac=[['Sec_Ctrl_frameLayout_ui', 'top', 3, 'RM_frameLayout_ui'], ['FX_Cloth_frameLayout_ui', 'top', 3, 'Sec_Ctrl_frameLayout_ui'], ['FSD_frameLayout_ui', 'top', 3, 'FX_Cloth_frameLayout_ui']])
        pm.formLayout('RM_formLayout_ui',e=1,af=[['RM_radio_formLayout_ui', 'top', 0], ['RM_radio_formLayout_ui', 'left', 0], ['RM_radio_formLayout_ui', 'right', 0], ['RM_separator_1_ui', 'left', 0], ['RM_separator_1_ui', 'right', 0], ['RM_skin_copy_button_ui', 'left', 0], ['RM_skin_copy_button_ui', 'right', 0], ['RM_add_targets_button_ui', 'left', 0], ['RM_copy_constraint_button_ui', 'right', 0], ['RM_separator_2_ui', 'left', 10], ['RM_separator_2_ui', 'right', 10], ['RM_match_button_ui', 'bottom', 0], ['RM_match_T_button_ui', 'left', 0], ['RM_match_R_button_ui', 'left', 0], ['RM_match_S_button_ui', 'right', 0], ['RM_match_P_button_ui', 'right', 0]],ac=[['RM_separator_1_ui', 'top', 5, 'RM_radio_formLayout_ui'], ['RM_skin_copy_button_ui', 'top', 5, 'RM_separator_1_ui'], ['RM_add_targets_button_ui', 'top', 3, 'RM_skin_copy_button_ui'], ['RM_transferUVs_button_ui', 'top', 3, 'RM_skin_copy_button_ui'], ['RM_copy_constraint_button_ui', 'top', 3, 'RM_skin_copy_button_ui'], ['RM_separator_2_ui', 'top', 5, 'RM_copy_constraint_button_ui'], ['RM_match_button_ui', 'top', 5, 'RM_separator_2_ui'], ['RM_match_button_ui', 'left', 3, 'RM_match_R_button_ui'], ['RM_match_button_ui', 'right', 3, 'RM_match_P_button_ui'], ['RM_match_T_button_ui', 'top', 5, 'RM_separator_2_ui'], ['RM_match_R_button_ui', 'top', 3, 'RM_match_T_button_ui'], ['RM_match_S_button_ui', 'top', 5, 'RM_separator_2_ui'], ['RM_match_P_button_ui', 'top', 3, 'RM_match_S_button_ui']],ap=[['RM_add_targets_button_ui', 'right', 1, 40], ['RM_transferUVs_button_ui', 'left', 1, 40], ['RM_transferUVs_button_ui', 'right', 1, 70], ['RM_copy_constraint_button_ui', 'left', 1, 70], ['RM_match_T_button_ui', 'right', 0, 25], ['RM_match_R_button_ui', 'right', 0, 25], ['RM_match_S_button_ui', 'left', 0, 75], ['RM_match_P_button_ui', 'left', 0, 75]])
        pm.formLayout('RM_radio_formLayout_ui',e=1,af=[['RM_one_to_one_radioButton_ui', 'top', 0], ['RM_one_to_one_radioButton_ui', 'bottom', 0], ['RM_all_to_all_radioButton_ui', 'top', 0], ['RM_all_to_all_radioButton_ui', 'bottom', 0]],ap=[['RM_one_to_one_radioButton_ui', 'left', 0, 15], ['RM_all_to_all_radioButton_ui', 'right', 0, 85]])
        pm.formLayout('Sec_Ctrl_formLayout_ui',e=1,af=[['Sec_Ctrl_add_button_ui', 'top', 0], ['Sec_Ctrl_add_button_ui', 'left', 0], ['Sec_Ctrl_add_button_ui', 'bottom', 0], ['Sec_Ctrl_build_button_ui', 'top', 0], ['Sec_Ctrl_build_button_ui', 'right', 0], ['Sec_Ctrl_build_button_ui', 'bottom', 0]],ap=[['Sec_Ctrl_add_button_ui', 'right', 1, 40], ['Sec_Ctrl_build_button_ui', 'left', 1, 40]])
        pm.formLayout('FX_Cloth_formLayout_ui',e=1,af=[['FX_Cloth_cfx_follow_button_ui', 'top', 0], ['FX_Cloth_cfx_follow_button_ui', 'left', 0], ['FX_Cloth_cfx_follow_button_ui', 'bottom', 0], ['FX_Cloth_build_button_ui', 'top', 0], ['FX_Cloth_build_button_ui', 'right', 0], ['FX_Cloth_build_button_ui', 'bottom', 0]],ap=[['FX_Cloth_cfx_follow_button_ui', 'right', 1, 40], ['FX_Cloth_build_button_ui', 'left', 1, 40]])
        pm.formLayout('FSD_formLayout_ui',e=1,af=[['FSD_create_loc_set_button_ui', 'top', 0], ['FSD_create_loc_set_button_ui', 'left', 0], ['FSD_sel_parent_node_button_ui', 'top', 0], ['FSD_parent_node_textField_ui', 'top', 0], ['FSD_load_parent_node_button_ui', 'top', 0], ['FSD_load_parent_node_button_ui', 'right', 0], ['FSD_fix_VLD_button_ui', 'left', 0], ['FSD_fix_VLD_button_ui', 'right', 0], ['FSD_break_fix_button_ui', 'left', 0], ['FSD_del_fix_button_ui', 'right', 0]],ac=[['FSD_parent_node_textField_ui', 'left', 1, 'FSD_sel_parent_node_button_ui'], ['FSD_parent_node_textField_ui', 'right', 1, 'FSD_load_parent_node_button_ui'], ['FSD_fix_VLD_button_ui', 'top', 2, 'FSD_load_parent_node_button_ui'], ['FSD_break_fix_button_ui', 'top', 2, 'FSD_fix_VLD_button_ui'], ['FSD_del_fix_button_ui', 'top', 2, 'FSD_fix_VLD_button_ui']],ap=[['FSD_create_loc_set_button_ui', 'right', 1, 15], ['FSD_sel_parent_node_button_ui', 'left', 1, 15], ['FSD_load_parent_node_button_ui', 'left', 0, 85], ['FSD_break_fix_button_ui', 'right', 1, 50], ['FSD_del_fix_button_ui', 'left', 1, 50]])
        
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
            flatten_check = pm.menuItem('ref_list_flatten_menuItem_ui', q=True, cb=True)
        elif button == 'mod':
            stuff = self.ui.modified_list
            flatten_check = pm.menuItem('mod_list_flatten_menuItem_ui', q=True, cb=True)
        sel = cmds.ls(sl=True,fl=flatten_check)
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
        if project == 'ref':
            stuff = self.ui.referenced_list
            unique_check = pm.menuItem('ref_list_on_unique_menuItem_ui', q=True, cb=True)
            flatten_check = pm.menuItem('ref_list_flatten_menuItem_ui', q=True, cb=True)
        elif project == 'mod':
            stuff = self.ui.modified_list
            unique_check = pm.menuItem('mod_list_on_unique_menuItem_ui', q=True, cb=True)
            flatten_check = pm.menuItem('mod_list_flatten_menuItem_ui', q=True, cb=True)
        sel = cmds.ls(sl=True,fl=flatten_check)
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
    
    # Rename Item
    def rename_item(self,button):
        self.print_command_out('Rename Item')
        modified_models = self.ui.modified_list.getAllItems()
        rename_check = pm.menuItem('Raname_Ignore_Referenced_menuItem_ui',q=True,cb=True)
        prefix = self.ui.prefix_text.getText()
        suffix = self.ui.suffix_text.getText()
        if rename_check:
            referenced_models = modified_models
        else:
            referenced_models = self.ui.referenced_list.getAllItems()
        for i, (modified_model,referenced_model) in enumerate(list(zip(modified_models,referenced_models))):
            index = self.ui.modified_list.setSelectItem(modified_model).getSelectIndexedItem()
            if button == 'rename':
                renamed = pm.rename(modified_model,prefix + referenced_model.split('|')[-1] + suffix)
            elif button == 'del_prefix':
                renamed = pm.rename(modified_model,modified_model.split('|')[-1].split('_',1)[-1])
            elif button == 'del_suffix':
                renamed = pm.rename(modified_model,modified_model.split('|')[-1].rsplit('_',1)[0])
            self.ui.modified_list.removeItem(modified_model)
            self.ui.modified_list.appendPosition([index[0],renamed])
            self.print_command_out('已将 {} 重命名为 {}'.format(modified_model,renamed),outWarning=False,outSep=False)
            self.progressBar_set(i+1,len(modified_models))
        pm.inViewMessage(amg='Rename Item: <hl style="color:#88FF88;">Final</hl>',pos='midCenterTop',fade=False,dk=True)
    
    # Sec Ctrl Build
    def sec_ctrl_build(self,button):
        stuff = self.ui.modified_list.getAllItems()
        sec_ctrl_build.sec_ctrl_build().main(button,stuff)

    # FX Cloth Build
    def fx_cloth_build(self):
        stuff = self.ui.modified_list.getAllItems()
        cloth_wrap_exclusive_bind_check = pm.menuItem('FX_Cloth_build_wrap_exclusive_bind_check_menuItem_ui',q=True,cb=True)
        fx_cloth_build.CreateCloth().CreateClothNode(stuff,cloth_wrap_exclusive_bind_check)
    
    # CFX Follow
    def cfx_follow(self,*args):
        self.print_command_out('CFX Follow')
        modified_models = self.ui.modified_list.getAllItems()
        referenced_models = [modified_models[:-4] for modified_model in modified_models if modified_model.endswith('_cfx')]
        for i, (modified_model,referenced_model) in enumerate(list(zip(modified_models,referenced_models))):
            bs_node = pm.listHistory(modified_model, pdo=1, type='blendShape')[0]
            if bs_node:
                while not pm.objExists('lw_cfx_wrapBase_Grp'):
                    pm.group(em=True,n='lw_cfx_wrapBase_Grp')
                    pm.setAttr('lw_cfx_wrapBase_Grp.visibility',0)
                    try:
                        pm.parent('lw_cfx_wrapBase_Grp','lw_cfx')
                    except:
                        pass
                pm.select(modified_model,referenced_model,r=True)
                pm.mel.eval(self.WrapMel)
                pm.parent('{0}Base'.format(referenced_model),'lw_cfx_wrapBase_Grp')
                for dfm in pm.mel.eval('findRelatedDeformer("{0}");'.format(modified_model)):
                    if pm.nodeType(dfm) == 'wrap':
                        pm.setAttr('{}.exclusiveBind'.format(dfm),1)
                        pm.rename(dfm,'{0}_Wrap'.format(modified_model))
                        break
                self.print_command_out('已将 {} 包裹与 {}'.format(modified_model,referenced_model),outWarning=False,outSep=False)
            else:
                ref_skinNode = pm.listHistory(referenced_model, pdo=1, type='skinCluster')
                ref_skinJnts = pm.skinCluster(ref_skinNode, q=True, inf=True)
                pm.skinCluster(modified_model, ref_skinJnts, tsb=True)
                pm.select(referenced_model,modified_model,r=True)
                pm.mel.eval(self.CopySkinWeightsMel)
                self.print_command_out('已将 {} 的权重复制到 {}'.format(referenced_model,modified_model),outWarning=False,outSep=False)
            self.progressBar_set(i+1,len(modified_models))
        pm.select(cl=True)
        pm.inViewMessage(amg='CFX Follow: <hl style="color:#88FF88;">Final</hl>',pos='midCenterTop',fade=False,dk=True)

    # Skin + Copy Weight
    def skin_copy_weight(self,*args):
        self.print_command_out('Skin + Copy Weight')
        modified_models = self.ui.modified_list.getAllItems()
        referenced_models = self.ui.referenced_list.getAllItems()
        radio = pm.radioCollection(self.ui.radio_collection,q=True,sl=True)
        for i, modified_model in enumerate(modified_models):
            if radio == 'RM_one_to_one_radioButton_ui':
                if i+1 > len(referenced_models):
                    break
                referenced_model = referenced_models[i]
                ref_skinNode = pm.listHistory(referenced_model, pdo=1, type='skinCluster')
                ref_skinJnts = pm.skinCluster(ref_skinNode, q=True, inf=True)
            elif radio == 'RM_all_to_all_radioButton_ui':
                referenced_model = referenced_models
                ref_skinNodes = pm.listHistory(referenced_model, pdo=1, type='skinCluster')
                ref_skinJnts = []
                for ref_skinNode in ref_skinNodes:
                    ref_skinJnt = pm.skinCluster(ref_skinNode, q=True, inf=True)
                    ref_skinJnts.extend(ref_skinJnt)
            mod_skinNode = pm.listHistory(modified_model, pdo=1, type='skinCluster')
            if not mod_skinNode:
                mod_skinNode = pm.skinCluster(modified_model, ref_skinJnts, tsb=True)
            else:
                mod_skinJnts = pm.skinCluster(mod_skinNode, q=True, inf=True)
                add_influence_jnts = [add_influence_jnt for add_influence_jnt in ref_skinJnts if add_influence_jnt not in mod_skinJnts]
                pm.skinCluster(mod_skinNode, e=True, addInfluence=add_influence_jnts, wt=0)
            pm.select(referenced_model, modified_model,r=True)
            pm.mel.eval(self.CopySkinWeightsMel)
            if pm.menuItem('remove_unused_influences_menuItem_ui',q=True,cb=True):
                pm.skinCluster(mod_skinNode, e=True, rui=True)
            self.print_command_out('{} > {}'.format(referenced_model,modified_model),outWarning=False,outSep=False)
            self.progressBar_set(i+1,len(modified_models))
        pm.select(cl=True)
        pm.inViewMessage(amg='Skin + Copy Weight: <hl style="color:#88FF88;">Final</hl>',pos='midCenterTop',fade=False,dk=True)

    # Add BlendShape Target
    def add_targets(self,*args):
        self.print_command_out('Add BlendShape Target')
        modified_models = self.ui.modified_list.getAllItems()
        referenced_models = self.ui.referenced_list.getAllItems()
        radio = pm.radioCollection(self.ui.radio_collection,q=True,sl=True)
        if len(referenced_models) == 0 or len(modified_models) == 0:
            pm.warning('请载入模型')
            return
        for i, modified_model in enumerate(modified_models):
            bs_node = pm.listHistory(modified_model, pdo=1, type='blendShape')[0]
            if not bs_node:
                self.print_command_out('{} 未查询到 BlendShape 节点，已跳过'.format(modified_model),outWarning=True,outSep=False)
                continue
            bs_num = pm.blendShape(bs_node,q=True,wc=True)
            if radio == 'RM_one_to_one_radioButton_ui':
                if i+1 > len(referenced_models):
                    break
                pm.blendShape(bs_node,e=True, t=(modified_model, bs_num, referenced_models[i], 1.0))
                self.print_command_out('{} > {} (target index: {})'.format(referenced_models[i],modified_model,bs_num),outWarning=False,outSep=False)
            elif radio == 'RM_all_to_all_radioButton_ui':
                for referenced_model in referenced_models:
                    pm.blendShape(bs_node,e=True, t=(modified_model, bs_num, referenced_model, 1.0))
                    self.print_command_out('{} > {} (target index: {})'.format(referenced_model,modified_model,bs_num),outWarning=False,outSep=False)
                    bs_num += 1
                self.print_command_out('',outWarning=False,outSep=True)
            self.progressBar_set(i+1,len(modified_models))
        pm.inViewMessage(amg='Add BlendShape Target: <hl style="color:#88FF88;">Final</hl>',pos='midCenterTop',fade=False,dk=True)
                    
    # transferUVs
    def transferUVs(self,UVsampleSpace=5):
        self.print_command_out('Transfer UVs')
        modified_models = self.ui.modified_list.getAllItems()
        referenced_models = self.ui.referenced_list.getAllItems()
        radio = pm.radioCollection(self.ui.radio_collection,q=True,sl=True)
        UVsampleSpace_radio_ditc = {
            'RM_transferUVs_world_ui':0,
            'RM_transferUVs_local_ui':1,
            'RM_transferUVs_component_ui':4,
            'RM_transferUVs_topology_ui':5}
        for k, i in UVsampleSpace_radio_ditc.items():
            if pm.menuItem(k, q=True, rb=True):
                UVsampleSpace = i
        for i, modified_model in enumerate(modified_models):
            if radio == 'RM_one_to_one_radioButton_ui':
                if i+1 > len(referenced_models):
                    return
                referenced_model = referenced_models[i]
            elif radio == 'RM_all_to_all_radioButton_ui':
                if len(referenced_models) != 1:
                    self.print_command_out('多对多模式下，请确保参考模型列表中仅有一个模型',outWarning=True,outSep=False)
                    return
                referenced_model = referenced_models[0]

            modified_shapes = pm.listRelatives(modified_model,s=True,type='mesh')
            if not modified_shapes:
                self.print_command_out('{} 未查询到 Mesh 节点，已跳过'.format(modified_model),outWarning=True,outSep=False)
                continue
            orgShapes = []
            for modified_shape in modified_shapes:
                if modified_shape.intermediateObject.get():
                    if pm.connectionInfo(modified_shape+'.worldMesh[0]', isSource=True) and not pm.connectionInfo(modified_shape+'.inMesh', isDestination=True):
                        orgShapes.append(modified_shape)
                    else:
                        self.print_command_out('{} 存在异常 ShapeOrig Mash 节点： {} ，请手动检查'.format(modified_model,modified_shape),outWarning=True,outSep=False)
                else:
                    shape = modified_shape   
            if orgShapes:
                for orgShape in orgShapes:
                    pm.transferAttributes(referenced_model,orgShape,transferUVs=2,transferColors=2,sampleSpace=UVsampleSpace,ihs=True)
                    pm.setAttr(orgShape+'.intermediateObject',False)
                    pm.delete(orgShape, constructionHistory=True)
                    pm.setAttr(orgShape+'.intermediateObject',True)
                self.print_command_out('{} > {} - {}'.format(referenced_model,modified_model,'Orig'),outWarning=False,outSep=False)
                self.print_command_out('',outWarning=False,outSep=True)
            else:
                pm.transferAttributes(referenced_model,shape,transferUVs=2,transferColors=2,sampleSpace=UVsampleSpace,ihs=True)
                pm.delete(shape, constructionHistory=True)
                self.print_command_out('{} > {} - {}'.format(referenced_model,modified_model,'Shape'),outWarning=False,outSep=False)
                self.print_command_out('',outWarning=False,outSep=True)
                #self.print_command_out('{} 未查询到有效 Org Mesh 节点，已跳过'.format(modified_model),outWarning=True,outSep=False)
            self.progressBar_set(i+1,len(modified_models))
        pm.inViewMessage(amg='Transfer UVs: <hl style="color:#88FF88;">Final</hl>',pos='midCenterTop',fade=False,dk=True)
                
    # Copy Constraint
    def copy_constraint(self,*args):
        self.print_command_out('Copy Constraint')
        modified_models = self.ui.modified_list.getAllItems()
        referenced_models = self.ui.referenced_list.getAllItems()
        radio = pm.radioCollection(self.ui.radio_collection,q=True,sl=True)
        for i, modified_model in enumerate(modified_models):
            if radio == 'RM_one_to_one_radioButton_ui':
                if i+1 > len(referenced_models):
                    break
                referenced_model = referenced_models[i]
            elif radio == 'RM_all_to_all_radioButton_ui':
                referenced_model = referenced_models
            getConnections = pm.listConnections(referenced_model,type='constraint')
            if not getConnections:
                self.print_command_out('{} 未查询到约束节点，已跳过'.format(referenced_model),outWarning=True,outSep=False)
                continue
            singleConnections = list(set(getConnections))
            connetions_types = [connetions_type.type() for connetions_type in singleConnections] 
            if set(['parentConstraint','pointConstraint']).issubset(set(connetions_types)) or set(['parentConstraint','orientConstraint']).issubset(set(connetions_types)):
                self.print_command_out('{} 同时存在 Parent + Point/Orient Constraint'.format(referenced_model),outWarning=True,outSep=False)
                break
            for constraint in singleConnections:
                if constraint.type() == 'parentConstraint':
                    getTargetList = pm.parentConstraint(constraint,q=True,tl=True)
                    pm.parentConstraint(getTargetList,modified_model,mo=True)
                elif constraint.type() == 'pointConstraint':
                    getTargetList = pm.pointConstraint(constraint,q=True,tl=True)
                    pm.pointConstraint(getTargetList,modified_model,mo=True)
                elif constraint.type() == 'orientConstraint':
                    getTargetList = pm.orientConstraint(constraint,q=True,tl=True)
                elif constraint.type() == 'scaleConstraint':
                    getTargetList = pm.scaleConstraint(constraint,q=True,tl=True)
                    pm.scaleConstraint(getTargetList,modified_model,mo=True)
            self.print_command_out('{} > {}'.format(referenced_model,modified_model),outWarning=False,outSep=False)
            self.progressBar_set(i+1,len(modified_models))
        pm.inViewMessage(amg='Copy Constraint: <hl style="color:#88FF88;">Final</hl>',pos='midCenterTop',fade=False,dk=True)

    # Match Transformations
    def match_transformations(self,T, R, S, P):
        self.print_command_out('Match Transformations')
        modified_models = self.ui.modified_list.getAllItems()
        referenced_models = self.ui.referenced_list.getAllItems()
        for modified_model, referenced_model in zip(modified_models, referenced_models):
            pm.matchTransform(modified_model, referenced_model, pos=T, rot=R, scl=S,piv=P)
            self.print_command_out('已将 {} 对齐于 {}'.format(modified_model, referenced_model), outWarning=False, outSep=False)
        pm.select(cl=True)

    # Fix Skin Distortion
    def fix_skin_distortion(self,button):
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
            pm.textField(self.ui.FSD_parent_node_text,e=True,tx='VLD_Loc')
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
                pm.textField(self.ui.FSD_parent_node_text,e=True,tx=sel[0])
            else:
                pm.textField(self.ui.FSD_parent_node_text,e=True,tx='')
            return
            
        FSD_parent_node = pm.textField(self.ui.FSD_parent_node_text,q=True,tx=True)
        
        if button == 'sel':
            if FSD_parent_node:
                pm.select(FSD_parent_node,r=True)
            return
        
        self.print_command_out('Fix Skin Distortion')
        modified_models = self.ui.modified_list.getAllItems()
        jnt_list = []
        for i, modified_model in enumerate(modified_models):
            skin = pm.mel.eval('findRelatedSkinCluster("{}")'.format(modified_model))
            if skin:
                jnt_list = pm.skinCluster(skin,q=True,inf=True)
            else:
                self.print_command_out('{} 未查询到蒙皮节点，已跳过'.format(modified_model),outWarning=True,outSep=False)
                continue
            multMat_name = modified_model
            if FSD_parent_node:
                multMat_name = FSD_parent_node
            if button == 'fix':
                if not jnt_list:
                    self.print_command_out('{} 未查询到骨骼节点或已创建修复，已跳过'.format(modified_model),outWarning=True,outSep=False)
                    continue
                for jnt in jnt_list:
                    multMat = '{}_multMatrix_{}'.format(multMat_name,jnt)
                    while not pm.objExists(multMat):
                        multMat = pm.createNode('multMatrix',n=multMat)
                        pm.connectAttr(jnt+'.worldMatrix[0]',multMat+'.matrixIn[0]',f=True)
                        pm.connectAttr(multMat_name+'.worldInverseMatrix[0]',multMat+'.matrixIn[1]',f=True)
                    conn_nodes = pm.listConnections(jnt+'.worldMatrix[0]',s=False,p=True,t='skinCluster')
                    conn_attrs = [conn_attr for conn_attr in conn_nodes if conn_attr.node() == skin]
                    if conn_attrs:
                        for conn_li in conn_attrs:
                            pm.connectAttr(multMat+'.matrixSum',conn_li,f=True)
                self.print_command_out('{} 已创建修复节点并连接'.format(modified_model),outWarning=False,outSep=False)
                if i == len(modified_models)-1:
                    pm.inViewMessage(amg='Fix Skin Distortion: <hl style="color:#88FF88;">Fix Fianl</hl>',pos='midCenterTop',fade=False,dk=True)
            else:
                multMats = pm.listConnections(skin+'.matrix',d=False,t='multMatrix')
                if not multMats and button == 'break':
                    self.print_command_out('{} 未查询到修复节点，已跳过'.format(modified_model),outWarning=True,outSep=False)
                    continue
                for multMat in multMats:
                    jnt = pm.listConnections(multMat+'.matrixIn[0]',d=False,p=True,t='joint')
                    conn_nodes = pm.listConnections(multMat+'.matrixSum',s=False,p=True,t='skinCluster')
                    conn_attrs = [conn_attr for conn_attr in conn_nodes if conn_attr.node() == skin]
                    for conn_li in conn_attrs:
                        pm.connectAttr(jnt[0],conn_li,f=True)
                if button == 'break':
                    self.print_command_out('{} 已断开修复节点连接'.format(modified_model),outWarning=False,outSep=False)
                    if i == len(modified_models)-1:
                        pm.inViewMessage(amg='Fix Skin Distortion: <hl style="color:#FFCF49;">Break Fianl</hl>',pos='midCenterTop',fade=False,dk=True)
                elif button == 'del':
                    jnt_list = pm.skinCluster(skin,q=True,inf=True)
                    for jnt in jnt_list:
                        multMats = pm.listConnections(jnt+'.worldMatrix[0]',s=False,t='multMatrix')
                        for multMat in multMats:
                            conn_nodes = pm.listConnections(multMat+'.matrixSum',s=False,p=True)
                            if not conn_nodes:
                                pm.delete(multMat)
                    self.print_command_out('{} 已删除修复节点'.format(modified_model),outWarning=False,outSep=False)
                    if i == len(modified_models)-1:
                        pm.inViewMessage(amg='Fix Skin Distortion: <hl style="color:#FF6666;">Delete Fianl</hl>',pos='midCenterTop',fade=False,dk=True)
            self.progressBar_set(i+1,len(modified_models))
                    
if __name__ == '__main__':
    MainPY().ui.create_window()