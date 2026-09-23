## ScriptName : posiPal
## Contents   : tool to help maintain shape 
## Author     : Joe Wu
## URL        : https://www.youtube.com/@Im3dJoe
## Since      : 2023/03
## Version    : 1.0  First version for public test
## Other Note : test in maya 2020.2 windows enviroment
##
##
## Install    : copy and paste script into a python tab in maya script editor


import re
import os
import json
import maya.cmds as mc
import os.path, time

def posiPal():
    documents_folder = mc.internalVar(userAppDir=True)
    filename = os.path.join(documents_folder, 'collectData.json')
    dispTime = ''
    if os.path.isfile(filename):
        readFileTime = os.path.getmtime(filename)
        readTime = time.ctime(readFileTime)
        timeData = readTime.split(' ')
        dispTime = '       ' + timeData[-2] + '    /  ' + timeData[-3]  + ' ' + timeData[-5]
    if mc.window('noteBook', exists=True):
        mc.deleteUI('noteBook')
    noteBook = mc.window('noteBook', title='Posi Pal v1.0', w=430, h=50)
    mc.frameLayout(labelVisible=False)
    mc.text(label='', h=3)
    mc.columnLayout(adj=1)
    mc.rowColumnLayout(nc=11, cw=[ (1, 40), (2, 20), (3, 40),(4, 50),(5, 75),(6, 140), (7, 1),(8, 40),(9, 2),(10, 40),(11, 15)])
    mc.iconTextButton(image='polyClearColors.png', bgc=[0.27, 0.27, 0.27],  c = 'removeRowColumnAll()' )
    mc.text(label='', h=3)
    mc.iconTextButton(image='create.png', h=40, bgc=[0.27, 0.27, 0.27],  c =  'addPdGo()' )
    mc.text(label='', h=3)
    mc.radioButtonGrp('ppQueryMethod' , vr = 1,nrb=2, sl=1, la2=("Local","World"))
    if os.path.isfile(filename):
        mc.text('fileTimeRecord', label= dispTime, h=3)
    else:
        mc.text('fileTimeRecord', label='', h=3)
    mc.text(label='', h=3)
    mc.iconTextButton(image='fileOpen.png', h=40, bgc=[0.27, 0.27, 0.27],  c =  'readDataFile()' )
    mc.text(label='', h=3)
    mc.iconTextButton(image='fileSave.png', h=40, bgc=[0.27, 0.27, 0.27],  c =  'exportData2File()' )
    mc.text(label='', h=3)
    mc.setParent('..')
    mc.rowColumnLayout(nc=5, cw=[(1, 280), (2, 60), (3, 60),(4, 7) ,(5, 40)])
    mc.text(label='', h=3)  
    mc.checkBox('PosiPalTrans', label='Trans', v=1)
    mc.checkBox('PosiPalRot',  label='Rotate', v=1)
    mc.text(label='', h=3) 
    mc.iconTextButton(image='executeAll.png', h=40, bgc=[0.27, 0.27, 0.27], c = 'pasteAllPosi()' )
    mc.setParent('..')
    mc.separator()
    mc.text(label='', h=3)
    mc.columnLayout(adj=1)
    mc.scrollLayout('pdScroll', h=300)
    mc.rowColumnLayout('pdRowList')
    mc.setParent('..')
    mc.showWindow(noteBook)
    removeRowColumnAll()
    if mc.objExists('ppDataNode'):
        user_defined_attrs = mc.listAttr('ppDataNode', ud=True)
        if user_defined_attrs:
            for attr in user_defined_attrs:
                mc.deleteAttr('ppDataNode' + '.' + attr)
    else:
        mc.createNode('transform', n = 'ppDataNode')
    mc.setAttr('ppDataNode.hiddenInOutliner',1)
    mc.window('noteBook', e=1, w=430, h=50)
