# -*- coding: utf-8 -*-
"""
curveToWeight.py

Maya 2022+ / Python 3 / Maya API 2.0
Single-file prototype:
    Curve CV -> Joint skin weight solver

Features
--------
- One CV <-> one joint mapping.
- Bar / Ring mode.
- Degree 1 / 2 / 3.
- No user-facing "Max Influences" limit.
- Uses curve arc-length parameterization rather than raw world-space CV distance.
- Degree uses compact B-spline-style positive kernels:
    degree 1 -> 2 local influences
    degree 2 -> local quadratic smoothing
    degree 3 -> local cubic smoothing
- Ring mode uses periodic arc-length mapping and seam-aware local weights.
- Writes weights through MFnSkinCluster.setWeights().
- Reuses an existing skinCluster on the mesh when possible.
- Creates a new skinCluster when one does not exist.
- Optional Bar-mode End Hold can pin a percentage of each end to the first/last joint.
- Selectable End Falloff for the transition: Linear / Ease In / Ease Out / Ease In Out / Smootherstep.
- Preview calculates weights and reports statistics without modifying the scene.
- Apply writes weights to the mesh.

Typical usage
-------------
import curveToWeight
curveToWeight.show()

Workflow
--------
1. Select the NURBS curve and click "Set".
2. Select the mesh and click "Set".
3. Select N joints in the exact CV order and click "Set".
4. Choose Bar/Ring and Degree 1/2/3.
5. Click Preview to inspect statistics.
6. Click Apply Weights.

Important
---------
The weighting core is a true non-uniform B-Spline/Cox-de Boor solver.
It does not yet try to reproduce every Wire Deformer option such as radial
dropoff/localInfluence. Those can be added after the longitudinal weighting
behavior is confirmed in production tests.
"""

from __future__ import absolute_import

import math
import traceback
from bisect import bisect_right

import maya.cmds as cmds
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma

from PySide2 import QtCore, QtWidgets
from shiboken2 import wrapInstance
from maya.OpenMayaUI import MQtUtil


_WINDOW = None


# ============================================================================
# Maya / Qt helpers
# ============================================================================

def maya_main_window():
    """Return Maya's main window as a Qt widget."""
    ptr = MQtUtil.mainWindow()
    if ptr is None:
        return None
    return wrapInstance(int(ptr), QtWidgets.QWidget)


def warning(message):
    try:
        om.MGlobal.displayWarning(str(message))
    except Exception:
        print("WARNING: {}".format(message))


def info(message):
    try:
        om.MGlobal.displayInfo(str(message))
    except Exception:
        print(message)


def get_dag_path(node):
    """Return an MDagPath for a DAG node."""
    sel = om.MSelectionList()
    sel.add(node)
    return sel.getDagPath(0)


def get_transform_from_shape(shape_node):
    """Return the transform name for a shape."""
    parent = cmds.listRelatives(shape_node, parent=True, fullPath=True) or []
    return parent[0] if parent else shape_node


def first_shape(node, shape_type):
    """Return the first non-intermediate shape of the requested type."""
    shapes = cmds.listRelatives(
        node,
        shapes=True,
        noIntermediate=True,
        fullPath=True
    ) or []

    for shape in shapes:
        if cmds.nodeType(shape) == shape_type:
            return shape
    return None


def get_mesh_shape(node):
    """Accept mesh transform or mesh shape and return the shape."""
    if cmds.objExists(node) and cmds.nodeType(node) == "mesh":
        return node

    shape = first_shape(node, "mesh")
    if shape:
        return shape

    return None


def get_curve_shape(node):
    """Accept curve transform or curve shape and return the shape."""
    if cmds.objExists(node) and cmds.nodeType(node) == "nurbsCurve":
        return node

    shape = first_shape(node, "nurbsCurve")
    if shape:
        return shape

    return None


def get_joint_paths(joints):
    """Return MDagPaths for joint nodes."""
    result = []
    for joint in joints:
        if not cmds.objExists(joint):
            raise RuntimeError("Joint does not exist: {}".format(joint))
        if cmds.nodeType(joint) != "joint":
            raise RuntimeError("{} is not a joint.".format(joint))
        result.append(get_dag_path(joint))
    return result


def find_skin_cluster(mesh_shape):
    """Return the first skinCluster deforming the mesh shape, or None."""
    history = cmds.listHistory(mesh_shape, pruneDagObjects=True) or []
    for node in history:
        if cmds.nodeType(node) == "skinCluster":
            return node
    return None


# ============================================================================
# Curve parameter mapping
# ============================================================================

