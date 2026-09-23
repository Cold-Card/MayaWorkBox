##--------------------------------------------------------------------------
## ScriptName : faceLoopPatch
## Author     : Joe Wu
## URL        : http://im3djoe.com
## LastUpdate : 2026/06
##            : rebuilding and smoothing uneven face-loop patches
## Version    : beta for public test
## Other Note : test in maya 2027 windows
## Install    : copy and paste script into a python tab in maya script editor
## how to use : use mouse, normal drag increase loft U direction, shift+drag increase loft V direction 
##            : exit tool to merge patch
##--------------------------------------------------------------------------

import maya.cmds as mc
import maya.api.OpenMaya as oma
import maya.mel as mel
import maya.utils as mu
import math
import re
from collections import defaultdict, Counter
from itertools import combinations

mel.eval('nurbsToPolygonsPref -pt 1 -f 3;')

FACE_LOOP_SMOOTH_VERSION = "beta"

TARGET_NAME        = "tempFaceLoop"
TARGET_NAME_SIMPLE = "tempFaceLoopSimple"
CAP_SET_PREFIX = "capEdgeSave"
ctx = 'smoothFLCtx'
smoothFL_tessNode    = None
smoothFL_simple_mode = True
smoothFL_curve_list  = []
smoothFL_cap_curves  = []
smoothFL_source_normal = None
screenX = 0.0
lockCount = 0
storeCount = 0
lockCountV = 0
storeCountV = 0
viewPortCount = 0
pixelAccum = 0.0
pixelAccumV = 0.0
smoothFL_drag_mode = 'U'
smoothFL_cap_edge_count = 0
smoothFL_undoJob = None
smoothFL_cancelJob = None
smoothFL_cancelling = False
smoothFL_orig_face_records = None

def _strip(n):
    m = re.match(r"(.+?)\.(vtx|e|f|map)\[", n)
    return m.group(1) if m else n
def _edge_id(c):
    m = re.search(r"\.e\[(\d+)\]", c)
    return int(m.group(1)) if m else None
def _face_id(c):
    m = re.search(r"\.f\[(\d+)\]", c)
    return int(m.group(1)) if m else None
def _mesh_shape(item):
    node = _strip(item)
    nodes = mc.ls(node, long=True) or []
    if not nodes: return None
    node = nodes[0]
    if mc.nodeType(node) == "mesh": return node
    shapes = mc.listRelatives(node, shapes=True, noIntermediate=True, fullPath=True) or []
    shapes = [s for s in shapes if mc.nodeType(s) == "mesh"]
    return shapes[0] if shapes else None
def _mesh_tr(shape):
    p = mc.listRelatives(shape, parent=True, fullPath=True) or []
    return p[0] if p else shape
def _dag(shape):
    s = oma.MSelectionList(); s.add(shape); return s.getDagPath(0)
def _fn(shape): return oma.MFnMesh(_dag(shape))
def _v(p): return oma.MVector(p.x, p.y, p.z)
def _dist(a, b): return (a - b).length()
def _q(t): return t.replace("\\", "\\\\").replace('"', '\\"')
def _edge_comp(shape, i): return "%s.e[%d]" % (_mesh_tr(shape), i)
def _face_comp(shape, i): return "%s.f[%d]" % (_mesh_tr(shape), i)
def _vtx_pos(shape, i, fn=None):
    if fn is None: fn = _fn(shape)
    return _v(fn.getPoint(i, oma.MSpace.kWorld))
def _set_vtx_pos(shape, i, p, fn=None):
    if fn is None: fn = _fn(shape)
    fn.setPoint(i, oma.MPoint(p.x, p.y, p.z), oma.MSpace.kWorld)
def _edge_is_boundary(it):
    try:
        b = it.onBoundary
        return b() if callable(b) else bool(b)
    except Exception: return False
def _delete_matches(patterns):
    if isinstance(patterns, str): patterns = [patterns]
    delete_list = []
    for p in patterns:
        delete_list.extend(mc.ls(p, long=True) or [])
    if delete_list:
        try: mc.delete(delete_list)
        except Exception: pass
def _close_undo_chunk_safely():
    try: mc.undoInfo(closeChunk=True)
    except Exception: pass
def _set_hidden_in_outliner(items, refresh=True):
    if isinstance(items, str): items = [items]
    nodes = []
    for it in items:
        nodes.extend(mc.ls(it, long=True) or [])
    for n in nodes:
        try:
            if mc.attributeQuery('hiddenInOutliner', node=n, exists=True):
                mc.setAttr(n + '.hiddenInOutliner', 1)
        except Exception:
            pass
    if refresh and nodes:
        for ed in (mc.lsUI(editors=True) or []):
            try:
                if mc.objectTypeUI(ed) == 'outlinerEditor':
                    mc.outlinerEditor(ed, edit=True, refresh=True)
            except Exception:
                pass

def _face_records(faces):
    records = []
    for f in mc.ls(faces, fl=True, long=True) or []:
        fid = _face_id(f)
        mesh = _strip(f)
        if fid is not None and mesh:
            records.append((mesh, fid))
    return records
def _faces_from_records(records):
    faces = []
    for mesh, fid in records:
        if not mc.objExists(mesh):
            continue
        try:
            if fid < int(mc.polyEvaluate(mesh, f=True)):
                faces.append('%s.f[%d]' % (mesh, fid))
        except Exception:
            pass
    return mc.filterExpand(mc.ls(faces, fl=True, long=True), sm=34) or []
def _transforms_from_faces(faces):
    trs = []
    seen = set()
    for f in mc.ls(faces, fl=True, long=True) or []:
        shape = _mesh_shape(f)
        if not shape:
            continue
        tr = _mesh_tr(shape)
        if tr not in seen:
            seen.add(tr)
            trs.append(tr)
    return trs
def _delete_history_keep_selection(transforms, face_records=None):
    if not transforms:
        return []
    try:
        mc.delete(transforms, ch=True)
    except Exception as e:
        mc.warning('Delete history failed: %s' % str(e))
    if face_records:
        faces = _faces_from_records(face_records)
        if faces:
            mc.select(faces, r=True)
        return faces
    return []
def _select_faces_in_face_mode(faces):
    faces = mc.filterExpand(mc.ls(faces, fl=True, long=True), sm=34) or []
    if not faces:
        return []
    mc.select(clear=True)
    mc.select(faces, r=True)
    mesh = faces[0].split('.')[0]
    try:
        mc.selectMode(component=True)
        mc.selectType(polymeshFace=True)
    except Exception:
        pass
    try:
        _set_poly_component_mode(mesh, 'facet')
    except Exception:
        pass
    mc.select(faces, r=True)
    return faces
def _install_restore_face_mode_after_undo():
    global smoothFL_undoJob
    try:
        if smoothFL_undoJob and mc.scriptJob(exists=smoothFL_undoJob):
            mc.scriptJob(kill=smoothFL_undoJob, force=True)
    except Exception:
        pass

    def _after_undo():
        global smoothFL_undoJob
        smoothFL_undoJob = None
        loft_back = mc.objExists(TARGET_NAME) or mc.objExists(TARGET_NAME_SIMPLE)

        def _finish():
            if loft_back:
                try:
                    mc.undo()
                except Exception:
                    pass
            faces = []
            try:
                if smoothFL_orig_face_records:
                    faces = _faces_from_records(smoothFL_orig_face_records)
            except Exception:
                faces = []
            if not faces:
                faces = mc.filterExpand(mc.ls(sl=True, fl=True, long=True), sm=34) or []
            if not faces:
                return
            mesh = faces[0].split('.')[0]
            try:
                mc.selectMode(component=True)
                mc.selectType(polymeshFace=True)
                mel.eval('doMenuComponentSelectionExt("%s", "facet", 0);' % _q(mesh))
                mc.select(faces, r=True)
            except Exception:
                pass
        mc.evalDeferred(_finish, lowestPriority=True)

    try:
        smoothFL_undoJob = mc.scriptJob(event=['Undo', _after_undo], runOnce=True, protected=True)
    except Exception:
        smoothFL_undoJob = None

def _install_cancel_on_undo(prev_ctx, face_records):
    global smoothFL_cancelJob
    try:
        if smoothFL_cancelJob and mc.scriptJob(exists=smoothFL_cancelJob):
            mc.scriptJob(kill=smoothFL_cancelJob, force=True)
    except Exception:
        pass
    smoothFL_cancelJob = None

    def _cancel():
        global smoothFL_cancelling, smoothFL_cancelJob
        smoothFL_cancelJob = None
        if mc.objExists(TARGET_NAME) or mc.objExists(TARGET_NAME_SIMPLE):
            _install_cancel_on_undo(prev_ctx, face_records)
            return
        smoothFL_cancelling = True
        try:
            if mc.headsUpDisplay('HUDunBevelStep', exists=True):
                mc.headsUpDisplay('HUDunBevelStep', rem=True)
        except Exception:
            pass
        try:
            faces = _faces_from_records(face_records) if face_records else []
            if faces:
                _select_faces_in_face_mode(faces)
        except Exception:
            pass
        def _leave_tool(pc=prev_ctx):
            try:
                mc.setToolTo(pc if pc else 'selectSuperContext')
            except Exception:
                try: mc.setToolTo('selectSuperContext')
                except Exception: pass
        mc.evalDeferred(_leave_tool, lowestPriority=True)

    try:
        smoothFL_cancelJob = mc.scriptJob(event=['Undo', _cancel], runOnce=True, protected=True)
    except Exception:
        smoothFL_cancelJob = None

def _border_edge_lengths(shape):
    dag = _dag(shape); fn = oma.MFnMesh(dag); it = oma.MItMeshEdge(dag)
    lengths = []
    while not it.isDone():
        if _edge_is_boundary(it):
            v0, v1 = fn.getEdgeVertices(it.index())
            a = _v(fn.getPoint(v0, oma.MSpace.kWorld))
            b = _v(fn.getPoint(v1, oma.MSpace.kWorld))
            lengths.append(_dist(a, b))
        it.next()
    return lengths
def _guide_length(shape):
    lengths = _border_edge_lengths(shape)
    if not lengths: raise RuntimeError("Target mesh has no border edges.")
    lengths.sort()
    n = len(lengths); mid = n // 2
    return (lengths[mid] + lengths[~mid]) / 2.0
def _longest_selected_edge(sel_edges):
    best = 0.0
    for c in sel_edges:
        shape = _mesh_shape(c); eid = _edge_id(c)
        if shape is None or eid is None: continue
        fn = _fn(shape); v0, v1 = fn.getEdgeVertices(eid)
        a = _v(fn.getPoint(v0, oma.MSpace.kWorld))
        b = _v(fn.getPoint(v1, oma.MSpace.kWorld))
        best = max(best, _dist(a, b))
    return best
def _auto_split_count(shape, sel_edges):
    try:
        guide   = _guide_length(shape)
        longest = _longest_selected_edge(sel_edges)
        if guide < 1e-7 or longest < 1e-7: return 0
        return max(0, int(round(longest / guide)))
    except Exception as e:
        mc.warning("BSR auto split count failed: %s" % str(e))
        return 0
def _polyinfo_int_list(info):
    if ".e[" in info:
        m = re.search(r"\.e\[(\d+)\]", info)
        if not m: return []
        eid  = int(m.group(1))
        nums = [int(x) for x in re.findall(r"\d+", info.split(":", 1)[1] if ":" in info else info)]
        return [eid] + nums
    return [int(x) for x in re.findall(r"\d+", info)]
def _edge_ring_groups(sel_edges):
    if not sel_edges: return []
    trans = _strip(sel_edges[0])
    infos = mc.polyInfo(sel_edges, ev=True) or []
    e2v   = {}
    for info in infos:
        ev = _polyinfo_int_list(info)
        if len(ev) >= 3: e2v[ev[0]] = ev[1:]
    groups = []
    while True:
        try: start_e, start_vs = e2v.popitem()
        except Exception: break
        grp = [start_e]; num = 0
        for vtx in start_vs:
            cur = vtx
            while True:
                nxt = [k for k in list(e2v.keys()) if cur in e2v[k]]
                if not nxt or len(nxt) != 1: break
                ne = nxt[0]
                if num == 0: grp.append(ne)
                else: grp.insert(0, ne)
                vs = e2v[ne]; cand = [x for x in vs if x != cur]
                e2v.pop(ne)
                if not cand: break
                cur = cand[0]
            num += 1
        groups.append(grp)
    return [["%s.e[%d]" % (trans, e) for e in g] for g in groups]
def _multi_loop_groups(sel_edges):
    by_mesh = {}
    for e in sel_edges: by_mesh.setdefault(_strip(e), []).append(e)
    out = []
    for edges in by_mesh.values():
        for g in _edge_ring_groups(edges):
            if g: out.append(g)
    return out
def _target_border_data(shape):
    dag = _dag(shape); fn = oma.MFnMesh(dag); it = oma.MItMeshEdge(dag)
    ids = set(); segs = []
    while not it.isDone():
        if _edge_is_boundary(it):
            v0, v1 = fn.getEdgeVertices(it.index())
            ids.add(int(v0)); ids.add(int(v1))
            a = _v(fn.getPoint(v0, oma.MSpace.kWorld))
            b = _v(fn.getPoint(v1, oma.MSpace.kWorld))
            segs.append((a, b))
        it.next()
    ids = sorted(ids)
    if not ids: raise RuntimeError("Target mesh has no open border vertices.")
    return [_vtx_pos(shape, i, fn) for i in ids], ids, segs