def sortListOrder():
    rowColumListCheck = mc.lsUI(controlLayouts=True)
    rowColumList = []
    for r in rowColumListCheck:
        if '_dataColumn' in r:
            new_str = r.replace('_dataColumn', '')
            rowColumList.append(new_str)
    collectData = []
    for c in rowColumList:
        qmData = mc.button((c + '_qMButton'), q=1, bgc=1)
        packData = []
        tData =  mc.text(c + '_dataTrans', q=1, l =1)
        tDataList = tData.split(', ')
        rData =  mc.text(c + '_dataRot', q=1, l =1)
        rDataList = rData.split(', ')
        packData = [c,tDataList,rDataList,qmData]
        collectData.append(packData)
    collectData = sorted(collectData, key=lambda x: x[0])
    removeRowColumnAll()   
    makeListButton(collectData)
    
def makeListButton(collectData):
    for c in collectData:
        if c[0] == 'set':
            checkAttrExit = mc.attributeQuery(c[1], node='ppDataNode', exists=True)
            if checkAttrExit == 0:
                mc.addAttr('ppDataNode', longName= c[1], dataType="string")
            readCompData = c[2]
            mc.setAttr(('ppDataNode.' + c[1]), readCompData, type="string")
        else:
            objectName = c[0]
            dataTrans = [c[1][0], c[1][1], c[1][2]]
            roundTransString = ", ".join(dataTrans)
            transString = str(dataTrans)
            dataRot = [c[2][0], c[2][1], c[2][2]]
            roundRotString =  ", ".join(dataRot)
            rotString = str(dataRot)
            mc.rowColumnLayout(c[0] + '_dataColumn', nc=11, cw=[(1, 30), (2, 2), (3, 80), (4, 10), (5, 110), (6, 10),(7, 110),(8, 10), (9, 40), (10, 2), (11, 40)])
            cmd = 'deletePDButton("' + str(objectName)+ '")'
            mc.iconTextButton(image='delete.png', h=30, bgc=[0.27, 0.27, 0.27], c=cmd)
            mc.text(label='', h=3)
            if '_P' in c[0]:
                mc.textField(ed=0, width=60, tx=c[0], bgc = (0.38,0.28,0.28))
            elif '_set' in c[0]:
                mc.textField(ed=0, width=60, tx=c[0], bgc = (0.5, 0.46, 0.25))
            else:
                mc.textField(ed=0, width=60, tx=c[0] ,bgc = (0.28,0.28,0.28))
            #mc.text(label='', h=3)
            mc.button((c[0] + '_qMButton'), l ='', en=0, bgc =(c[3][0],c[3][1],c[3][2]))
            mc.text(c[0] + '_dataTrans', label=str(roundTransString), h=3)
            mc.text(label='', h=3)
            mc.text(c[0] + '_dataRot', label=str(roundRotString), h=3)
            mc.text(label='', h=3)
            pickCmd = 'pickDataObj("' + str(objectName)+ '")'
            mc.iconTextButton( (c[0] + '_pickButton'),image='selectNonOverlappingUV.png', bgc=[0.27, 0.27, 0.27],label='pick', c = pickCmd )
            mc.text(label='', h=3)
            pressCmd = 'pasteData( "' + str(objectName) + '" ,' + transString + ',' + rotString +')'
            mc.iconTextButton( (c[0] + '_pressButton'),image='execute.png', bgc=[0.27, 0.27, 0.27], label='paste', c = pressCmd )
            mc.setParent('..')
            try:
                mc.deleteUI(c[0]  + '_seperator')
            except:
                pass
            mc.separator(c[0]  + '_seperator')



def readDataFile():
    documents_folder = mc.internalVar(userAppDir=True)
    filename = os.path.join(documents_folder, 'collectData.json')
    collectData = []
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            collectData = json.load(f)
        collectData = sorted(collectData, key=lambda x: x[0])
        removeRowColumnAll()
        makeListButton(collectData)

