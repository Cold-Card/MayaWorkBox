# -*- coding: utf-8 -*-

"""Qt 兼容层，优先使用系统安装的 Qt；缺失时提供轻量级占位实现。"""

try:
    from PySide2 import QtCore, QtGui, QtWidgets
except ImportError:  # pragma: no cover
    try:
        from PyQt5 import QtCore, QtGui, QtWidgets
    except ImportError:  # pragma: no cover
        try:
            from PySide6 import QtCore, QtGui, QtWidgets
        except ImportError:  # pragma: no cover
            class _QtCoreStub(object):
                class Qt(object):
                    Window = 0x00000001
                    WindowMinimizeButtonHint = 0x00000002
                    WindowMaximizeButtonHint = 0x00000004
                    WindowCloseButtonHint = 0x00000008
                    WA_DeleteOnClose = 0x00000001
                    AlignCenter = 0
                    Horizontal = 0
                    Vertical = 1
                    KeepAspectRatio = 0
                    SmoothTransformation = 0
                    CustomContextMenu = 0

                class QTimer(object):
                    @staticmethod
                    def singleShot(delay, func):
                        return func()

            class _QtGuiStub(object):
                class QIcon(object):
                    def __init__(self, *args, **kwargs):
                        pass

                class QPixmap(object):
                    def __init__(self, *args, **kwargs):
                        self._path = args[0] if args else None

                    def isNull(self):
                        return True

                    def scaled(self, *args, **kwargs):
                        return self

            class _QtWidgetsStub(object):
                class QWidget(object):
                    def __init__(self, *args, **kwargs):
                        pass

                    def setAttribute(self, *args, **kwargs):
                        pass

                    def setWindowFlags(self, *args, **kwargs):
                        pass

                    def setWindowTitle(self, *args, **kwargs):
                        pass

                    def loadWindowSettings(self):
                        pass

                    def show(self):
                        pass

                    def close(self):
                        pass

                    def deleteLater(self):
                        pass

                    def raise_(self):
                        pass

                    def activateWindow(self):
                        pass

                class QDialog(QWidget):
                    def exec_(self):
                        return 0

                class QMessageBox(object):
                    Yes = 1
                    No = 0
                    Warning = 0
                    Information = 0
                    Critical = 0
                    Question = 0

                    @staticmethod
                    def warning(*args, **kwargs):
                        return 0

                    @staticmethod
                    def information(*args, **kwargs):
                        return 0

                    @staticmethod
                    def critical(*args, **kwargs):
                        return 0

                    @staticmethod
                    def question(*args, **kwargs):
                        return 0

                class QFileDialog(object):
                    @staticmethod
                    def getExistingDirectory(*args, **kwargs):
                        return ''

                class QVBoxLayout(object):
                    def __init__(self, *args, **kwargs):
                        pass

                    def addLayout(self, *args, **kwargs):
                        pass

                    def addWidget(self, *args, **kwargs):
                        pass

                    def setStretch(self, *args, **kwargs):
                        pass

                    def setContentsMargins(self, *args, **kwargs):
                        pass

                class QHBoxLayout(QVBoxLayout):
                    pass

                class QLabel(QWidget):
                    def __init__(self, *args, **kwargs):
                        self._text = args[0] if args else ''

                    def setText(self, value):
                        self._text = value

                    def text(self):
                        return self._text

                    def setStyleSheet(self, *args, **kwargs):
                        pass

                    def setFixedWidth(self, *args, **kwargs):
                        pass

                    def setWordWrap(self, *args, **kwargs):
                        pass

                    def setAlignment(self, *args, **kwargs):
                        pass

                    def setMaximumHeight(self, *args, **kwargs):
                        pass

                    def setMinimumSize(self, *args, **kwargs):
                        pass

                    def clear(self):
                        self._text = ''

                    def setPixmap(self, *args, **kwargs):
                        pass

                class QLineEdit(QWidget):
                    def __init__(self, *args, **kwargs):
                        self._text = ''

                    def setText(self, value):
                        self._text = value

                    def text(self):
                        return self._text

                    def setPlaceholderText(self, *args, **kwargs):
                        pass

                class QComboBox(QWidget):
                    def __init__(self, *args, **kwargs):
                        self._items = []

                    def addItem(self, *args, **kwargs):
                        self._items.append(args[0])

                    def clear(self):
                        self._items = []

                    def currentText(self):
                        return self._items[0] if self._items else ''

                    def currentData(self):
                        return self._items[0] if self._items else ''

                    def setCurrentIndex(self, *args, **kwargs):
                        pass

                    def findText(self, *args, **kwargs):
                        return -1

                class QListWidget(QWidget):
                    def __init__(self, *args, **kwargs):
                        self._items = []

                    def clear(self):
                        self._items = []

                    def addItems(self, items):
                        self._items.extend(items)

                    def addItem(self, item):
                        self._items.append(item)

                    def item(self, index):
                        if 0 <= index < len(self._items):
                            return type('Item', (), {'text': lambda self: self._items[index]})()
                        return None

                    def count(self):
                        return len(self._items)

                class QTextEdit(QWidget):
                    def __init__(self, *args, **kwargs):
                        self._text = ''

                    def setPlainText(self, value):
                        self._text = value

                    def clear(self):
                        self._text = ''

                class QPushButton(QWidget):
                    def __init__(self, *args, **kwargs):
                        self._text = args[0] if args else ''

                    def setText(self, value):
                        self._text = value

                    def text(self):
                        return self._text

                    def setEnabled(self, *args, **kwargs):
                        pass

                    def setVisible(self, *args, **kwargs):
                        pass

                    def setStyleSheet(self, *args, **kwargs):
                        pass

                    def setMaximumHeight(self, *args, **kwargs):
                        pass

                    def setFixedWidth(self, *args, **kwargs):
                        pass

                class QGroupBox(QWidget):
                    pass

                class QSplitter(QWidget):
                    def __init__(self, *args, **kwargs):
                        pass

                    def addWidget(self, *args, **kwargs):
                        pass

                    def setSizes(self, *args, **kwargs):
                        pass

                    def setStretchFactor(self, *args, **kwargs):
                        pass

                class QFrame(object):
                    Box = 0
                    Sunken = 0

                QFrame = QFrame

            QtCore = _QtCoreStub()
            QtGui = _QtGuiStub()
            QtWidgets = _QtWidgetsStub()


__all__ = ['QtCore', 'QtGui', 'QtWidgets']