class CurveAnalyzer(object):
    """
    Builds a normalized arc-length coordinate system for the selected curve.

    "s" is always normalized to [0, 1] for an open curve.
    For a closed curve, the same value is treated as a periodic coordinate.
    """

    def __init__(self, curve_shape):
        self.curve_shape = curve_shape
        self.dag = get_dag_path(curve_shape)
        self.fn = om.MFnNurbsCurve(self.dag)

        self.form = self.fn.form
        self.degree = int(self.fn.degree)
        self.spans = int(self.fn.numSpans)
        self.closed = self.form in (
            om.MFnNurbsCurve.kClosed,
            om.MFnNurbsCurve.kPeriodic
        )
        self.length = float(self.fn.length())

        if self.length <= 1.0e-8:
            raise RuntimeError("Curve length is zero.")

        # Maya NURBS periodic curves contain degree duplicated/locked CVs
        # internally.  MFnNurbsCurve.numCVs can therefore be larger than the
        # editable CV count that the artist sees/selects.  For the tool's
        # one-CV-to-one-joint mapping we want editable CVs:
        #
        #   open/closed:   spans + degree
        #   periodic:      spans
        #
        # This matches Maya's editable CV behavior for periodic curves.
        if self.form == om.MFnNurbsCurve.kPeriodic:
            self.cv_count = self.spans
        else:
            self.cv_count = self.spans + self.degree

        self.raw_cv_count = int(self.fn.numCVs)

    def cv_positions(self):
        """Return CV positions in object space."""
        positions = []
        for i in range(self.cv_count):
            positions.append(self.fn.cvPosition(i, om.MSpace.kObject))
        return positions

    def cv_parameters_and_s(self):
        """
        Project every CV onto the actual curve and convert the resulting
        parameter to normalized arc length.

        For high-degree NURBS, a CV is not necessarily on the curve, so the
        closest-point projection is intentional.
        """
        values = []

        for i in range(self.cv_count):
            cv_point = self.fn.cvPosition(i, om.MSpace.kObject)
            _, param = self.fn.closestPoint(cv_point)
            arc_length = self.fn.findLengthFromParam(param)
            s = arc_length / self.length

            # Numerical safety.
            s = max(0.0, min(1.0, float(s)))
            values.append((float(param), s))

        return values

    def mesh_vertex_s(self, mesh_shape):
        """
        Return:
            points: list[MPoint]
            normalized s values for every mesh vertex
            radial distances from the curve

        Mesh points are converted to the curve's object space so closestPoint
        uses a consistent coordinate system.
        """
        mesh_dag = get_dag_path(mesh_shape)
        mesh_fn = om.MFnMesh(mesh_dag)
        points = mesh_fn.getPoints(om.MSpace.kWorld)

        curve_world_matrix = self.dag.inclusiveMatrix()
        world_to_curve = curve_world_matrix.inverse()

        s_values = []
        radial_distances = []

        for point_world in points:
            point_curve = point_world * world_to_curve

            # Do not reuse the previous vertex's parameter as a guess here.
            # Mesh vertex order is arbitrary, and on rings or self-near curves
            # a wrong guess can send the closest-point search into the wrong
            # local region. A global closest-point query is more reliable for
            # weight generation.
            closest_point, param = self.fn.closestPoint(point_curve)

            arc_length = self.fn.findLengthFromParam(param)
            s = arc_length / self.length
            s = max(0.0, min(1.0, float(s)))

            # MPoint.distanceTo is unavailable in some API combinations, so
            # use vector length explicitly.
            delta = point_curve - closest_point
            distance = float(delta.length())

            s_values.append(s)
            radial_distances.append(distance)

        return points, s_values, radial_distances


# ============================================================================
# Non-uniform B-Spline / Cox-de Boor weight solver
# ============================================================================

def _effective_degree(degree, control_count):
    """Keep the requested degree valid for the available number of bones."""
    if control_count <= 1:
        return 0
    return max(0, min(int(degree), int(control_count) - 1))


def _build_open_knot_vector(parameters, degree):
    """
    Build a clamped, non-uniform B-Spline knot vector.

    The interior knots use the standard averaging construction from the
    supplied control-parameter sequence.  For p=1 this reduces exactly to:

        [t0, t0, t1, t2, ..., tn-2, tn-1, tn-1]

    so Degree 1 is ordinary linear interpolation between the supplied bone
    positions.  Higher degrees use averaged interior knots and therefore
    preserve non-uniform parameter spacing while providing true B-Spline
    continuity.
    """
    params = [float(v) for v in parameters]
    count = len(params)
    degree = _effective_degree(degree, count)

    if count <= 1:
        return [0.0, 1.0], degree

    start = params[0]
    end = params[-1]

    knots = [start] * (degree + 1)

    interior_count = count - degree - 1
    if interior_count > 0:
        inv_degree = 1.0 / float(degree)
        for j in range(1, interior_count + 1):
            value = sum(params[j:j + degree]) * inv_degree
            # Keep the averaged knot inside the valid domain.  Repeated knots
            # are legal and simply reduce continuity at that location.
            value = max(start, min(end, value))
            knots.append(value)

    knots.extend([end] * (degree + 1))
    return knots, degree


def _cox_de_boor_local(u, degree, span, knot_getter):
    """
    Cox-de Boor / The NURBS Book A2.2 local basis evaluation.

    Returns:
        (first_basis_index, basis_values)

    Only the p+1 non-zero basis functions around the current knot span are
    returned, making this suitable for per-vertex skin-weight evaluation.
    """
    p = int(degree)
    span = int(span)

    if p == 0:
        return span, [1.0]

    values = [1.0] + [0.0] * p
    left = [0.0] * (p + 1)
    right = [0.0] * (p + 1)

    for j in range(1, p + 1):
        left[j] = u - knot_getter(span + 1 - j)
        right[j] = knot_getter(span + j) - u

        saved = 0.0

        for r in range(j):
            denominator = right[r + 1] + left[j - r]

            if abs(denominator) <= 1.0e-12:
                temp = 0.0
            else:
                temp = values[r] / denominator

            values[r] = saved + right[r + 1] * temp
            saved = left[j - r] * temp

        values[j] = saved

    return span - p, values


def _evaluate_open_bspline(u, parameters, degree):
    """Evaluate all non-zero open B-Spline basis weights at u."""
    count = len(parameters)

    if count == 1:
        return [(0, 1.0)]

    knots, degree = _build_open_knot_vector(parameters, degree)

    start = knots[0]
    end = knots[-1]

    if end - start <= 1.0e-12:
        return [(0, 1.0)]

    u = float(u)

    # Open B-Splines are clamped. Outside the first/last joint parameter we
    # intentionally pin to the corresponding end joint rather than allowing
    # extrapolation.
    if u <= start:
        return [(0, 1.0)]

    if u >= end:
        return [(count - 1, 1.0)]

    # For 0 <= u < end, find the knot span. The valid basis span indices are
    # [degree, count-1].
    span = bisect_right(knots, u) - 1
    span = max(degree, min(count - 1, span))

    first, local_values = _cox_de_boor_local(
        u,
        degree,
        span,
        lambda index: knots[index]
    )

    result = []
    for offset, value in enumerate(local_values):
        index = first + offset
        if 0 <= index < count and value > 1.0e-12:
            result.append((index, float(value)))

    return WeightSolver._normalize_sparse(result, count)