def exportData2File():
    rowColumListCheck = mc.lsUI(controlLayouts=True)
    rowColumList = []
    for r in rowColumListCheck:
        if '_dataColumn' in r:
            new_str = r.replace('_dataColumn', '')
            rowColumList.append(new_str)
    collectData = []
    for c in rowColumList:
        qmData = mc.button((c + '_qMButton'), q=1, bgc=1)
        packData = []
        tData =  mc.text(c + '_dataTrans', q=1, l =1)
        tDataList = tData.split(', ')
        rData =  mc.text(c + '_dataRot', q=1, l =1)
        rDataList = rData.split(', ')
        packData = [c,tDataList,rDataList,qmData]
        collectData.append(packData)
    #collect complist data
    
    if mc.objExists('ppDataNode'):
        user_defined_attrs = mc.listAttr('ppDataNode', ud=True)
        if user_defined_attrs:
            for attr in user_defined_attrs:
                getData = mc.getAttr('ppDataNode' + '.' + attr)
                packData = ['set',attr,getData]
                collectData.append(packData)
                    
                    
    documents_folder = mc.internalVar(userAppDir=True)
    filename = documents_folder + 'collectData.json'
    with open(filename, 'w') as f:
        json.dump(collectData, f)
    readFileTime = os.path.getmtime(filename)
    readTime = time.ctime(readFileTime)
    timeData = readTime.split(' ')
    dispTime = '       ' + timeData[-2] + '    /  ' + timeData[-3]  + ' ' + timeData[-5]
    mc.text('fileTimeRecord', e=1, label=dispTime)
    

def removeRowColumnAll():
    checkRowColumnLayout = mc.rowColumnLayout('pdRowList', q=True, ex=True)
    if checkRowColumnLayout:
        mc.deleteUI('pdRowList')
        mc.setParent('pdScroll')
        mc.rowColumnLayout('pdRowList')

    rowColumListCheck = mc.lsUI(controlLayouts=True)
    if rowColumListCheck:
        rowColumList = []
        for r in rowColumListCheck:
            if '_dataColumn' in r:
                mc.deleteUI(r)
    
def addPdGo():
    selComp = mc.filterExpand( sm=(31,32,34,35) )
    if selComp:
        addPdComps()
    else:
        selObject = mc.ls(sl=True, fl=True)
        if selObject:
            addPdMesh()
    sortListOrder()
  

def addPdComps():
    selComp = mc.filterExpand( sm=(31,32,34,35) )
    shapesNode = mc.listRelatives(selComp[0], parent=True)[0]
    transformNode = mc.listRelatives(shapesNode, parent=True)[0]
    selComp = mc.filterExpand( sm=(31,32,34,35) )
    shapesNode = mc.listRelatives(selComp[0], parent=True)[0]
    transformNode = mc.listRelatives(shapesNode, parent=True)[0]
    setName = transformNode + '_set1'
    checkNameExist = mc.attributeQuery(setName, node='ppDataNode', exists=True)
    i=1
    while checkNameExist == 1 and i < 50:
        setName = transformNode + '_set' + str(i) 
        checkNameExist = mc.attributeQuery(setName, node='ppDataNode', exists=True)
        i = i + 1
    toString = ', '.join(selComp)
    mc.addAttr('ppDataNode', longName= setName, dataType="string")
    mc.setAttr(('ppDataNode.' + setName), toString, type="string")
    mc.setToolTo('moveSuperContext')
    dataTrans = mc.manipMoveContext("Move", query=True, position=True)
    roundTransString = ", ".join(["{:.2f}".format(x) for x in dataTrans])
    transString = str(roundTransString)
    dataRot = mc.getAttr(transformNode + '.rotate')[0]
    roundRotString = ", ".join(["{:.2f}".format(x) for x in dataRot])
    rotString = str(roundRotString)
    mc.rowColumnLayout((setName + '_dataColumn'), nc=11, cw=[(1, 30), (2, 2), (3, 90), (4, 2), (5, 110), (6, 10),(7, 110),(8, 10), (9, 40), (10, 2), (11, 40)])
    mc.iconTextButton(image='delete.png', h=30, bgc=[0.27, 0.27, 0.27])
    mc.button((setName + '_qMButton'), l ='', en=0, bgc=[0.5,0.05,0.05])
    #mc.text(label='', h=3)
    mc.textField(setName + '_dataText', ed=0, width=60, tx=setName, bgc =(0.5, 0.46, 0.25))
    mc.text(label='', h=3)
    mc.text(setName + '_dataTrans', label= str(roundTransString), h=3)
    mc.text(label='', h=3)
    mc.text(setName + '_dataRot',label=str(roundRotString), h=3)
    mc.text(label='', h=3)
    mc.iconTextButton( (setName + '_pickButton'),image='execute.png', label='pick', bgc=[0.27, 0.27, 0.27])
    mc.iconTextButton( (setName + '_pressButton'),image='execute.png',  label='paste',bgc=[0.27, 0.27, 0.27])
    mc.setParent('..')


