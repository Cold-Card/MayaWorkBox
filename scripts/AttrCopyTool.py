# -*- coding: utf-8 -*-
"""
Maya 批量属性复制工具  (Py2/Py3, PySide2/PySide6)

功能：
  1. 双列表，Load/Add 从通道盒 sma 选中属性载入 (node.attr)
  2. Copy L→R / R→L（按列表顺序配对）
  3. Auto Mirror 双向（L↔R），根据非空侧自动判断源
  4. 右键菜单：Sort A-Z / Reverse / Export JSON / Import JSON
  5. Apply JSON Values：按 JSON 值直接 setAttr（不改列表）
  6. 模式：Direct / Negate / Mirror(Axis X/Y/Z)
  7. 每次批量操作都是单个 undo step
  8. 单实例窗口
"""
import contextlib
import json
import numbers
import os
import re

import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMayaUI as omui

try:
    from PySide6 import QtWidgets, QtCore
    from shiboken6 import wrapInstance
except ImportError:
    from PySide2 import QtWidgets, QtCore
    from shiboken2 import wrapInstance

try:
    import Qt_style
except ImportError:
    Qt_style = None

_MISSING = object()

def _u(x):
    return x if isinstance(x, str) else str(x)

# ---------------- 通用 ----------------
def _maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    if ptr:
        return wrapInstance(int(ptr), QtWidgets.QWidget)
    return None


def _default_dir():
    try:
        return cmds.workspace(q=True, rootDirectory=True) or ''
    except Exception:
        return ''


@contextlib.contextmanager
def _undo(name):
    opened = False
    try:
        cmds.undoInfo(openChunk=True, chunkName=name)
        opened = True
    except Exception:
        pass
    try:
        yield
    finally:
        if opened:
            try:
                cmds.undoInfo(closeChunk=True)
            except Exception:
                pass


# ---------------- 通道盒 / 属性解析 ----------------
def _channel_box():
    try:
        n = mel.eval('$tmp = $gChannelBoxName')
        if n:
            return n
    except Exception:
        pass
    return 'mainChannelBox'


def _box_attrs():
    for name in (_channel_box(), 'mainChannelBox'):
        try:
            return list(cmds.channelBox(name, q=True, sma=True) or [])
        except Exception:
            pass
    return []


def _resolve(node, attr):
    if cmds.objExists('{}.{}'.format(node, attr)):
        return node
    for s in cmds.listRelatives(node, shapes=True) or []:
        if cmds.objExists('{}.{}'.format(s, attr)):
            return s
    return None


def _selection_entries():
    attrs, entries, seen = _box_attrs(), [], set()
    for node in cmds.ls(sl=True) or []:
        for a in attrs:
            t = _resolve(node, a)
            if t:
                e = '{}.{}'.format(t, a)
                if e not in seen:
                    seen.add(e)
                    entries.append(e)
    return entries


# ---------------- 读写 / JSON ----------------
def _set_value(plug, value):
    if isinstance(value, (list, tuple)):
        cmds.setAttr(plug, *value)
    elif isinstance(value, str):
        try:
            cmds.setAttr(plug, value, type='string')
        except Exception:
            cmds.setAttr(plug, _u(value))
    else:
        cmds.setAttr(plug, value)


def _json_safe(v):
    if isinstance(v, (list, tuple)):
        return [_json_safe(x) for x in v]
    if isinstance(v, (bool, numbers.Number)) or v is None:
        return v
    return _u(v)


def _item_of(item):
    """(attr, value)；value 可能为 _MISSING"""
    if isinstance(item, dict):
        attr = item.get('attr') or item.get('attribute') or item.get('name')
        return attr, (item['value'] if 'value' in item else item.get('val', _MISSING))
    if isinstance(item, str):
        return item, _MISSING
    return None, _MISSING


def _items_of(data):
    if isinstance(data, dict):
        return data.get('attributes') or data.get('attrs') or data.get('items') or []
    return data


def _attrs_of(data):
    return [a for a, _ in (_item_of(i) for i in _items_of(data)) if a]