def _build_periodic_knot_sequence(parameters):
    """
    Return a periodic knot accessor.

    parameters must be an increasing ring coordinate with:
        parameters[0] == 0
        parameters[-1] < 1

    The infinite knot sequence is:
        ... t[-2], t[-1], t[0], t[1], ...

    with t[i+n] = t[i] + 1.
    """
    base = [float(v) for v in parameters]
    count = len(base)

    def knot(index):
        q, r = divmod(int(index), count)
        return base[r] + float(q)

    return knot


def _evaluate_periodic_bspline(u, parameters, degree):
    """
    Evaluate a periodic non-uniform B-Spline basis.

    The curve coordinate is one complete loop in [0, 1). The first control
    point is associated with the basis located at the first supplied parameter
    and the support is cyclically re-labeled so Degree 1/2/3 have the expected
    local neighbors across the seam.

    For a requested degree p, the relabel offset is:
        floor((p + 1) / 2)

    This makes the support around u=0 look like:

        Degree 1 -> last, first
        Degree 2 -> last, first, second
        Degree 3 -> previous, last, first, second

    while the actual basis values are produced by Cox-de Boor evaluation on
    the non-uniform periodic knot sequence.
    """
    count = len(parameters)

    if count == 1:
        return [(0, 1.0)]

    degree = _effective_degree(degree, count)
    base = [float(v) for v in parameters]

    # Normalize the periodic coordinate to exactly one revolution.
    u = float(u) % 1.0

    # Extremely close-to-zero values should use the first interval. This also
    # makes exact seam behavior deterministic.
    if u < 1.0e-12:
        u = 0.0

    knot = _build_periodic_knot_sequence(base)

    # Find the base interval containing u. The final interval is the seam
    # [last_parameter, 1.0).
    span = bisect_right(base, u) - 1
    span = max(0, min(count - 1, span))

    first, local_values = _cox_de_boor_local(
        u,
        degree,
        span,
        knot
    )

    # Periodic B-Spline bases are cyclic. The mathematical basis indices
    # around the seam are therefore re-labeled back into the joint range.
    # The offset is chosen to center the support around the corresponding CV
    # parameter for odd degrees and as closely as possible for even degrees.
    label_offset = (degree + 1) // 2

    accum = {}
    for offset, value in enumerate(local_values):
        basis_index = first + offset
        joint_index = (basis_index + label_offset) % count
        if value > 1.0e-12:
            accum[joint_index] = accum.get(joint_index, 0.0) + float(value)

    return WeightSolver._normalize_sparse(
        sorted(accum.items(), key=lambda item: item[0]),
        count
    )