def addPdMesh():
    sel = mc.ls(sl=True, fl=True)
    qMethod = mc.radioButtonGrp('ppQueryMethod' ,q=1, sl=1)
    if qMethod == 2:
        if mc.objExists('getWorldPos') == 0:
            mc.group(empty=1,n='getWorldPos')
    if sel:
        mc.setParent('pdRowList')
        #s = sel[0]
        for s in sel:
            objectName = s
            dataTrans = [0,0,0]
            if qMethod == 1 :
                dataTrans = mc.getAttr(s + '.translate')[0]
            else:
                currentSel = mc.ls(s,l=1)[0]
                upperNodeList = currentSel.split('|')[0:-1]
                upperNode = '|'.join(upperNodeList)
                if len(upperNode) > 0:
                    mc.parent('getWorldPos',upperNode)
                    mc.matchTransform('getWorldPos',currentSel)
                    mc.parent('getWorldPos',w=1)
                    dataTrans = mc.getAttr('getWorldPos.translate')[0]
                else:
                    dataTrans = mc.getAttr(s + '.translate')[0]
                
            roundTransString = ", ".join(["{:.2f}".format(x) for x in dataTrans])
            transString = str(roundTransString)
            dataRot = mc.getAttr(s + '.rotate')[0]
            roundRotString = ", ".join(["{:.2f}".format(x) for x in dataRot])
            rotString = str(roundRotString)
            newRowColumnName = s + '_dataColumn'
            checkRowColumnName = mc.rowColumnLayout(newRowColumnName, q=True, ex=True)
            i = 0
            columnColorState = 0
            while checkRowColumnName == 1 and i < 10:
                columnColorState = 1
                if i == 0:
                    s = s + '_P1' 
                else:
                    s = s.replace('_P' + str(i), '_P' + str(i+1))
                    
                newRowColumnName = s + '_dataColumn'
                checkRowColumnName = mc.rowColumnLayout(newRowColumnName, q=True, ex=True)
                i = i + 1
            mc.rowColumnLayout((s + '_dataColumn'), nc=11, cw=[(1, 30), (2, 2), (3, 90), (4, 2), (5, 110), (6, 10),(7, 110),(8, 10), (9, 40), (10, 2), (11, 40)])
            mc.iconTextButton(image='delete.png', h=30, bgc=[0.27, 0.27, 0.27])
            mc.text(label='', h=3)
            if columnColorState == 0:
                mc.textField(s + '_dataText', ed=0, width=60, tx=s, bgc = [0.28,0.28,0.28])
            else:
                mc.textField(s + '_dataText', ed=0, width=60, tx=s, bgc = [0.38,0.28,0.28])
            if qMethod == 1:
                mc.button(s + '_qMButton', l ='', en=0, bgc=[0,0.3,0.7])
            else:
                mc.button(s + '_qMButton', l ='', en=0, bgc=[0.5,0.05,0.05])
            #mc.text(label='', h=3)
            mc.text(s + '_dataTrans', label= str(roundTransString), h=3)
            mc.text(label='', h=3)
            mc.text(s + '_dataRot',label=str(roundRotString), h=3)
            mc.text(label='', h=3)
            mc.iconTextButton( (s + '_pickButton'),image='execute.png', label='pick', bgc=[0.27, 0.27, 0.27])
            mc.iconTextButton( (s + '_pressButton'),image='execute.png',  label='paste',bgc=[0.27, 0.27, 0.27])
            mc.setParent('..')
    if mc.objExists('getWorldPos'):
        mc.delete('getWorldPos')

