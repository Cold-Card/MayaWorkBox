def run_ssdr_convert(mesh):
    start = '1001'
    end = '1038'
    maxinf = 8
    boneNum = 4
    #mesh = self.getMesh()

    cmds.demBones(mesh,b=boneNum,sf=int(start),ef=int(end),mi=maxinf)

for mesh in cmds.ls(sl=True):
    run_ssdr_convert(mesh)
    jnts = cmds.ls('dembones_joint*',type='joint')
    for jnt in jnts:
        cmds.rename(jnt,mesh+'_'+jnt)