def _point_on_seg(p, a, b):
    ab = b - a; l = ab * ab
    if l < 1e-10: return None, None
    t = ((p - a) * ab) / l
    return t, _dist(p, a + ab * t)
def _closest_on_seg(p, a, b):
    ab = b - a; l = ab * ab
    if l < 1e-10: return a, _dist(p, a)
    t = max(0.0, min(1.0, ((p - a) * ab) / l))
    return a + ab * t, _dist(p, a + ab * t)
def _closest_pos(p, targets):
    bp = None; bd = 1e18
    for tp in targets:
        d = _dist(p, tp)
        if d < bd: bd = d; bp = tp
    return bp, bd
def _closest_border_pos(p, targets, segs):
    bp = None; bd = 1e18
    for a, b in segs:
        c, d = _closest_on_seg(p, a, b)
        if d < bd: bd = d; bp = c
    if bp is None: return _closest_pos(p, targets)
    return bp, bd
def _build_edge_data(edges):
    if not edges: raise RuntimeError("No selected moving edges found.")
    data = []; first = None
    for c in edges:
        shape = _mesh_shape(c); eid = _edge_id(c)
        if shape is None or eid is None: continue
        if first is None: first = shape
        elif shape != first: raise RuntimeError("One edge loop group must be from one mesh only.")
        fn = _fn(shape); v0, v1 = fn.getEdgeVertices(eid)
        a = _v(fn.getPoint(v0, oma.MSpace.kWorld))
        b = _v(fn.getPoint(v1, oma.MSpace.kWorld))
        data.append({"mesh_shape": shape, "edge_id": eid, "start": a, "end": b})
    if not data: raise RuntimeError("No valid moving edges found.")
    return data
def _find_current_edge(shape, orig_a, orig_b, target, tol=None):
    orig_len = _dist(orig_a, orig_b)
    if orig_len < 1e-7:
        return None, None
    endpoint_tol = max(0.00001, orig_len * 0.001)
    target_tol   = max(0.0001,  orig_len * 0.01)
    min_sub_len  = orig_len * 0.05

    dag = _dag(shape); fn = oma.MFnMesh(dag); it = oma.MItMeshEdge(dag)
    best_e = None; best_t = None; best_d = 1e18
    while not it.isDone():
        eid = it.index()
        try: v0, v1 = fn.getEdgeVertices(eid)
        except Exception: it.next(); continue
        a = _v(fn.getPoint(v0, oma.MSpace.kWorld))
        b = _v(fn.getPoint(v1, oma.MSpace.kWorld))
        if _dist(a, b) < min_sub_len:
            it.next(); continue
        ta, da = _point_on_seg(a, orig_a, orig_b)
        tb, db = _point_on_seg(b, orig_a, orig_b)
        if (ta is None or tb is None
                or da > endpoint_tol or db > endpoint_tol
                or ta < -0.001 or ta > 1.001
                or tb < -0.001 or tb > 1.001):
            it.next(); continue
        lt, d = _point_on_seg(target, a, b)
        if lt is not None and d <= target_tol and 0.0001 < lt < 0.9999 and d < best_d:
            best_d = d; best_e = eid; best_t = lt
        it.next()
    return best_e, best_t
def _add_split_points(edge_data, split_count, _debug=False):
    if split_count <= 0: return
    for d in edge_data:
        shape = d["mesh_shape"]; a = d["start"]; b = d["end"]
        vec = b - a; l = vec.length()
        if l < 1e-7: continue
        placed = 0
        for i in reversed(range(1, split_count + 1)):
            t      = float(i) / float(split_count + 1)
            target = a + vec * t
            ce, cp = _find_current_edge(shape, a, b, target)
            if ce is None:
                continue
            mel.eval('polySplit -ch on -s 1 -sma 0 -ief 0 -ep %d %.10f "%s";' % (ce, cp, _q(shape)))
            placed += 1
def _collect_verts(shape, edge_data):
    fn = _fn(shape); segs = []
    for d in edge_data:
        a = d["start"]; b = d["end"]; l = _dist(a, b)
        if l > 1e-7: segs.append((a, b, l))
    if not segs: raise RuntimeError("No valid original edge segments.")
    tol = max(0.00001, (sum(s[2] for s in segs) / float(len(segs))) * 0.0005)
    found = []
    pts = fn.getPoints(oma.MSpace.kWorld)
    for i in range(len(pts)):
        p = _v(pts[i])
        for a, b, l in segs:
            t, d = _point_on_seg(p, a, b)
            if t is not None and d <= tol and -0.001 <= t <= 1.001:
                found.append(i); break
    found = sorted(set(found))
    if not found: raise RuntimeError("Could not collect moving vertices after split.")
    return found
def _edge_group_to_points_and_segs(edge_group):
    edges = mc.filterExpand(mc.ls(edge_group, fl=True, long=True), sm=32) or []
    if not edges:
        return [], []
    shape = _mesh_shape(edges[0])
    if not shape:
        return [], []
    fn = _fn(shape)
    pts_map = {}
    segs = []
    for e in edges:
        eid = _edge_id(e)
        if eid is None:
            continue
        try:
            v0, v1 = fn.getEdgeVertices(eid)
        except Exception:
            continue
        a = _v(fn.getPoint(v0, oma.MSpace.kWorld))
        b = _v(fn.getPoint(v1, oma.MSpace.kWorld))
        pts_map[int(v0)] = a
        pts_map[int(v1)] = b
        segs.append((a, b))
    return list(pts_map.values()), segs

def _save_component_groups(prefix, groups):
    _delete_matches(prefix + "*")
    for i, grp in enumerate(groups or []):
        comps = mc.filterExpand(mc.ls(grp, fl=True, long=True), sm=32) or []
        if comps:
            mc.sets(comps, name="%s%d" % (prefix, i), text="gCharacterSet")
def _load_component_groups(prefix, sm=32):
    result = []
    set_names = sorted(mc.ls(prefix + "*", type="objectSet") or [])
    for s in set_names:
        raw = mc.sets(s, q=True) or []
        comps = mc.filterExpand(mc.ls(raw, fl=True, long=True), sm=sm) or []
        if comps:
            result.append(comps)
    return result
def _avg_vec(points):
    if not points:
        return oma.MVector()
    total = oma.MVector()
    for p in points:
        total += p
    return total / float(len(points))
def _polyline_lengths(points):
    lengths = [0.0]
    total = 0.0
    for i in range(len(points) - 1):
        total += _dist(points[i], points[i + 1])
        lengths.append(total)
    return lengths, total
def _resample_polyline(points, count):
    if not points or count <= 0:
        return []
    if len(points) == 1 or count == 1:
        return [points[0] for _ in range(count)]
    lengths, total = _polyline_lengths(points)
    if total < 1e-8:
        return [points[0] for _ in range(count)]
    result = []
    for i in range(count):
        target = total * (float(i) / float(max(1, count - 1)))
        j = 0
        while j < len(lengths) - 2 and lengths[j + 1] < target:
            j += 1
        seg_len = max(1e-8, lengths[j + 1] - lengths[j])
        t = (target - lengths[j]) / seg_len
        result.append(points[j] + (points[j + 1] - points[j]) * t)
    return result
def _ordered_edge_chain_data(edge_group):
    edges = mc.filterExpand(mc.ls(edge_group, fl=True, long=True), sm=32) or []
    if not edges:
        return None
    shape = _mesh_shape(edges[0])
    if not shape:
        return None
    fn = _fn(shape)
    base = edges[0].rsplit('.', 1)[0]
    e2v = {}
    v2e = defaultdict(list)
    for e in edges:
        if e.rsplit('.', 1)[0] != base:
            continue
        eid = _edge_id(e)
        if eid is None:
            continue
        try:
            v0, v1 = fn.getEdgeVertices(eid)
        except Exception:
            continue
        e2v[eid] = (int(v0), int(v1))
        v2e[int(v0)].append(eid)
        v2e[int(v1)].append(eid)
    if not e2v:
        return None
    endpoints = [v for v, es in v2e.items() if len(es) == 1]
    start_v = endpoints[0] if endpoints else e2v[next(iter(e2v))][0]
    ordered_edges = []
    ordered_verts = [start_v]
    visited = set()
    current_v = start_v
    previous_e = None
    max_steps = len(e2v) + 5
    for _ in range(max_steps):
        candidates = [e for e in v2e.get(current_v, []) if e != previous_e and e not in visited]
        if not candidates:
            break
        eid = candidates[0]
        visited.add(eid)
        ordered_edges.append(eid)
        a, b = e2v[eid]
        next_v = b if current_v == a else a
        ordered_verts.append(next_v)
        previous_e = eid
        current_v = next_v
        if len(visited) == len(e2v):
            break
    if len(visited) != len(e2v):
        ordered_edges = sorted(e2v.keys())
        ordered_verts = []
        for eid in ordered_edges:
            a, b = e2v[eid]
            if not ordered_verts:
                ordered_verts.extend([a, b])
            elif ordered_verts[-1] == a:
                ordered_verts.append(b)
            elif ordered_verts[-1] == b:
                ordered_verts.append(a)
    ordered_verts = [v for i, v in enumerate(ordered_verts) if i == 0 or v != ordered_verts[i - 1]]
    positions = [_vtx_pos(shape, v, fn) for v in ordered_verts]
    return {"shape": shape, "verts": ordered_verts, "positions": positions, "center": _avg_vec(positions)}
def _cleanup_scene():
    _delete_matches(["reMeshCurve*", TARGET_NAME_SIMPLE])
def _set_poly_component_mode(mesh_name, mode):
    mel.eval('doMenuComponentSelectionExt("%s", "%s", 0);' % (_q(mesh_name), mode))

SIDE_VTX_PREFIX = "sideEdgeSave"
CAP_VTX_PREFIX  = "capEdgeSave"
LOFT_SIDE_VTX_PREFIX = "loftSideEdgeSave"
LOFT_CAP_VTX_PREFIX  = "loftCapEdgeSave"

def _vtx_set_name(prefix, index):
    return "%s%d_vtx" % (prefix, index)

def _edge_group_to_vtx_ids(edge_group):
    edges = mc.filterExpand(mc.ls(edge_group, fl=True, long=True), sm=32) or []
    if not edges:
        return None, []
    shape = _mesh_shape(edges[0])
    if not shape:
        return None, []
    fn = _fn(shape)
    ids = set()
    for e in edges:
        eid = _edge_id(e)
        if eid is None:
            continue
        try:
            v0, v1 = fn.getEdgeVertices(eid)
            ids.add(int(v0))
            ids.add(int(v1))
        except Exception:
            continue
    return shape, sorted(ids)

def _grp_corner_positions(edge_group):
    data = _ordered_edge_chain_data(edge_group)
    if not data or len(data["positions"]) < 2:
        return None, None
    return data["positions"][0], data["positions"][-1]

def _corners_match(src_a, src_b, loft_a, loft_b, tol=1e-4):
    fwd = (_dist(src_a, loft_a) < tol and _dist(src_b, loft_b) < tol)
    rev = (_dist(src_a, loft_b) < tol and _dist(src_b, loft_a) < tol)
    return fwd or rev

def _match_groups_by_corners(src_groups, loft_groups):

    def _pos_library(edge_group):
        shape, ids = _edge_group_to_vtx_ids(edge_group)
        if not shape or not ids:
            return frozenset()
        fn = _fn(shape)
        pts = set()
        for vid in ids:
            p = _vtx_pos(shape, vid, fn)
            pts.add((round(p.x, 4), round(p.y, 4), round(p.z, 4)))
        return frozenset(pts)

    src_libs  = [_pos_library(g) for g in src_groups]
    loft_libs = [_pos_library(g) for g in loft_groups]

    used  = set()
    pairs = []

    for i, src_lib in enumerate(src_libs):
        matched_j     = None
        best_shared   = 0

        for j, loft_lib in enumerate(loft_libs):
            if j in used:
                continue
            shared = len(src_lib & loft_lib)
            if shared > best_shared:
                best_shared = shared
                matched_j   = j

        if matched_j is not None and best_shared >= 2:
            used.add(matched_j)
            pairs.append((src_groups[i], loft_groups[matched_j]))
        elif matched_j is not None and best_shared == 1:
            used.add(matched_j)
            pairs.append((src_groups[i], loft_groups[matched_j]))
        else:
            pairs.append((src_groups[i], None))

    return pairs