class WeightSolver(object):
    """
    True non-uniform B-Spline weight solver.

    Degree 1/2/3 are the actual B-Spline polynomial degrees. The weights are
    evaluated with Cox-de Boor basis functions from non-uniform knot vectors,
    rather than an approximate distance kernel.
    """

    @staticmethod
    def validate_bone_s(bone_s, closed):
        if len(bone_s) < 1:
            raise RuntimeError("At least one joint is required.")

        cleaned = [float(v) for v in bone_s]

        for i in range(1, len(cleaned)):
            if cleaned[i] < cleaned[i - 1] - 1.0e-6:
                raise RuntimeError(
                    "CV-to-curve mapping is not monotonic. "
                    "Please verify the curve/CV/joint order."
                )

        # Repeated projected locations are allowed. The B-Spline knot builder
        # can handle repeated knots, and this is preferable to rejecting a
        # valid high-degree NURBS curve outright.
        return cleaned

    @staticmethod
    def prepare_ring_bone_s(raw_bone_s):
        """
        Convert CV projection positions into a complete periodic coordinate.

        The first CV is the ring origin. We test both possible directions and
        choose the direction whose cumulative CV traversal plus closing seam is
        closest to exactly one full circumference. The cumulative distances
        are then normalized by that full loop, preserving non-uniform spacing.

        Returns:
            oriented_bone_s, origin_raw_s, direction
        """
        if not raw_bone_s:
            raise RuntimeError("At least one joint is required.")

        raw = [float(v) % 1.0 for v in raw_bone_s]
        count = len(raw)

        if count == 1:
            return [0.0], raw[0], 1

        origin = raw[0]

        def build_direction(direction):
            cumulative = [0.0]
            travel = 0.0

            for i in range(1, count):
                if direction > 0:
                    delta = (raw[i] - raw[i - 1]) % 1.0
                else:
                    delta = (raw[i - 1] - raw[i]) % 1.0

                # A repeated projection location is valid. Keep it as a very
                # small interval so the knot sequence remains usable.
                if delta < 1.0e-10:
                    delta = 0.0

                travel += delta
                cumulative.append(travel)

            if direction > 0:
                closing = (raw[0] - raw[-1]) % 1.0
            else:
                closing = (raw[-1] - raw[0]) % 1.0

            total = travel + closing
            return cumulative, closing, total

        candidates = [
            (1,) + build_direction(1),
            (-1,) + build_direction(-1),
        ]

        direction, cumulative, closing, total = min(
            candidates,
            key=lambda item: abs(item[3] - 1.0)
        )

        if total <= 1.0e-10:
            return [float(i) / float(count) for i in range(count)], origin, direction

        bone_s = [
            max(0.0, min(1.0 - 1.0e-10, value / total))
            for value in cumulative
        ]
        bone_s[0] = 0.0

        return bone_s, origin, direction

    @staticmethod
    def transform_ring_vertex_s(raw_s, origin, direction):
        """Map an absolute normalized curve s into ring coordinates."""
        if direction > 0:
            return (float(raw_s) - float(origin)) % 1.0
        return (float(origin) - float(raw_s)) % 1.0

    @staticmethod
    def end_falloff(t, mode):
        """Map 0..1 transition amount using a selectable easing curve."""
        t = max(0.0, min(1.0, float(t)))
        mode = str(mode or "Ease In Out")

        if mode == "Linear":
            return t

        if mode == "Ease In":
            return t * t

        if mode == "Ease Out":
            return 1.0 - (1.0 - t) * (1.0 - t)

        if mode == "Ease In Out":
            return t * t * (3.0 - 2.0 * t)

        if mode == "Smootherstep":
            return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)

        return t

    @staticmethod
    def _blend_with_endpoint(weights, endpoint_index, t, count):
        """Blend standard weights toward a pure endpoint influence."""
        t = max(0.0, min(1.0, float(t)))
        accum = {}

        for index, weight in weights:
            accum[index] = accum.get(index, 0.0) + float(weight) * t

        accum[endpoint_index] = (
            accum.get(endpoint_index, 0.0) + (1.0 - t)
        )

        return WeightSolver._normalize_sparse(
            sorted(accum.items(), key=lambda item: item[0]),
            count
        )

    @staticmethod
    def solve_bar(s, bone_s, degree, end_hold=0.0, end_falloff="Ease In Out"):
        count = len(bone_s)

        if count == 1:
            return [(0, 1.0)]

        s = max(0.0, min(1.0, float(s)))
        result = _evaluate_open_bspline(s, bone_s, degree)

        # The clamped B-Spline already pins the exact endpoints to the first
        # and last control points. End Hold is an optional artist control that
        # extends that pinning over a small normalized curve-length region.
        # The transition after the hold uses the actual adjacent CV interval
        # so it remains meaningful when the CV spacing is non-uniform.
        hold = max(0.0, min(0.49, float(end_hold)))

        if hold <= 1.0e-12 or count <= 1:
            return result

        first_span = max(1.0e-12, bone_s[1] - bone_s[0])
        last_span = max(1.0e-12, bone_s[-1] - bone_s[-2])

        first_transition_end = min(0.5, hold + first_span)
        last_transition_start = max(0.5, 1.0 - hold - last_span)

        if s <= hold:
            return [(0, 1.0)]

        if s < first_transition_end:
            transition_span = max(1.0e-12, first_transition_end - hold)
            t = (s - hold) / transition_span
            t = WeightSolver.end_falloff(t, end_falloff)
            return WeightSolver._blend_with_endpoint(
                result, 0, t, count
            )

        if s >= 1.0 - hold:
            return [(count - 1, 1.0)]

        if s > last_transition_start:
            transition_span = max(1.0e-12, (1.0 - hold) - last_transition_start)
            t = ((1.0 - hold) - s) / transition_span
            t = WeightSolver.end_falloff(t, end_falloff)
            return WeightSolver._blend_with_endpoint(
                result, count - 1, t, count
            )

        return result

    @staticmethod
    def solve_ring(s, bone_s, degree):
        return _evaluate_periodic_bspline(float(s), bone_s, degree)

    @staticmethod
    def _normalize_sparse(weights, count):
        if not weights:
            return [(0, 1.0)]

        total = sum(float(w) for _, w in weights)

        if total <= 1.0e-12:
            index = weights[0][0]
            return [(index, 1.0)]

        return [
            (idx, float(value) / total)
            for idx, value in weights
            if abs(float(value)) > 1.0e-12
        ]


# ============================================================================
# SkinCluster utilities
# ============================================================================

