# -*- coding: utf-8 -*-

import os
import shutil
from datetime import datetime

try:
    from PySide6 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui

from .Pipeline import file_operations as file_ops

from .Pipeline.pipelineUtils import (
    open_folder_in_explorer,
    open_file_in_explorer
)

import maya.cmds as cmds

def _show_info_inview(title=u"Finished", color='yellow'):
    cmds.inViewMessage(amg=u"<hl style='color:{};'>{}</hl>".format(color,title),pos='midCenterBot',fade=False,dk=True)


def add_menu_label(menu, text):
    widget = QtWidgets.QWidget()
    layout = QtWidgets.QHBoxLayout(widget)

    label = QtWidgets.QLabel(text)
    label.setProperty("menuHeader", "true")
    #label.setStyleSheet("color: yellow;")

    layout.addWidget(label)
    layout.setContentsMargins(20, 2, 5, 2)
    widget.setLayout(layout)

    label_action = QtWidgets.QWidgetAction(menu)
    label_action.setDefaultWidget(widget)
    menu.addAction(label_action)


class PipelineContext(object):

    def __init__(self, main_window):
        self.ui = main_window

    @property
    def pmgr(self):
        return self.ui.pmgr

    @property
    def asset_type(self):
        return self.ui.current_asset_type

    @property
    def asset(self):
        return self.ui.selected_asset

    @property
    def task(self):
        return self.ui.selected_task

    def validate_asset(self):
        return bool(self.pmgr and self.asset_type)

    def validate_task(self):
        return bool(
            self.pmgr and
            self.asset_type and
            self.asset and
            self.task
        )


class PathService(PipelineContext):

    def asset_dir(self, asset_name=None):
        asset_name = asset_name or self.asset
        return self.pmgr.get_asset_dir(
            self.asset_type,
            asset_name
        )

    def task_dir(self, task_name=None):
        task_name = task_name or self.task
        return os.path.join(
            self.asset_dir(),
            'components',
            task_name
        )

    def workshop_dir(self):
        return os.path.join(
            self.task_dir(),
            'workshop'
        )

    def version_path(self, version_name):
        return os.path.join(
            self.workshop_dir(),
            version_name
        )

    def open_asset_path(self, asset_name):
        if not self.validate_asset():
            self.ui.show_warning(
                u'错误',
                u'请先选择资产类型'
            )
            return

        path = self.asset_dir(asset_name)

        if os.path.exists(path):
            open_folder_in_explorer(path.replace("/", "\\"))
        else:
            self.ui.show_warning(
                u'错误',
                u'资产路径不存在:\n{}'.format(path)
            )

    def open_task_path(self, task_name):
        if not self.validate_task():
            self.ui.show_warning(
                u'错误',
                u'请先选择资产和任务'
            )
            return

        path = os.path.join(
            self.asset_dir(),
            'components',
            task_name
        )

        if os.path.exists(path):
            open_folder_in_explorer(path.replace("/", "\\"))
        else:
            self.ui.show_warning(
                u'错误',
                u'任务路径不存在:\n{}'.format(path)
            )

    def open_version_path(self, version_name):
        if not self.validate_task():
            self.ui.show_warning(
                u'错误',
                u'请先选择资产和任务'
            )
            return

        path = self.version_path(version_name)

        if os.path.exists(path):
            open_file_in_explorer(path.replace("/", "\\"))
        else:
            self.ui.show_warning(
                u'错误',
                u'版本文件不存在:\n{}'.format(path)
            )

    def get_file_info(self, version_filename):
        file_path = self.version_path(version_filename)

        if not os.path.exists(file_path):
            return ""

        try:
            size_bytes = os.path.getsize(file_path)
            mod_time = os.path.getmtime(file_path)

            return u"\n\n文件大小: {:.1f} KB\n最后修改: {}".format(
                size_bytes / 1024.0,
                datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M')
            )
        except:
            return u"\n\n(无法获取文件信息)"