def _make_vtx_quick_sets(src_groups, loft_groups, src_prefix, loft_prefix):
    _delete_matches([src_prefix  + "*_vtx",
                     loft_prefix + "*_vtx"])

    if not src_groups or not loft_groups:
        return

    pairs = _match_groups_by_corners(src_groups, loft_groups)

    for idx, (src_grp, loft_grp) in enumerate(pairs):
        src_shape, src_ids = _edge_group_to_vtx_ids(src_grp)
        if src_shape and src_ids:
            tr = _mesh_tr(src_shape)
            comps = ["%s.vtx[%d]" % (tr, v) for v in src_ids]
            sn = _vtx_set_name(src_prefix, idx)
            if mc.objExists(sn):
                mc.delete(sn)
            mc.sets(comps, name=sn, text="gCharacterSet")

        if loft_grp:
            loft_shape, loft_ids = _edge_group_to_vtx_ids(loft_grp)
            if loft_shape and loft_ids:
                tr = _mesh_tr(loft_shape)
                comps = ["%s.vtx[%d]" % (tr, v) for v in loft_ids]
                ln = _vtx_set_name(loft_prefix, idx)
                if mc.objExists(ln):
                    mc.delete(ln)
                mc.sets(comps, name=ln, text="gCharacterSet")

def _rebuild_vtx_quick_sets():
    raw_side = (mc.ls(
        mc.filterExpand(
            mc.ls(mc.sets("borderEdgeSave", q=True) or [], fl=True, long=True),
            sm=32) or [], fl=True, long=True) or []) if mc.objExists("borderEdgeSave") else []
    src_side_grps = _multi_loop_groups(raw_side) if raw_side else []
    src_cap_grps  = _load_component_groups(CAP_SET_PREFIX, sm=32)

    target_name = TARGET_NAME_SIMPLE if smoothFL_simple_mode else TARGET_NAME
    loft_cls = None
    if mc.objExists(target_name):
        loft_faces = mc.filterExpand(
            mc.polyListComponentConversion(target_name, tf=True),
            sm=34, ex=True) or []
        loft_cls = _cd_classify_patch(loft_faces) if loft_faces else None

    loft_side_grps = loft_cls.get("side_edge_groups", []) if loft_cls else []
    loft_cap_grps  = loft_cls.get("cap_edge_groups",  []) if loft_cls else []

    _delete_matches([
        SIDE_VTX_PREFIX      + "*_vtx",
        CAP_VTX_PREFIX       + "*_vtx",
        LOFT_SIDE_VTX_PREFIX + "*_vtx",
        LOFT_CAP_VTX_PREFIX  + "*_vtx",
    ])

    src_labelled = (
        [("side", i, g) for i, g in enumerate(src_side_grps)] +
        [("cap",  i, g) for i, g in enumerate(src_cap_grps)]
    )
    all_loft_grps = loft_side_grps + loft_cap_grps

    if not src_labelled or not all_loft_grps:
        return

    def _pos_lib(edge_group):
        shape, ids = _edge_group_to_vtx_ids(edge_group)
        if not shape or not ids:
            return frozenset()
        fn = _fn(shape)
        pts = set()
        for vid in ids:
            p = _vtx_pos(shape, vid, fn)
            pts.add((round(p.x, 4), round(p.y, 4), round(p.z, 4)))
        return frozenset(pts)

    src_libs  = [_pos_lib(g) for _, _, g in src_labelled]
    loft_libs = [_pos_lib(g) for g in all_loft_grps]

    used = set()
    for i, (src_type, src_idx, src_grp) in enumerate(src_labelled):
        best_j      = None
        best_shared = 0
        for j, loft_lib in enumerate(loft_libs):
            if j in used:
                continue
            shared = len(src_libs[i] & loft_lib)
            if shared > best_shared:
                best_shared = shared
                best_j      = j

        src_set_prefix  = SIDE_VTX_PREFIX if src_type == "side" else CAP_VTX_PREFIX
        loft_set_prefix = LOFT_SIDE_VTX_PREFIX if src_type == "side" else LOFT_CAP_VTX_PREFIX

        src_shape, src_ids = _edge_group_to_vtx_ids(src_grp)
        if src_shape and src_ids:
            tr    = _mesh_tr(src_shape)
            comps = ["%s.vtx[%d]" % (tr, v) for v in src_ids]
            sn    = _vtx_set_name(src_set_prefix, src_idx)
            if mc.objExists(sn):
                mc.delete(sn)
            mc.sets(comps, name=sn, text="gCharacterSet")

        if best_j is not None and best_shared >= 1:
            shared_pts = sorted(src_libs[i] & loft_libs[best_j])
            used.add(best_j)
            loft_grp = all_loft_grps[best_j]
            loft_shape, loft_ids = _edge_group_to_vtx_ids(loft_grp)
            if loft_shape and loft_ids:
                tr    = _mesh_tr(loft_shape)
                comps = ["%s.vtx[%d]" % (tr, v) for v in loft_ids]
                ln    = _vtx_set_name(loft_set_prefix, src_idx)
                if mc.objExists(ln):
                    mc.delete(ln)
                mc.sets(comps, name=ln, text="gCharacterSet")

def _cd_warn(msg):
    mc.warning("[faceLoopPatch cornerDetect] %s" % msg)

def _cd_ints_after_colon(info):
    result = []
    for line in info or []:
        if ":" in line:
            line = line.split(":", 1)[1]
        result += [int(x) for x in re.findall(r"\d+", line)]
    return result

def _cd_v_sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def _cd_v_dot(a, b): return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]
def _cd_v_len(a):    return math.sqrt(_cd_v_dot(a, a))
def _cd_v_norm(a):
    l = _cd_v_len(a)
    if l < 1e-6: return (0.0, 0.0, 0.0)
    return (a[0]/l, a[1]/l, a[2]/l)
def _cd_dist(a, b): return _cd_v_len(_cd_v_sub(a, b))

def _cd_analyze_one_mesh(obj, obj_faces):
    edge_face_count = Counter()
    vtx_face_count  = Counter()
    for line in (mc.polyInfo(obj_faces, fe=True) or []):
        for e in _cd_ints_after_colon([line]): edge_face_count[e] += 1
    for line in (mc.polyInfo(obj_faces, fv=True) or []):
        for v in _cd_ints_after_colon([line]): vtx_face_count[v]  += 1
    border_edges = sorted([e for e, c in edge_face_count.items() if c == 1])
    edge_to_vtx  = {}
    vtx_to_edges = defaultdict(list)
    if border_edges:
        ev_comps = ["{}.e[{}]".format(obj, e) for e in border_edges]
        ev_lines = mc.polyInfo(ev_comps, ev=True) or []
        for e, line in zip(border_edges, ev_lines):
            vtxs = _cd_ints_after_colon([line])
            if len(vtxs) != 2: continue
            a, b = vtxs
            edge_to_vtx[e] = (a, b)
            vtx_to_edges[a].append(e)
            vtx_to_edges[b].append(e)
    return {
        "obj": obj, "faces": obj_faces, "border_edges": border_edges,
        "edge_to_vtx": edge_to_vtx, "vtx_to_edges": vtx_to_edges,
        "vtx_face_count": vtx_face_count
    }

def _cd_walk_one_loop(data, start_edge, start_v):
    edge_to_vtx  = data["edge_to_vtx"]
    vtx_to_edges = data["vtx_to_edges"]
    loop_edges, loop_vertices, visited = [], [], set()
    current_edge, current_v = start_edge, start_v
    for _ in range(len(data["border_edges"]) + 10):
        if current_edge in visited: return None
        visited.add(current_edge)
        loop_edges.append(current_edge)
        loop_vertices.append(current_v)
        a, b = edge_to_vtx[current_edge]
        next_v = b if current_v == a else (a if current_v == b else None)
        if next_v is None: return None
        if next_v == start_v:
            return {"edges": loop_edges, "vertices": loop_vertices, "visited": visited}
        next_edges = [e for e in vtx_to_edges[next_v] if e != current_edge]
        if len(next_edges) != 1: return None
        current_v, current_edge = next_v, next_edges[0]
    return None

def _cd_build_border_loop(data):
    obj = data["obj"]
    border_edges = data["border_edges"]
    edge_to_vtx  = data["edge_to_vtx"]
    vtx_to_edges = data["vtx_to_edges"]
    if not border_edges:
        _cd_warn("{} has no border edges.".format(obj)); return False
    bad = [v for v, es in vtx_to_edges.items() if len(es) != 2]
    if bad:
        _cd_warn("{} border not closed loop. Bad vtxs: {}".format(obj, len(bad))); return False
    unvisited = set(border_edges)
    loops = []
    while unvisited:
        start_edge = list(unvisited)[0]
        start_v = edge_to_vtx[start_edge][0]
        loop = _cd_walk_one_loop(data, start_edge, start_v)
        if not loop:
            _cd_warn("{} border loop walk failed.".format(obj)); return False
        loops.append(loop)
        for e in loop["visited"]:
            unvisited.discard(e)
    loops.sort(key=lambda x: len(x["edges"]), reverse=True)
    if len(loops) > 1:
        _cd_warn("{} multiple loops; using longest.".format(obj))
    main = loops[0]
    data["loop_edges"]    = main["edges"]
    data["loop_vertices"] = main["vertices"]
    return True

def _cd_get_loop_positions(obj, loop_vertices):
    shape = _mesh_shape(obj)
    if shape is None:
        return [tuple(mc.xform("{}.vtx[{}]".format(obj, v), q=True, ws=True, t=True))
                for v in loop_vertices]
    fn = _fn(shape)
    out = []
    for v in loop_vertices:
        p = fn.getPoint(v, oma.MSpace.kWorld)
        out.append((p.x, p.y, p.z))
    return out

def _cd_build_pos_cache(obj, loop_vertices, edge_to_vtx):
    all_vtx = set(loop_vertices)
    for a, b in edge_to_vtx.values():
        all_vtx.add(a)
        all_vtx.add(b)
    shape = _mesh_shape(obj)
    if shape:
        fn = _fn(shape)
        cache = {}
        for v in all_vtx:
            p = fn.getPoint(v, oma.MSpace.kWorld)
            cache[v] = (p.x, p.y, p.z)
    else:
        cache = {}
        for v in all_vtx:
            cache[v] = tuple(mc.xform("{}.vtx[{}]".format(obj, v), q=True, ws=True, t=True))
    return cache

def _cd_topo_angle_at_loop_idx(i, loop_vertices, edge_to_vtx, vtx_to_edges, pos_cache):
    vtx = loop_vertices[i]
    edges = vtx_to_edges.get(vtx, [])
    if len(edges) != 2:
        return 180.0
    pos_v = pos_cache.get(vtx)
    if pos_v is None:
        return 180.0
    nbrs = []
    for e in edges:
        a, b = edge_to_vtx[e]
        nbrs.append(b if a == vtx else a)
    pos_a = pos_cache.get(nbrs[0])
    pos_b = pos_cache.get(nbrs[1])
    if pos_a is None or pos_b is None:
        return 180.0
    vec_a = _cd_v_norm(_cd_v_sub(pos_a, pos_v))
    vec_b = _cd_v_norm(_cd_v_sub(pos_b, pos_v))
    if _cd_v_len(vec_a) < 1e-6 or _cd_v_len(vec_b) < 1e-6:
        return 180.0
    d = max(-1.0, min(1.0, _cd_v_dot(vec_a, vec_b)))
    return math.degrees(math.acos(d))

