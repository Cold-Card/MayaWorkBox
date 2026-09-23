##--------------------------------------------------------------------------
##
## ScriptName : OffsetEdgeSlide
## Author     : Joe Wu
## URL        : https://www.youtube.com/@Im3dJoe
## LastUpdate : 2026/02/28
##            : keep edges same distance from side  
## Version    : 1.0  First version for public test
##
## Other Note : test in maya 2023.3 windows
##
## Install    : copy and paste script into a python tab in maya script editor
##				use ctrl + drag to adjust droop 
##--------------------------------------------------------------------------


import maya.cmds as mc
import maya.api.OpenMaya as oma


def _get_component_positions_world(components):
    if not components:
        return []
    verts = mc.polyListComponentConversion(components, toVertex=True)
    verts = mc.ls(verts, fl=True) or []
    if not verts:
        return []
    sel = oma.MSelectionList()
    for v in verts:
        sel.add(v)
    out = []
    it = oma.MItSelectionList(sel, oma.MFn.kMeshVertComponent)
    while not it.isDone():
        dag, comp = it.getComponent()
        itv = oma.MItMeshVertex(dag, comp)
        while not itv.isDone():
            out.append(itv.position(oma.MSpace.kWorld))
            itv.next()
        it.next()
    return out


def _avg_displacement(pos_a, pos_b):
    if not pos_a or not pos_b or len(pos_a) != len(pos_b):
        return 1e18, 1e18, 0.0
    total = 0.0
    minSave = 1e18
    maxSave = 0.0
    for a, b in zip(pos_a, pos_b):
        dist = (b - a).length()
        total += dist
        if dist < minSave:
            minSave = dist
        if dist > maxSave:
            maxSave = dist
    avgMove = total / float(len(pos_a))
    return avgMove, minSave, maxSave


def _try_slide_and_measure(ed=0.5, d=0):
    sel = mc.ls(sl=True, fl=True) or []
    if not sel:
        return 1e18, 0.0, 1e18, False
    before = _get_component_positions_world(sel)
    mc.undoInfo(openChunk=True)
    try:
        mc.polySlideEdge(ed=ed, d=d)
        after = _get_component_positions_world(sel)
        avgMove, minSave, maxSave = _avg_displacement(before, after)
    except Exception:
        avgMove, minSave, maxSave = 1e18, 1e18, 0.0
    finally:
        try:
            mc.undo()
        except Exception:
            pass
        mc.undoInfo(closeChunk=True)
    return avgMove, maxSave, minSave, (avgMove < 1e17)

def auto_slide_pick_smaller(ed=0.5, prefer_if_equal=0, verbose=True):
    sel = mc.ls(sl=True, fl=True) or []
    if not sel:
        if verbose:
            mc.warning("Nothing selected.")
        return None
    move0, max0, min0, ok0 = _try_slide_and_measure(ed=ed, d=0)
    move1, max1, min1, ok1 = _try_slide_and_measure(ed=ed, d=1)
    if not (ok0 or ok1):
        if verbose:
            mc.warning("polySlideEdge test failed for both directions.")
        return None
    eps = 1e-9
    if abs(move0 - move1) <= eps:
        chosen = prefer_if_equal
    else:
        chosen = 0 if move0 < move1 else 1
    mc.undoInfo(openChunk=True)
    guessMinA = min0 / ( min0 + max1 )
    guessMinB = min1 / ( min1 + max0 )
    mimmin = 0
    if guessMinA > guessMinB:
        mimmin = guessMinB
    else:
        mimmin = guessMinA    
    mimmin = mimmin * 1.5
    try:
        mc.polySlideEdge(ed=ed, d=chosen)
        opposite = 1 - chosen
        mc.polySlideEdge(a=1, ed=mimmin, d=opposite)  # 0.1 is scene units
    finally:
        mc.undoInfo(closeChunk=True)
    return chosen


def offsetSlide():
    auto_slide_pick_smaller(ed=0.99)
    mc.setToolTo("polySlideEdgeContext")
    mc.polySlideEdgeCtx("polySlideEdgeContext", e=True, a=1)


offsetSlide()