def _apply_data(data):
    items = _items_of(data)
    if not isinstance(items, list):
        return 0, 0, 0, ['Unsupported JSON structure (expected a list)']
    ok = fail = skip = 0
    errors = []
    for item in items:
        attr, value = _item_of(item)
        if not attr:
            skip += 1
            continue
        if value is _MISSING or value is None:
            skip += 1
            errors.append('No value for: ' + attr)
            continue
        try:
            _set_value(attr, value)
            ok += 1
        except Exception as e:
            fail += 1
            errors.append('{}: {}'.format(attr, e))
    return ok, fail, skip, errors


# ---------------- 镜像 ----------------
_MIRROR_RULES = [
    (re.compile(r'^(?:translate|trans|t)([XYZ])$', re.I), 'pos'),
    (re.compile(r'^(?:rotate|rot|r)([XYZ])$', re.I), 'rot'),
    (re.compile(r'^(?:scale|s)([XYZ])$', re.I), 'scale'),
]
_AXIS = {'X': 0, 'Y': 1, 'Z': 2}


def _mirror_factor(attr, axis):
    short = attr.rsplit('.', 1)[-1]
    idx = _AXIS.get(axis.upper(), 0)
    for rx, kind in _MIRROR_RULES:
        m = rx.match(short)
        if not m:
            continue
        a = _AXIS.get(m.group(1).upper())
        if a is None:
            return 1.0
        if kind == 'pos':
            return -1.0 if a == idx else 1.0
        if kind == 'rot':
            return 1.0 if a == idx else -1.0
        return 1.0
    return 1.0


def _transform(value, attr, mode, axis):
    if mode == 'direct':
        return value
    if isinstance(value, (list, tuple)):
        return type(value)(_transform(v, attr, mode, axis) for v in value)
    if isinstance(value, bool) or not isinstance(value, numbers.Number):
        return value
    if mode == 'negate':
        return -value
    if mode == 'mirror':
        return value * _mirror_factor(attr, axis)
    return value


def _copy_plug(src, dst, mode='direct', axis='X'):
    if src == dst:
        return True, None
    try:
        value = _transform(cmds.getAttr(src), dst, mode, axis)
    except Exception as e:
        return False, "getAttr '{}' failed: {}".format(src, e)
    try:
        _set_value(dst, value)
    except Exception as e:
        return False, "setAttr '{}' failed: {}".format(dst, e)
    return True, None


def _parse_name_map(text):
    out = []
    for chunk in (text or '').split(','):
        if '=>' in chunk:
            l, r = chunk.split('=>', 1)
            l, r = l.strip(), r.strip()
            if l and r:
                out.append((l, r))
    return out


def _regex_for(token):
    if not token:
        return None
    esc = re.escape(token)
    if token[0].isalnum() and token[-1].isalnum():
        return re.compile(r'(?<![A-Za-z])' + esc + r'(?![a-z])')
    return re.compile(esc)


def _find_mirror(node, pairs):
    """返回 (mirror_node, 'l2r'|'r2l') 或 (None, None)"""
    for l, r in pairs:
        rx = _regex_for(l)
        if rx:
            c = rx.sub(r, node, count=1)
            if c != node and cmds.objExists(c):
                return c, 'l2r'
        rx = _regex_for(r)
        if rx:
            c = rx.sub(l, node, count=1)
            if c != node and cmds.objExists(c):
                return c, 'r2l'
    return None, None