def _cd_turn_scores(positions, data=None):
    n = len(positions)
    if n < 4: return []
    if data is not None:
        obj           = data["obj"]
        loop_vertices = data["loop_vertices"]
        edge_to_vtx   = data["edge_to_vtx"]
        vtx_to_edges  = data["vtx_to_edges"]
        pos_cache     = _cd_build_pos_cache(obj, loop_vertices, edge_to_vtx)
        return [
            _cd_topo_angle_at_loop_idx(i, loop_vertices, edge_to_vtx, vtx_to_edges, pos_cache)
            for i in range(n)
        ]
    win = max(1, min(5, n // 14))
    scores = []
    for i in range(n):
        v1 = _cd_v_norm(_cd_v_sub(positions[i], positions[(i - win) % n]))
        v2 = _cd_v_norm(_cd_v_sub(positions[(i + win) % n], positions[i]))
        d = max(-1.0, min(1.0, _cd_v_dot(v1, v2)))
        scores.append(math.degrees(math.acos(d)))
    return scores

def _cd_edge_lengths_from_positions(positions):
    n = len(positions)
    return [_cd_dist(positions[i], positions[(i + 1) % n]) for i in range(n)]

def _cd_cyclic_count(a, b, n):
    return (b - a) if b > a else (n - a + b)

def _cd_cyclic_length(a, b, prefix, total):
    return (prefix[b] - prefix[a]) if b > a else (total - prefix[a] + prefix[b])

def _cd_segment_lengths(indices, edge_lengths):
    n = len(edge_lengths)
    indices = sorted(indices)
    prefix = [0.0]
    for l in edge_lengths: prefix.append(prefix[-1] + l)
    total = prefix[-1]
    counts, worlds = [], []
    for i in range(4):
        a, b = indices[i], indices[(i + 1) % 4]
        counts.append(_cd_cyclic_count(a, b, n))
        worlds.append(_cd_cyclic_length(a, b, prefix, total))
    return counts, worlds

def _cd_face_factor(fc):
    if fc <= 1: return 1.0
    if fc == 2: return 0.30
    if fc == 3: return 0.10
    return 0.03

def _cd_corner_likelihood(scores, vtx_face_count, loop_vertices):
    out = []
    for i, v in enumerate(loop_vertices):
        out.append(scores[i] * _cd_face_factor(vtx_face_count.get(v, 9999)))
    return out

def _cd_local_max_candidates(values, keep=24):
    n = len(values)
    result = [i for i in range(n)
              if values[i] >= values[(i - 1) % n] and values[i] >= values[(i + 1) % n]]
    return sorted(result, key=lambda i: values[i], reverse=True)[:keep]

CD_TOP_N_SHARP = 8
CD_MIN_CORNER_TURN = 45.0
CD_MAX_CORNER_TURN = 135.0
CD_MAX_CORNER_TURN_FC1 = 150.0

def _cd_is_valid_corner_turn(angle, fc=9999):
    max_turn = CD_MAX_CORNER_TURN_FC1 if fc <= 1 else CD_MAX_CORNER_TURN
    return CD_MIN_CORNER_TURN < angle < max_turn

def _cd_corner_score_90(angle):
    return 90.0 - abs(angle - 90.0)

def _cd_corner_candidate_order(data, scores):
    loop_vertices  = data["loop_vertices"]
    vtx_face_count = data["vtx_face_count"]

    def key(i):
        v  = loop_vertices[i]
        fc = vtx_face_count.get(v, 9999)
        cs = _cd_corner_score_90(scores[i])
        one_face_bucket = 0 if fc <= 1 else 1
        multi_fc = 0 if fc <= 1 else fc
        return (one_face_bucket, -cs, multi_fc, i)

    eligible = [i for i in range(len(scores))
                if _cd_is_valid_corner_turn(scores[i],
                    fc=vtx_face_count.get(loop_vertices[i], 9999))]
    return sorted(eligible, key=key)

def _cd_top_sharp_indices(data, scores, n_top=CD_TOP_N_SHARP):
    return sorted(_cd_corner_candidate_order(data, scores)[:n_top])

def _cd_corner_candidates(data, scores):
    candidates = _cd_top_sharp_indices(data, scores)
    if len(candidates) < 4:
        _cd_warn(
            "Only {} corner candidates found (need 4). Use 'Curves From Selected Edges' to bypass.".format(
                len(candidates)))
        return None
    return sorted(candidates)

def _cd_classify_segments(counts, worlds):
    pair_a = (0, 2)
    pair_b = (1, 3)
    a_count = max(counts[0], counts[2])
    b_count = max(counts[1], counts[3])
    if a_count > b_count:
        return pair_a, pair_b
    if b_count > a_count:
        return pair_b, pair_a
    a_world = worlds[0] + worlds[2]
    b_world = worlds[1] + worlds[3]
    if a_world >= b_world:
        return pair_a, pair_b
    return pair_b, pair_a

def _cd_score_combo(combo, data, scores, edge_lengths):
    combo = sorted(combo)
    counts, worlds = _cd_segment_lengths(combo, edge_lengths)
    if min(counts) < 1: return None
    side_ids, cap_ids = _cd_classify_segments(counts, worlds)
    s_c_avg = (counts[side_ids[0]] + counts[side_ids[1]]) * 0.5
    c_c_avg = (counts[cap_ids[0]]  + counts[cap_ids[1]])  * 0.5
    s_w_avg = (worlds[side_ids[0]] + worlds[side_ids[1]]) * 0.5
    c_w_avg = (worlds[cap_ids[0]]  + worlds[cap_ids[1]])  * 0.5
    if s_c_avg <= 0 or s_w_avg <= 1e-6: return None
    sbc = abs(counts[side_ids[0]] - counts[side_ids[1]]) / max(1.0, s_c_avg)
    cbc = abs(counts[cap_ids[0]]  - counts[cap_ids[1]])  / max(1.0, c_c_avg)
    sbw = abs(worlds[side_ids[0]] - worlds[side_ids[1]]) / max(1e-6, s_w_avg)
    cbw = abs(worlds[cap_ids[0]]  - worlds[cap_ids[1]])  / max(1e-6, c_w_avg)
    r_c = c_c_avg / max(1.0, s_c_avg)
    r_w = c_w_avg / max(1e-6, s_w_avg)
    shortest_two_w = sorted(range(4), key=lambda i: worlds[i])[:2]
    sp_pen = 8.0 if set(shortest_two_w) != set(cap_ids) else 0.0
    total_w = sum(worlds)
    deg_pen = 0.0
    if total_w > 1e-6:
        for w in worlds:
            frac = w / total_w
            if frac < 0.03: deg_pen += (0.03 - frac) * 300.0
    lv = data["loop_vertices"]; vfc = data["vtx_face_count"]
    bonus = 0.0
    for i in combo:
        fc = vfc.get(lv[i], 9999)
        bonus += _cd_corner_score_90(scores[i]) * 0.5
        if   fc == 1: pass
        elif fc == 2: bonus -= 20.0
        else:         bonus -= 50.0
    score = (sp_pen + deg_pen
             + sbc*1.0 + sbw*8.0
             + cbc*1.0 + cbw*5.0
             + r_c*1.0 + r_w*2.5
             - bonus*1.0)
    return score, side_ids, cap_ids, counts, worlds

def _cd_point_line_distance(p, a, b):
    ab = _cd_v_sub(b, a)
    ap = _cd_v_sub(p, a)
    ab_len = _cd_v_len(ab)
    if ab_len < 1e-9:
        return _cd_v_len(ap)
    cross = (ab[1]*ap[2] - ab[2]*ap[1],
             ab[2]*ap[0] - ab[0]*ap[2],
             ab[0]*ap[1] - ab[1]*ap[0])
    return _cd_v_len(cross) / ab_len

def _cd_find_corners_via_max_deviation(positions):
    n = len(positions)
    if n < 4:
        return None
    cx = sum(p[0] for p in positions) / n
    cy = sum(p[1] for p in positions) / n
    cz = sum(p[2] for p in positions) / n
    centroid = (cx, cy, cz)
    p1 = max(range(n), key=lambda i: _cd_dist(positions[i], centroid))
    p2 = max(range(n), key=lambda i: _cd_dist(positions[i], positions[p1]))
    if p1 == p2:
        return None
    a, b = sorted([p1, p2])
    arc1 = list(range(a + 1, b))
    arc2 = list(range(b + 1, n)) + list(range(0, a))
    def max_dev(arc):
        best_i, best_d = None, -1.0
        for i in arc:
            d = _cd_point_line_distance(positions[i], positions[p1], positions[p2])
            if d > best_d:
                best_d, best_i = d, i
        return best_i
    p3 = max_dev(arc1)
    p4 = max_dev(arc2)
    if p3 is None or p4 is None:
        return None
    corners = sorted({p1, p2, p3, p4})
    if len(corners) != 4:
        return None
    return corners

def _cd_find_corners_via_smooth_sides(data, scores, edge_lengths):
    loop_vertices  = data["loop_vertices"]
    vtx_face_count = data["vtx_face_count"]
    n = len(scores)
    top_sharp = _cd_top_sharp_indices(data, scores)
    if len(top_sharp) < 4:
        return None
    sharp_indices = sorted(top_sharp)
    prefix = [0.0]
    for l in edge_lengths:
        prefix.append(prefix[-1] + l)
    total = prefix[-1]
    def arc(a, b):
        return (prefix[b] - prefix[a]) if b > a else (total - prefix[a] + prefix[b])
    arcs = []
    m = len(sharp_indices)
    for k in range(m):
        a = sharp_indices[k]
        b = sharp_indices[(k + 1) % m]
        arcs.append((arc(a, b), a, b))
    arcs.sort(reverse=True)
    if len(arcs) < 2:
        return None
    _, a1, b1 = arcs[0]
    _, a2, b2 = arcs[1]
    corner_set = {a1, b1, a2, b2}
    if len(corner_set) != 4:
        return None
    return sorted(corner_set)

def _cd_rescue_fourth_corner(data, scores, pool3):
    obj           = data["obj"]
    loop_vertices = data["loop_vertices"]
    n             = len(loop_vertices)
    positions    = _cd_get_loop_positions(obj, loop_vertices)
    edge_lengths = _cd_edge_lengths_from_positions(positions)
    pool_set   = set(pool3)
    best_idx   = None
    best_score = None
    for i in range(n):
        if i in pool_set:
            continue
        combo = sorted(pool3 + [i])
        counts, worlds = _cd_segment_lengths(combo, edge_lengths)
        if min(counts) < 1:
            continue
        side_ids, cap_ids = _cd_classify_segments(counts, worlds)
        def _bal(vals, pair):
            a, b = vals[pair[0]], vals[pair[1]]
            return abs(a - b) / max(1e-6, (a + b) * 0.5)
        sbw = _bal(worlds, side_ids)
        cbw = _bal(worlds, cap_ids)
        score = max(sbw, cbw)
        if best_score is None or score < best_score:
            best_score = score
            best_idx   = i
    if best_idx is not None:
        return pool3 + [best_idx]
    mc.warning("[faceLoopPatch] 3-pt rescue: no valid 4th candidate found.")
    return pool3

def _cd_find_best_corner_solution(data):
    if not _cd_build_border_loop(data): return None
    obj = data["obj"]
    loop_vertices = data["loop_vertices"]
    loop_edges    = data["loop_edges"]
    positions    = _cd_get_loop_positions(obj, loop_vertices)
    scores       = _cd_turn_scores(positions, data)
    edge_lengths = _cd_edge_lengths_from_positions(positions)

    method = "top4_valid45_135_fc1_first_by_90score"
    ranked = _cd_corner_candidate_order(data, scores)
    top4 = ranked[:4]

    if len(top4) == 3:
        top4 = _cd_rescue_fourth_corner(data, scores, top4)

    if len(top4) < 4:
        _cd_warn("{} fewer than 4 usable corner candidates after 45-135 turn filter.".format(obj)); return None
    corners = sorted(top4)

    counts, worlds = _cd_segment_lengths(corners, edge_lengths)
    side_ids, cap_ids = _cd_classify_segments(counts, worlds)

    s_w_avg = (worlds[side_ids[0]] + worlds[side_ids[1]]) * 0.5
    c_w_avg = (worlds[cap_ids[0]]  + worlds[cap_ids[1]])  * 0.5
    sbw = abs(worlds[side_ids[0]] - worlds[side_ids[1]]) / max(1e-6, s_w_avg)
    cbw = abs(worlds[cap_ids[0]]  - worlds[cap_ids[1]])  / max(1e-6, c_w_avg)

    segments = []
    for i in range(4):
        a, b = corners[i], corners[(i + 1) % 4]
        seg = loop_edges[a:b] if b > a else (loop_edges[a:] + loop_edges[:b])
        segments.append(seg)

    return {
        "corner_indices": corners,
        "side_ids": side_ids,
        "cap_ids": cap_ids,
        "counts": counts,
        "worlds": worlds,
        "segments": segments,
        "loop_vertices": loop_vertices,
        "scores": scores,
        "face_counts_in_loop": [data["vtx_face_count"].get(v, 0) for v in loop_vertices],
        "method": method,
        "side_world_balance": sbw,
        "cap_world_balance": cbw,
    }

def _cd_classify_patch(faces):
    faces = mc.ls(faces, fl=True, long=True) or []
    if not faces:
        return None
    by_obj = defaultdict(list)
    for f in faces:
        by_obj[f.rsplit(".", 1)[0]].append(f)
    side_groups = []
    cap_groups  = []
    cap_counts  = []
    for obj, obj_faces in by_obj.items():
        data = _cd_analyze_one_mesh(obj, obj_faces)
        solution = _cd_find_best_corner_solution(data)
        if not solution:
            continue
        segments = solution["segments"]
        side_ids = solution["side_ids"]
        cap_ids  = solution["cap_ids"]
        counts   = solution["counts"]
        for sid in side_ids:
            side_groups.append(["{}.e[{}]".format(obj, eid) for eid in segments[sid]])
        for cid in cap_ids:
            cap_groups.append(["{}.e[{}]".format(obj, eid) for eid in segments[cid]])
        cap_counts.append(max(counts[cap_ids[0]], counts[cap_ids[1]]))
    if not side_groups:
        return None
    cap_edge_count = max(1, max(cap_counts) if cap_counts else 1)
    return {
        "side_edge_groups": side_groups,
        "cap_edge_groups": cap_groups,
        "cap_edge_count": cap_edge_count
    }

def _order_edge_chain(edges, edge_verts_map):
    edges = list(edges)
    if len(edges) <= 1:
        return edges
    v_to_e = {}
    for e in edges:
        for v in edge_verts_map.get(e, frozenset()):
            v_to_e.setdefault(v, []).append(e)
    start_e = None
    start_v = None
    for v, ve in v_to_e.items():
        if len(ve) == 1:
            start_e = ve[0]
            start_v = v
            break
    if start_e is None:
        start_e = edges[0]
        start_v = next(iter(edge_verts_map.get(start_e, frozenset())), None)
    ordered  = [start_e]
    visited  = {start_e}
    prev_v   = start_v
    for _ in range(len(edges) - 1):
        cur_verts = edge_verts_map.get(ordered[-1], frozenset())
        nxt_v = None
        for v in cur_verts:
            if v != prev_v:
                nxt_v = v
                break
        if nxt_v is None:
            break
        found = False
        for nxt_e in v_to_e.get(nxt_v, []):
            if nxt_e not in visited:
                ordered.append(nxt_e)
                visited.add(nxt_e)
                prev_v = nxt_v
                found = True
                break
        if not found:
            break
    return ordered

def _get_all_profile_loops(sel_faces, side_group_0, side_group_1):
    sel_face_set = set(mc.ls(sel_faces,    fl=True, long=True))
    side1_set    = frozenset(mc.ls(side_group_1, fl=True, long=True))
    face_edges = {}
    edge_verts = {}
    edge_faces = {}
    for f in sel_face_set:
        fe_raw = mc.filterExpand(
            mc.polyListComponentConversion(f, ff=True, te=True), sm=32) or []
        fe_long = mc.ls(fe_raw, fl=True, long=True) or []
        face_edges[f] = fe_long
        for e in fe_long:
            if e not in edge_verts:
                vs = mc.filterExpand(
                    mc.polyListComponentConversion(e, fe=True, tv=True), sm=31) or []
                edge_verts[e] = frozenset(mc.ls(vs, fl=True, long=True) or [])
            edge_faces.setdefault(e, set()).add(f)
    side_verts = set()
    for e in list(mc.ls(side_group_0, fl=True, long=True) or []) + \
             list(mc.ls(side_group_1, fl=True, long=True) or []):
        side_verts |= edge_verts.get(e, frozenset())
    visited_faces = set()
    current       = list(mc.ls(side_group_0, fl=True, long=True))
    all_loops     = [side_group_0]
    for _ in range(1000):
        nxt        = set()
        step_faces = set()
        for e in current:
            ev = edge_verts.get(e, frozenset())
            for f in edge_faces.get(e, set()):
                if f not in sel_face_set or f in visited_faces:
                    continue
                step_faces.add(f)
                for fe in face_edges.get(f, []):
                    if not (ev & edge_verts.get(fe, frozenset())):
                        nxt.add(fe)
        if not nxt:
            break
        visited_faces.update(step_faces)
        if nxt & side1_set:
            all_loops.append(side_group_1)
            break
        nxt = {e for e in nxt if not (edge_verts.get(e, frozenset()) & side_verts)}
        if not nxt:
            all_loops.append(side_group_1)
            break
        ordered = _order_edge_chain(nxt, edge_verts)
        current = ordered
        all_loops.append(ordered)
    if all_loops[-1] is not side_group_1:
        all_loops.append(side_group_1)
    return all_loops

def _is_single_connected_face_region(faces):
    if not faces or len(faces) <= 1:
        return True
    face_long = mc.ls(faces, fl=True, long=True) or []
    face_set  = set(face_long)
    if len(face_set) <= 1:
        return True
    visited = set()
    queue   = [face_long[0]]
    while queue:
        f = queue.pop()
        if f in visited:
            continue
        visited.add(f)
        verts = mc.filterExpand(
            mc.polyListComponentConversion(f, ff=True, tv=True), sm=31) or []
        if verts:
            adj = mc.filterExpand(
                mc.polyListComponentConversion(verts, fv=True, tf=True), sm=34) or []
            for af in (mc.ls(adj, fl=True, long=True) or []):
                if af in face_set and af not in visited:
                    queue.append(af)
    if len(visited) != len(face_set):
        return False
    return True

_fls_debug = {
    "loft_name":              None,
    "loft_shape":             None,
    "source_side_grps":       None,
    "source_cap_grps":        None,
    "source_side_snapshots":  None,
    "source_cap_snapshots":   None,
    "loft_cls":               None,
    "split_done":             False,
}

def _fls_snapshot_groups(grp_list):

    snapshots = []
    for grp in (grp_list or []):
        try:
            snapshots.append(_build_edge_data(grp))
        except Exception as e:
            mc.warning('[fls_debug] snapshot failed: %s' % e)
            snapshots.append([])
    return snapshots

def _fls_chain_world_length(edge_group):

    edges = mc.filterExpand(mc.ls(edge_group, fl=True, long=True), sm=32) or []
    if not edges:
        return 0.0
    shape = _mesh_shape(edges[0])
    if not shape:
        return 0.0
    fn = _fn(shape)
    total = 0.0
    for e in edges:
        eid = _edge_id(e)
        if eid is None:
            continue
        try:
            v0, v1 = fn.getEdgeVertices(eid)
            a = _v(fn.getPoint(v0, oma.MSpace.kWorld))
            b = _v(fn.getPoint(v1, oma.MSpace.kWorld))
            total += _dist(a, b)
        except Exception:
            pass
    return total

def _fls_border_vtx_count(edge_group):

    _, ids = _edge_group_to_vtx_ids(edge_group)
    return len(ids)

def _fls_border_total_length(edge_group):

    return _fls_chain_world_length(edge_group)

def _add_split_points_per_edge(edge_data, splits_list, _debug=False):

    for d, split_count in zip(edge_data, splits_list):
        if split_count <= 0:
            continue
        shape = d["mesh_shape"]
        a     = d["start"]
        b     = d["end"]
        vec   = b - a
        l     = vec.length()
        if l < 1e-7:
            continue
        for i in reversed(range(1, split_count + 1)):
            t      = float(i) / float(split_count + 1)
            target = a + vec * t
            ce, cp = _find_current_edge(shape, a, b, target)
            if ce is None:
                continue
            mel.eval('polySplit -ch on -s 1 -sma 0 -ief 0 -ep %d %.10f "%s";'
                     % (ce, cp, _q(shape)))

def _fls_grp_centroid_from_snapshot(snapshot):

    pts = []
    for d in snapshot:
        pts.append(d["start"])
        pts.append(d["end"])
    if not pts:
        return oma.MVector()
    total = oma.MVector()
    for p in pts:
        total += p
    return total / float(len(pts))

def _fls_grp_centroid_from_edges(edge_group):

    pts, _ = _edge_group_to_points_and_segs(edge_group)
    if not pts:
        return oma.MVector()
    total = oma.MVector()
    for p in pts:
        total += p
    return total / float(len(pts))

def _fls_match_by_centroid(src_items, loft_grps):

    src_centroids  = [_fls_grp_centroid_from_snapshot(snap) for snap, _ in src_items]
    loft_centroids = [_fls_grp_centroid_from_edges(lg) for lg in loft_grps]

    used = set()
    matched = []
    for i, sc in enumerate(src_centroids):
        snap, src_grp = src_items[i]
        best_j, best_d = None, 1e18
        for j, lc in enumerate(loft_centroids):
            if j in used:
                continue
            d = _dist(sc, lc)
            if d < best_d:
                best_d = d
                best_j = j
        if best_j is not None:
            used.add(best_j)
            matched.append((snap, src_grp, loft_grps[best_j]))
        else:
            matched.append((snap, src_grp, None))
    return matched

def _fls_per_edge_splits_for_target(target_edges_data, denser_total_length, denser_vtx_count):
\
\
\
\
\
\
\
\
\
\
\
\

    if denser_vtx_count < 2 or denser_total_length < 1e-7:
        n = len(target_edges_data)
        return [1] * n

    avg_spacing = denser_total_length / float(denser_vtx_count - 1)
    if avg_spacing < 1e-7:
        return [1] * len(target_edges_data)

    per_edge = []

    if target_edges_data and isinstance(target_edges_data[0], dict):

        for d in target_edges_data:
            edge_len = _dist(d["start"], d["end"])
            splits   = int(round(edge_len / avg_spacing)) + 2
            splits   = max(1, min(splits, 20))
            per_edge.append(splits)
    else:

        edges = mc.filterExpand(mc.ls(target_edges_data, fl=True, long=True), sm=32) or []
        if not edges:
            return [1]
        shape = _mesh_shape(edges[0])
        fn    = _fn(shape) if shape else None
        for e in edges:
            eid = _edge_id(e)
            if eid is None or fn is None:
                per_edge.append(1)
                continue
            try:
                v0, v1   = fn.getEdgeVertices(eid)
                a        = _v(fn.getPoint(v0, oma.MSpace.kWorld))
                b        = _v(fn.getPoint(v1, oma.MSpace.kWorld))
                edge_len = _dist(a, b)
                splits   = int(round(edge_len / avg_spacing)) + 2
                splits   = max(1, min(splits, 20))
                per_edge.append(splits)
            except Exception:
                per_edge.append(1)

    return per_edge

def _fls_make_pair(label, snap, src_grp, loft_grp):
    src_vtx_count  = _fls_border_vtx_count(src_grp)  if src_grp  else 0
    loft_vtx_count = _fls_border_vtx_count(loft_grp) if loft_grp else 0
    src_total_len  = _fls_border_total_length(src_grp)  if src_grp  else 0.0
    loft_total_len = _fls_border_total_length(loft_grp) if loft_grp else 0.0
    sc = len(snap)
    lc = len(mc.filterExpand(mc.ls(loft_grp, fl=True, long=True), sm=32) or []) if loft_grp else 0

    empty = {
        "label": label, "source_grp": src_grp, "source_snapshot": snap,
        "loft_grp": loft_grp or [], "source_count": sc, "loft_count": lc,
        "src_vtx_count": src_vtx_count, "loft_vtx_count": loft_vtx_count,
        "src_total_len": src_total_len, "loft_total_len": loft_total_len,
        "split_target": "none", "splits": 0, "per_edge_splits": [],
    }

    if src_vtx_count == 0 or loft_vtx_count == 0:
        return empty

    if loft_vtx_count > src_vtx_count:
        per_edge = _fls_per_edge_splits_for_target(
            snap, loft_total_len, loft_vtx_count)
        return dict(empty,
                    split_target="source",
                    splits=max(per_edge) if per_edge else 1,
                    per_edge_splits=per_edge)

    elif src_vtx_count > loft_vtx_count:
        loft_edges = mc.filterExpand(mc.ls(loft_grp, fl=True, long=True), sm=32) or []
        per_edge   = _fls_per_edge_splits_for_target(
            loft_edges, src_total_len, src_vtx_count)
        return dict(empty,
                    split_target="loft",
                    splits=max(per_edge) if per_edge else 1,
                    per_edge_splits=per_edge)

    else:
        return dict(empty, split_target="none", splits=0, per_edge_splits=[])

def _border_edges_from_vtx_comps(vtx_comps):
    if not vtx_comps:
        return []
    vtx_ids = set()
    for c in vtx_comps:
        m = re.search(r'\.vtx\[(\d+)\]', c)
        if m:
            vtx_ids.add(int(m.group(1)))
    if not vtx_ids:
        return []
    shape = _mesh_shape(vtx_comps[0])
    if not shape:
        return []
    tr  = _mesh_tr(shape)
    dag = _dag(shape)
    fn  = oma.MFnMesh(dag)
    it  = oma.MItMeshEdge(dag)
    result = []
    while not it.isDone():
        if _edge_is_boundary(it):
            v0, v1 = fn.getEdgeVertices(it.index())
            if int(v0) in vtx_ids and int(v1) in vtx_ids:
                result.append("%s.e[%d]" % (tr, it.index()))
        it.next()
    return result

def _stats_from_vtx_set_data(set_name):
    if not mc.objExists(set_name):
        return 0, 0.0, []
    raw      = mc.sets(set_name, q=True) or []
    vtx_comp = mc.filterExpand(mc.ls(raw, fl=True, long=True), sm=31) or []
    n = len(vtx_comp)
    if n == 0:
        return 0, 0.0, []
    border_edges = _border_edges_from_vtx_comps(vtx_comp)
    if border_edges:
        shape = _mesh_shape(border_edges[0])
        fn    = _fn(shape) if shape else None
        total = 0.0
        if fn:
            for e in border_edges:
                eid = _edge_id(e)
                if eid is None:
                    continue
                try:
                    v0, v1 = fn.getEdgeVertices(eid)
                    a = _v(fn.getPoint(v0, oma.MSpace.kWorld))
                    b = _v(fn.getPoint(v1, oma.MSpace.kWorld))
                    total += _dist(a, b)
                except Exception:
                    pass
    else:
        pts   = [mc.xform(v, q=True, ws=True, t=True) for v in vtx_comp]
        total = sum(
            math.sqrt(sum((pts[i][k] - pts[i-1][k])**2 for k in range(3)))
            for i in range(1, n)
        )

    return n, total, vtx_comp

def _fls_analyze_pairs():
    d = _fls_debug

    seg_defs = [
        ("Side 0", SIDE_VTX_PREFIX + "0_vtx", LOFT_SIDE_VTX_PREFIX + "0_vtx"),
        ("Side 1", SIDE_VTX_PREFIX + "1_vtx", LOFT_SIDE_VTX_PREFIX + "1_vtx"),
        ("Cap 0",  CAP_VTX_PREFIX  + "0_vtx", LOFT_CAP_VTX_PREFIX  + "0_vtx"),
        ("Cap 1",  CAP_VTX_PREFIX  + "1_vtx", LOFT_CAP_VTX_PREFIX  + "1_vtx"),
    ]
    side_snaps = d.get("source_side_snapshots") or []
    cap_snaps  = d.get("source_cap_snapshots")  or []

    pairs = []
    for seg_idx, (label, src_set, loft_set) in enumerate(seg_defs):
        sv, sl, src_vtx_comps  = _stats_from_vtx_set_data(src_set)
        lv, ll, loft_vtx_comps = _stats_from_vtx_set_data(loft_set)

        is_cap   = label.startswith("Cap")
        snap_idx = seg_idx - 2 if is_cap else seg_idx
        snap     = (cap_snaps[snap_idx]  if is_cap  else side_snaps[snap_idx]) \
                   if (0 <= snap_idx < (len(cap_snaps) if is_cap else len(side_snaps))) \
                   else []

        loft_grp = []
        if mc.objExists(loft_set):
            raw   = mc.sets(loft_set, q=True) or []
            vtx_c = mc.filterExpand(mc.ls(raw, fl=True, long=True), sm=31) or []
            if vtx_c:
                loft_grp = _border_edges_from_vtx_comps(vtx_c)

        src_grp = []
        if mc.objExists(src_set):
            raw   = mc.sets(src_set, q=True) or []
            vtx_c = mc.filterExpand(mc.ls(raw, fl=True, long=True), sm=31) or []
            if vtx_c:
                src_grp = _border_edges_from_vtx_comps(vtx_c)

        p = {
            "label":           label,
            "src_set_name":    src_set,
            "loft_set_name":   loft_set,
            "source_grp":      src_grp,
            "source_snapshot": snap,
            "loft_grp":        loft_grp,
            "src_vtx_count":   sv,
            "loft_vtx_count":  lv,
            "src_total_len":   sl,
            "loft_total_len":  ll,
            "split_target":    "none",
            "splits":          0,
            "per_edge_splits": [],
        }

        if sv == 0 or lv == 0:
            pairs.append(p)
            continue

        if lv > sv:

            per_edge = _fls_per_edge_splits_for_target(snap, ll, lv) if snap \
                       else _fls_per_edge_splits_for_target(src_grp, ll, lv)
            p.update(split_target="source",
                     splits=max(per_edge) if per_edge else 1,
                     per_edge_splits=per_edge)
        elif sv > lv:
            per_edge = _fls_per_edge_splits_for_target(loft_grp, sl, sv)
            p.update(split_target="loft",
                     splits=max(per_edge) if per_edge else 1,
                     per_edge_splits=per_edge)

        pairs.append(p)

    return pairs

def _fls_collect_border_segs(loft_edges):
    edges = mc.filterExpand(mc.ls(loft_edges, fl=True, long=True), sm=32) or []
    if not edges:
        return []
    shape = _mesh_shape(edges[0])
    if not shape:
        return []
    fn   = _fn(shape)
    segs = []
    for e in edges:
        eid = _edge_id(e)
        if eid is None:
            continue
        try:
            v0, v1 = fn.getEdgeVertices(eid)
            a = _v(fn.getPoint(v0, oma.MSpace.kWorld))
            b = _v(fn.getPoint(v1, oma.MSpace.kWorld))
            segs.append((a, b))
        except Exception:
            pass
    return segs

def _fls_snap_new_verts_to_segs(loft_shape, pre_split_vtx_ids, orig_segs):
    if not orig_segs or not loft_shape:
        return 0
    dag = _dag(loft_shape)
    fn  = oma.MFnMesh(dag)
    it  = oma.MItMeshEdge(dag)

    border_vtx_ids = set()
    while not it.isDone():
        if _edge_is_boundary(it):
            v0, v1 = fn.getEdgeVertices(it.index())
            border_vtx_ids.add(int(v0))
            border_vtx_ids.add(int(v1))
        it.next()

    new_vtx_ids = border_vtx_ids - pre_split_vtx_ids
    if not new_vtx_ids:
        return 0

    n_snapped = 0
    pts = fn.getPoints(oma.MSpace.kWorld)
    for vid in new_vtx_ids:
        p = _v(pts[vid])
        best_pos = None
        best_d   = 1e18
        for a, b in orig_segs:
            cp, d = _closest_on_seg(p, a, b)
            if d < best_d:
                best_d   = d
                best_pos = cp
        if best_pos is not None:
            pts[vid] = oma.MPoint(best_pos.x, best_pos.y, best_pos.z)
            n_snapped += 1
    if n_snapped:
        fn.setPoints(pts, oma.MSpace.kWorld)

    return n_snapped

def _fls_add_new_verts_to_set(set_name, shape, pre_vtx_ids):
    if not mc.objExists(set_name) or not shape:
        return 0
    tr  = _mesh_tr(shape)
    dag = _dag(shape)
    fn  = oma.MFnMesh(dag)
    it  = oma.MItMeshEdge(dag)

    cur_border = set()
    while not it.isDone():
        if _edge_is_boundary(it):
            v0, v1 = fn.getEdgeVertices(it.index())
            cur_border.add(int(v0))
            cur_border.add(int(v1))
        it.next()

    new_ids = sorted(cur_border - pre_vtx_ids)
    if not new_ids:
        return 0

    new_comps = ["%s.vtx[%d]" % (tr, v) for v in new_ids]
    try:
        mc.sets(new_comps, addElement=set_name)
    except Exception as e:
        mc.warning('[fls_split] could not add verts to %s: %s' % (set_name, e))
        return 0
    return len(new_ids)

def _fls_pre_border_vtx_ids(shape):

    dag = _dag(shape)
    fn  = oma.MFnMesh(dag)
    it  = oma.MItMeshEdge(dag)
    ids = set()
    while not it.isDone():
        if _edge_is_boundary(it):
            v0, v1 = fn.getEdgeVertices(it.index())
            ids.add(int(v0))
            ids.add(int(v1))
        it.next()
    return ids

def _fls_run_splits(pairs):
    d = _fls_debug
    any_split = False

    for p in pairs:
        sv  = p["src_vtx_count"]
        lv  = p["loft_vtx_count"]
        sl  = p["src_total_len"]
        ll  = p["loft_total_len"]
        snap          = p["source_snapshot"]
        src_grp       = p["source_grp"]
        loft_grp      = p["loft_grp"]
        src_set_name  = p.get("src_set_name",  "")
        loft_set_name = p.get("loft_set_name", "")

        if sv == 0 or lv == 0:
            continue

        denser_vtx = max(sv, lv)
        denser_len = sl if sv >= lv else ll
        if denser_vtx < 2 or denser_len < 1e-7:
            continue
        avg_spacing = denser_len / float(denser_vtx - 1)

        src_edge_data = snap if snap else []
        if not src_edge_data and src_grp:
            try:
                src_edges = mc.filterExpand(mc.ls(src_grp, fl=True, long=True), sm=32) or []
                src_edge_data = _build_edge_data(src_edges) if src_edges else []
            except Exception:
                src_edge_data = []

        src_splits = []
        for ed in src_edge_data:
            edge_len = _dist(ed["start"], ed["end"])
            n = max(0, int(math.ceil(edge_len / avg_spacing)) - 1)
            src_splits.append(n)

        loft_edges = mc.filterExpand(mc.ls(loft_grp, fl=True, long=True), sm=32) or [] if loft_grp else []
        loft_edge_data = []
        if loft_edges:
            try:
                loft_edge_data = _build_edge_data(loft_edges)
            except Exception:
                loft_edge_data = []

        loft_splits = []
        for ed in loft_edge_data:
            edge_len = _dist(ed["start"], ed["end"])
            n = max(0, int(math.ceil(edge_len / avg_spacing)) - 1)
            loft_splits.append(n)

        if src_edge_data and any(s > 0 for s in src_splits):
            src_shape = src_edge_data[0]["mesh_shape"]
            try:
                pre_src_ids = _fls_pre_border_vtx_ids(src_shape)
                _add_split_points_per_edge(src_edge_data, src_splits, _debug=True)
                mc.delete(_mesh_tr(src_shape), ch=True)
                n_added = _fls_add_new_verts_to_set(src_set_name, src_shape, pre_src_ids)
                any_split = True
            except Exception as e:
                mc.warning('[fls_debug] source split failed (%s): %s' % (p["label"], e))

        if loft_edge_data and any(s > 0 for s in loft_splits):
            loft_shape = loft_edge_data[0]["mesh_shape"]
            try:

                orig_segs   = _fls_collect_border_segs(loft_edges)
                pre_loft_ids = _fls_pre_border_vtx_ids(loft_shape)

                _add_split_points_per_edge(loft_edge_data, loft_splits, _debug=True)
                mc.delete(_mesh_tr(loft_shape), ch=True)

                n_snapped = _fls_snap_new_verts_to_segs(loft_shape, pre_loft_ids, orig_segs)
                mc.delete(_mesh_tr(loft_shape), ch=True)

                n_added = _fls_add_new_verts_to_set(loft_set_name, loft_shape, pre_loft_ids)
                any_split = True
            except Exception as e:
                mc.warning('[fls_debug] loft split failed (%s): %s' % (p["label"], e))

    d["split_done"] = any_split
    if any_split:
        _fls_refresh_loft_cls()
    if not any_split:
        mc.warning('[fls_debug] All border pairs already balanced — no splits needed.')

def _fls_snap_one_pair(src_set_name, loft_set_name):
    snapshot     = _fls_debug.get("loft_vtx_snapshot") or {}
    snap_entries = snapshot.get(loft_set_name) or []
    if not snap_entries:
        return 0, 0, ('No snapshot for "%s" — did the tool run to completion?'
                      % loft_set_name)

    loft_pts = [oma.MVector(x, y, z) for (_, x, y, z) in snap_entries]

    def _snap_set(set_name):
        if not mc.objExists(set_name):
            return 0, None, 'Set "%s" not found.' % set_name
        raw   = mc.sets(set_name, q=True) or []
        comps = mc.filterExpand(mc.ls(raw, fl=True, long=True), sm=31) or []
        if not comps:
            return 0, None, 'Set "%s" has no vertices.' % set_name
        shape = _mesh_shape(comps[0])
        if not shape:
            return 0, None, 'Cannot resolve mesh shape from "%s".' % set_name
        fn  = _fn(shape)
        pts = fn.getPoints(oma.MSpace.kWorld)
        n = 0
        for c in comps:
            m = re.search(r'\.vtx\[(\d+)\]', c)
            if not m:
                continue
            vid      = int(m.group(1))
            p        = _v(pts[vid])
            best_pos = min(loft_pts, key=lambda lp: _dist(p, lp))
            pts[vid] = oma.MPoint(best_pos.x, best_pos.y, best_pos.z)
            n += 1
        if n:
            fn.setPoints(pts, oma.MSpace.kWorld)
        return n, shape, None

    if not mc.objExists(src_set_name):
        return 0, 0, 'Set "%s" not found — run the tool first.' % src_set_name

    n_src, src_shape, src_err = _snap_set(src_set_name)
    if src_err:
        return 0, 0, src_err
    n_loft, loft_shape, loft_err = _snap_set(loft_set_name)
    if loft_err:
        if src_shape:
            try:
                mc.delete(_mesh_tr(src_shape), ch=True)
            except Exception:
                pass
        return n_src, 0, loft_err
    for shape in set(s for s in (src_shape, loft_shape) if s):
        try:
            mc.delete(_mesh_tr(shape), ch=True)
        except Exception:
            pass

    return n_src, n_loft, None

def _fls_merge_loft_to_source():
    target_name = TARGET_NAME_SIMPLE if smoothFL_simple_mode else TARGET_NAME
    if not mc.objExists(target_name):
        mc.warning('[fls_merge] Loft mesh "%s" not found.' % target_name)
        return None
    src_shape = None
    if mc.objExists('borderEdgeSave'):
        raw = mc.sets('borderEdgeSave', q=True) or []
        comps = mc.filterExpand(mc.ls(raw, fl=True, long=True), sm=32) or []
        if comps:
            src_shape = _mesh_shape(comps[0])
    if not src_shape:
        mc.warning('[fls_merge] Cannot find source mesh from borderEdgeSave.')
        return None

    src_tr   = _mesh_tr(src_shape)
    loft_tr  = target_name
    loft_shape = _mesh_shape(loft_tr)
    tol = 0.001
    if loft_shape:
        lengths = _border_edge_lengths(loft_shape)
        if lengths:
            avg_len = sum(lengths) / float(len(lengths))
            tol = max(1e-5, avg_len * 0.001)

    mc.undoInfo(openChunk=True, chunkName='fls_mergeToSource')
    merged_tr = None
    try:
        src_face_count  = int(mc.polyEvaluate(src_tr,  f=True))
        loft_face_count = int(mc.polyEvaluate(loft_tr, f=True))
        united = mc.polyUnite(src_tr, loft_tr, ch=True, mergeUVSets=True,
                              centerPivot=True)
        merged_tr = united[0] if isinstance(united, (list, tuple)) else united
        mc.polyMergeVertex(merged_tr, d=tol, am=True, ch=True)
        mc.delete(merged_tr, ch=True)

        _delete_matches([
            'reMeshCurve*',
            TARGET_NAME, TARGET_NAME_SIMPLE,
            'borderEdgeSave',
            CAP_SET_PREFIX + '*',
            SIDE_VTX_PREFIX      + '*_vtx',
            CAP_VTX_PREFIX       + '*_vtx',
            LOFT_SIDE_VTX_PREFIX + '*_vtx',
            LOFT_CAP_VTX_PREFIX  + '*_vtx',
        ])

        try:
            all_faces = mc.filterExpand(
                mc.polyListComponentConversion(merged_tr, tf=True),
                sm=34, ex=True) or []
            loft_faces = all_faces[src_face_count : src_face_count + loft_face_count] \
                         if len(all_faces) >= src_face_count + loft_face_count \
                         else all_faces[src_face_count:] if len(all_faces) > src_face_count \
                         else all_faces
            _select_faces_in_face_mode(loft_faces if loft_faces else all_faces)
            _install_restore_face_mode_after_undo()
        except Exception as _re:
            mc.warning('[fls_merge] face-mode restore failed: %s' % _re)

        mc.undoInfo(closeChunk=True)
        return merged_tr

    except Exception as e:
        mc.undoInfo(closeChunk=True)
        mc.warning('[fls_merge] Merge failed: %s' % e)
        return None

def fls_do_all_in_one(*args):
    d = _fls_debug
    target_name = TARGET_NAME_SIMPLE if smoothFL_simple_mode else TARGET_NAME
    if not mc.objExists(target_name):
        mc.warning('[fls_all] No loft mesh found — run the tool on a face selection first.')
        return

    d["loft_shape"] = _mesh_shape(target_name)
    if not d["loft_shape"]:
        mc.warning('[fls_all] Loft mesh shape not found.')
        return
    try:
        _fls_refresh_loft_cls()
        pairs = _fls_analyze_pairs()
        needs_split = any(p["split_target"] != "none" for p in pairs)
        if needs_split:
            _fls_run_splits(pairs)
            _fls_refresh_loft_cls()
    except Exception as e:
        mc.warning('[fls_all] Split pass failed: %s' % e)
        return
    snap_pairs = [
        (_vtx_set_name(SIDE_VTX_PREFIX,      0), _vtx_set_name(LOFT_SIDE_VTX_PREFIX, 0)),
        (_vtx_set_name(SIDE_VTX_PREFIX,      1), _vtx_set_name(LOFT_SIDE_VTX_PREFIX, 1)),
        (_vtx_set_name(CAP_VTX_PREFIX,       0), _vtx_set_name(LOFT_CAP_VTX_PREFIX,  0)),
        (_vtx_set_name(CAP_VTX_PREFIX,       1), _vtx_set_name(LOFT_CAP_VTX_PREFIX,  1)),
    ]
    for src_set, loft_set in snap_pairs:
        if mc.objExists(src_set):
            ns, nl, err = _fls_snap_one_pair(src_set, loft_set)
            if err:
                mc.warning('[fls_all] Snap %s: %s' % (src_set, err))

    _fls_merge_loft_to_source()

def _fls_refresh_loft_cls():
    d = _fls_debug
    target_name = TARGET_NAME_SIMPLE if smoothFL_simple_mode else TARGET_NAME
    if not mc.objExists(target_name):
        d["loft_cls"] = None
        return
    loft_shape = _mesh_shape(target_name)
    d["loft_shape"] = loft_shape
    d["loft_name"]  = target_name
    if not loft_shape:
        d["loft_cls"] = None
        return
    loft_faces = mc.filterExpand(
        mc.polyListComponentConversion(_mesh_tr(loft_shape), tf=True),
        sm=34, ex=True) or []
    d["loft_cls"] = _cd_classify_patch(loft_faces) if loft_faces else None

def _fls_snapshot_loft_vtx_positions():
    d = _fls_debug
    loft_sets = [
        LOFT_SIDE_VTX_PREFIX + "0_vtx",
        LOFT_CAP_VTX_PREFIX  + "0_vtx",
        LOFT_SIDE_VTX_PREFIX + "1_vtx",
        LOFT_CAP_VTX_PREFIX  + "1_vtx",
    ]

    snapshot = {}
    for set_name in loft_sets:
        entries = []
        if mc.objExists(set_name):
            raw   = mc.sets(set_name, q=True) or []
            comps = mc.filterExpand(mc.ls(raw, fl=True, long=True), sm=31) or []
            for c in sorted(comps):
                p = mc.xform(c, q=True, ws=True, t=True)
                entries.append((c, p[0], p[1], p[2]))
        snapshot[set_name] = entries

    d["loft_vtx_snapshot"] = snapshot

def faceLoopPatch():
    global smoothFL_tessNode, smoothFL_cap_edge_count, smoothFL_simple_mode, smoothFL_curve_list, smoothFL_cap_curves, smoothFL_source_normal, ctx, smoothFL_cancelling, smoothFL_cancelJob, smoothFL_orig_face_records
    smoothFL_tessNode       = None
    smoothFL_cap_edge_count = 0
    smoothFL_simple_mode    = True
    smoothFL_curve_list     = []
    smoothFL_cap_curves     = []
    smoothFL_source_normal  = None
    smoothFL_cancelling     = False
    try:
        if smoothFL_cancelJob and mc.scriptJob(exists=smoothFL_cancelJob):
            mc.scriptJob(kill=smoothFL_cancelJob, force=True)
    except Exception:
        pass
    smoothFL_cancelJob      = None

    selFace = mc.filterExpand(mc.ls(sl=True, fl=True, long=True), sm=34) or []
    if not selFace or len(selFace) <= 1:
        mc.warning("faceLoopPatch: select more than one face."); return

    if not _is_single_connected_face_region(selFace):
        mc.warning("faceLoopPatch: selection contains more than one face loop. "
                   "Please select a single connected face patch.")
        return

    _delete_matches(['borderEdgeSave', CAP_SET_PREFIX + '*', 'reMeshCurve*', TARGET_NAME, TARGET_NAME_SIMPLE])
    face_records = _face_records(selFace)
    smoothFL_orig_face_records = face_records
    source_transforms = _transforms_from_faces(selFace)
    mc.undoInfo(openChunk=True, chunkName='faceLoopPatch')
    try:
        selFace = _delete_history_keep_selection(source_transforms, face_records)
        if not selFace or len(selFace) <= 1:
            mc.warning("Selected faces were lost after deleting history.")
            _close_undo_chunk_safely(); return
        classification = _cd_classify_patch(selFace)
        if not classification:
            mc.warning("Could not classify side / cap edges from face patch.")
            _close_undo_chunk_safely(); return
        side_edge_groups = classification["side_edge_groups"]
        cap_edge_groups  = classification.get("cap_edge_groups", [])
        cap_edge_count   = classification["cap_edge_count"]
        sideEdgeGet      = [e for grp in side_edge_groups for e in grp]
        capEdgeGet       = [e for grp in cap_edge_groups for e in grp]
        if not sideEdgeGet or len(side_edge_groups) < 2:
            mc.warning("Could not find side edges.")
            _close_undo_chunk_safely(); return
        mc.sets(sideEdgeGet, name="borderEdgeSave", text="gCharacterSet")
        if capEdgeGet:
            _save_component_groups(CAP_SET_PREFIX, cap_edge_groups)
        source_normal = _average_face_normal(selFace)
        smoothFL_source_normal = source_normal

        all_profile_loops = _get_all_profile_loops(
            selFace, side_edge_groups[0], side_edge_groups[1])

        curveList = []
        mc.select(clear=True)
        for loop_edges in all_profile_loops:
            if not loop_edges: continue
            mc.select(loop_edges, r=True)
            mc.polyToCurve(form=0, degree=1, n='reMeshCurve01')
            newC = (mc.ls(sl=True, long=True) or [None])[0]
            if not newC: continue
            curveList.append(newC)
            mc.rebuildCurve(newC, ch=False, rpo=True, rt=0, end=True, kr=0,
                            kcp=False, kep=True, kt=False, s=3, d=3, tol=0.01)
            mc.delete(newC, ch=True)

        if len(curveList) < 2:
            mc.warning('Need at least two profile curves to loft.')
            _close_undo_chunk_safely(); return

        cap_curves = []
        if cap_edge_count > 0 and len(cap_edge_groups) >= 2:
            for capGrp in cap_edge_groups:
                if not capGrp: continue
                mc.select(capGrp, r=True)
                mc.polyToCurve(form=0, degree=1, n='reMeshCurve01')
                newC = (mc.ls(sl=True, long=True) or [None])[0]
                if not newC: continue
                mc.rebuildCurve(newC, ch=False, rpo=True, rt=0, end=True, kr=0,
                                kcp=False, kep=True, kt=False, s=3, d=3, tol=0.01)
                mc.delete(newC, ch=True)
                cap_curves.append(newC)

        for c in curveList + cap_curves:
            mc.hide(c)

        smoothFL_curve_list = list(curveList)
        smoothFL_cap_curves = list(cap_curves)

        _set_hidden_in_outliner(
            ['borderEdgeSave', CAP_SET_PREFIX + '*'] + curveList + cap_curves)

        _initial_target = TARGET_NAME_SIMPLE
        _initial_curves = [curveList[0], curveList[-1]] if len(curveList) >= 2 else curveList
        _initial_result = None
        if len(cap_curves) >= 2:
            try:
                _initial_result = mc.doubleProfileBirailSurface(
                    _initial_curves[0], _initial_curves[1],
                    cap_curves[0], cap_curves[1],
                    po=1, ch=True, tm=0, n=TARGET_NAME_SIMPLE)
            except Exception as _e:
                mc.warning('[faceLoopPatch] initial birail failed, falling back to loft: %s' % _e)
        if _initial_result is None:
            _initial_result = mc.loft(_initial_curves, ch=True, u=True, c=False, ar=True,
                                      d=3, ss=1, rn=False, po=1, rsn=True, n=TARGET_NAME_SIMPLE)
        loftResult = _initial_result
        mc.delete(selFace)
        mc.select(TARGET_NAME_SIMPLE, r=True)
        mc.setAttr(TARGET_NAME_SIMPLE + '.hiddenInOutliner', 1)
        tessNode = next((n for n in (mc.listHistory(loftResult, pruneDagObjects=True, interestLevel=2, future=False) or []) if mc.nodeType(n) == 'nurbsTessellate'), None)
        if tessNode:
            smoothFL_tessNode = tessNode
            smoothFL_cap_edge_count = cap_edge_count
            mc.setAttr(tessNode + '.format', 2)
            mc.setAttr(tessNode + '.uNumber', 10)
            mc.setAttr(tessNode + '.vNumber', max(1, cap_edge_count + 1))

        loft_mesh = _initial_target
        def _deferred_normal_check(mesh=loft_mesh, src_n=source_normal):
            if not mc.objExists(mesh): return
            loft_faces  = mc.filterExpand(mc.polyListComponentConversion(mesh, tf=True), sm=34, ex=True) or []
            loft_normal = _average_face_normal(loft_faces) if loft_faces else None
            if src_n and loft_normal:
                if _dot(src_n, loft_normal) < 0.0:
                    mc.polyNormal(mesh, normalMode=0, userNormalMode=0, ch=False)
            else:
                mc.polyNormal(mesh, normalMode=0, userNormalMode=0, ch=False)
        prev_ctx = None
        try: prev_ctx = mc.currentCtx()
        except Exception: prev_ctx = None
        def _finish_setup(prev_ctx=prev_ctx, frecords=face_records):
            global ctx
            try:
                _deferred_normal_check()
            except Exception:
                pass
            finally:
                _close_undo_chunk_safely()

            ctx = 'smoothFLCtx'
            try:
                if mc.draggerContext(ctx, exists=True):
                    mc.deleteUI(ctx)
                mc.draggerContext(ctx, pressCommand=smoothFaceLoopPress, rc=smoothFaceLoopOff,
                                  dragCommand=smoothFaceLoopDrag,
                                  finalize=smoothFaceLoopFinalize,
                                  name=ctx, cursor='crossHair', undoMode='none')
                mc.setToolTo(ctx)
            except Exception as _te:
                mc.warning('[faceLoopPatch] tool activation failed: %s' % _te)
            _install_cancel_on_undo(prev_ctx, frecords)
        mu.executeDeferred(_finish_setup)
    except Exception as e:
        _close_undo_chunk_safely()
        mc.confirmDialog(title="faceLoopPatch Error", message=str(e), button=["OK"])

def smoothFaceLoopOff():
    if mc.headsUpDisplay('HUDunBevelStep', exists=True):
        mc.headsUpDisplay('HUDunBevelStep', rem=True)

def smoothFaceLoopFinalize():
    global smoothFL_cancelling
    if mc.headsUpDisplay('HUDunBevelStep', exists=True):
        mc.headsUpDisplay('HUDunBevelStep', rem=True)
    if smoothFL_cancelling:
        smoothFL_cancelling = False
        return
    _run_pipeline()

def _run_pipeline():
    global smoothFL_simple_mode, smoothFL_cancelJob
    try:
        if smoothFL_cancelJob and mc.scriptJob(exists=smoothFL_cancelJob):
            mc.scriptJob(kill=smoothFL_cancelJob, force=True)
    except Exception:
        pass
    smoothFL_cancelJob = None
    target_name = TARGET_NAME_SIMPLE if smoothFL_simple_mode else TARGET_NAME
    if not mc.objExists(target_name):
        mc.warning('[faceLoopPatch] loft mesh not found.')
        return
    mc.undoInfo(openChunk=True, chunkName='faceLoopPatchApply')
    try:
        target_shape = _mesh_shape(target_name)
        if target_shape:
            try:
                mc.delete(_mesh_tr(target_shape), ch=True)
            except Exception:
                pass
        try:
            mc.setAttr(target_name + '.visibility', 1)
            mc.setAttr(target_name + '.hiddenInOutliner', 0)
        except Exception:
            pass

        try:
            _rebuild_vtx_quick_sets()
        except Exception as e:
            mc.warning('[faceLoopPatch] quick-set creation failed: %s' % e)

        try:
            _fls_snapshot_loft_vtx_positions()
        except Exception as e:
            mc.warning('[faceLoopPatch] loft vtx snapshot failed: %s' % e)

        fls_do_all_in_one()
    finally:
        mc.undoInfo(closeChunk=True)

def currentStep():
    global viewPortCount, smoothFL_drag_mode, smoothFL_simple_mode
    mode = 'Border' if smoothFL_simple_mode else 'Ridge'
    return '%s: %s %d' % (mode, smoothFL_drag_mode, max(0, int(viewPortCount)))

def smoothFaceLoopPress():
    global ctx, screenX, lockCount, storeCount, lockCountV, storeCountV, viewPortCount, pixelAccum, pixelAccumV, smoothFL_drag_mode, smoothFL_tessNode
    try:
        if mc.draggerContext(ctx, query=True, modifier=True) == 'alt':
            return
    except Exception:
        pass
    if not smoothFL_tessNode or not mc.objExists(smoothFL_tessNode):
        mc.warning('Tessellate node not found.')
        return
    lockCount     = int(mc.getAttr(smoothFL_tessNode + '.uNumber'))
    storeCount    = lockCount
    lockCountV    = int(mc.getAttr(smoothFL_tessNode + '.vNumber'))
    storeCountV   = lockCountV
    viewPortCount = lockCount
    pixelAccum    = 0.0
    pixelAccumV   = 0.0
    smoothFL_drag_mode = 'U'
    vpX, _, _     = mc.draggerContext(ctx, query=True, anchorPoint=True)
    screenX       = vpX
    if mc.headsUpDisplay('HUDunBevelStep', exists=True):
        mc.headsUpDisplay('HUDunBevelStep', rem=True)
    mc.headsUpDisplay('HUDunBevelStep', section=3, block=1, blockSize='large', label='smoothFaceLoop', labelFontSize='large', command=currentStep, atr=1, ao=1)

def _switch_loft_mode(want_simple):
    global smoothFL_tessNode, smoothFL_simple_mode, smoothFL_curve_list, smoothFL_cap_curves, smoothFL_cap_edge_count, smoothFL_source_normal, storeCount, storeCountV, lockCount, lockCountV, viewPortCount
    if want_simple == smoothFL_simple_mode:
        return
    cur_u = storeCount
    cur_v = storeCountV
    if smoothFL_tessNode and mc.objExists(smoothFL_tessNode):
        try:
            cur_u = int(mc.getAttr(smoothFL_tessNode + '.uNumber'))
            cur_v = int(mc.getAttr(smoothFL_tessNode + '.vNumber'))
        except Exception:
            pass
    mc.undoInfo(openChunk=True, chunkName='faceLoopPatchModeSwitch')
    try:
        cur_name = TARGET_NAME_SIMPLE if smoothFL_simple_mode else TARGET_NAME
        _delete_matches([cur_name])
        curves = [c for c in smoothFL_curve_list if mc.objExists(c)]
        caps   = [c for c in smoothFL_cap_curves  if mc.objExists(c)]
        if want_simple:
            side_curves = [curves[0], curves[-1]] if len(curves) >= 2 else curves
            newResult = None
            if len(caps) >= 2:
                try:
                    newResult = mc.doubleProfileBirailSurface(
                        side_curves[0], side_curves[1],
                        caps[0], caps[1],
                        po=1, ch=True, tm=0, n=TARGET_NAME_SIMPLE)
                except Exception as e:
                    mc.warning('[faceLoopPatch] simple birail failed: %s' % e)
            if newResult is None:
                newResult = mc.loft(side_curves, ch=True, u=True, c=False, ar=True,
                                    d=3, ss=1, rn=False, po=1, rsn=True, n=TARGET_NAME_SIMPLE)
        else:
            newResult = mc.loft(curves, ch=True, u=True, c=False, ar=True,
                                d=3, ss=1, rn=False, po=1, rsn=True, n=TARGET_NAME)
        new_name = TARGET_NAME_SIMPLE if want_simple else TARGET_NAME
        mc.setAttr(new_name + '.hiddenInOutliner', 1)
        tessNode = next((n for n in (mc.listHistory(newResult, pruneDagObjects=True,
                         interestLevel=2, future=False) or [])
                         if mc.nodeType(n) == 'nurbsTessellate'), None)
        if tessNode:
            mc.setAttr(tessNode + '.format', 2)
            mc.setAttr(tessNode + '.uNumber', max(1, cur_u))
            mc.setAttr(tessNode + '.vNumber', max(1, cur_v))
            smoothFL_tessNode = tessNode
        lockCount = storeCount = cur_u
        lockCountV = storeCountV = cur_v
        viewPortCount = cur_u
        smoothFL_simple_mode = want_simple
        try:
            if mc.objExists(new_name) and smoothFL_source_normal:
                loft_faces  = mc.filterExpand(mc.polyListComponentConversion(new_name, tf=True), sm=34, ex=True) or []
                loft_normal = _average_face_normal(loft_faces) if loft_faces else None
                if loft_normal and _dot(smoothFL_source_normal, loft_normal) < 0.0:
                    mc.polyNormal(new_name, normalMode=0, userNormalMode=0, ch=False)
        except Exception as e:
            mc.warning('[faceLoopPatch] normal check on switch failed: %s' % e)
        mc.refresh(f=True)
        try:
            _rebuild_vtx_quick_sets()
        except Exception as _qe:
            mc.warning('[faceLoopPatch] quick-set rebuild after mode switch failed: %s' % _qe)
    except Exception as e:
        mc.warning('[faceLoopPatch] mode switch failed: %s' % e)
    finally:
        mc.undoInfo(closeChunk=True)

def smoothFaceLoopDrag():
    global storeCount, storeCountV, viewPortCount, screenX, lockCount, lockCountV, pixelAccum, pixelAccumV, smoothFL_drag_mode, smoothFL_tessNode, smoothFL_simple_mode
    if not smoothFL_tessNode or not mc.objExists(smoothFL_tessNode): return
    PIXELS_PER_STEP_V = 12
    PIXELS_PER_STEP_U = 5
    modifier = mc.draggerContext(ctx, query=True, modifier=True)
    if modifier == 'alt':
        return
    vpX, _, _ = mc.draggerContext(ctx, query=True, dragPoint=True)
    delta     = screenX - vpX
    screenX   = vpX
    if modifier == 'ctrl':
        if abs(delta) < 1:
            return
        _switch_loft_mode(want_simple=(delta > 0))
        return
    shift_held = (modifier == 'shift')
    smoothFL_drag_mode = 'V' if shift_held else 'U'

    mc.undoInfo(stateWithoutFlush=False)
    try:
        if shift_held:
            pixelAccumV += delta
            steps = int(pixelAccumV / PIXELS_PER_STEP_U)
            if steps:
                lockCountV  -= steps
                pixelAccumV -= steps * PIXELS_PER_STEP_U
            getV = max(1, lockCountV)
            lockCountV = getV
            if storeCountV != getV:
                storeCountV = getV
                mc.setAttr(smoothFL_tessNode + '.vNumber', storeCountV)
            viewPortCount = storeCountV
        else:
            pixelAccum += delta
            steps = int(pixelAccum / PIXELS_PER_STEP_V)
            if steps:
                lockCount  -= steps
                pixelAccum -= steps * PIXELS_PER_STEP_V
            if lockCount > 0:
                getX = max(1, lockCount)
                if storeCount != getX:
                    storeCount = getX
                    mc.setAttr(smoothFL_tessNode + '.uNumber', storeCount)
                viewPortCount = storeCount
            else:
                viewPortCount = 0.1
        mc.refresh(f=True)
    finally:
        mc.undoInfo(stateWithoutFlush=True)

def _flatten(data):
    result = []
    for x in data:
        if isinstance(x, (list, tuple)):
            result.extend(_flatten(x))
        else:
            result.append(x)
    return result
def _dot(a, b):
    return sum(a[i] * b[i] for i in range(3))
def _normalize(v):
    l = math.sqrt(_dot(v, v))
    return [v[i] / l for i in range(3)] if l > 1e-6 else None
def _edge_vector(edge):
    vtxs = mc.filterExpand(mc.polyListComponentConversion(edge, fe=True, tv=True), sm=31, ex=True) or []
    if len(vtxs) != 2: return None
    p1 = mc.xform(vtxs[0], q=True, ws=True, t=True)
    p2 = mc.xform(vtxs[1], q=True, ws=True, t=True)
    return _normalize([p2[i] - p1[i] for i in range(3)])
def _average_face_normal(faces):
    total = [0.0, 0.0, 0.0]; count = 0
    for info in (mc.polyInfo(faces, faceNormals=True) or []):
        nums = re.findall(r'[-+]?\d*\.\d+(?:[eE][-+]?\d+)?|\d+', info)
        if len(nums) >= 4:
            total[0] += float(nums[1]); total[1] += float(nums[2]); total[2] += float(nums[3])
            count += 1
    if count == 0: return None
    return _normalize([total[i] / count for i in range(3)])
def select_most_similar_edge_from_guide(guide_edges, candidate_edges):
    guide_edges     = _flatten(guide_edges)
    candidate_edges = _flatten(candidate_edges)
    if not guide_edges or not candidate_edges:
        mc.warning('select_most_similar_edge_from_guide: empty input.'); return None
    guide_vec = _edge_vector(guide_edges[0])
    if not guide_vec:
        mc.warning('Cannot compute guide edge vector.'); return None
    return max(candidate_edges, key=lambda e: abs(_dot(guide_vec, _edge_vector(e) or [0, 0, 0])))
def _dag_path(mesh):
    if mc.nodeType(mesh) != 'mesh':
        shapes = mc.listRelatives(mesh, s=True, ni=True, f=True, type='mesh') or []
        if not shapes: return None
        mesh = shapes[0]
    sel = oma.MSelectionList()
    sel.add(mesh)
    return sel.getDagPath(0)
def _face_edges(mesh, face_id):
    it = oma.MItMeshPolygon(_dag_path(mesh))
    it.setIndex(face_id)
    return list(it.getEdges())
def find_end_faces_from_selected_faces(faces=None, select_result=False):
    if faces is None:
        faces = mc.filterExpand(mc.ls(sl=True, fl=True, long=True), sm=34) or []
    else:
        faces = mc.filterExpand(mc.ls(faces, fl=True, long=True), sm=34) or []
    if not faces:
        mc.warning('Please select faces first.'); return []
    mesh_faces = defaultdict(list)
    for f in faces:
        mesh = f.rsplit('.', 1)[0]
        fid  = int(re.search(r'\.f\[(\d+)\]', f).group(1))
        mesh_faces[mesh].append(fid)
    end_faces = []
    for mesh, face_ids in mesh_faces.items():
        edge_to_faces = defaultdict(list)
        for fid in face_ids:
            for e in _face_edges(mesh, fid):
                edge_to_faces[e].append(fid)
        shared_count = defaultdict(int)
        for connected in edge_to_faces.values():
            if len(connected) > 1:
                for fid in connected:
                    shared_count[fid] += 1
        for fid in face_ids:
            if shared_count[fid] == 1:
                end_faces.append('%s.f[%d]' % (mesh, fid))
    if select_result and end_faces:
        mc.select(end_faces, r=True)
    return end_faces
def getEdgeRingGroupList(edges):
    if not edges: return []
    edges = mc.ls(edges, fl=True, long=True) or []
    if not edges: return []
    transform = edges[0].split('.')[0]
    e2v, v2e  = {}, defaultdict(set)
    for info in (mc.polyInfo(edges, ev=True) or []):
        ev = _polyinfo_int_list(info)
        if len(ev) >= 3:
            eid, v1, v2 = ev[0], ev[1], ev[2]
            e2v[eid] = (v1, v2)
            v2e[v1].add(eid)
            v2e[v2].add(eid)
    groups = []
    while e2v:
        start, (v1, v2) = next(iter(e2v.items()))
        del e2v[start]
        v2e[v1].discard(start)
        v2e[v2].discard(start)
        ring = [start]
        for seed, prepend in ((v2, False), (v1, True)):
            cur = seed
            while True:
                adj = v2e.get(cur)
                if not adj or len(adj) != 1: break
                nxt   = adj.pop()
                verts = e2v.pop(nxt, None)
                if verts is None: break
                a, b = verts
                v2e[a].discard(nxt)
                v2e[b].discard(nxt)
                ring.insert(0, nxt) if prepend else ring.append(nxt)
                cur = b if a == cur else a
        groups.append(['%s.e[%d]' % (transform, e) for e in ring])
    return groups

faceLoopPatch()
