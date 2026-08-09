# -----------------------<About>-------------------------
# This script is designed to create corrective joints.
# 
#
# ---------------------<Important>-----------------------
# The script uses the quatNodes.mll plugin. Make sure it 
# is enabled in Maya plugins.
#
# --------------------<How to use>-----------------------
# Quick way: 
# select two joints and press the "Create corrective joints" button.  
#
# The way with adjustments:
# select two joints and press the "Fit" button.
# Turn on the checkboxes on the joints you want (w, s, a, d, Average)
#
# Adjust joint displacement and reaction strength using 
# corresponding float fields.
# If the "Fit rig" is created in the wrong axis, change
# the "Forward axis" menu item.
# Set "Use driven key" flag to be able to adjust reaction curve.
# Set the "Hip mode" flag to create joints at the hip or 
# wrist, where the axes of the selected bones may be different.
#
# Select the visible element of the system and press "Delete" 
# if you want to delete it.
# 
# There are two modes "Joints" and "Blendshapes". The "Joints"
# mode is for creating corrective joints. The "Blendshapes" mode 
# only creates a helper system to connect the blendshapes.
# 
# ------------------<Installiation>----------------------
# Place script to your "C:\Users\User\Documents\maya\scripts" foulder. 
# Put code below to a shelf:
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''
# Python 2 shelf button

import mxgdn_corrective_joints
reload(mxgdn_corrective_joints)
mxgdn_corrective_joints.IB()



#Python 3 shelf button

import mxgdn_corrective_joints
import imp
imp.reload(mxgdn_corrective_joints)
mxgdn_corrective_joints.IB()
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''
# Rum from MEL area
# python("import mxgdn_inbetween_joints; reload(mxgdn_inbetween_joints); mxgdn_corrective_joints.IB()") 
# -------------------<Version history>-------------------
# mxgdn_corrective_joints v001 
# - Start version
# -----------------------<Author>------------------------
# m.poklonov(a)gmail.com


from maya import cmds as mc
from maya import OpenMaya as om
import maya.api.OpenMaya as om2
import math