class VersionService(PathService):

    def refresh_version_list(self):
        if not self.validate_task():
            return

        versions = self.pmgr.get_workshop_versions(
            self.asset_type,
            self.asset,
            self.task
        ) or []

        version_list = self.ui.version_list
        version_list.clear()

        for version in versions:
            version_list.addItem(version)

    def backup_to_deleted_folder(self, file_path):
        if not os.path.exists(file_path):
            return False

        deleted_dir = os.path.join(
            self.task_dir(),
            "deleted"
        )

        if not os.path.exists(deleted_dir):
            os.makedirs(deleted_dir)

        filename = os.path.basename(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        backup_name = "{}_{}".format(timestamp, filename)
        backup_path = os.path.join(
            deleted_dir,
            backup_name
        )

        shutil.copy2(file_path, backup_path)
        return True

    def is_master_version(self, version_filename):
        try:
            master_path = self.pmgr.get_master_file(
                self.asset_type,
                self.asset,
                self.task
            )

            if not master_path:
                return False

            master_name = os.path.basename(master_path)
            return master_name == version_filename
        except:
            return False

    def delete_selected_version(self, version_filename):
        if not self.validate_task():
            self.ui.show_warning(
                u'错误',
                u'请先选择资产和任务'
            )
            return False

        file_path = self.version_path(version_filename)

        if not os.path.exists(file_path):
            self.ui.show_warning(
                u'错误',
                u'文件不存在:\n{}'.format(file_path)
            )
            return False

        if self.is_master_version(version_filename):
            reply = QtWidgets.QMessageBox.question(
                self.ui,
                u'警告',
                u'该版本是 Master，删除后 Master 将失效。\n确定继续？',
                QtWidgets.QMessageBox.Yes |
                QtWidgets.QMessageBox.No
            )

            if reply != QtWidgets.QMessageBox.Yes:
                return False
        else:
            reply = QtWidgets.QMessageBox.question(
                self.ui,
                u'确认删除',
                u'确定删除版本？\n{}'.format(version_filename),
                QtWidgets.QMessageBox.Yes |
                QtWidgets.QMessageBox.No
            )

            if reply != QtWidgets.QMessageBox.Yes:
                return False

        try:
            self.backup_to_deleted_folder(file_path)
        except Exception as e:
            print(u"备份删除文件失败: {}".format(e))

        try:
            os.remove(file_path)
        except Exception as e:
            self.ui.show_critical(
                u'删除失败',
                str(e)
            )
            return False

        # Remove stored notes metadata for this version.
        version_filename = os.path.basename(file_path)
        try:
            self.pmgr.delete_note_entry(self.asset_type, self.asset, self.task, version_filename)
        except Exception:
            pass

        self.refresh_version_list()

        if hasattr(self.ui, "show_info"):
            try:
                self.ui.show_info(u'文件删除成功',
                                  u"已删除 {}".format(version_filename)
                                  )
            except:
                pass

        return True

class FileOperationService(PathService):

    def open_version(self, version_name):
        path = self.version_path(version_name)
        return file_ops.open_file(path)

    def import_version(self, version_name, namespace=None):
        path = self.version_path(version_name)
        return file_ops.import_file(
            path,
            namespace=namespace
        )

    def reference_version(self, version_name, namespace=None):
        path = self.version_path(version_name)
        # 若未指定命名空间，则使用文件名前缀（与原有行为一致）
        if namespace is None:
            namespace = version_name.split('.')[0]
        return file_ops.reference_file(
            path,
            namespace=namespace,
            group_locator=True
        )

    def open_master(self):
        return file_ops.open_master_file(
            self.pmgr,
            self.asset_type,
            self.asset,
            self.task
        )

    def import_master(self, namespace=None):
        return file_ops.import_master_file(
            self.pmgr,
            self.asset_type,
            self.asset,
            self.task,
            namespace=namespace
        )

    def reference_master(self, namespace=None):
        """
        引用 Master。
        若 namespace 为 None（默认），则无命名空间（使用 ":" 合并到根）。
        若指定 namespace，则使用该命名空间。
        """
        mf = self.pmgr.get_master_file(
            self.asset_type,
            self.asset,
            self.task
        )

        if not mf or not os.path.exists(mf):
            raise FileNotFoundError("Master file not found")

        # 默认无命名空间：使用 ":"（表示根命名空间）
        if namespace is None:
            # 使用 ":" 并设置 group_locator=True，但不合并命名空间merge_namespaces
            return file_ops.reference_file(
                mf,
                namespace=":",
                group_locator=True
            )
        else:
            return file_ops.reference_file(
                mf,
                namespace=namespace,
                group_locator=True
            )

    def set_master(self, version_name):
        return file_ops.set_master_from_version(
            self.pmgr, self.asset_type, self.asset, self.task, version_name
        )

    def write_note_info(self, task_name, version_filename, info="", workshop=True):
        task_dir = os.path.join(
            self.asset_dir(),
            'components',
            task_name
        )
        self.pmgr.write_note_info(task_dir, version_filename, info, workshop)


class VersionContextMenu(PipelineContext):

    def __init__(self, main_window):
        super(VersionContextMenu, self).__init__(main_window)

        self.path_service = PathService(main_window)
        self.version_service = VersionService(main_window)
        self.file_ops = FileOperationService(main_window)

    def show_asset_menu(self, position):
        list_widget = self.ui.asset_list
        item = list_widget.itemAt(position)

        if not item:
            return

        asset_name = item.text()

        menu = QtWidgets.QMenu(list_widget)

        open_path_action = menu.addAction(u"📂 打开资产目录 ")

        def _open():
            self.path_service.open_asset_path(asset_name)

        open_path_action.triggered.connect(_open)
        menu.exec_(list_widget.mapToGlobal(position))

    def show_task_menu(self, position):
        list_widget = self.ui.task_list
        item = list_widget.itemAt(position)

        if not item:
            return

        task_name = item.text()

        menu = QtWidgets.QMenu(list_widget)

        open_path_action = menu.addAction(u"📂 打开任务目录 ")
        menu.addSeparator()
        open_master_action = menu.addAction(u"打开 Master")
        import_master_action = menu.addAction(u"导入 Master")
        reference_master_action = menu.addAction(u"引用 Master")

        def safe_run(func):
            try:
                func()
            except Exception as e:
                QtWidgets.QMessageBox.warning(
                    self.ui,
                    u"错误",
                    str(e)
                )

        def _open():
            self.path_service.open_task_path(task_name)

        def _open_master():
            safe_run(lambda: self.file_ops.open_master())
            _show_info_inview('Master opened', 'yellow')

        def _import_master():
            safe_run(lambda: self.file_ops.import_master())
            _show_info_inview('Master imported', 'yellow')

        def _reference_master():
            # 引用 Master 无命名空间（默认 None → 无命名空间）
            safe_run(lambda: self.file_ops.reference_master())
            _show_info_inview('Master referenced', 'yellow')

        open_path_action.triggered.connect(_open)
        open_master_action.triggered.connect(_open_master)
        import_master_action.triggered.connect(_import_master)
        reference_master_action.triggered.connect(_reference_master)
        menu.exec_(list_widget.mapToGlobal(position))

    def show_version_menu(self, position):
        list_widget = self.ui.version_list
        item = list_widget.itemAt(position)

        if not item:
            return

        version_name = item.text()
        menu = QtWidgets.QMenu(list_widget)

        add_menu_label(menu, u'📋 版本信息: {} '.format(version_name))
        menu.addSeparator()
        locate_action = menu.addAction(u"📂 打开版本目录 ")
        menu.addSeparator()
        open_action = menu.addAction(u" 打开")
        import_action = menu.addAction(u" 导入")
        reference_action = menu.addAction(u" 引用")
        menu.addSeparator()
        set_master_action = menu.addAction(u"⚙ Set Master ")
        menu.addSeparator()
        #add_menu_label(menu, "⭐ fbx:")

        #set_fbx_action = menu.addAction(u'⚙ 设置FBX导出对象')
        #menu.addSeparator()
        #fbx_menu = menu.addMenu(u"Export FBX")
        #export_fbx_action = fbx_menu.addAction(u"📤 导出 FBX")
        #export_fbx_ue_action = fbx_menu.addAction(u'📤 导出FBX to UE')
        #menu.addSeparator()
        #add_menu_label(menu, u"  删除:")
        delete_action = menu.addAction(u"🗑️ 删除当前选择 ")

        def safe_run(func):
            try:
                func()
            except Exception as e:
                QtWidgets.QMessageBox.warning(
                    self.ui,
                    u"错误",
                    str(e)
                )

        def _open():
            safe_run(lambda: self.file_ops.open_version(version_name))
            _show_info_inview('The selected version has been opened', 'yellow')

        def _import():
            safe_run(lambda: self.file_ops.import_version(version_name))
            _show_info_inview('The selected version has been imported', 'yellow')

        def _reference():
            ns = version_name.split('.')[0]
            safe_run(
                lambda: self.file_ops.reference_version(version_name, namespace=ns)
            )
            _show_info_inview('The selected version has been reference', 'yellow')

        def _locate():
            safe_run(lambda: self.path_service.open_version_path(version_name))

        def _set_master():
            safe_run(lambda: self.file_ops.set_master(version_name))
            if hasattr(self.ui, "show_info"):
                self.ui.show_info(u'设置Master成功', u'{} 设置Master完成'.format(version_name))

        def _export(to_ue=False):
            safe_run(lambda: self.exporter.export_fbx_for_version(version_name, to_ue))

        def _delete():
            ok = self.version_service.delete_selected_version(version_name)
            if ok and hasattr(self.ui, "refresh_all"):
                self.ui.refresh_all()

        open_action.triggered.connect(_open)
        import_action.triggered.connect(_import)
        reference_action.triggered.connect(_reference)
        locate_action.triggered.connect(_locate)
        set_master_action.triggered.connect(_set_master)
        delete_action.triggered.connect(_delete)

        menu.exec_(list_widget.mapToGlobal(position))


def show_asset_context_menu(main_window, position):
    ctx = VersionContextMenu(main_window)
    ctx.show_asset_menu(position)


def show_task_context_menu(main_window, position):
    ctx = VersionContextMenu(main_window)
    ctx.show_task_menu(position)


def show_version_context_menu(main_window, position):
    ctx = VersionContextMenu(main_window)
    ctx.show_version_menu(position)


__all__ = [
    'show_asset_context_menu',
    'show_task_context_menu',
    'show_version_context_menu'
]