class SkinClusterWriter(object):

    @staticmethod
    def get_or_create_skin_cluster(mesh_shape, joint_paths):
        mesh_transform = get_transform_from_shape(mesh_shape)
        joint_names = [path.fullPathName() for path in joint_paths]

        existing = find_skin_cluster(mesh_shape)

        if existing:
            skin_fn = oma.MFnSkinCluster(
                om.MSelectionList().add(existing).getDependNode(0)
            )

            existing_influences = {
                path.fullPathName(): i
                for i, path in enumerate(skin_fn.influenceObjects())
            }

            missing = [
                joint_name
                for joint_name in joint_names
                if joint_name not in existing_influences
            ]

            for joint_name in missing:
                cmds.skinCluster(
                    existing,
                    edit=True,
                    addInfluence=joint_name,
                    lockWeights=False,
                    weight=0.0
                )

            return existing

        # Create with a permissive cluster configuration. maximumInfluences is
        # set to the total joint count only so the skinCluster itself does not
        # impose a smaller structural cap.
        skin = cmds.skinCluster(
            joint_names,
            mesh_transform,
            toSelectedBones=True,
            normalizeWeights=2,
            maximumInfluences=max(1, len(joint_names)),
            obeyMaxInfluences=False,
            name="curveToWeightSkinCluster#"
        )[0]

        try:
            cmds.setAttr(skin + ".obeyMaxInfluences", 0)
        except Exception:
            pass

        return skin

    @staticmethod
    def ensure_influences(skin_cluster, joint_paths):
        """
        Add missing joints to an existing skinCluster and return influence
        physical indices in the same order as joint_paths.
        """
        skin_obj = (
            om.MSelectionList()
            .add(skin_cluster)
            .getDependNode(0)
        )
        skin_fn = oma.MFnSkinCluster(skin_obj)

        existing_paths = list(skin_fn.influenceObjects())
        existing_by_name = {
            path.fullPathName(): i
            for i, path in enumerate(existing_paths)
        }

        for joint_path in joint_paths:
            if joint_path.fullPathName() not in existing_by_name:
                cmds.skinCluster(
                    skin_cluster,
                    edit=True,
                    addInfluence=joint_path.fullPathName(),
                    lockWeights=False,
                    weight=0.0
                )

        # Refresh after edits.
        skin_fn = oma.MFnSkinCluster(
            om.MSelectionList()
            .add(skin_cluster)
            .getDependNode(0)
        )

        influence_paths = list(skin_fn.influenceObjects())

        physical_indices = []
        for joint_path in joint_paths:
            target = joint_path.fullPathName()
            found = None

            for physical_index, influence_path in enumerate(influence_paths):
                if influence_path.fullPathName() == target:
                    found = physical_index
                    break

            if found is None:
                raise RuntimeError(
                    "Could not resolve influence index for {}".format(target)
                )

            physical_indices.append(found)

        return skin_fn, physical_indices

    @staticmethod
    def write_weights(mesh_shape, skin_cluster, joint_paths, vertex_weights):
        """
        Write all mesh vertex weights in one API operation.

        vertex_weights:
            list[ list[(joint_local_index, weight)] ]
        """
        mesh_dag = get_dag_path(mesh_shape)
        mesh_fn = om.MFnMesh(mesh_dag)
        vertex_count = mesh_fn.numVertices

        if len(vertex_weights) != vertex_count:
            raise RuntimeError(
                "Weight array size {} does not match vertex count {}."
                .format(len(vertex_weights), vertex_count)
            )

        skin_fn, physical_indices = SkinClusterWriter.ensure_influences(
            skin_cluster,
            joint_paths
        )

        component_fn = om.MFnSingleIndexedComponent()
        components = component_fn.create(om.MFn.kMeshVertComponent)
        component_fn.addElements(list(range(vertex_count)))

        # Write every influence in the skinCluster, not only the newly selected
        # joints. This makes Apply behave as a true replacement operation:
        # old/unselected influences are explicitly set to zero instead of
        # remaining on the mesh and corrupting the normalization.
        all_influence_paths = list(skin_fn.influenceObjects())
        all_physical_indices = list(range(len(all_influence_paths)))

        selected_physical_by_local = {
            local_index: physical_index
            for local_index, physical_index in enumerate(physical_indices)
        }

        influence_indices = om.MIntArray(all_physical_indices)
        flat_values = []

        for vertex_data in vertex_weights:
            local_map = dict(vertex_data)

            # Start every existing influence at zero.
            row = [0.0] * len(all_physical_indices)

            # Put the solver result into the corresponding physical slots.
            for local_joint_index, weight in local_map.items():
                physical_index = selected_physical_by_local[local_joint_index]
                row[physical_index] = float(weight)

            flat_values.extend(row)

        weights = om.MDoubleArray(flat_values)

        # normalize=False because the solver has already normalized every
        # vertex. All existing skinCluster influences are written explicitly,
        # so there is no stale influence weight left behind.
        skin_fn.setWeights(
            mesh_dag,
            components,
            influence_indices,
            weights,
            False,
            False
        )

        try:
            cmds.setAttr(skin_cluster + ".obeyMaxInfluences", 0)
        except Exception:
            pass

        return skin_cluster


# ============================================================================
# Main solver
# ============================================================================

class CurveToWeightProcessor(object):
    def __init__(
        self,
        curve_shape,
        mesh_shape,
        joints,
        mode,
        degree,
        end_hold=0.0,
        end_falloff="Ease In Out"
    ):
        self.curve_shape = curve_shape
        self.mesh_shape = mesh_shape
        self.joints = list(joints)
        self.mode = mode
        self.degree = int(degree)
        self.end_hold = max(0.0, min(0.49, float(end_hold))) if mode == "Bar" else 0.0
        self.end_falloff = str(end_falloff or "Ease In Out")

        if self.degree not in (1, 2, 3):
            raise ValueError("Degree must be 1, 2 or 3.")

        self.curve = CurveAnalyzer(curve_shape)
        self.joint_paths = get_joint_paths(self.joints)

    def solve(self):
        if self.curve.cv_count != len(self.joints):
            raise RuntimeError(
                "CV count ({}) must match joint count ({})."
                .format(self.curve.cv_count, len(self.joints))
            )

        cv_data = self.curve.cv_parameters_and_s()
        raw_bone_s = [item[1] for item in cv_data]

        _, vertex_s, radial_distances = self.curve.mesh_vertex_s(
            self.mesh_shape
        )

        if self.mode == "Ring":
            bone_s, ring_origin, ring_direction = WeightSolver.prepare_ring_bone_s(
                raw_bone_s
            )
            vertex_s = [
                WeightSolver.transform_ring_vertex_s(
                    s, ring_origin, ring_direction
                )
                for s in vertex_s
            ]
        else:
            bone_s = WeightSolver.validate_bone_s(
                raw_bone_s,
                self.curve.closed
            )

        vertex_weights = []

        if self.mode == "Ring":
            for s in vertex_s:
                vertex_weights.append(
                    WeightSolver.solve_ring(
                        s,
                        bone_s,
                        self.degree
                    )
                )
        else:
            for s in vertex_s:
                vertex_weights.append(
                    WeightSolver.solve_bar(
                        s,
                        bone_s,
                        self.degree,
                        self.end_hold,
                        self.end_falloff
                    )
                )

        return {
            "bone_s": bone_s,
            "vertex_s": vertex_s,
            "radial_distances": radial_distances,
            "weights": vertex_weights,
            "vertex_count": len(vertex_weights),
            "cv_count": self.curve.cv_count,
            "joint_count": len(self.joints),
            "curve_length": self.curve.length,
            "closed_curve": self.curve.closed,
            "ring_direction": (ring_direction if self.mode == "Ring" else None),
            "end_hold": self.end_hold,
            "end_falloff": self.end_falloff,
        }

    @staticmethod
    def statistics(result):
        weights = result["weights"]

        active_counts = []
        sums = []

        for vertex_data in weights:
            active_counts.append(len(vertex_data))
            sums.append(sum(w for _, w in vertex_data))

        return {
            "min_active": min(active_counts) if active_counts else 0,
            "max_active": max(active_counts) if active_counts else 0,
            "avg_active": (
                sum(active_counts) / float(len(active_counts))
                if active_counts else 0.0
            ),
            "min_sum": min(sums) if sums else 0.0,
            "max_sum": max(sums) if sums else 0.0,
            "curve_length": result["curve_length"],
            "vertex_count": result["vertex_count"],
            "joint_count": result["joint_count"],
        }