class IB (object):

    def __init__( self ):

        loadedPlugs = mc.pluginInfo( q=True, ls=True, l=True )
        if not 'quatNodes' in loadedPlugs:
            self.alert( 'Load plugins', 'The script uses the "quatNodes.mll" plugin. Please turn it on in Maya plugins.' )
            return


        # Define librarys
        self.fitRig_lib = {}
        self.p0_ib_lib = {}                             #self.p0_ib_lib.keys()
        self.p1_ib_lib = {}                             #self.p1_ib_lib.keys()
        self.p0_sets_lib = {}
        self.p1_sets_lib = {}

        # Variables
        self.name = ['']
        self.prefix = None
        self.bones = None
        self.symBones = None
        self.geo = None

        # Config
        self.ib_offset = 1                              # Default offset of ib locators
        self.ib_react = 2.0                             # Default move reaction value
        self.jntRad = 1                                 # Default joint radius
        self.avg_offset = .01                           # Average joint offset to avoid troubles with skin mirroring
        self.remapAxis = (0,1)                          # Forward axis = x, upnode axis = y 
        self.mirrorAxis = ['x', 'X', 0]                 # Means mirror axis is "x" or "X" or "0"
        self.hipMode = False                            # Mode when "name_ib_ori1_loc" aligned to second bone
        self.buttonColor = [(.36,.36,.36), (.5,.5,.3) ] # Button's "on" and "over" color

        self.searchPatterns = [ ('l', 'r'),
                              ('L', 'R'),
                              ('left', 'right'),
                              ('Left', 'Right')]        # Opposite bones searching patterns


        # UI window
        winWidth = 290
        mainWin = "correctiveJoins"

        if mc.window( mainWin, exists=True ):
            mc.deleteUI( mainWin, window=True )

        mc.window( mainWin, title="Corrective joins.", s=0, mxb=0 )
        mc.window( mainWin, edit=True, wh = (300, 116), rtf=True )

        # Main layout
        main = mc.columnLayout()
        mc.columnLayout( main, e=1, co = ("right", 4) )
        mc.columnLayout( main, e=1, co = ("left", 5) )

        # Input fields
        mc.text( h = 4, l="" )
        mc.rowLayout( numberOfColumns=4 )
        self.geo_btn = mc.button( w=30, h=18, l="Geo", c = self.on_geo_btn_pressed )
        mc.text( w=45, l="Name" )
        self.name_txtf = mc.textField( w=110)
        self.mode_om = mc.optionMenu( w=95, cc = self.on_mode_changed )
        mc.menuItem( label='Joints' )
        mc.menuItem( label='Blendshape' )
        mc.setParent( '..' )

        # WSAD settings
        mc.text( h = 4, l="" )
        mc.rowLayout( numberOfColumns=9 )
        self.w_chBox=mc.checkBox( w=32, label='W', v=1, cc = self.on_checkBox_changed )
        self.s_chBox=mc.checkBox( w=32, label='S', v=1, cc = self.on_checkBox_changed )
        self.a_chBox=mc.checkBox( w=32, label='A', v=1, cc = self.on_checkBox_changed )
        self.d_chBox=mc.checkBox( w=32, label='D', v=1, cc = self.on_checkBox_changed )
        self.avg_chBox=mc.checkBox( w=40, label='Avg',v=0, cc = self.on_checkBox_changed )
        mc.text( w=13, l="" )
        self.fit_btn = mc.button( w=30, h=18, l="Fit", c = self.on_fit_btn_pressed )
        self.ibOffset_ffld = mc.floatField( w = 30, pre=2, en=False, dc = self.on_ibOffset_ffld_changed, cc = self.on_ibOffset_ffld_changed )
        self.ibMove_ffld = mc.floatField(w = 30, pre=2, en=False, dc = self.on_ibMove_ffld_chahged, cc = self.on_ibMove_ffld_chahged )
        mc.setParent( '..' )

        # Additional settings
        mc.text( h = 4, l="" )
        mc.rowLayout( numberOfColumns=5 )
        self.useDKey_chBox=mc.checkBox( w=100, label='Use driven key', v=1 )
        self.hipMode_chBox=mc.checkBox( w=75, label='Hip mode ', v=0 )
        mc.text( w=19, l="" )
        mc.text( w=45, l="Fwd axis" )
        self.fwdAx_om = mc.optionMenu( w=40)#, cc = self.on_mode_changed )
        mc.menuItem( label='X' )
        mc.menuItem( label='Y' )
        mc.menuItem( label='Z' )
        mc.setParent( '..' )

        # Create button
        mc.text (h = 5, l = "")
        mc.rowLayout( numberOfColumns=2 )
        self.create_btn = mc.button( w=237, h=28, l="Ceate corrective joints", c = self.on_create_btn_pressed )
        self.deleteSys_btn = mc.button( w=48, h=28, l="Delete", c = self.on_deleteSys_btn_pressed )
        mc.setParent( '..' )
        mc.text (h = 5, l = "")

        mc.showWindow (mainWin)

        # on window open events
        self.on_geo_btn_pressed()
        mc.floatField( self.ibMove_ffld, e=True, v=self.ib_react )

    ### Events ###

    # On geo_btn pressed
    def on_geo_btn_pressed( self, *srgs ):
        geo = mc.filterExpand( sm = 12 )
        if geo:
            self.geo = geo[0]
            self.info( 'Geometry {0} selected.'.format( geo[0] ) )
            mc.button( self.geo_btn, e=True, bgc=self.buttonColor[1] )
        else:
            self.geo = None
            #self.info( '*Select geometry.' )
            mc.button( self.geo_btn, e=True, bgc=self.buttonColor[0] )




    # On mode changed
    def on_mode_changed( self, *args ):
        val = mc.optionMenu( self.mode_om, q=True, v=True )
        if 'Blendshape' in val:
            mc.checkBox( self.avg_chBox, e=True, en=False )
            mc.checkBox( self.avg_chBox, e=True, v=False )
        else:
            mc.checkBox( self.avg_chBox, e=True, en=True )

    # Om fit_btn pressed
    def on_fit_btn_pressed( self, *args ):


        if mc.objExists( 'FitRig_Ib_grp' ):
            mc.delete( 'FitRig_Ib_grp' )

            mc.floatField( self.ibOffset_ffld, e=True, v=self.ib_offset )
            mc.floatField( self.ibMove_ffld, e=True, v=self.ib_react )

            mc.floatField( self.ibOffset_ffld, e=True, en=False )
            mc.floatField( self.ibMove_ffld, e=True, en=False )
            mc.button( self.fit_btn, e=True, bgc=self.buttonColor[0] )
            return

        if self.getSelection():

            self.getName()
            self.fitRig()
            mc.floatField( self.ibOffset_ffld, e=True, en=True )
            mc.floatField( self.ibMove_ffld, e=True, en=True )
            mc.button( self.fit_btn, e=True, bgc=self.buttonColor[1] )

            mc.floatField( self.ibOffset_ffld, e=True, v=self.ib_offset )
            mc.floatField( self.ibMove_ffld, e=True, v=self.ib_react )


    # On ibOffset_ffld changed
    def on_ibOffset_ffld_changed( self, *args ):

        self.ib_offset = val = mc.floatField( self.ibOffset_ffld, q=True, v=True )

        wsad = self.fitRig_lib[ 'WSAD' ]
        if val>0.0:
            [ mc.setAttr( x+'.moveOffset', val ) for x in wsad ]
        else:
            mc.floatField( self.ibOffset_ffld, e=True, v=0 )


    # On ibMove_ffld changed
    def on_ibMove_ffld_chahged( self, *args ):

        self.ib_react = val = mc.floatField( self.ibMove_ffld, q=True, v=True )

        offset_grp = self.fitRig_lib[ 'MoveOffsetCir' ]
        if val>=0.0:
            mc.setAttr( offset_grp+'.moveReact', val )
        else:
            mc.floatField( self.ibMove_ffld, e=True, v=0 )


    # On checkBox changed
    def on_checkBox_changed( self, *args ):
        # self.fitRig_lib.keys()

        val1 = mc.checkBox( self.w_chBox, q=True, v=True )
        val2 = mc.checkBox( self.s_chBox, q=True, v=True )
        val3 = mc.checkBox( self.a_chBox, q=True, v=True )
        val4 = mc.checkBox( self.d_chBox, q=True, v=True )
        val5 = mc.checkBox( self.avg_chBox, q=True, v=True )
        val_arr = [ val1, val2, val3, val4, val5 ]

        if len(self.fitRig_lib)>0:
            arr = [x for x in self.fitRig_lib['WSAD']]
            arr.append( self.fitRig_lib['Avg'] )
            [ mc.setAttr( arr[x]+'.v', val_arr[x] ) for x in range(5) if mc.objExists( arr[x] ) ]


    # On create_btn pressed
    def on_create_btn_pressed( self, *args ):

        if mc.objExists( 'FitRig_Ib_grp' ):
            mc.delete( 'FitRig_Ib_grp' )

            mc.floatField( self.ibOffset_ffld, e=True, en=False )
            mc.floatField( self.ibMove_ffld, e=True, en=False )
            mc.button( self.fit_btn, e=True, bgc=self.buttonColor[0] )
            mc.floatField( self.ibOffset_ffld, e=True, v=self.ib_offset )
            mc.floatField( self.ibMove_ffld, e=True, v=.0 )
            #mc.button( self.geo_btn, e=True, bgc=self.buttonColor[0] )
            #self.geo = None

        if not self.bones:
            if not self.getSelection():
                pass
                return False

        if not self.getName():
            pass
            return False

        self.createSystem()
        # Connecting Angle and WSAD Systems
        p0_drvNodes_arr = []
        self.connectAngleSystem( self.p0_ib_lib, self.bones )
        p0_drvNodes_arr.extend( self.connectWsadSystem( self.p0_ib_lib ) )
        self.p0_ib_lib['DrivenNodes'] = p0_drvNodes_arr
        if self.symBones:
            p1_drvNodes_arr = []
            self.connectAngleSystem( self.p1_ib_lib, self.symBones )
            p1_drvNodes_arr.extend( self.connectWsadSystem( self.p1_ib_lib ) )
            self.p1_ib_lib['DrivenNodes'] = p1_drvNodes_arr

        # Connect opposite inbetweens in "Blendshape" or "Joints" mode
        # self.p0_ib_lib.keys()
        # self.p0_ib_lib['AvgSys']
        if self.symBones:
            p0_avgLoc = self.p0_ib_lib['AvgSys'][2]
            p1_avgLoc = self.p1_ib_lib['AvgSys'][2]
            self.connectOpposite( [p0_avgLoc], [p1_avgLoc] )
        mode = mc.optionMenu( self.mode_om, q=True, v=True )
        if 'Blendshape' in mode:
            if self.symBones:
                p0_wsad = [x[0][4] for x in self.p0_ib_lib['WSAD'] if x ]
                p1_wsad = [x[0][4] for x in self.p1_ib_lib['WSAD'] if x ]
                self.connectOpposite( p0_wsad, p1_wsad )

                p0_wsad_x = [x[0][4] for x in self.p0_ib_lib['WSAD_X'] if x ]
                p1_wsad_x = [x[0][4] for x in self.p1_ib_lib['WSAD_X'] if x ]
                self.connectOpposite( p0_wsad_x, p1_wsad_x )

        if 'Joints' in mode:
            self.createIbJoints()
            if self.symBones:
                p0_wsad_jnt = [x for x in self.p0_ib_lib['WSADJoints'] if self.p0_ib_lib['WSADJoints'] ]
                p1_wsad_jnt = [x for x in self.p1_ib_lib['WSADJoints'] if self.p1_ib_lib['WSADJoints'] ]
                self.connectOpposite( p0_wsad_jnt, p1_wsad_jnt )

                p0_wsad_x_jnt = [x for x in self.p0_ib_lib['WSAD_XJoint'] if x ]
                p1_wsad_x_jnt = [x for x in self.p1_ib_lib['WSAD_XJoint'] if x ]
                self.connectOpposite( p0_wsad_x_jnt, p1_wsad_x_jnt )

        self.hideAndLock()
        self.organizeSets()
        self.delAttr()

        # Clear variables
        self.fitRig_lib = {}
        self.p0_ib_lib = {}
        self.p1_ib_lib = {}
        self.name = ""
        self.prefix = None
        self.bones = None
        self.symBones = None
        mc.textField( self.name_txtf, e=True, tx='' )

    # Delete sys
    def on_deleteSys_btn_pressed( self, *args ):
        sel = mc.ls( sl=1 )[0]
        if mc.objExists( sel+'.delString' ):
            attr = mc.getAttr( sel+'.delString' )
            split_string = attr.split(';')
            mc.select( cl=True )
            [mc.select(x,add=1) for x in split_string if mc.objExists( x )]
            mc.delete()

            grp = 'Corrective_joints_system_grp'
            if mc.objExists( grp ) and not mc.listRelatives( grp ):
                 mc.delete( grp )
        else:
            self.info( 'Select any corrective joints element' )



    # Get selection, try to find symmetrical joints, define global vars
    def getSelection( self ):
        # get selection
        sel = mc.ls(sl=1)
        if len( sel ) == 2 and mc.nodeType( sel[0] ) == 'joint' and mc.nodeType( sel[1] ) == 'joint':

            # get bones selection 
            self.bones = sel
            self.symBones = self.findSymJoints()
            self.jntRad = mc.getAttr( self.bones[1]+'.radius')

            # if geometry specifyed get closest point to get ib_joint offset
            if self.geo:
                posA = mc.xform( self.bones[1],q=1,t=1,ws=1)
                posB = self.closestPointMesh(self.geo,posA)[1]
                self.ib_offset = math.sqrt((posA[0]-posB[0])**2+(posA[1]-posB[1])**2+(posA[2]-posB[2])**2)
        else:
            self.info( 'Select two joints.' )
            return False

        self.getAxis()        # returns self.remapAxis
        return True


    def getName( self ):
        # set name
        nameString = mc.textField (self.name_txtf, q = 1, tx = 1)
        if nameString =='':
            if self.prefix[0] !='M':
                if self.symBones:
                    self.name = [ self.bones[1], self.symBones[1] ]
                else:
                    self.name = [ self.bones[1], None ]
            else:
                self.name = [self.bones[1], None] 
        else:
            if self.prefix[0] !='M':
                if self.symBones:
                    self.name = [ nameString+'_'+self.prefix[0], nameString+'_'+self.prefix[1] ]
                else:
                    self.name = [ nameString+'_'+self.prefix[0], None ]
            else:
                self.name = [ nameString+'_'+self.prefix[0], None ]

        # check for name exists
        for nm in self.name:
            # nm=self.name[0]
            if mc.objExists( '{0}_ib_offset_grp'.format( nm ) ):
                self.alert( 'Naming error', 'Name "{0}" already exists.'.format(nm) )
                return False
            else:
                return True



    ### Service FN ###

    # DisplayMessage
    def error( self, msg, *args ):
        mc.inViewMessage( amg='{0}'.format(msg), pos='botCenter', fade=True )
        om.MGlobal.displayError( "{0}".format( msg ) )

    def info( self, msg, *args ):
        mc.inViewMessage( amg='<hl>{0}</hl>'.format( msg), pos='botCenter', fade=True )
        om.MGlobal.displayInfo( "{0}".format( msg ) )

    def alert( self, t, msg, *args ):
        mc.confirmDialog( title = t, message = msg )

    # Get start jnt side
    def getSide( self ):

        tol = .01
        pos = mc.xform( self.bones[1], q=True, t=True, ws=True )

        if pos[self.mirrorAxis[2]] < 0 :
            self.mirrorPrefix = "right"
            prefix0 = "R"
            prefix1 = "L"

        if pos[self.mirrorAxis[2]] > 0:
            self.mirrorPrefix = "left"
            prefix0 = "L"
            prefix1 = "R"

        if pos[self.mirrorAxis[2]] > 0-tol and pos[self.mirrorAxis[2]] < 0+tol:
            self.mirrorPrefix = "single"
            prefix0 = "M"
            prefix1 = None

        self.prefix = [prefix0, prefix1]


    # Find symmetry joints
    def  findSymJoints( self, *args ):

        def getOppositePos( obj ):
            # obj = self.bones[0]
            tmp_loc = mc.spaceLocator()[0]
            mc.xform( tmp_loc, t=mc.xform(obj,q=1,ws=1,t=1) )
            self.mirror(tmp_loc)
            tmpPos = mc.xform( tmp_loc, q=True, ws=True, t=True )
            mc.delete( tmp_loc )
            return tmpPos

        def comparePos( position1, position2 ):
            # position1, position2 = pos1,pos2
            mPoint1 = om2.MPoint( position1 )
            mPoint2 = om2.MPoint( position2 )
            if om2.MPoint.isEquivalent( mPoint1, mPoint2, tolerance=.05 )==False:
                return None
            else:
                return True

        def searchSymName( name, index ):
            # name, index = bn, ind

            splitString = name.split( '_' )

            for ptrn in self.searchPatterns:
                # ptrn = self.searchPatterns[0]
                ptrnPos = [x for x in range(len(splitString)) if splitString[x]==ptrn[index[0]]]

                if len(ptrnPos)>0:
                    p = ptrnPos[0]
                    splitString[p] = ptrn[index[1]]

                    newString = ''
                    for i in range(len(splitString)):
                        # i=0
                        newString += splitString[i]
                        if i != len(splitString)-1:
                            newString += '_'
                    return newString
            return False
        # tmp = searchSymName( bn, ind )



        self.getSide()  # returns self.prefix

        # get side left or right
        if self.prefix[0] == 'L':
            ind = (0,1)
        elif self.prefix[0] == 'R':
            ind = (1,0)
        else:
            # have middle joint
            self.symBones = None
            return None

        # try to find symmetry joints
        symBones_arr = []
        for bn in self.bones:
            # bn = self.bones[1]
            symName = searchSymName( bn, ind )
            if symName and mc.objExists( symName ):
                symBones_arr.append( symName )
            else:
                pos1 = mc.xform( bn, q=True, t=True, ws=True )
                pos2 = getOppositePos( bn )
                if comparePos( pos1,pos2 ):
                    symBones_arr.append( bn )

        # if symmetry joints found try to check if their positions are symmetry too
        if len( symBones_arr )!=2:
            # have no symmetry joints
            self.info( 'Symmetrical joints are not found.' )
            self.symBones = None
            return None
        else:
            for i in range(2):
                # i=1
                pos1 = getOppositePos( self.bones[i] )
                pos2 = mc.xform( symBones_arr[i], q=True, ws=True, t=True )
                if not comparePos( pos1,pos2 ):
                    self.symBones = None
                    self.info( 'Symmetrical joints are found, but their positions do not match.' )
                    return None
            self.info( 'Symmetrical joints found.' )
            return symBones_arr



    # Rename
    def rename( self, nm, rem, rep, *args ):
        # nm, rem, rep = bn, '', [ p[ind[0]], p[ind[1]] ]
        # self.rename(bn, '', [ p[ind[0]], p[ind[1]] ])

        if rem != '':
            splitString = nm.rpartition( rem )
            if splitString[1]:
                nm = splitString[0] + splitString[2]
                #nm.replace( rem,'' )
                return nm

        if rep[0] != '':
            splitString = nm.rpartition( rep[0] )
            if splitString[1]:
                nm = splitString[0] + rep[1] + splitString[2]
                #nm.replace( rep[0], rep[1] )
                return nm
        return ''
        '''
        tst = bn.partition( 'l_' )
        tst = bn.startswith( 'l_' )
        tst = bn.endswith( '_l' )
        '''


    # Align
    def align( self, *args ): # source, source..., target
        #args = [jawOriA_loc[0], jawOriB_loc[0], jawOriTmp_loc[0]]
        for i in range(len(args)-1):
            #i = 0
            parentConstr = mc.parentConstraint( args[len(args)-1], args[i], mo = False )
            mc.delete( parentConstr )
        return True


    # Remapeg axis align
    def remapedAlign( self, *args ): # source, source..., target
        # args = zero_grp, bones[1]

        ax = self.remapAxis

        # create vector helper
        vectors_loc = mc.spaceLocator()[0]
        x_loc = mc.spaceLocator()[0]
        y_loc = mc.spaceLocator()[0]
        z_loc = mc.spaceLocator()[0]
        mc.parent( x_loc, y_loc, z_loc, vectors_loc )
        mc.setAttr( x_loc + '.tx', 1 )
        mc.setAttr( y_loc + '.ty', 1 )
        mc.setAttr( z_loc + '.tz', 1 )
        vectors_arr = [x_loc,y_loc,z_loc]

        self.align( vectors_loc, args[-1] )

        # create axis helper
        axis_loc = mc.spaceLocator()[0]
        self.align( axis_loc, args[-1] )
        mc.aimConstraint( vectors_arr[ax[0]], axis_loc, aim=(1,0,0), u=(0,1,0), wut='object', wuo=vectors_arr[ax[1]] )

        [self.align(x,axis_loc) for x in args if x!=args[-1]]

        mc.delete( [vectors_loc, axis_loc] )


    # Snap
    def snap (self, *args): # source, source..., target
        for i in range(len(args)-1):
            #i = 0
            pos = mc.xform(args[len(args)-1], q = True, ws = True, t = True)
            rpA = mc.xform(args[len(args)-1], q = True, rp = True)
            rpB = mc.xform(args[len(args)-1], q = True, rp = True)
            mc.xform(args[i], ws = True, t = ((pos[0] + rpA[0] - rpB[0] ), (pos[1] + rpA[1] - rpB[1]), (pos[2] + rpA[2] - rpB[2])))
        return True


    # Override color
    def color( self, index, *args ):
        for a in args:
            shape = self.shapes(a)
            mc.setAttr( '{0}.overrideEnabled'.format(shape[0]), True )
            mc.setAttr( '{0}.overrideColor'.format(shape[0]), index )
        return True


    # Get shape node
    def shapes( self, obj ):
        shapes = ( mc.listRelatives( obj, shapes = True ) )
        return shapes


    # Set locks
    def setLocks( self, sourceObj, vis = 1, posLock = (1,1,1), rotLock = (1,1,1), scLock = (1,1,1), visLock = 1 ):

        posLock = (posLock,posLock,posLock) if posLock==1 or posLock==0 else posLock
        rotLock = (rotLock,rotLock,rotLock) if rotLock==1 or rotLock==0 else rotLock
        scLock = (scLock,scLock,scLock) if scLock==1 or scLock==0 else scLock

        arr = range(10)
        True if len(arr)!=0 else False
     
        # sourceObj = 'lips_lipU1_guide'
        mc.setAttr( sourceObj + '.v', vis)
        mc.setAttr( sourceObj + '.tx', l = posLock[0], k = 1-posLock[0], cb = 0 )
        mc.setAttr( sourceObj + '.ty', l = posLock[1], k = 1-posLock[1], cb = 0 )
        mc.setAttr( sourceObj + '.tz', l = posLock[2], k = 1-posLock[2], cb = 0 )
        mc.setAttr( sourceObj + '.rx', l = rotLock[0], k = 1-rotLock[0], cb = 0 )
        mc.setAttr( sourceObj + '.ry', l = rotLock[1], k = 1-rotLock[1], cb = 0 )
        mc.setAttr( sourceObj + '.rz', l = rotLock[2], k = 1-rotLock[2], cb = 0 )
        mc.setAttr( sourceObj + '.sx', l = scLock[0], k = 1-scLock[0], cb = 0 )
        mc.setAttr( sourceObj + '.sy', l = scLock[1], k = 1-scLock[1], cb = 0 )
        mc.setAttr( sourceObj + '.sz', l = scLock[2], k = 1-scLock[2], cb = 0 )
        mc.setAttr( sourceObj + '.v', l = visLock, k = 1-visLock, cb = 0 )
        return True


    # Mirror objects
    def mirror( self, obj ):
        # obj = zero_grp
        axis = self.mirrorAxis[0]

        mirror_grp = mc.group( obj )
        mc.xform( mirror_grp, os = True, piv = ( 0, 0, 0 ) )
        mc.setAttr( mirror_grp + '.s'+ axis, -1 )

        mc.ungroup( mirror_grp )
        return obj


    def closestPointMesh( self, mesh, pos ):     # ( mesh, pos = edges[0].rpartition( '.' )[0], pos )
        shapes = self.shapes( mesh )
        shape  = [x for x in shapes if not 'Orig' in x][0]

        cpm_nod = mc.createNode( 'closestPointOnMesh' )
        mc.connectAttr( shape +'.outMesh', cpm_nod +'.inMesh' )
        mc.setAttr( cpm_nod +'.inPosition', pos[0], pos[1], pos[2] )

        vtxIndex = mc.getAttr( cpm_nod +'.closestVertexIndex' )
        vtx = mesh +'.vtx[{0}]'.format( vtxIndex )
        pos = mc.xform( vtx, q=True, t=True, ws=True )

        mc.delete( cpm_nod )

        return [vtx, pos]


    # Create groups
    def groups( self, obj, nm, num, *args ):
        # obj, nm, num = w_loc, name+'_w', 0

        return_arr = []
        mc.select( cl = True )
        return_arr.append( obj )

        if num == 0:
            offset_grp = mc.group( em = True, n = "{0}_offset_grp".format( nm ) )
            zero_grp = mc.group( em = True, n = "{0}_zero_grp".format( nm ) )
            self.align( offset_grp, obj )
            self.align( zero_grp, obj )
            return_arr.append( zero_grp )
            return_arr.append( offset_grp )
            mc.parent( obj, zero_grp)
            mc.parent( zero_grp, offset_grp)
        else:
            for i in range( num-1, -1, -1 ):
                if i == num-1:
                    trns_grp = mc.group( em = True, n = "{0}_zero_grp".format( nm ) )
                    mc.xform( trns_grp, ws = True, piv = ( 0, 0, 0 ) )
                    return_arr.append( trns_grp )
                if i >= 0:
                    trns_grp = mc.group( return_arr[-1], n = "{0}_trns{1}_grp".format( nm, i ) )
                    mc.xform( trns_grp, ws = True, piv = ( 0, 0, 0 ) )
                    return_arr.append( trns_grp )

            base_grp = mc.group( return_arr[-1], n = "{0}_offset_grp".format( nm ) )
            return_arr.append( base_grp )
            self.align( base_grp, obj )
            mc.parent( obj, return_arr[1] )

        return return_arr[::-1] # ['offset_grp', 'trns0_grp', 'trns1_grp', 'trns2_grp', 'trns3_grp', 'zero_grp', 'locator1']


    # Matrix parent
    def mtxParent( self, t, r, s, mo, pi, *args ): # source, source..., target
        # t, r, s, mo, pi, args = 1, 1, 1, 1, 1, [ 'locator1', 'joint_3_R']

        sel = [x for x in args]

        # get objects
        parent = sel[-1]; sel.pop(-1)
        chld_arr = sel

        for c in chld_arr:
            #c=chld_arr[0]
            nam = c.split('_')[-1]

            # create nodes
            parentMtx_nod = mc.createNode('multMatrix', n=nam+'_parentMultMtx' )
            decomposeMtx_nod = mc.createNode('decomposeMatrix', n = nam+'_decomposeMtx' )

            # connect attr
            mc.connectAttr( parent + '.worldMatrix', parentMtx_nod+'.matrixIn[1]' )
            mc.connectAttr( parentMtx_nod + '.matrixSum', decomposeMtx_nod + '.inputMatrix' )

            # if Maintain Offset flagged
            if mo:
                offsetMtx_nod = mc.createNode( 'multMatrix', n=nam+'_offset_multMatrix' )
                mc.connectAttr( c+'.worldMatrix', offsetMtx_nod+'.matrixIn[0]' )
                mc.connectAttr( parent + '.worldInverseMatrix', offsetMtx_nod+'.matrixIn[1]' )
                offset = mc.getAttr( offsetMtx_nod+'.matrixSum' )
                mc.setAttr( parentMtx_nod+'.matrixIn[0]', offset, type='matrix')
                mc.delete( offsetMtx_nod )

            # if Parent Inverse flagged
            if pi:
                mc.connectAttr( c + '.parentInverseMatrix', parentMtx_nod + '.matrixIn[2]' )

            # if Translate flagged
            if t:
                mc.connectAttr(decomposeMtx_nod + '.outputTranslate', c + '.t')

            # if Rotate flagged
            if r:
                if mc.objectType( c ) == 'joint': 
                    eulerOrient_nod = mc.createNode( 'eulerToQuat', n = nam + '_orient_eulerToQuat' )
                    invertQuat_nod = mc.createNode( 'quatInvert', n = nam + '_point_quatInvert' )
                    eulerRotate_nod = mc.createNode( 'quatToEuler', n = nam + '_rotate_quatToEuler' )
                    quatProd_nod = mc.createNode( 'quatProd', n = nam + '_point_quatProd' )

                    mc.connectAttr( c + '.jointOrient', eulerOrient_nod + '.inputRotate' )
                    mc.connectAttr( eulerOrient_nod +'.outputQuat', invertQuat_nod + '.inputQuat' )
                    mc.connectAttr( decomposeMtx_nod + '.outputQuat', quatProd_nod + '.input1Quat' )
                    mc.connectAttr( invertQuat_nod + '.outputQuat', quatProd_nod +'.input2Quat' )
                    mc.connectAttr( quatProd_nod + '.outputQuat', eulerRotate_nod + '.inputQuat' )
                    mc.connectAttr( eulerRotate_nod + '.outputRotate',c + '.r' )
                else:
                    mc.connectAttr( decomposeMtx_nod + '.outputRotate', c + '.r' )

            # if Scale flagged
            if s:
                mc.connectAttr(decomposeMtx_nod + '.outputScale', c + '.s')




    ### Creation FN ###


    def getAxis( self ):

        ax = mc.optionMenu( self.fwdAx_om, q=True, v=True )

        if ax == 'X':
            fwdAxis = 0
            secAxis = 1

        if ax == 'Y':
            fwdAxis = 1
            secAxis = 0

        if ax == 'Z':
            fwdAxis = 2
            secAxis = 0

        self.remapAxis = [fwdAxis, secAxis]
        return [fwdAxis, secAxis]  



    def fitRig( self ):

        def fit( name, suf, rx, sz, vis ):
            # name, suf, rx, sz, vis = name, 'Avg', 0, 0, ib[4]

            loc = mc.spaceLocator( n=name+'_'+suf+'_fit' )[0]
            loc_shp = self.shapes( loc )[0]
            loc = self.groups( loc, name+'_'+suf+'_fitRig', 2 )
            mc.setAttr( loc[4]+'.localScale', self.jntRad/2, self.jntRad/2, self.jntRad/2 )
            mc.setAttr( loc[0]+'.rx', rx )
            self.color( 6, loc[4] )

            # create visible attr
            mc.addAttr( loc[4], ln="moveOffset", at="double", min=.0 ); mc.setAttr( loc[4]+".moveOffset", k=False )
            mc.setAttr( loc[4]+".moveOffset", sz )

            mc.connectAttr( loc[4]+'.moveOffset', loc[2]+'.ty' )

            label = mc.createNode( 'annotationShape', n=name+'_'+suf+'_lblShape'  )
            lblTrns_nod = mc.listRelatives( label, p=1 )[0]
            mc.setAttr( label+'.displayArrow', 0 )
            mc.setAttr( label+'.text', suf, type='string' )
            self.color( 6, lblTrns_nod )
            mc.parent( lblTrns_nod, loc[4], r=1 )
            #mc.connectAttr( loc[4]+'.worldPosition[0]', lblTrns_nod+'.t' )

            self.setLocks( loc[4], visLock=0 )
            self.setLocks( lblTrns_nod )
            mc.setAttr( loc[4]+'.v', vis )

            return [loc, suf]


        name = self.name[0]
        root = mc.ls( self.bones[1], l=1 )[0].split ('|')[1]

        w = mc.checkBox( self.w_chBox, q=True, v=True )
        s = mc.checkBox( self.s_chBox, q=True, v=True )
        a = mc.checkBox( self.a_chBox, q=True, v=True )
        d = mc.checkBox( self.d_chBox, q=True, v=True )
        avg = mc.checkBox( self.avg_chBox, q=True, v=True )

        ib = [x for x in [w,s,a,d,avg]]

        ib_offset = self.ib_offset

        if not mc.objExists( 'Corrective_joints_system_grp' ):
            base_grp = mc.group( n='Corrective_joints_system_grp', em=True )
            mc.parent( base_grp, root )
        else:
            base_grp = 'Corrective_joints_system_grp'


        offset_grp = mc.group( n='FitRig_Ib_grp', em=True )
        zero_grp = mc.group( n=name+'_fit_zero_grp', em=True )
        wsad_grp = mc.group( n=name+'_fit_wsad_offset_grp', em=True )

        # create w s a d system
        w_fit = fit( name, 'W', 0, ib_offset, ib[0] )
        s_fit = fit( name, 'S', 180, ib_offset, ib[1] )
        a_fit = fit( name, 'A', 90, ib_offset, ib[2] )
        d_fit = fit( name, 'D', -90, ib_offset, ib[3] )
        avg_fit = fit( name, 'Avg', 0, 0, ib[4] )

        # create moveOffset display circle
        moveReact_crv = mc.circle( n=name+'_fit_moveOffset_cir', nr=(1,0,0), r=ib_offset )
        mc.addAttr( moveReact_crv[0], ln="moveReact", at="double", min=.0, dv=.0 )
        moveReactAdl_nod = mc.createNode( 'addDoubleLinear', n=name+'_fit_moveReact_adl' )
        mc.connectAttr( w_fit[0][4]+'.moveOffset', moveReactAdl_nod+'.input1' )
        mc.connectAttr( moveReact_crv[0]+'.moveReact', moveReactAdl_nod+'.input2' )
        mc.connectAttr( moveReactAdl_nod+'.output', moveReact_crv[1]+'.radius' )
        mc.setAttr( moveReact_crv[0]+'.moveReact', self.ib_react )

        #self.color( 6, moveReact_crv[0] )
        mc.setAttr( moveReact_crv[0]+'.overrideEnabled', 1 )
        mc.setAttr( moveReact_crv[0]+'.overrideDisplayType', 1 )
        self.setLocks( moveReact_crv[0] )

        # parenting
        mc.parent( moveReact_crv[0], wsad_grp )
        mc.parent( [x[0][0] for x in [w_fit, s_fit, a_fit, d_fit, avg_fit] if x], wsad_grp )
        mc.parent( wsad_grp, zero_grp )
        mc.parent( zero_grp, offset_grp )
        mc.parent( offset_grp, base_grp )

        # ilign objects
        self.align( offset_grp, self.bones[1] )
        self.remapedAlign( zero_grp, self.bones[1] )
        mc.parentConstraint( self.bones[1], offset_grp )

        self.fitRig_lib[ 'OffsetGrp' ] = offset_grp
        self.fitRig_lib[ 'WSAD' ] = [w_fit[0][4], s_fit[0][4], a_fit[0][4], d_fit[0][4]]
        self.fitRig_lib[ 'Avg' ] = avg_fit[0][4]
        self.fitRig_lib[ 'MoveOffsetCir' ] = moveReact_crv[0]



    def createSystem( self ):

        def wsad( ib, name, suf, rx ):
            # ib, name, suf, rx, = ib[4], name, 'Avg', 0
            if not ib:
                return None

            loc = mc.spaceLocator( n=name+'_'+suf+'_loc' )[0]
            loc = self.groups( loc, name+'_'+suf, 2 )
            mc.setAttr( loc[4]+'.localScale', self.jntRad/2, self.jntRad/2, self.jntRad/2 )
            mc.setAttr( loc[0]+'.rx', rx )
            if suf!='Avg':
                mc.setAttr( loc[2]+'.ty', self.ib_offset )
            else:
                mc.setAttr( loc[2]+'.ty', self.avg_offset )
            self.color( 6, loc[4] )

            # create visible attr
            if suf!='Avg':

                mc.addAttr( loc[4], ln="sepAngle", nn="____________________", at="enum", en="Angle", k=True )
                mc.addAttr( loc[4], ln="angleMin", at="double", min=.0, max=180, dv=0, k=True )
                mc.addAttr( loc[4], ln="angleMax", at="double", min=.0, max=180, dv=90, k=True )

                mc.addAttr( loc[4], ln="sepReact", nn="____________________", at="enum", en="React", k=True )
                mc.addAttr( loc[4], ln="reactionMove", at="double", dv=2.0, k=True )
                mc.addAttr( loc[4], ln="reactionRotate", at="double", dv=.0, k=True )
                mc.addAttr( loc[4], ln="reactionScale", at="double", dv=1.0, k=True )
                mc.addAttr( loc[4], ln="inverseBehaviour", at="enum", en="Direct:Invert", k=True )

                mc.addAttr( loc[4], ln="sepReactRev", nn="____________________", at="enum", en="React REV", k=True )
                mc.addAttr( loc[4], ln="reactionMoveRev", at="double", dv=.0, k=True )
                mc.addAttr( loc[4], ln="reactionRotateRev", at="double", dv=.0, k=True )
                mc.addAttr( loc[4], ln="reactionScaleRev", at="double", dv=1.0, k=True )

                mc.addAttr( loc[4], ln="sepOffset", nn="____________________", at="enum", en="Offset", k=True )
                mc.addAttr( loc[4], ln="moveOffset", at="double", min=.0, dv=1.0, k=True )
                mc.addAttr( loc[4], ln="rotOffset", at="double", dv=.0, k=True )

                mc.addAttr( loc[4], ln="sepInfo", nn="____________________", at="enum", en="Info", k=True )
                mc.addAttr( loc[4], ln="connectBS", at="double", k=True )
                mc.addAttr( loc[4], ln="connectBS_Rev", at="double", k=True )
                mc.addAttr( loc[4], ln="currentAngle", at="double", k=True )

                # create hidden attr
                mc.addAttr( loc[4], ln="currentMove", at="double", k=False )

                # set attr
                mc.setAttr( loc[4]+".moveOffset", self.ib_offset )
                mc.setAttr( loc[4]+".reactionMove", self.ib_react )
            else:
                mc.addAttr( loc[4], ln="moveOffset", at="double", min=.0, dv=1.0 ); mc.setAttr( loc[4]+".moveOffset", k=False, cb=True )
                mc.setAttr( loc[4]+".moveOffset", self.avg_offset )

            if suf == 'S' or suf == 'D':
                mc.setAttr( loc[4]+".inverseBehaviour", 1 )

            return [loc, suf]


        def createObjects( name, base_grp, ib, sym ):
            # name, base_grp, ib, sym = name[0], base_grp, ib, None
            # name, base_grp, ib, sym = name[1], base_grp, ib, True

            # create objects
            offset_grp = mc.group( n= name+'_ib_offset_grp', em=True )
            trns_grp = mc.group( n= name+'_ib_trns_grp', em=True )
            zero_grp = mc.group( n= name+'_ib_zero_grp', em=True )
            avg_grp = mc.group( n= name+'_ib_avg_grp', em=True )
            ang_grp = mc.group( n= name+'_ib_ang_grp', em=True )
            wsad_grp = mc.group( n= name+'_ib_wsad_offset_grp', em=True )

            # create ori locators
            ori1_loc = mc.spaceLocator( n=name+'_ib_ori1_loc' )[0]
            ori2_loc = mc.spaceLocator( n=name+'_ib_ori2_loc' )[0]
            avg_loc = mc.spaceLocator( n=name+'_ib_avg_loc' )[0]

            # create w s a d system
            w_loc = wsad( ib[0], name, 'W', 0 )
            s_loc = wsad( ib[1], name, 'S', 180 )
            a_loc = wsad( ib[2], name, 'A', 90 )
            d_loc = wsad( ib[3], name, 'D', -90 )
            x_loc = wsad( ib[4], name, 'Avg', 0 )

            # create vector system
            xVecAvg_loc = mc.spaceLocator( n=name+'_X_vec_avg_loc' )[0]
            xVec_loc = mc.spaceLocator( n=name+'_X_vec_loc' )[0]
            yVec_loc = mc.spaceLocator( n=name+'_Y_vec_loc' )[0]
            zVec_loc = mc.spaceLocator( n=name+'_Z_vec_loc' )[0]

            # parenting
            mc.parent( xVec_loc, xVecAvg_loc )
            mc.parent( xVecAvg_loc, yVec_loc, zVec_loc, ang_grp )
            mc.parent( [x[0][0] for x in [w_loc, s_loc, a_loc, d_loc, x_loc] if x], wsad_grp )
            mc.parent( wsad_grp, avg_loc )
            mc.parent( ori1_loc, ori2_loc, avg_loc, avg_grp )
            mc.parent( avg_grp, ang_grp, zero_grp )
            mc.parent( trns_grp, offset_grp )
            mc.parent( offset_grp, base_grp )

            mc.setAttr( xVec_loc+'.tx', 1 )
            mc.setAttr( yVec_loc+'.ty', 1 )
            mc.setAttr( zVec_loc+'.tz', 1 )

            # set size and color 
            mc.setAttr( avg_loc+'.localScale', self.jntRad*3, self.jntRad*3, self.jntRad*3 )
            [mc.setAttr(x+'.localScale', self.jntRad/2, self.jntRad/2, self.jntRad/2) for x in [xVecAvg_loc,xVec_loc,yVec_loc,zVec_loc] ]
            [mc.setAttr(x+'.localScale', self.jntRad, self.jntRad, self.jntRad) for x in [ori1_loc,ori2_loc] ]
            [self.color( 14, x ) for x in [xVecAvg_loc,xVec_loc,yVec_loc,zVec_loc]]
            [self.color( 14, x ) for x in [ori1_loc,ori2_loc,avg_loc]]

            # create attributes
            mc.addAttr( avg_loc, ln = "weight", at="double", dv=.5, min=.0, max=1.0, k = True )


            # plase objects
            self.align( offset_grp, self.bones[0] )
            self.snap( trns_grp, self.bones[1] )
            self.remapedAlign( zero_grp, self.bones[1] )

            # If hip mode enabled align angle system to second bone
            if mc.checkBox( self.hipMode_chBox, q=True, v=True ):
                self.remapedAlign( ori1_loc, self.bones[1] ); self.snap( ori1_loc, self.bones[1] )
            else:
                self.remapedAlign( ori1_loc, self.bones[0] ); self.snap( ori1_loc, self.bones[1] )

            if sym:
                self.align( offset_grp, self.symBones[0] )
                self.snap( trns_grp, self.symBones[1] )
                self.remapedAlign( zero_grp, self.bones[1] )

                # If hip mode enabled align angle system to second bone
                if mc.checkBox( self.hipMode_chBox, q=True, v=True ):
                    self.remapedAlign( ori1_loc, self.bones[1] ); self.snap( ori1_loc, self.bones[1] )
                else:
                    self.remapedAlign( ori1_loc, self.bones[0] ); self.snap( ori1_loc, self.bones[1] )

                self.mirror( zero_grp )
            mc.parent( zero_grp, trns_grp )

            # add to lib
            returnArr = []
            returnArr.append( [ offset_grp, trns_grp, zero_grp, avg_grp, ang_grp, wsad_grp ] ) # self.ib_lib['IbGroups']
            returnArr.append( [ ori1_loc, ori2_loc, avg_loc ] )                                # self.ib_lib['AvgSys']
            returnArr.append( [x for x in [w_loc,s_loc,a_loc,d_loc]] )                         # self.ib_lib['WSAD']
            returnArr.append( [x_loc] )                                                          # self.ib_lib['WSAD_X']
            returnArr.append( [ xVecAvg_loc, xVec_loc, yVec_loc, zVec_loc ] )                  # self.ib_lib['AngSys']

            return returnArr



        name = self.name
        root = mc.ls( self.bones[1], l=1 )[0].split ('|')[1]

        w = mc.checkBox( self.w_chBox, q=True, v=True )
        s = mc.checkBox( self.s_chBox, q=True, v=True )
        a = mc.checkBox( self.a_chBox, q=True, v=True )
        d = mc.checkBox( self.d_chBox, q=True, v=True )
        wsad_x = mc.checkBox( self.avg_chBox, q=True, v=True )

        ib = [x for x in [w,s,a,d,wsad_x]]


        ib_offset = self.ib_offset

        if not mc.objExists( 'Corrective_joints_system_grp' ):
            base_grp = mc.group( n='Corrective_joints_system_grp', em=True )
            mc.parent( base_grp, root )
            self.setLocks( base_grp, visLock=0 )
        else:
            base_grp = 'Corrective_joints_system_grp'

        # create system
        p0_obj_arr = createObjects( name[0], base_grp, ib, None )
        self.p0_ib_lib['IbGroups'] = p0_obj_arr[0] 
        self.p0_ib_lib['AvgSys'] = p0_obj_arr[1]
        self.p0_ib_lib['WSAD'] = p0_obj_arr[2]
        self.p0_ib_lib['WSAD_X'] = p0_obj_arr[3]
        self.p0_ib_lib['AngSys'] = p0_obj_arr[4]

        if self.symBones:
            p1_obj_arr = createObjects( name[1], base_grp, ib, True )
            self.p1_ib_lib['IbGroups'] = p1_obj_arr[0] 
            self.p1_ib_lib['AvgSys'] = p1_obj_arr[1]
            self.p1_ib_lib['WSAD'] = p1_obj_arr[2]
            self.p1_ib_lib['WSAD_X'] = p1_obj_arr[3]
            self.p1_ib_lib['AngSys'] = p1_obj_arr[4]
            [mc.setAttr( x[0][4]+'.sz',-1 )  for x in self.p1_ib_lib['WSAD'] if x]


    def connectAngleSystem( self, lib, bones ):
        # lib, bones = self.p0_ib_lib, self.bones
        # lib, bones = self.p1_ib_lib, self.symBones

        # prepare vars  
        offset_grp = lib['IbGroups'][0]
        trns_grp = lib['IbGroups'][1]
        zero_grp = lib['IbGroups'][2]
        ang_grp = lib['IbGroups'][4]
        ori1_loc = lib['AvgSys'][0]
        ori2_loc = lib['AvgSys'][1]
        avg_loc = lib['AvgSys'][2]
        xVecAvg_loc = lib['AngSys'][0]

        # connect base objects
        self.mtxParent( 1, 1, 1, 1, 1, offset_grp, bones[0] ) # t,r,s,mo, parentInv, source, source..., target
        self.mtxParent( 1, 0, 0, 1, 1, trns_grp, bones[1] )
        self.mtxParent( 0, 1, 0, 1, 1, ori2_loc, bones[1] )

        # connect avg sys
        avgSys_pairBlend_nod = mc.createNode( 'pairBlend', n=avg_loc.replace( '_avg_loc','_avg_pairBlend' ) )
        mc.connectAttr( ori1_loc+'.r', avgSys_pairBlend_nod+'.inRotate2' )
        mc.connectAttr( ori2_loc+'.r', avgSys_pairBlend_nod+'.inRotate1' )
        mc.connectAttr( avgSys_pairBlend_nod+'.outRotate', avg_loc+'.r' )
        mc.connectAttr( avg_loc+'.weight', avgSys_pairBlend_nod+'.weight' )

        # connect ang sys
        angSys_pairBlend_nod = mc.createNode( 'pairBlend', n=avg_loc.replace( '_avg_loc','_ang_pairBlend' ) )
        mc.connectAttr( ang_grp+'.r', angSys_pairBlend_nod+'.inRotate2' )
        mc.connectAttr( ori2_loc+'.r', angSys_pairBlend_nod+'.inRotate1' )
        mc.connectAttr( angSys_pairBlend_nod+'.outRotate', xVecAvg_loc+'.r' )

        mc.setAttr( avgSys_pairBlend_nod+'.rotInterpolation', 1 )
        mc.setAttr( angSys_pairBlend_nod+'.rotInterpolation', 1 )
        mc.setAttr( angSys_pairBlend_nod+'.weight', .5 )




    def connectWsadSystem( self, lib ):
        # lib = self.p0_ib_lib
        # lib = self.p1_ib_lib

        def connectWsad( item, angle_nod ):
            # item, angle_nod = wsad[0], yVecAng_nod
            # item, angle_nod = item, yVecAng_nod
            return_arr = []

            offset_grp = item[0][0]
            trns0_grp = item[0][1]
            trns1_grp = item[0][2]
            zero_grp = item[0][3]
            loc = item[0][4]
            nm = item[1]

            # create nodes
            range180_nod = mc.createNode( 'setRange', n=loc.replace( '_loc', '_range_to_180' ) )
            angUnit_nod = mc.createNode( 'unitConversion', n=loc.replace( '_loc', '_ang_unit' ) ); mc.setAttr( angUnit_nod+'.conversionFactor', 57.29577951308232 )
            valInvertUnit_nod = mc.createNode( 'unitConversion', n=loc.replace( '_loc', '_val_invert_unit' ) ); mc.setAttr( valInvertUnit_nod+'.conversionFactor', -1 )
            trueAngDl_nod = mc.createNode( 'addDoubleLinear', n=loc.replace( '_loc', '_true_ang_dl' ) )
            customizeRange_nod = mc.createNode( 'setRange', n=loc.replace( '_loc', '_customize_range' ) )
            switchBehaviourBlend_nod = mc.createNode( 'blendTwoAttr', n=loc.replace( '_loc', '_switch_behaviour_blend' ) )
            switchBehaviourBlend_rev_nod = mc.createNode( 'blendTwoAttr', n=loc.replace( '_loc', '_switch_behaviour_blend_rev' ) )
            reactMoveMl_nod = mc.createNode( 'multDoubleLinear', n=loc.replace( '_loc', '_react_move_ml' ) )
            reactMoveMl_rev_nod = mc.createNode( 'multDoubleLinear', n=loc.replace( '_loc', '_react_move_ml_rev' ) )
            reactRotMl_nod = mc.createNode( 'multDoubleLinear', n=loc.replace( '_loc', '_react_rot_ml' ) )
            reactRotMl_rev_nod = mc.createNode( 'multDoubleLinear', n=loc.replace( '_loc', '_react_rot_ml_rev' ) )
            reactScaleBlend_nod = mc.createNode( 'blendTwoAttr', n=loc.replace( '_loc', '_react_scale_blend' ) )
            reactScaleBlend_rev_nod = mc.createNode( 'blendTwoAttr', n=loc.replace( '_loc', '_react_scale_blend_rev' ) )
            mixMoveDl_nod = mc.createNode( 'addDoubleLinear', n=loc.replace( '_loc', '_mix_mov_dl' ) )
            mixScakeDl_nod = mc.createNode( 'addDoubleLinear', n=loc.replace( '_loc', '_mix_scl_dl' ) )
            mixRotBWeight_nod = mc.createNode( 'blendWeighted', n=loc.replace( '_loc', '_mix_rot_bw' ) )
            rotReactUnit_nod = mc.createNode( 'unitConversion', n=loc.replace( '_loc', '_rot_react_unit' ) ); mc.setAttr( rotReactUnit_nod+'.conversionFactor', 0.017453292519943295 )

            # set attr
            mc.setAttr( range180_nod+'.oldMinX', 90 )
            mc.setAttr( range180_nod+'.oldMinY', 0 )
            mc.setAttr( range180_nod+'.oldMaxX', 180 )
            mc.setAttr( range180_nod+'.oldMaxY', 90 )
            mc.setAttr( range180_nod+'.minX', 0 )
            mc.setAttr( range180_nod+'.minY', 180 )
            mc.setAttr( range180_nod+'.maxX', 180 )
            mc.setAttr( range180_nod+'.maxY', 0 )

            mc.setAttr( customizeRange_nod+'.minX', 0 )
            mc.setAttr( customizeRange_nod+'.minY', 0 )
            mc.setAttr( customizeRange_nod+'.maxX', 1 )
            mc.setAttr( customizeRange_nod+'.maxY', 1 )

            mc.setAttr( reactScaleBlend_nod+'.input[0]', 1 )
            mc.setAttr( reactScaleBlend_rev_nod+'.input[0]', 1 )

            # connect attr
            mc.connectAttr( angle_nod+'.angle', angUnit_nod+'.input' )
            mc.connectAttr( angUnit_nod+'.output', range180_nod+'.valueX' )
            mc.connectAttr( angUnit_nod+'.output', range180_nod+'.valueY' )

            mc.connectAttr( range180_nod+'.outValueX', trueAngDl_nod+'.input2' )
            mc.connectAttr( range180_nod+'.outValueX', customizeRange_nod+'.valueY' )
            mc.connectAttr( range180_nod+'.outValueY', valInvertUnit_nod+'.input' )
            mc.connectAttr( range180_nod+'.outValueY', customizeRange_nod+'.valueX' )
            mc.connectAttr( valInvertUnit_nod+'.output', trueAngDl_nod+'.input1' )
            mc.connectAttr( trueAngDl_nod+'.output', loc+'.currentAngle' )

            mc.connectAttr( loc+'.angleMin', customizeRange_nod+'.oldMinX' )
            mc.connectAttr( loc+'.angleMin', customizeRange_nod+'.oldMinY' )
            mc.connectAttr( loc+'.angleMax', customizeRange_nod+'.oldMaxX' )
            mc.connectAttr( loc+'.angleMax', customizeRange_nod+'.oldMaxY' )

            drivenKey_nod = None
            drivenKey_rev_nod = None
            if mc.checkBox( self.useDKey_chBox, q=True, v=True ):
                # bind uValue to attribute
                mc.setDrivenKeyframe ( loc+'.connectBS', cd = switchBehaviourBlend_nod+'.output', dv = .0, v = .0, ott='auto' )
                mc.setDrivenKeyframe ( loc+'.connectBS', cd = switchBehaviourBlend_nod+'.output', dv = .5, v = .5 )
                mc.setDrivenKeyframe ( loc+'.connectBS', cd = switchBehaviourBlend_nod+'.output', dv = 1.0, v = 1.0, itt='auto' )

                mc.setDrivenKeyframe ( loc+'.connectBS_Rev', cd = switchBehaviourBlend_rev_nod+'.output', dv = .0, v = .0, ott='auto' )
                mc.setDrivenKeyframe ( loc+'.connectBS_Rev', cd = switchBehaviourBlend_rev_nod+'.output', dv = .5, v = .5 )
                mc.setDrivenKeyframe ( loc+'.connectBS_Rev', cd = switchBehaviourBlend_rev_nod+'.output', dv = 1.0, v = 1.0, itt='auto' )

                drivenKey_nod = mc.listConnections( loc+'.connectBS' )[0]
                drivenKey_rev_nod = mc.listConnections( loc+'.connectBS_Rev' )[0]


                mc.connectAttr( drivenKey_nod+'.output', reactScaleBlend_nod+'.attributesBlender' )
                mc.connectAttr( drivenKey_nod+'.output', reactMoveMl_nod+'.input1' )
                mc.connectAttr( drivenKey_nod+'.output', reactRotMl_nod+'.input1' )

                mc.connectAttr( drivenKey_rev_nod+'.output', reactScaleBlend_rev_nod+'.attributesBlender' )
                mc.connectAttr( drivenKey_rev_nod+'.output', reactMoveMl_rev_nod+'.input1' )
                mc.connectAttr( drivenKey_rev_nod+'.output', reactRotMl_rev_nod+'.input1' )
            else:
                mc.connectAttr( switchBehaviourBlend_nod+'.output', loc+'.connectBS' )
                mc.connectAttr( switchBehaviourBlend_nod+'.output', loc+'.connectBS_Rev' )

                mc.connectAttr( switchBehaviourBlend_nod+'.output', reactMoveMl_nod+'.input1' )
                mc.connectAttr( switchBehaviourBlend_rev_nod+'.output', reactMoveMl_rev_nod+'.input1' )

                mc.connectAttr( switchBehaviourBlend_nod+'.output', reactRotMl_nod+'.input1' )
                mc.connectAttr( switchBehaviourBlend_rev_nod+'.output', reactRotMl_rev_nod+'.input1' )

                mc.connectAttr( switchBehaviourBlend_nod+'.output', reactScaleBlend_nod+'.attributesBlender' )
                mc.connectAttr( switchBehaviourBlend_rev_nod+'.output', reactScaleBlend_rev_nod+'.attributesBlender' )

            mc.connectAttr( customizeRange_nod+'.outValueX', switchBehaviourBlend_nod+'.input[0]' )
            mc.connectAttr( customizeRange_nod+'.outValueY', switchBehaviourBlend_nod+'.input[1]' )
            mc.connectAttr( customizeRange_nod+'.outValueX', switchBehaviourBlend_rev_nod+'.input[1]' )
            mc.connectAttr( customizeRange_nod+'.outValueY', switchBehaviourBlend_rev_nod+'.input[0]' )

            mc.connectAttr( loc+'.inverseBehaviour', switchBehaviourBlend_nod+'.attributesBlender' )
            mc.connectAttr( loc+'.inverseBehaviour', switchBehaviourBlend_rev_nod+'.attributesBlender' )
            mc.connectAttr( loc+'.reactionMove', reactMoveMl_nod+'.input2' )
            mc.connectAttr( loc+'.reactionMoveRev', reactMoveMl_rev_nod+'.input2' )
            mc.connectAttr( loc+'.reactionRotate', reactRotMl_nod+'.input2' )
            mc.connectAttr( loc+'.reactionRotateRev', reactRotMl_rev_nod+'.input2' )
            mc.connectAttr( reactMoveMl_nod+'.output', loc+'.currentMove' )
            mc.connectAttr( reactMoveMl_nod+'.output', mixMoveDl_nod+'.input1' )
            mc.connectAttr( reactMoveMl_rev_nod+'.output', mixMoveDl_nod+'.input2' )
            mc.connectAttr( mixMoveDl_nod+'.output', zero_grp+'.ty' )
            mc.connectAttr( loc+'.rotOffset', mixRotBWeight_nod+'.input[0]' )
            mc.connectAttr( reactRotMl_nod+'.output', mixRotBWeight_nod+'.input[1]' )
            mc.connectAttr( reactRotMl_rev_nod+'.output', mixRotBWeight_nod+'.input[2]' )
            mc.connectAttr( mixRotBWeight_nod+'.output', rotReactUnit_nod+'.input' )
            mc.connectAttr( rotReactUnit_nod+'.output', trns0_grp+'.rz' )

            mc.connectAttr( loc+'.reactionScale', reactScaleBlend_nod+'.input[1]' )
            mc.connectAttr( loc+'.reactionScaleRev', reactScaleBlend_rev_nod+'.input[1]' )
            mc.connectAttr( reactScaleBlend_nod+'.output', mixScakeDl_nod+'.input1' )
            mc.connectAttr( reactScaleBlend_rev_nod+'.output', mixScakeDl_nod+'.input2' )
            mc.connectAttr( mixScakeDl_nod+'.output', zero_grp+'.sx' )
            mc.connectAttr( mixScakeDl_nod+'.output', zero_grp+'.sy' )
            mc.connectAttr( mixScakeDl_nod+'.output', zero_grp+'.sz' )
            mc.connectAttr( loc+'.moveOffset', trns1_grp+'.ty' )

            return_arr.append( drivenKey_nod )
            return_arr.append( drivenKey_rev_nod )

            return return_arr



        wsad = lib['WSAD']
        wsad_x = lib['WSAD_X']
        xVecAvg_shp = self.shapes( lib['AngSys'][0] )[0]
        xVec_shp = self.shapes( lib['AngSys'][1] )[0]
        yVec_shp = self.shapes( lib['AngSys'][2] )[0]
        zVec_shp = self.shapes( lib['AngSys'][3] )[0]


        # create angle nodes if specified
        if wsad[0] or wsad[1] or wsad[2] or wsad[3]:
            xVecPlusMin_nod = mc.createNode( 'plusMinusAverage', n=xVec_shp.replace( '_vec_locShape','_vec_plusMin' ) )
            mc.setAttr( xVecPlusMin_nod+'.operation', 2 )
            mc.connectAttr( xVec_shp+'.worldPosition', xVecPlusMin_nod+'.input3D[0]' )
            mc.connectAttr( xVecAvg_shp+'.worldPosition', xVecPlusMin_nod+'.input3D[1]' )

        if wsad[0] or wsad[1]:
            # get angles
            yVecPlusMin_nod = mc.createNode( 'plusMinusAverage', n=yVec_shp.replace( '_vec_locShape','_vec_plusMin' ) )
            mc.setAttr( yVecPlusMin_nod+'.operation', 2 )
            mc.connectAttr( yVec_shp+'.worldPosition', yVecPlusMin_nod+'.input3D[0]' )
            mc.connectAttr( xVecAvg_shp+'.worldPosition', yVecPlusMin_nod+'.input3D[1]' )

            # connect angle between nodes
            yVecAng_nod = mc.createNode( 'angleBetween', n=yVec_shp.replace( '_vec_locShape','_vec_angBetween' ) )
            mc.connectAttr( xVecPlusMin_nod+'.output3D', yVecAng_nod+'.vector1' )
            mc.connectAttr( yVecPlusMin_nod+'.output3D', yVecAng_nod+'.vector2' )

        if wsad[2] or wsad[3]:
            # get angles
            zVecPlusMin_nod = mc.createNode( 'plusMinusAverage', n=zVec_shp.replace( '_vec_locShape','_vec_plusMin' ) )
            mc.setAttr( zVecPlusMin_nod+'.operation', 2 )
            mc.connectAttr( zVec_shp+'.worldPosition', zVecPlusMin_nod+'.input3D[0]' )
            mc.connectAttr( xVecAvg_shp+'.worldPosition', zVecPlusMin_nod+'.input3D[1]' )

            # connect angle between nodes
            zVecAng_nod = mc.createNode( 'angleBetween', n=zVec_shp.replace( '_vec_locShape','_vec_angBetween' ) )
            mc.connectAttr( xVecPlusMin_nod+'.output3D', zVecAng_nod+'.vector1' )
            mc.connectAttr( zVecPlusMin_nod+'.output3D', zVecAng_nod+'.vector2' )

        returnNodes_arr=[]
        for item in lib['WSAD']:
            # item = lib['WSAD'][0]
            if item:
                if item[1]=='W' or item[1]=='S':
                    returnNodes_arr.extend( connectWsad( item, yVecAng_nod ) )

                if item[1]=='A' or item[1]=='D':
                    returnNodes_arr.extend( connectWsad( item, zVecAng_nod ) )

        wsad_x = lib['WSAD_X']
        if len( wsad_x )>0 and wsad_x[0]:
            mc.connectAttr( wsad_x[0][0][4]+'.moveOffset', wsad_x[0][0][2]+'.ty' )

        return returnNodes_arr


    def createIbJoints( self ):

        def do_createJoint( name, suf, loc, parent ):
            # name, suf, loc, parent = n, x[1], x[0][4], self.bones[1]
            # name, suf, loc, parent = n, x[1], x[0][4], self.symBones[1]
            mc.select( parent )
            jnt = mc.joint( n = name, rad=self.jntRad/2 )

             # create visible attr
            if suf!='Avg':
                mc.addAttr( jnt, ln="sepAngle", nn="____________________", at="enum", en="Angle", k=True )
                mc.addAttr( jnt, ln="angleMin", at="double", min=.0, max=180, dv=0, k=True )
                mc.addAttr( jnt, ln="angleMax", at="double", min=.0, max=180, dv=90, k=True )

                mc.addAttr( jnt, ln="sepReact", nn="____________________", at="enum", en="React", k=True )
                mc.addAttr( jnt, ln="reactionMove", at="double", dv=2.0, k=True )
                mc.addAttr( jnt, ln="reactionRotate", at="double", dv=.0, k=True )
                mc.addAttr( jnt, ln="reactionScale", at="double", dv=1.0, k=True )
                mc.addAttr( jnt, ln="inverseBehaviour", at="enum", en="Direct:Invert", k=True )

                mc.addAttr( jnt, ln="sepReactRev", nn="____________________", at="enum", en="React REV", k=True )
                mc.addAttr( jnt, ln="reactionMoveRev", at="double", dv=.0, k=True )
                mc.addAttr( jnt, ln="reactionRotateRev", at="double", dv=.0, k=True )
                mc.addAttr( jnt, ln="reactionScaleRev", at="double", dv=1.0, k=True )

                mc.addAttr( jnt, ln="sepOffset", nn="____________________", at="enum", en="Offset", k=True )
                mc.addAttr( jnt, ln="moveOffset", at="double", min=.0, dv=1.0, k=True )
                mc.addAttr( jnt, ln="rotOffset", at="double", dv=.0, k=True )

                mc.addAttr( jnt, ln="sepInfo", nn="____________________", at="enum", en="Info", k=True )
                mc.addAttr( jnt, ln="connectBS", at="double", k=True )
                mc.addAttr( jnt, ln="connectBS_Rev", at="double", k=True )
                mc.addAttr( jnt, ln="currentAngle", at="double", k=True )

                # create hidden attr
                mc.addAttr( jnt, ln="currentMove", at="double", k=False )

                # set attr
                mc.setAttr( jnt+".moveOffset", self.ib_offset )
                mc.setAttr( jnt+".reactionMove", self.ib_react )

                # connect out attr to locator
                out_attributes = ['.angleMin', '.angleMax', '.reactionMove', '.reactionRotate', '.reactionScale', '.inverseBehaviour', '.reactionMoveRev', '.reactionRotateRev', '.reactionScaleRev', '.moveOffset', '.rotOffset']
                [mc.connectAttr( jnt+x, loc+x ) for x in out_attributes]

                # connect in attr from locator
                in_attributes = ['.currentMove', '.currentAngle', '.connectBS', '.connectBS_Rev']
                [mc.connectAttr( loc+x, jnt+x ) for x in in_attributes]

            else:
                mc.addAttr( jnt, ln="moveOffset", at="double", dv=.1 ); mc.setAttr( jnt+".moveOffset", k=False, cb=True )
                mc.setAttr( jnt+".moveOffset", self.avg_offset )
                mc.connectAttr( jnt+'.moveOffset', loc+'.moveOffset' )
                mc.setAttr( jnt+'.radius', self.jntRad*2 )

            if suf == 'S' or suf == 'D':
                mc.setAttr( jnt+".inverseBehaviour", 1 )

            # mtxParent( t, r, s, mo, pi, source, source..., target )
            self.mtxParent( True, True, True, False, True, jnt, loc ) # t, r, s, mo, pi

            return jnt


        # Create inbetween joints
        p0_wsad = self.p0_ib_lib['WSAD']
        p0_wsad_x = self.p0_ib_lib['WSAD_X'][0]
        p0_wsadJnt = []
        p0_wsad_Xjnt = []

        for x in p0_wsad:
            # x = p0_wsad[0]
            if x:
                n = x[0][4].replace( '_loc', '_ib_jnt' )
                jnt = do_createJoint( n, x[1], x[0][4], self.bones[1] )
                p0_wsadJnt.append( jnt )

        self.p0_ib_lib['WSADJoints'] = p0_wsadJnt

        if p0_wsad_x:
            n = p0_wsad_x[0][4].replace( '_loc', '_ib_jnt' )
            jnt = do_createJoint( n, p0_wsad_x[1], p0_wsad_x[0][4], self.bones[1] )
            p0_wsad_Xjnt.append( jnt )

        self.p0_ib_lib['WSAD_XJoint'] = p0_wsad_Xjnt

        # Create opposite joints
        if len( self.p1_ib_lib )>0:
            p1_wsad = self.p1_ib_lib['WSAD']
            p1_wsad_x = self.p1_ib_lib['WSAD_X'][0]
            p1_wsadJnt = []
            p1_wsad_Xjnt = []

            for x in p1_wsad:
                # x = p1_wsad[0]
                if x:
                    n = x[0][4].replace( '_loc', '_ib_jnt' )
                    jnt = do_createJoint( n, x[1], x[0][4], self.symBones[1] )
                    p1_wsadJnt.append( jnt )

            self.p1_ib_lib['WSADJoints'] = p1_wsadJnt

            if p1_wsad_x:
                n = p1_wsad_x[0][4].replace( '_loc', '_ib_jnt' )
                jnt = do_createJoint( n, p1_wsad_x[1], p1_wsad_x[0][4], self.symBones[1] )
                p1_wsad_Xjnt.append( jnt )

            self.p1_ib_lib['WSAD_XJoint'] = p1_wsad_Xjnt



    def connectOpposite( self, source, target ):
        # source, target = p0_avgLoc, p1_avgLoc

        attributes = ['.angleMin', '.angleMax', '.reactionMove', '.reactionRotate', '.reactionScale', '.inverseBehaviour', '.reactionMoveRev', '.reactionRotateRev', '.reactionScaleRev', '.moveOffset', '.rotOffset', '.weight']

        if len(source) > 0:
            for i in range( len(source) ):
                for attr in attributes:
                    if mc.objExists( source[i]+attr ):
                        mc.connectAttr( source[i]+attr, target[i]+attr )


    def hideAndLock( self ):
        # sourceObj, vis = 1, posLock = (1,1,1), rotLock = (1,1,1), scLock = (1,1,1), visLock = 1
        #self.p0_ib_lib # ['IbGroups', 'AvgSys', 'WSAD_XJoint', 'WSADJoints', 'AngSys', 'WSAD_X', 'WSAD']
        #self.p0_ib_lib['WSADJoints']
        #mc.select(self.p0_ib_lib['IbGroups'])

        def doMakeLocks( lib ):
            # lib = self.p0_ib_lib
            # lib = self.p1_ib_lib

            # name_ib_offset_grp, name_ib_trns_grp, name_ib_zero_grp
            [self.setLocks(lib['IbGroups'][x])for x in range(3)]
            # name_ib_ang_grp
            self.setLocks(lib['IbGroups'][4], vis=0)
            # name_ib_avg_grp
            self.setLocks(lib['IbGroups'][3] )
            # name_ib_ori1_loc, name_ib_ori2_loc, name_ib_avg_loc 
            self.setLocks(lib['AvgSys'][0], vis=0, posLock = 0, rotLock = 0, visLock = 0)
            self.setLocks(lib['AvgSys'][1], vis=0, visLock = 0)
            self.setLocks(lib['AvgSys'][2], visLock = 1)
            # name_X_vec_loc, name_Y_vec_loc, name_Z_vec_loc
            [self.setLocks(x)for x in lib['AngSys']]
            # name_wsad_offset_grp
            self.setLocks(lib['IbGroups'][5], visLock=0 )
            # WSAD
            [self.setLocks(x[0][0])for x in lib['WSAD'] if x]
            [self.setLocks(x[0][1])for x in lib['WSAD'] if x]
            [self.setLocks(x[0][2])for x in lib['WSAD'] if x]
            [self.setLocks(x[0][3])for x in lib['WSAD'] if x]
            [self.setLocks(x[0][4])for x in lib['WSAD'] if x]
            # WSAD_X Branch
            [lib['WSAD_X'][0][0][x] for x in range(5) if lib['WSAD_X'] and len(lib['WSAD_X'])==2]
            # If "Joints" mode enabled
            if 'Joints' in mc.optionMenu( self.mode_om, q=True, v=True ):
                [self.setLocks(x, vis=1)for x in lib['WSADJoints'] if x]
                [self.setLocks(x, vis=1)for x in lib['WSAD_XJoint'] if x]
                mc.setAttr( lib['IbGroups'][5]+'.v', 0 )

        doMakeLocks( self.p0_ib_lib )
        doMakeLocks( self.p1_ib_lib ) if self.symBones else False


    # Sreate selection sets
    def organizeSets( self, *args ):

        def createSets( lib, name ):
            # lib, name = self.p0_ib_lib, self.name[0]
            # lib, name = self.p1_ib_lib, self.name[1]

            # create main control set
            if not mc.objExists( 'Corrective_joints_set' ):
                main_set = mc.sets( em=True, n='Corrective_joints_set' )
            else:
                main_set = 'Corrective_joints_set'

            # create base set
            if not mc.objExists( '{0}_ib_set'.format( name ) ):
                ib_set = mc.sets( em=True, n='{0}_ib_set'.format( name ) )
                mc.sets( ib_set, e=True, fe=main_set )
            else:
                ib_set = '{0}_ib_set'.format( name )

            # create system set
            if not mc.objExists( '{0}_system_set'.format( name ) ):
                sys_set = mc.sets( em=True, n='{0}_system_set'.format( name ) )
                mc.sets( sys_set, e=True, fe=ib_set )
            else:
                sys_set = '{0}_system_set'.format( name )

            # create wsad_loc set
            if not mc.objExists( '{0}_loc_set'.format( name ) ):
                loc_set = mc.sets( em=True, n='{0}_loc_set'.format( name ) )
                mc.sets( loc_set, e=True, fe=ib_set )
            else:
                loc_set = '{0}_loc_set'.format( name )

            if 'Joints' in mc.optionMenu( self.mode_om, q=True, v=True ):
                if not mc.objExists( '{0}_joints_set'.format( name ) ):
                    jnt_set = mc.sets( em=True, n='{0}_joints_set'.format( name ) )
                    mc.sets( jnt_set, e=True, fe=ib_set )
                else:
                    jnt_set = '{0}_joints_set'.format( name )
            else:
                jnt_set = None

            if mc.checkBox( self.useDKey_chBox, q=True, v=True ):
                if not mc.objExists( '{0}_extention_set'.format( name ) ):
                    ext_set = mc.sets( em=True, n='{0}_extention_set'.format( name ) )
                    mc.sets( ext_set, e=True, fe=ib_set )
                else:
                    ext_set = '{0}_extention_set'.format( name )
            else:
                ext_set = None

            # Place pobjects in sets
            [mc.sets(x,e=1,fe=sys_set) for x in lib['AvgSys']]
            [mc.sets(x[0][4],e=1,fe=loc_set) for x in lib['WSAD'] if x]
            [mc.sets(x[0][4],e=1,fe=loc_set) for x in lib['WSAD_X'] if x]
            if 'Joints' in mc.optionMenu( self.mode_om, q=True, v=True ):
                [mc.sets(x,e=1,fe=jnt_set) for x in lib['WSADJoints']]
                [mc.sets(x,e=1,fe=jnt_set) for x in lib['WSAD_XJoint']]
            if mc.checkBox( self.useDKey_chBox, q=True, v=True ):
                [mc.sets(x,e=1,fe=ext_set) for x in lib['DrivenNodes']]

            return [main_set, ib_set, sys_set, loc_set, jnt_set, ext_set]


        p0_sets = createSets( self.p0_ib_lib, self.name[0] )
        self.p0_sets_lib['Main_set'] = p0_sets[0]       # main_set
        self.p0_sets_lib['IB_set'] = p0_sets[1]         # ib_set
        self.p0_sets_lib['Sys_set'] = p0_sets[2]        # sys_set
        self.p0_sets_lib['Loc_set'] = p0_sets[3]        # loc_set
        self.p0_sets_lib['Jnt_set'] = p0_sets[4]        # jnt_set
        self.p0_sets_lib['Ext_set'] = p0_sets[5]        # ext_set

        if self.symBones:
            p1_sets = createSets( self.p1_ib_lib, self.name[1] )
            self.p1_sets_lib['Main_set'] = p1_sets[0]   # main_set
            self.p1_sets_lib['IB_set'] = p1_sets[1]     # ib_set
            self.p1_sets_lib['Sys_set'] = p1_sets[2]    # sys_set
            self.p1_sets_lib['Loc_set'] = p1_sets[3]    # loc_set
            self.p1_sets_lib['Jnt_set'] = p1_sets[4]    # jnt_set
            self.p1_sets_lib['Ext_set'] = p1_sets[5]    # ext_set


    def delAttr( self ):
        # self.p0_sets_lib['IB_set']
        # self.p0_ib_lib['WSAD']

        # self.p0_ib_lib.keys()
        # ['DrivenNodes', 'IbGroups', 'AvgSys', 'WSAD_XJoint', 'WSADJoints', 'AngSys', 'WSAD_X', 'WSAD']
        # self.p0_sets_lib.keys()
        # ['Sys_set', 'Jnt_set', 'IB_set', 'Main_set', 'Ext_set', 'Loc_set']


        def collectObj( ib_lib, sets_lib ):
            # ib_lib, sets_lib = self.p0_ib_lib, self.p0_sets_lib
            objects_arr.extend( ib_lib['AvgSys'] )
            [objects_arr.append(x[0][4]) for x in ib_lib['WSAD'] if x]
            [objects_arr.append(x[0][4]) for x in ib_lib['WSAD_X'] if x]

            if 'Joints' in mc.optionMenu( self.mode_om, q=True, v=True ):
                objects_arr.extend( ib_lib['WSADJoints'] )
                objects_arr.extend( ib_lib['WSAD_XJoint'] )

            self.del_str += sets_lib['IB_set']
            self.del_str += ';'
            self.del_str += ib_lib['IbGroups'][0]
            self.del_str += ';'

        objects_arr = []
        self.del_str = ''

        collectObj( self.p0_ib_lib, self.p0_sets_lib )
        collectObj( self.p1_ib_lib, self.p1_sets_lib ) if self.symBones else False

        # Asssign attributes
        for obj in objects_arr:
            if mc.objExists( obj ):
                mc.addAttr (obj, ln='delString', dt='string')
                mc.setAttr (obj+'.delString', self.del_str, type = 'string')
                mc.setAttr (obj+'.delString', l=1)

        return [objects_arr, self.del_str] 

#self = IB()
