"""
This script allows to rig a catenary curve.

Usage: drag into Maya's script editor, select some curves and run.


---
Author: Kevin Rosso (kevin.rosso98@gmail.com)

Version: 1.2
Added "cvs distribution" attribute

Version: 1.1
Minor bugfix

Version: 1.0
Initial release

License:
+ commercial use
+ you must attribute me
+ you can share whatever product you will produce using this code, with any license you want
- you can't redistribute this python code
"""

import maya.cmds as mc

def createCtrl(name, scale=1, secondary=False):
    """
    Creates a control.

    Args:
        name (str): The name of the control to create.
        scale (float): The world scale of the control.
        secondary (bool | int): If `TRUE` the control will be secondary.

    Returns:
        (str[]): control, position group
    """
    # INITIALIZE VARIABLES
    orient = [0, 0, 0]
    t = [1, 1, 1]
    r = [1, 1, 1]
    s = [0, 0, 0]

    # rename
    ctrl = mc.circle(n=f"{name}_ctrl")[0]
    mc.delete(ctrl, constructionHistory = True)
    mc.setAttr(f'{ctrl}.v', k=0, channelBox=1)

    # create the group
    grp = mc.group(ctrl, n=f'{name}_posGrp')
    mc.xform(os=1, piv=(0, 0, 0))
    
    # scaling
    mc.scale(scale, scale, scale, grp)
    mc.rotate(0, 90, 0, grp)

    # freeze the transform
    mc.makeIdentity(grp, apply=1, t=1, r=1, s=1, n=0)

    
    # color
    if secondary:
        color = 23
    else:
        color = 17
    shape = mc.listRelatives(ctrl, s=1)[0]
    mc.setAttr(f'{shape}.overrideEnabled', 1)
    mc.setAttr(f"{shape}.overrideRGBColors", 0)
    mc.setAttr(f'{shape}.overrideColor', color)

    # finalize
    mc.controller(ctrl)
    mc.select(cl=1)

    return [ctrl, grp]


def multMatrix(*attributes, n="", destination=None):
    """
    Given some matrix attributes, multiply them in the given order and return the result.

    Args:
        *attributes (*str): Matrix attributes to multiply
        n (str): The name for the multMatrix node
        destination (str): Attribute to connect the ouput matrix to

    Returns:
        (str): The matrixSum attribute.
    """
    if n:
        mult = mc.createNode("multMatrix", n=n)
    else:
        mult = mc.createNode("multMatrix")

    for i, attr in enumerate(attributes):
        if isinstance(attr, str):
            mc.connectAttr(attr, f"{mult}.matrixIn[{i}]")
        else:
            mc.setAttr(f"{mult}.matrixIn[{i}]", attr, type="matrix")

    # CONNECT OUTPUT
    if destination:
        mc.connectAttr(f"{mult}.matrixSum", destination, f=1)

    return f"{mult}.matrixSum"
    
    
def decomposeMatrix(attr, n="", getValues=False):
    """
    Given a matrix attribute, decompose it and return all the decomposed data.

    If `getValues == False` it returns the output plugs.
    If `getValues == True` it returns the actual float values.

    Args:
        attr (str): the matrix attribute to decompose
        n (str): decomposeMatrix node name
        getValues (bool): if `TRUE` it will return the decomposed float values

    Returns:
        (list): translate, rotate, scale, shear, quaternions
    """
    if n:
        decompose = mc.createNode("decomposeMatrix", n=n)
    else:
        decompose = mc.createNode("decomposeMatrix")
    mc.connectAttr(attr, f"{decompose}.inputMatrix")

    return f"{decompose}.outputTranslate"
    