# ============================================================================
# UI
# ============================================================================

class CurveToWeightUI(QtWidgets.QDialog):
    WINDOW_TITLE = "Curve To Weight"

    def __init__(self, parent=None):
        super(CurveToWeightUI, self).__init__(parent or maya_main_window())

        self.setWindowTitle(self.WINDOW_TITLE)
        self.setObjectName("CurveToWeightUI")
        self.setMinimumWidth(520)
        self.setWindowFlags(
            self.windowFlags() |
            QtCore.Qt.Tool
        )

        self.curve_edit = QtWidgets.QLineEdit()
        self.curve_edit.setReadOnly(True)
        self.mesh_edit = QtWidgets.QLineEdit()
        self.mesh_edit.setReadOnly(True)
        self.joints_edit = QtWidgets.QLineEdit()
        self.joints_edit.setReadOnly(True)

        self.curve_btn = QtWidgets.QPushButton("Set")
        self.mesh_btn = QtWidgets.QPushButton("Set")
        self.joints_btn = QtWidgets.QPushButton("Set")

        self.mode_combo = QtWidgets.QComboBox()
        self.mode_combo.addItems(["Bar", "Ring"])

        self.degree_combo = QtWidgets.QComboBox()
        self.degree_combo.addItems(["1", "2", "3"])
        self.degree_combo.setCurrentIndex(2)

        self.end_hold_spin = QtWidgets.QDoubleSpinBox()
        self.end_hold_spin.setRange(0.0, 49.0)
        self.end_hold_spin.setDecimals(1)
        self.end_hold_spin.setSingleStep(1.0)
        self.end_hold_spin.setValue(0.0)
        self.end_hold_spin.setSuffix(" %")
        self.end_hold_spin.setToolTip(
            "Bar mode only: keep this percentage of the curve at each end "
            "fully driven by the first/last joint. 0% uses pure clamped "
            "B-Spline endpoint behavior."
        )

        self.end_falloff_combo = QtWidgets.QComboBox()
        self.end_falloff_combo.addItems([
            "Linear",
            "Ease In",
            "Ease Out",
            "Ease In Out",
            "Smootherstep",
        ])
        self.end_falloff_combo.setCurrentText("Ease In Out")
        self.end_falloff_combo.setToolTip(
            "Controls how End Hold transitions back into the normal weighting "
            "over the first/last joint interval."
        )

        self.preview_btn = QtWidgets.QPushButton("Preview")
        self.apply_btn = QtWidgets.QPushButton("Apply Weights")
        self.close_btn = QtWidgets.QPushButton("Close")

        self.status_label = QtWidgets.QLabel(
            "Select a curve, mesh and joints in CV order."
        )
        self.status_label.setWordWrap(True)

        self.report = QtWidgets.QPlainTextEdit()
        self.report.setReadOnly(True)
        self.report.setMinimumHeight(130)

        self._build_ui()
        self._connect_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)

        input_group = QtWidgets.QGroupBox("Input")
        input_layout = QtWidgets.QGridLayout(input_group)

        input_layout.addWidget(QtWidgets.QLabel("Curve"), 0, 0)
        input_layout.addWidget(self.curve_edit, 0, 1)
        input_layout.addWidget(self.curve_btn, 0, 2)

        input_layout.addWidget(QtWidgets.QLabel("Mesh"), 1, 0)
        input_layout.addWidget(self.mesh_edit, 1, 1)
        input_layout.addWidget(self.mesh_btn, 1, 2)

        input_layout.addWidget(QtWidgets.QLabel("Joints"), 2, 0)
        input_layout.addWidget(self.joints_edit, 2, 1)
        input_layout.addWidget(self.joints_btn, 2, 2)

        main_layout.addWidget(input_group)

        settings_group = QtWidgets.QGroupBox("Distribution")
        settings_layout = QtWidgets.QFormLayout(settings_group)

        settings_layout.addRow("Mode", self.mode_combo)
        settings_layout.addRow("Degree", self.degree_combo)
        settings_layout.addRow("End Hold", self.end_hold_spin)
        settings_layout.addRow("End Falloff", self.end_falloff_combo)

        main_layout.addWidget(settings_group)

        note = QtWidgets.QLabel(
            "Degree 1 = 2 local influences, "
            "Degree 2 = 3, Degree 3 = 4. "
            "There is no Max Influences limit; only the B-Spline support "
            "determines non-zero weights. End Hold optionally pins a percentage "
            "of each Bar-mode end to the first/last joint; End Falloff controls "
            "the transition back into the normal weighting."
        )
        note.setWordWrap(True)

        main_layout.addWidget(note)

        report_group = QtWidgets.QGroupBox("Preview Report")
        report_layout = QtWidgets.QVBoxLayout(report_group)
        report_layout.addWidget(self.report)
        main_layout.addWidget(report_group)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.preview_btn)
        button_layout.addWidget(self.apply_btn)
        button_layout.addStretch(1)
        button_layout.addWidget(self.close_btn)

        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.status_label)

    def _connect_ui(self):
        self.curve_btn.clicked.connect(self._set_curve)
        self.mesh_btn.clicked.connect(self._set_mesh)
        self.joints_btn.clicked.connect(self._set_joints)

        self.preview_btn.clicked.connect(self._preview)
        self.apply_btn.clicked.connect(self._apply)
        self.close_btn.clicked.connect(self.close)
        self.mode_combo.currentIndexChanged.connect(
            self._update_end_controls_state
        )
        self.end_hold_spin.valueChanged.connect(
            self._update_end_controls_state
        )

        self._update_end_controls_state()

    def _update_end_controls_state(self):
        is_bar = self.mode_combo.currentText() == "Bar"
        hold_enabled = is_bar and self.end_hold_spin.value() > 0.0

        self.end_hold_spin.setEnabled(is_bar)
        self.end_falloff_combo.setEnabled(hold_enabled)

        if is_bar:
            self.end_hold_spin.setToolTip(
                "Percentage of the curve length at each end that is held "
                "100% to the first/last joint. 0% = pure clamped B-Spline."
            )
            self.end_falloff_combo.setToolTip(
                "Transition shape from End Hold back to normal B-Spline weights."
            )
        else:
            self.end_hold_spin.setToolTip(
                "End Hold is only used in Bar mode."
            )
            self.end_falloff_combo.setToolTip(
                "End Falloff is only used when End Hold is greater than 0 in Bar mode."
            )

    # ------------------------------------------------------------------
    # Selection capture
    # ------------------------------------------------------------------

    @staticmethod
    def _selected_nodes():
        return cmds.ls(sl=True, long=True) or []

    def _set_curve(self):
        selection = self._selected_nodes()

        if not selection:
            self._set_status("Please select a NURBS curve first.", True)
            return

        curve = get_curve_shape(selection[0])

        if not curve:
            self._set_status(
                "{} does not contain a NURBS curve shape.".format(
                    selection[0]
                ),
                True
            )
            return

        transform = get_transform_from_shape(curve)
        self.curve_edit.setText(transform)

        analyzer = CurveAnalyzer(curve)

        form_name = {
            om.MFnNurbsCurve.kOpen: "open",
            om.MFnNurbsCurve.kClosed: "closed",
            om.MFnNurbsCurve.kPeriodic: "periodic",
        }.get(analyzer.form, str(analyzer.form))

        if analyzer.raw_cv_count != analyzer.cv_count:
            cv_text = "{} editable ({} internal)".format(
                analyzer.cv_count,
                analyzer.raw_cv_count
            )
        else:
            cv_text = str(analyzer.cv_count)

        self._set_status(
            "Curve set: {} | CVs: {} | spans: {} | degree: {} | form: {}"
            .format(
                transform,
                cv_text,
                analyzer.spans,
                analyzer.degree,
                form_name
            )
        )

    def _set_mesh(self):
        selection = self._selected_nodes()

        if not selection:
            self._set_status("Please select a mesh first.", True)
            return

        mesh = get_mesh_shape(selection[0])

        if not mesh:
            self._set_status(
                "{} does not contain a mesh shape.".format(selection[0]),
                True
            )
            return

        transform = get_transform_from_shape(mesh)
        self.mesh_edit.setText(transform)

        dag = get_dag_path(mesh)
        mesh_fn = om.MFnMesh(dag)

        self._set_status(
            "Mesh set: {} | Vertices: {}"
            .format(transform, mesh_fn.numVertices)
        )

    def _set_joints(self):
        selection = self._selected_nodes()
        joints = [
            node for node in selection
            if cmds.objExists(node) and cmds.nodeType(node) == "joint"
        ]

        if not joints:
            self._set_status(
                "Please select joints in exact CV order.",
                True
            )
            return

        self.joints_edit.setText(
            "{} joints".format(len(joints))
        )

        curve = self._current_curve_shape()

        if curve:
            analyzer = CurveAnalyzer(curve)
            cv_count = analyzer.cv_count

            if len(joints) != cv_count:
                self._set_status(
                    "Joints: {} | Editable curve CVs: {} | count does not match."
                    .format(len(joints), cv_count),
                    True
                )
            else:
                self._set_status(
                    "Joints set: {} | Editable CV count matched."
                    .format(len(joints))
                )
        else:
            self._set_status(
                "Joints set: {}. Set the curve to validate CV count."
                .format(len(joints))
            )

        self._joint_names = joints

    # ------------------------------------------------------------------
    # Current input
    # ------------------------------------------------------------------

    def _current_curve_shape(self):
        node = self.curve_edit.text().strip()

        if not node:
            return None

        curve = get_curve_shape(node)

        if not curve:
            raise RuntimeError("Invalid curve: {}".format(node))

        return curve

    def _current_mesh_shape(self):
        node = self.mesh_edit.text().strip()

        if not node:
            return None

        mesh = get_mesh_shape(node)

        if not mesh:
            raise RuntimeError("Invalid mesh: {}".format(node))

        return mesh

    def _current_joints(self):
        joints = getattr(self, "_joint_names", None)

        if not joints:
            raise RuntimeError(
                "No joints set. Select joints in CV order and click Set."
            )

        return list(joints)

    def _build_processor(self):
        curve = self._current_curve_shape()
        mesh = self._current_mesh_shape()
        joints = self._current_joints()

        if not curve:
            raise RuntimeError("Curve is not set.")

        if not mesh:
            raise RuntimeError("Mesh is not set.")

        mode = self.mode_combo.currentText()
        degree = int(self.degree_combo.currentText())
        end_hold = self.end_hold_spin.value() / 100.0
        end_falloff = self.end_falloff_combo.currentText()

        processor = CurveToWeightProcessor(
            curve_shape=curve,
            mesh_shape=mesh,
            joints=joints,
            mode=mode,
            degree=degree,
            end_hold=end_hold,
            end_falloff=end_falloff
        )

        return processor

    # ------------------------------------------------------------------
    # Preview
    # ------------------------------------------------------------------

    def _preview(self):
        try:
            self._set_status("Calculating weights...")

            processor = self._build_processor()
            result = processor.solve()
            stats = processor.statistics(result)

            lines = [
                "Curve: {}".format(self.curve_edit.text()),
                "Mesh: {}".format(self.mesh_edit.text()),
                "Mode: {}".format(processor.mode),
                "Degree: {}".format(processor.degree),
                "Ring direction: {}".format(result.get("ring_direction")) if processor.mode == "Ring" else "End Hold: {:.1f}%".format(result.get("end_hold", 0.0) * 100.0),
                "End Falloff: {}".format(processor.end_falloff),
                "Curve length: {:.6f}".format(stats["curve_length"]),
                "Vertices: {}".format(stats["vertex_count"]),
                "Joints / CVs: {}".format(stats["joint_count"]),
                "Active influences per vertex:",
                "  min = {}".format(stats["min_active"]),
                "  max = {}".format(stats["max_active"]),
                "  avg = {:.3f}".format(stats["avg_active"]),
                "Weight sum:",
                "  min = {:.8f}".format(stats["min_sum"]),
                "  max = {:.8f}".format(stats["max_sum"]),
                "",
                "First 5 vertices:"
            ]

            for vertex_index, vertex_data in enumerate(
                result["weights"][:5]
            ):
                parts = []
                for local_joint_index, weight in vertex_data:
                    joint_name = processor.joints[local_joint_index]
                    short_name = joint_name.split("|")[-1]
                    parts.append(
                        "{}={:.4f}".format(short_name, weight)
                    )

                lines.append(
                    "  v{}: {}".format(
                        vertex_index,
                        ", ".join(parts)
                    )
                )

            self.report.setPlainText("\n".join(lines))
            self._set_status("Preview calculated. Scene was not modified.")

        except Exception as exc:
            self.report.setPlainText(
                "ERROR\n\n{}\n\n{}".format(
                    exc,
                    traceback.format_exc()
                )
            )
            self._set_status(str(exc), True)

    # ------------------------------------------------------------------
    # Apply
    # ------------------------------------------------------------------

    def _apply(self):
        try:
            self._set_status("Calculating and writing skin weights...")

            processor = self._build_processor()
            result = processor.solve()

            mesh_shape = processor.mesh_shape
            joint_paths = processor.joint_paths

            existing_skin = find_skin_cluster(mesh_shape)

            cmds.undoInfo(
                openChunk=True,
                chunkName="CurveToWeight"
            )

            try:
                skin_cluster = SkinClusterWriter.get_or_create_skin_cluster(
                    mesh_shape,
                    joint_paths
                )

                SkinClusterWriter.write_weights(
                    mesh_shape=mesh_shape,
                    skin_cluster=skin_cluster,
                    joint_paths=joint_paths,
                    vertex_weights=result["weights"]
                )

                try:
                    cmds.refresh(suspend=False)
                except Exception:
                    pass

            finally:
                cmds.undoInfo(closeChunk=True)

            stats = processor.statistics(result)

            self.report.setPlainText(
                "Applied successfully.\n\n"
                "SkinCluster: {}\n"
                "Reused existing: {}\n"
                "Mode: {}\n"
                "Degree: {}\n"
                "End Hold: {:.1f}%\n"
                "End Falloff: {}\n"
                "Vertices: {}\n"
                "Joints / CVs: {}\n"
                "Active influences per vertex: {:.3f} avg, {}~{}.\n"
                "Weight sum: {:.8f}~{:.8f}"
                .format(
                    skin_cluster,
                    bool(existing_skin),
                    processor.mode,
                    processor.degree,
                    processor.end_hold * 100.0,
                    processor.end_falloff,
                    stats["vertex_count"],
                    stats["joint_count"],
                    stats["avg_active"],
                    stats["min_active"],
                    stats["max_active"],
                    stats["min_sum"],
                    stats["max_sum"]
                )
            )

            self._set_status(
                "Weights applied to {}.".format(
                    get_transform_from_shape(mesh_shape)
                )
            )

        except Exception as exc:
            try:
                cmds.undoInfo(closeChunk=True)
            except Exception:
                pass

            self._set_status(str(exc), True)
            self.report.setPlainText(
                "ERROR\n\n{}\n\n{}".format(
                    exc,
                    traceback.format_exc()
                )
            )

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def _set_status(self, message, is_error=False):
        self.status_label.setText(message)

        if is_error:
            self.status_label.setStyleSheet(
                "QLabel { color: #d77; }"
            )
        else:
            self.status_label.setStyleSheet(
                "QLabel { color: palette(text); }"
            )


# ============================================================================
# Public entry
# ============================================================================

def show():
    """Show / raise the tool window."""
    global _WINDOW

    try:
        if _WINDOW is not None:
            _WINDOW.close()
            _WINDOW.deleteLater()
    except Exception:
        pass

    _WINDOW = CurveToWeightUI()
    _WINDOW.show()
    _WINDOW.raise_()
    _WINDOW.activateWindow()

    return _WINDOW


def main():
    return show()


if __name__ == "__main__":
    show()