def deletePDButton(object):
    mc.deleteUI( object + '_seperator')
    mc.deleteUI( object + '_dataColumn')
    if '_set' in object:
        if mc.attributeQuery(object, node='ppDataNode', exists=True):
            mc.deleteAttr('ppDataNode' + '.' + object)

def pickDataObj(object):
    if '_P' in object:
        object = object.split('_P')[0]
    if mc.objExists(object):
        mc.select(object)
    else:
        mc.select(cl=1)
    if '_set' in object:
        if mc.attributeQuery(object, node='ppDataNode', exists=True):
            getList = mc.getAttr('ppDataNode.'+ object)
            my_list = getList.split(',')
            mc.select(my_list)

def pasteData(object, transData, RotData):
    transYes = mc.checkBox('PosiPalTrans', q=1 , v=1)
    rotYes = mc.checkBox('PosiPalRot',  q=1 , v=1)
    sel = mc.ls(sl=True, fl=True)
    if len(sel) == 1:
        if transYes == 1:
            mc.setAttr((sel[0]+'.translate'),float(transData[0]),float(transData[1]),float(transData[2]))
        if rotYes == 1:
            mc.setAttr((sel[0]+'.rotate'),float(RotData[0]),float(RotData[1]),float(RotData[2]))

    elif len(sel) == 0:
        if '_set' not in object:
            if '_P' in object:
                object = object.split('_P')[0]
            if mc.objExists(object):
                if transYes == 1:
                    mc.setAttr((object+'.translate'),float(transData[0]),float(transData[1]),float(transData[2]))
                if rotYes == 1:
                    mc.setAttr((object+'.rotate'),float(RotData[0]),float(RotData[1]),float(RotData[2]))
            mc.select(sel)

def pasteAllPosi():
    transYes = mc.checkBox('PosiPalTrans', q=1 , v=1)
    rotYes = mc.checkBox('PosiPalRot',  q=1 , v=1)
    buttonListCheck = mc.lsUI(ctl=True)
    buttonList = []
    for b in buttonListCheck:
        if '_pressButton' in b and '_P' not in b and '_set' not in b:
            buttonList.append(b)
    if buttonList:
        for u in buttonList:
            cmd = mc.iconTextButton(u, q=1, c = 1)
            dataList = cmd.split(',')
            objectName = dataList[0].split('"')[1]
            if mc.objExists(objectName):
                transX = extractNumber(dataList[1])
                transY = extractNumber(dataList[2])
                transZ = extractNumber(dataList[3])
                rotX = extractNumber(dataList[4])
                rotY = extractNumber(dataList[5])
                rotZ = extractNumber(dataList[6])
                if transYes == 1:
                    mc.setAttr((objectName+'.translate'),float(transX),float(transY),float(transZ))
                if rotYes == 1:
                    mc.setAttr((objectName+'.rotate'),float(rotX),float(rotY),float(rotZ))

def extractNumber(data):
    match = re.search(r"-?\d+\.?\d*", data)
    if match:
        number = float(match.group())
    return number

posiPal()