# =====================================================================
#                            列表面板
# =====================================================================
class AttrListPanel(QtWidgets.QWidget):
    def __init__(self, title, log_func):
        super(AttrListPanel, self).__init__()
        self._title = title
        self._log = log_func
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)

        hdr = QtWidgets.QLabel(title)
        hdr.setStyleSheet('font-weight: bold; padding: 2px;')
        lay.addWidget(hdr)

        self.list = QtWidgets.QListWidget()
        self.list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.list.setAlternatingRowColors(True)
        self.list.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self._menu)
        lay.addWidget(self.list, 1)

        lay.addLayout(self._row([
            ('Load Sel', self._load), ('Add Sel', self._add),
            ('Remove', self._remove), ('Clear', self._clear),
        ]))
        lay.addLayout(self._row([
            (u'\u2191 Up', lambda: self._move(-1)),
            (u'\u2193 Down', lambda: self._move(1)),
        ]))

    def _row(self, specs):
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(2)
        for text, slot in specs:
            b = QtWidgets.QPushButton(text)
            b.setMinimumHeight(22)
            b.clicked.connect(slot)
            row.addWidget(b)
        return row

    def _menu(self, pos):
        m = QtWidgets.QMenu(self.list)
        acts = [
            (m.addAction('Sort A-Z'), self._sort),
            (m.addAction('Reverse Order'), self._reverse),
        ]
        m.addSeparator()
        acts += [
            (m.addAction('Export JSON...'), self._export),
            (m.addAction('Import JSON...'), self._import_list),
        ]
        chosen = m.exec_(self.list.mapToGlobal(pos))
        for act, fn in acts:
            if chosen == act:
                return fn()

    # ---- 数据 ----
    def items(self):
        return [self.list.item(i).text() for i in range(self.list.count())]

    def set_items(self, items):
        self.list.clear()
        for it in items or []:
            self.add_item(it)

    def add_item(self, text, select=False):
        text = _u(text).strip()
        if not text or text in self.items():
            return
        item = QtWidgets.QListWidgetItem(text)
        self.list.addItem(item)
        if select:
            item.setSelected(True)

    # ---- 按钮 ----
    def _load(self):
        if not cmds.ls(sl=True):
            return self._log('Nothing selected.')
        entries = _selection_entries()
        if not entries:
            return self._log('No attributes selected in Channel Box.')
        self.set_items(entries)
        self._log('Loaded {} attribute(s).'.format(len(entries)))

    def _add(self):
        if not cmds.ls(sl=True):
            return self._log('Nothing selected.')
        entries = _selection_entries()
        if not entries:
            return self._log('No attributes selected in Channel Box.')
        for e in entries:
            self.add_item(e)
        self._log('Added {} attribute(s).'.format(len(entries)))

    def _remove(self):
        for r in sorted([self.list.row(i) for i in self.list.selectedItems()], reverse=True):
            self.list.takeItem(r)

    def _clear(self):
        self.list.clear()

    def _move(self, d):
        items = self.list.selectedItems()
        if not items:
            return
        for r in sorted([self.list.row(i) for i in items], reverse=(d > 0)):
            new = r + d
            if not 0 <= new < self.list.count():
                continue
            it = self.list.takeItem(r)
            self.list.insertItem(new, it)
            it.setSelected(True)

    def _sort(self):
        self.set_items(sorted(self.items(), key=lambda s: s.lower()))

    def _reverse(self):
        self.set_items(list(reversed(self.items())))

    # ---- JSON ----
    def _ask(self, save):
        if save:
            tag = re.sub(r'[^a-z0-9]+', '_', self._title.lower()).strip('_') or 'attrs'
            p, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, 'Export JSON',
                os.path.join(_default_dir(), 'attrs_{}.json'.format(tag)), 'JSON (*.json)')
            if p and not p.lower().endswith('.json'):
                p += '.json'
            return p
        return QtWidgets.QFileDialog.getOpenFileName(
            self, 'Import JSON', _default_dir(), 'JSON (*.json)')[0]

    def _export(self):
        items = self.items()
        if not items:
            return self._log('List is empty.')
        data, skipped = [], 0
        for e in items:
            try:
                data.append({'attr': e, 'value': _json_safe(cmds.getAttr(e))})
            except Exception as ex:
                self._log('  ! Skip {}: {}'.format(e, ex))
                skipped += 1
        if not data:
            return self._log('No valid attributes.')
        path = self._ask(save=True)
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(json.dumps(data, indent=4, ensure_ascii=False))
        except Exception as e:
            return self._log('Export failed: {}'.format(e))
        msg = 'Exported {} to {}'.format(len(data), path)
        if skipped:
            msg += ' (skipped {})'.format(skipped)
        self._log(msg)

    def _import_list(self):
        path = self._ask(save=False)
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.loads(f.read())
        except Exception as e:
            return self._log('Import failed: {}'.format(e))
        attrs = _attrs_of(data)
        if not attrs:
            return self._log('No attributes found in file.')
        self.set_items(attrs)
        self._log('Imported {} attribute(s) into {} list.'.format(len(attrs), self._title))