def catenaryExpression(objects, startLoc, endLoc, length, n, precision=10):
    """
    Create an expression node to calculate catenary function. The catenary will be on the Y axis.

    Source: https://www.geogebra.org/m/ptpy5xfn

    Args:
        objects (list | str): objects whose translation y will be calculated as catenary.
        startLoc: start object
        endLoc: end object
        length: length of the catenary
        n: name for the expression node
        precision (int): precision of the calculation. DO NOT GO BELOW 5

    Returns:
        (str): the expression node.
    """
    if not isinstance(objects, list):
        objects = [objects]

    # create expression
    expressionNode = mc.createNode("expression", n=f"{n}_expr")
    if isinstance(length, float) or isinstance(length, int):
        lengthAttr = f"{expressionNode}.length"
        if not mc.objExists(lengthAttr):
            mc.addAttr(expressionNode, ln="length", at="double", dv=length)
        mc.setAttr(lengthAttr, length)
        length = lengthAttr
    expressionText = f"""
// FUNCTIONS
global proc float sinh(float $x) {{
    $e = 2.718281828459;
    $ret = (pow($e, $x) - pow($e, -$x))/2;
    return($ret);
}}
global proc float cosh(float $x) {{
    $e = 2.718281828459;
    $ret = (pow($e, $x) + pow($e, -$x))/2;
    return($ret);
}}
global proc float atanh(float $x) {{
    $ret = 0.5 * log((1+$x)/(1-$x));
    return($ret);
}}


global proc float catenary_{n}(float $x, float $pt1x, float $pt1y, float $pt1z, float $pt2x, float $pt2y, float $pt2z, float $len) {{
    // VARIABLES
    //$pt1x = {startLoc}.translateX;
    //$pt1y = {startLoc}.translateY;
    //$pt1z = {startLoc}.translateZ;

    //$pt2x = {endLoc}.translateX;
    //$pt2y = {endLoc}.translateY;
    //$pt2z = {endLoc}.translateZ;

    //$len = {length};

    // BASE DATA
    $dx = $pt2x - $pt1x;
    $dy = $pt2y - $pt1y;
    $dz = $pt2z - $pt1z;
    
    // CHECK DISTANCE
    $distance = sqrt(pow($dx, 2) + pow($dy, 2) + pow($dz, 2));
    $linear = $pt1y + ($x-$pt1x)*($dy/$dx);
    if ($len < $distance){{
        return($linear);
    }}

    // R
    $r = sqrt(pow($len, 2)-pow($dy, 2))/$dx;

    // ITERATION
    $A0 = log(2*$r)+log(log(2*$r));
    $A = $A0;
    for($i=0; $i<{precision}; $i++){{
        $A = $A - ((sinh($A) - ($r*$A))/(cosh($A)-$r));
    }}

    // FINAL DATA
    $xb = ($pt1x + $pt2x)/2;

    $a = $dx/(2*$A);
    $b = $xb - $a*atanh($dy/$len);
    $c = $pt1y - $a*cosh(($pt1x-$b)/$a);

    // CALCULATION
    $catenary = $a*cosh(($x-$b)/$a) + $c;
    return($catenary);
}}
"""
    for obj in objects:
        expressionText += f"""
{obj}.translateY = catenary_{n}({obj}.translateX, {startLoc}.translateX, {startLoc}.translateY, {startLoc}.translateZ, {endLoc}.translateX, {endLoc}.translateY, {endLoc}.translateZ, {length});
"""
    mc.expression(expressionNode, e=True, s=expressionText, alwaysEvaluate=True, unitConversion="all")

    return expressionNode


