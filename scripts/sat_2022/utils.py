# uncompyle6 version 3.8.0
# Python bytecode 2.7 (62211)
# Decompiled from: Python 3.10.2 (tags/v3.10.2:a58ebcc, Jan 17 2022, 14:12:15) [MSC v.1929 64 bit (AMD64)]
# Embedded file name: F:/Maya_Projects\sat\utils.py
# Compiled at: 2016-11-18 02:31:26
import maya.cmds as cmds
import pickle
import os, imp

def pyToAttr(objAttr, data):
    """
        Write (pickle) Python data to the given Maya obj.attr.  This data can
        later be read back (unpickled) via attrToPy().

        Arguments:
        objAttr : string : a valid object.attribute name in the scene.  If the
                object exists, but the attribute doesn't, the attribute will be added.
                The if the attribute already exists, it must be of type 'string', so
                the Python data can be written to it.
        data : some Python data :  Data that will be pickled to the attribute
                in question.
        """
    obj, attr = objAttr.split('.')
    if not cmds.objExists(objAttr):
        cmds.addAttr(obj, longName=attr, dataType='string')
    if cmds.getAttr(objAttr, type=True) != 'string':
        raise Exception("Object '%s' already has an attribute called '%s', but it isn't type 'string'" % (obj, attr))
    # print("data", data)
    stringData = pickle.dumps(data)
    stringData = str(stringData)
    # print("stringData", stringData)
    cmds.setAttr(objAttr, edit=True, lock=False)
    cmds.setAttr(objAttr, stringData, type='string')
    cmds.setAttr(objAttr, edit=True, lock=True)


def attrToPy(objAttr):
    """
        Take previously stored (pickled) data on a Maya attribute (put there via
        pyToAttr() ) and read it back (unpickle) to valid Python values.

        Arguments:
        objAttr : string : A valid object.attribute name in the scene.  And of course,
                it must have already had valid Python data pickled to it.

        Return : some Python data :  The reconstituted, unpickled Python data.
        """
    stringAttrData = str(cmds.getAttr(objAttr))
    loadedData = pickle.loads(stringAttrData)
    # print('loadedData', loadedData)
    return loadedData


def compileUI():
    from pysideuic import compileUi
    print ('!!!')
    modulePath = os.path.abspath(imp.find_module('sat2')[1])
    pyfile = open(modulePath + '\\mainWindow.py', 'w')
    compileUi(modulePath + '\\mainWindow.ui', pyfile, False, 4, False)
    pyfile.close()
    pyfile2 = open(modulePath + '\\aboutWindow.py', 'w')
    compileUi(modulePath + '\\aboutWindow.ui', pyfile2, False, 4, False)
    pyfile2.close()