# =====================================================================
#                            主窗口
# =====================================================================
class AttrCopyTool(QtWidgets.QDialog):
    TITLE = 'Batch Attribute Copy Tool'
    NAME = 'mayaAttrCopyTool'
    DEFAULT_MAP = '_L=>_R, _l=>_r, left=>right, Left=>Right, LEFT=>RIGHT, L=>R'

    def __init__(self):
        super(AttrCopyTool, self).__init__(_maya_main_window())
        self.setObjectName(self.NAME)
        self.setWindowTitle(self.TITLE)
        self.setWindowFlags(QtCore.Qt.Window |
                    QtCore.Qt.WindowMinimizeButtonHint |
                    QtCore.Qt.WindowMaximizeButtonHint |
                    QtCore.Qt.WindowCloseButtonHint)

        try:
            Qt_style.apply_style(self)  # 应用优化后的样式表
        except Exception:
            cmds.warning("未找到样式表，使用默认样式")
            
        #self.setMinimumSize(760, 660)
        #self.resize(820, 740)
        self._build()
        self._sync_axis()

    def _build(self):
        main = QtWidgets.QVBoxLayout(self)
        main.setContentsMargins(8, 8, 8, 8)
        main.setSpacing(6)

        # 双列表
        panels = QtWidgets.QHBoxLayout()
        panels.setSpacing(6)
        self.lpanel = AttrListPanel('Source  [node.attr]', self._log)
        self.rpanel = AttrListPanel('Target  [node.attr]', self._log)
        panels.addWidget(self.lpanel, 1)
        panels.addWidget(self.rpanel, 1)
        main.addLayout(panels, 1)

        # 手动添加
        row = QtWidgets.QHBoxLayout()
        self.manual = QtWidgets.QLineEdit()
        self.manual.setPlaceholderText('e.g. pCube1.translateX')
        row.addWidget(QtWidgets.QLabel('Manual:'))
        row.addWidget(self.manual, 1)
        for text, panel in (('Add to L', self.lpanel), ('Add to R', self.rpanel)):
            b = QtWidgets.QPushButton(text)
            b.clicked.connect(lambda *_, p=panel: self._add_manual(p))
            row.addWidget(b)
        main.addLayout(row)

        # 选项
        opt = QtWidgets.QGroupBox('Copy Options')
        g = QtWidgets.QGridLayout(opt)
        g.addWidget(QtWidgets.QLabel('Mode:'), 0, 0)
        self.mode = QtWidgets.QComboBox()
        self.mode.addItems(['Direct', 'Negate', 'Mirror (Axis)'])
        g.addWidget(self.mode, 0, 1)
        g.addWidget(QtWidgets.QLabel('Axis:'), 0, 2)
        self.axis = QtWidgets.QComboBox()
        self.axis.addItems(['X', 'Y', 'Z'])
        self.axis.setEnabled(False)
        g.addWidget(self.axis, 0, 3)
        g.addWidget(QtWidgets.QLabel('Name Map:'), 1, 0)
        self.name_map = QtWidgets.QLineEdit(self.DEFAULT_MAP)
        self.name_map.setToolTip('L <-> R name rules, comma separated.\nExample: _L=>_R, left=>right')
        g.addWidget(self.name_map, 1, 1, 1, 3)
        g.setColumnStretch(1, 1)
        main.addWidget(opt)
        self.mode.currentIndexChanged.connect(self._sync_axis)

        # 操作按钮
        op = QtWidgets.QHBoxLayout()
        op.setSpacing(4)
        actions = [
            ('Copy  L  \u2192  R', lambda: self._copy(self.lpanel, self.rpanel), None),
            ('Copy  R  \u2192  L', lambda: self._copy(self.rpanel, self.lpanel), None),
            ('Auto Mirror  (L\u2194R)', self._auto_mirror,
             'Fill the empty list by mirroring the other.\nEach rule tried both directions.'),
            ('Apply JSON Values...', self._apply_json,
             'Set values from a JSON file directly; lists are not touched.'),
        ]
        for text, slot, tip in actions:
            b = QtWidgets.QPushButton(text)
            b.setMinimumHeight(28)
            if tip:
                b.setToolTip(tip)
            b.clicked.connect(slot)
            op.addWidget(b)
        main.addLayout(op)

        # 日志
        self.log = QtWidgets.QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(1000)
        self.log.setMaximumHeight(120)
        self.log.setStyleSheet('font-family: monospace;')
        main.addWidget(self.log)

    # ---- 辅助 ----
    def _log(self, msg):
        msg = _u(msg)
        self.log.appendPlainText(msg)
        sb = self.log.verticalScrollBar()
        sb.setValue(sb.maximum())
        try:
            print('[AttrCopyTool] ' + msg)
        except Exception:
            pass

    def _sync_axis(self):
        self.axis.setEnabled(self.mode.currentIndex() == 2)

    def _mode(self):
        i = self.mode.currentIndex()
        if i == 0:
            return 'direct', 'X'
        if i == 1:
            return 'negate', 'X'
        return 'mirror', self.axis.currentText()

    def _add_manual(self, panel):
        t = self.manual.text().strip()
        if t:
            panel.add_item(t)
            self.manual.clear()

    # ---- 核心 ----
    def _copy(self, src, dst):
        ls, rs = src.items(), dst.items()
        if not ls or not rs:
            return self._log('Both lists must be non-empty.')
        n = min(len(ls), len(rs))
        if len(ls) != len(rs):
            self._log('Count mismatch (L={}, R={}). Pairs: {}.'.format(len(ls), len(rs), n))
        mode, axis = self._mode()
        ok = fail = 0
        with _undo('AttrCopy [{}/{}]'.format(mode, axis)):
            for i in range(n):
                s, err = _copy_plug(ls[i], rs[i], mode, axis)
                if s:
                    ok += 1
                else:
                    fail += 1
                    self._log('  ! ' + err)
        self._log('Copy done [{}/{}]: {} ok, {} failed.'.format(mode, axis, ok, fail))

    def _auto_mirror(self):
        ls, rs = self.lpanel.items(), self.rpanel.items()
        if not ls and not rs:
            return self._log('Both lists are empty.')
        if ls and rs:
            return self._log('Clear one list first (or use Copy).')
        pairs = _parse_name_map(self.name_map.text())
        if not pairs:
            return self._log('Name map is empty or invalid.')
        src, dst, direction = (self.lpanel, self.rpanel, 'L->R') if ls \
            else (self.rpanel, self.lpanel, 'R->L')
        mode, axis = self._mode()
        entries = []
        ok = fail = nf = l2r = r2l = 0
        with _undo('AttrCopy AutoMirror [{}/{}]'.format(mode, axis)):
            for e in src.items():
                if '.' not in e:
                    fail += 1
                    self._log('  ! Invalid entry: ' + e)
                    continue
                node, attr = e.split('.', 1)
                m, d = _find_mirror(node, pairs)
                if not m:
                    nf += 1
                    self._log('  ! Mirror node not found: ' + node)
                    continue
                l2r += d == 'l2r'
                r2l += d == 'r2l'
                de = '{}.{}'.format(m, attr)
                entries.append(de)
                s, err = _copy_plug(e, de, mode, axis)
                if s:
                    ok += 1
                else:
                    fail += 1
                    self._log('  ! ' + err)
        dst.set_items(entries)
        self._log('Auto mirror ({}): {} ok, {} failed, {} not found (L->R: {}, R->L: {}).'.format(
            direction, ok, fail, nf, l2r, r2l))

    def _apply_json(self):
        p = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Apply JSON Values', _default_dir(), 'JSON (*.json)')[0]
        if not p:
            return
        try:
            with open(p, 'r', encoding='utf-8') as f:
                data = json.loads(f.read())
        except Exception as e:
            return self._log('Apply failed: {}'.format(e))
        with _undo('AttrCopy ApplyJSON'):
            ok, fail, skip, errors = _apply_data(data)
        for err in errors[:20]:
            self._log('  ! ' + err)
        if len(errors) > 20:
            self._log('  ... and {} more.'.format(len(errors) - 20))
        self._log('Apply done: {} ok, {} failed, {} skipped.'.format(ok, fail, skip))


# =====================================================================
#                            入口（单实例）
# =====================================================================
def show():
    global _attr_copy_tool_win
    try:
        if _attr_copy_tool_win is not None:
            _attr_copy_tool_win.close()
            _attr_copy_tool_win.deleteLater()
    except Exception:
        pass
    _attr_copy_tool_win = None
    win = AttrCopyTool()
    win.show()
    _attr_copy_tool_win = win
    return win


if __name__ == '__main__':
    show()