def catenaryCurve(crv=None, n="catenary", offset=1, precision=10):
    """
    Given a curve, create a catenary rig that will behave physically accurate. The catenary will bend on the y axis.

    Source: https://www.geogebra.org/m/ptpy5xfn

    Args:
        crv (str): The curve to rig.
        offset (float): The Y offset for the middle control.
        n (str): The name for the system.
        precision (int): Precision of the calculation. DO NOT GO BELOW 5!

    Returns:
        (str): The system connect group.
    """
    if not crv:
        selection = mc.ls(sl=True)
        if not selection:
            mc.warning("Please select a curve and try again.")
            return
        crv = selection[0]

    # find main points
    cvs = mc.ls(f"{crv}.cv[*]", fl=True)
    cvStart = cvs[0]
    cvEnd = cvs[-1]
    cvMid = cvs[round(len(cvs) / 2)]

    posStart = mc.pointPosition(cvStart)
    posEnd = mc.pointPosition(cvEnd)
    posMid = mc.pointPosition(cvMid)

    # create main controls
    startCtrl, startOffGrp = createCtrl(f"{n}_start", scale=1)
    mc.move(*posStart, startOffGrp)
    endCtrl, endOffGrp = createCtrl(f"{n}_end", scale=1)
    mc.move(*posEnd, endOffGrp)
    midCtrl, midOffGrp = createCtrl(f"{n}_mid", scale=1)
    mc.move(*posMid, midOffGrp)

    # create main group
    mainGrp = mc.group(n=f"{n}_connect", em=True)
    mc.delete(mc.pointConstraint(startCtrl, endCtrl, mainGrp, mo=False))

    aimLoc = mc.spaceLocator(n=f"{n}_aimLoc")[0]
    mc.matchTransform(aimLoc, mainGrp)
    mc.move(0, 100, 0, aimLoc, ws=True, r=True)
    mc.delete(mc.aimConstraint(aimLoc, mainGrp, aimVector=(0, 1, 0), upVector=(1, 0, 0), worldUpType="object", worldUpObject=endCtrl))

    mc.parent(startOffGrp, midOffGrp, endOffGrp, mainGrp)
    mc.rotate(0, 0, 0, startOffGrp, os=True)
    mc.rotate(0, 0, 0, midOffGrp, os=True)
    mc.rotate(0, 0, 0, endOffGrp, os=True)

    # center mid control
    midGrp = mc.group(n=f"{n}_midGrp", em=True)
    mc.matchTransform(midGrp, mainGrp)
    mc.pointConstraint(midGrp, aimLoc, mo=True)
    mc.parent(aimLoc, midGrp, mainGrp)
    mc.pointConstraint(startCtrl, midGrp, mo=False)
    mc.aimConstraint(aimLoc, midGrp, aimVector=(0, 1, 0), upVector=(1, 0, 0), worldUpType="object", worldUpObject=endCtrl)

    mc.pointConstraint(startCtrl, endCtrl, midOffGrp, skip="y", mo=False)
    mc.move(0, -offset, 0, midOffGrp, r=True, os=True)

    startLoc = mc.spaceLocator(n=f"{n}_startLoc")[0]
    mc.parentConstraint(startCtrl, startLoc, mo=False)
    mc.parent(startLoc, midGrp)

    endLoc = mc.spaceLocator(n=f"{n}_endLoc")[0]
    mc.parentConstraint(endCtrl, endLoc, mo=False)
    mc.parent(endLoc, midGrp)

    mc.parent(midOffGrp, midGrp)
    length = mc.arclen(crv, ch=False)
    expr = catenaryExpression(midOffGrp, startLoc, endLoc, length, f"{n}_midCtrl", precision=5)
    length = f"{expr}.length"

    mc.hide(startLoc, endLoc)

    # create locators group
    locGrp = mc.group(n=f"{n}_locGrp", em=True)
    mc.parent(locGrp, mainGrp, r=True)
    mc.pointConstraint(startCtrl, endCtrl, locGrp, mo=False)
    mc.aimConstraint(midCtrl, locGrp, aimVector=(0, -1, 0), upVector=(1, 0, 0), worldUpType="object", worldUpObject=endCtrl)

    # create locators and connect to curve cvs
    locs = []
    offGrps = []
    for i, cv in enumerate(cvs):
        loc = mc.group(n=f"{n}_{i}_loc", em=True)
        pos = mc.pointPosition(cv)
        mc.parent(loc, locGrp, r=True)
        mc.move(*pos, loc, ws=True)
        multM = multMatrix(f"{loc}.worldMatrix[0]", f"{crv}.worldInverseMatrix[0]")
        mc.connectAttr(decomposeMatrix(multM), cv, f=True)
        locs.append(loc)

        ctrl, offGrp = createCtrl(f"{n}_{i}", scale=.5, secondary=True)
        mc.matchTransform(offGrp, loc)
        mc.parent(offGrp, locGrp)
        mc.parent(loc, ctrl)
        offGrps.append(offGrp)
        mc.hide(loc)

    # constrain extremities
    startLoc = offGrps[0]
    mc.parentConstraint(startCtrl, startLoc, mo=False)
    endLoc = offGrps[-1]
    mc.parentConstraint(endCtrl, endLoc, mo=False)

    # constrain x and z axis
    blendAttr = f"{startCtrl}.cvs_distribution"
    mc.addAttr(startCtrl, ln="cvs_distribution", at="double", dv=.5, min=0, max=1)
    mc.setAttr(blendAttr, cb=True)
    mc.setAttr(blendAttr, k=True)
    mc.addAttr(endCtrl, ln="cvs_distribution", proxy=blendAttr)
    amt = len(offGrps)-1
    for i, loc in enumerate(offGrps[1:-1]):
        startX = mc.getAttr(f"{startLoc}.tx")
        endX = mc.getAttr(f"{endLoc}.tx")
        x = mc.getAttr(f"{loc}.tx")

        # cvs distribution
        dx = endX - startX
        startWeight1 = (endX - x) / dx
        endWeight1 = (x - startX) / dx
        
        # uniform distribution
        endWeight2 = 1/amt*(i+1)
        startWeight2 = 1-endWeight2

        # create constraint
        con = mc.pointConstraint(startLoc, loc, w=startWeight1, skip="y", mo=False)[0]
        mc.pointConstraint(endLoc, loc, w=endWeight1, skip="y", mo=False)
        
        # blend start weight
        remap = mc.createNode("remapValue")
        mc.connectAttr(blendAttr, f"{remap}.inputValue", f=True)
        mc.setAttr(f"{remap}.outputMin", startWeight1)
        mc.setAttr(f"{remap}.outputMax", startWeight2)
        mc.connectAttr(f"{remap}.outValue", f"{con}.{startLoc}W0", f=True)
        
        # blend end weight
        remap = mc.createNode("remapValue")
        mc.connectAttr(blendAttr, f"{remap}.inputValue", f=True)
        mc.setAttr(f"{remap}.outputMin", endWeight1)
        mc.setAttr(f"{remap}.outputMax", endWeight2)
        mc.connectAttr(f"{remap}.outValue", f"{con}.{endLoc}W1", f=True)

    # create expression
    catenaryExpression(offGrps[1:-1], offGrps[0], offGrps[-1], length, n, precision)

    # length attr
    for obj in [startCtrl, endCtrl]:
        mc.addAttr(obj, ln="length", proxy=length)

    return mainGrp
    

sel = mc.ls(sl=True)
if not sel:
    mc.warning("Please select one or more curves.")
else:
    for crv in sel:
        if mc.objectType(mc.listRelatives(crv, s=True)[0]) == "nurbsCurve":
            catenaryCurve(crv, n=crv)
