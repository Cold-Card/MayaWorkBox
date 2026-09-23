# -*- coding: UTF-8 -*-
"""
Pure influence-tree UI helpers.

This module intentionally avoids Maya and Qt imports so its state transitions
can be exercised outside Maya with small duck-typed test objects.
"""
from __future__ import unicode_literals

import time


SEARCH_PLACEHOLDER = "搜索影响物名称，空格可输入多个关键词…"
SEARCH_TOOLTIP = (
    "输入骨骼名称的一部分进行搜索。\n"
    "多个关键词用空格分隔，匹配任意一个关键词。\n"
    "* 表示任意字符，例如：leg_*。\n"
    "点击右侧 × 清空搜索。"
)


def expand_parent_chain(item):
    """Expand every ancestor of ``item`` without expanding the item itself."""
    parent = None if item is None else item.parent()
    while parent is not None:
        parent.setExpanded(True)
        parent = parent.parent()


def set_branch_expanded(item, expanded):
    """Recursively apply one expanded state to an item and its descendants."""
    if item is None:
        return

    item.setExpanded(expanded)
    for child_index in range(item.childCount()):
        set_branch_expanded(item.child(child_index), expanded)


def is_recursive_toggle_request(button, modifiers, left_button, control_modifier, shift_modifier):
    """Return whether an input event requests recursive branch toggling."""
    required_modifiers = control_modifier | shift_modifier
    return button == left_button and (modifiers & required_modifiers) == required_modifiers


def is_branch_indicator_hit(x, depth, indentation, column_left=0):
    """Test whether a viewport x coordinate is inside an item's disclosure cell."""
    if indentation <= 0 or depth < 0:
        return False
    indicator_left = column_left + depth * indentation
    return indicator_left <= x < indicator_left + indentation


def reveal_item(view, item, scroll_hint, set_current=True):
    """Make an item current, reveal its ancestors, and center it in the view."""
    if item is None:
        return
    expand_parent_chain(item)
    if set_current:
        view.setCurrentItem(item)
    view.scrollToItem(item, scroll_hint)


def first_existing_target(tree_items, paint_targets):
    """Return the first visible tree item following paint target order."""
    for target in paint_targets or []:
        if target in tree_items:
            return tree_items[target]
    return None


def filter_hierarchy_records(records, is_match):
    """
    Keep only name-matching records and connect them to matching ancestors.

    Non-matching Maya DAG parents are intentionally omitted. A matching record
    becomes a root row when none of its matching DAG ancestors are present.
    Special rows without searchable influence text, such as Mask and DQ, are
    also excluded while an influence-name search is active.
    """
    matched_records = [
        record
        for record in records
        if record.get("search_text") is not None
        and is_match(record["search_text"])
    ]
    matched_paths = set(
        record["dag_path"]
        for record in matched_records
        if record.get("dag_path")
    )

    result = []
    for record in matched_records:
        filtered_record = dict(record)
        parent_path = None
        dag_path = record.get("dag_path")
        if dag_path and "|" in dag_path:
            candidate = dag_path.rsplit("|", 1)[0]
            while candidate:
                if candidate in matched_paths:
                    parent_path = candidate
                    break
                candidate = candidate.rsplit("|", 1)[0]
        filtered_record["search_parent_path"] = parent_path
        result.append(filtered_record)
    return result


def prepare_display_records(records, hierarchy_enabled, is_match=None):
    """
    Prepare influence rows for hierarchical or original flat presentation.

    ``display_parent_path`` is always explicit so the Qt builder does not need
    to infer a parent in flat mode. Search excludes special non-influence rows
    in both modes.
    """
    if is_match is not None:
        if hierarchy_enabled:
            result = filter_hierarchy_records(records, is_match)
        else:
            result = [
                dict(record)
                for record in records
                if record.get("search_text") is not None
                and is_match(record["search_text"])
            ]
    else:
        result = [dict(record) for record in records]

    for record in result:
        if hierarchy_enabled:
            record["display_parent_path"] = record.get("search_parent_path")
        else:
            record["display_parent_path"] = None
    return result


def apply_expansion_policy(view, hierarchy_items, had_items, filter_text, expanded_keys):
    """
    Expand all only while searching; otherwise preserve or start collapsed.

    The current target's ancestor chain is revealed separately by
    ``reveal_item`` so unrelated skeleton branches remain collapsed.
    """
    if filter_text:
        view.expandAll()
        return

    if not had_items:
        return

    for hierarchy_key, item in hierarchy_items.items():
        item.setExpanded(hierarchy_key in expanded_keys)


class SampleInfluenceRevealState(object):
    """Track the real sample-influence hotkey lifecycle."""

    def __init__(self, clock=None, grace_seconds=0.25):
        self.clock = time.time if clock is None else clock
        self.grace_seconds = grace_seconds
        self.active = False
        self.grace_deadline = None

    def begin(self):
        self.active = True
        self.grace_deadline = None

    def end(self):
        self.active = False
        self.grace_deadline = self.clock() + self.grace_seconds

    def cancel(self):
        self.active = False
        self.grace_deadline = None

    def should_reveal(self):
        if self.active:
            return True
        if self.grace_deadline is None:
            return False
        if self.clock() <= self.grace_deadline:
            self.grace_deadline = None
            return True
        self.grace_deadline = None
        return False


sample_influence_reveal_state = SampleInfluenceRevealState()


def resolve_unique_dag_paths(raw_paths, long_matches):
    """
    Resolve each raw path from one batch ``cmds.ls(..., long=True)`` result.

    Ambiguous short names intentionally resolve to ``None`` so callers can keep
    those influences as independent root rows instead of merging them.
    """
    matches = list(long_matches or [])
    result = []
    for raw_path in raw_paths:
        if not raw_path:
            result.append(None)
            continue
        if raw_path in matches:
            result.append(raw_path)
            continue

        suffix = "|" + raw_path.lstrip("|")
        candidates = [candidate for candidate in matches if candidate.endswith(suffix)]
        result.append(candidates[0] if len(candidates) == 1 else None)
    return result


def drop_duplicate_dag_paths(paths):
    """Demote every repeated DAG path so no logical influence is overwritten."""
    counts = {}
    for path in paths:
        if path is not None:
            counts[path] = counts.get(path, 0) + 1
    return [path if path is None or counts[path] == 1 else None for path in paths]


class SearchTransition(object):
    """Store one pre-search snapshot until search is cleared or invalidated."""

    def __init__(self):
        self.snapshot = None

    def enter(self, text, snapshot):
        if text and self.snapshot is None:
            self.snapshot = snapshot
        return self.snapshot

    def leave(self, text):
        if text or self.snapshot is None:
            return None
        snapshot = self.snapshot
        self.snapshot = None
        return snapshot

    def clear(self):
        self.snapshot = None


class TreeSnapshot(object):
    """Serializable values needed to restore the influence tree after search."""

    def __init__(self, skin_cluster, layer_id, expanded_keys, scroll_value, current_id, selected_ids, paint_targets):
        self.skin_cluster = skin_cluster
        self.layer_id = layer_id
        self.expanded_keys = set(expanded_keys)
        self.scroll_value = scroll_value
        self.current_id = current_id
        self.selected_ids = list(selected_ids)
        self.paint_targets = list(paint_targets)

    def matches(self, skin_cluster, layer_id):
        return self.skin_cluster == skin_cluster and self.layer_id == layer_id


def capture_tree_snapshot(view, hierarchy_items, get_item_id, skin_cluster, layer_id, paint_targets):
    """Capture stable IDs and values instead of short-lived Qt item objects."""
    expanded_keys = set(
        hierarchy_key for hierarchy_key, item in hierarchy_items.items() if item.isExpanded()
    )
    selected_ids = []
    for item in view.selectedItems():
        item_id = get_item_id(item)
        if item_id is not None:
            selected_ids.append(item_id)

    return TreeSnapshot(
        skin_cluster=skin_cluster,
        layer_id=layer_id,
        expanded_keys=expanded_keys,
        scroll_value=view.verticalScrollBar().value(),
        current_id=get_item_id(view.currentItem()),
        selected_ids=selected_ids,
        paint_targets=paint_targets or [],
    )


def restore_tree_snapshot(view, hierarchy_items, tree_items, snapshot):
    """
    Restore tree widgets and return paint targets that still exist in the tree.

    Signal blocking remains the caller's responsibility because the real Qt
    owner already provides a project-specific context manager for it.
    """
    for hierarchy_key, item in hierarchy_items.items():
        item.setExpanded(hierarchy_key in snapshot.expanded_keys)

    selected_ids = set(snapshot.selected_ids)
    for item_id, item in tree_items.items():
        item.setSelected(item_id in selected_ids)

    current_item = tree_items.get(snapshot.current_id)
    if current_item is not None:
        view.setCurrentItem(current_item)

    view.verticalScrollBar().setValue(snapshot.scroll_value)
    return [item_id for item_id in snapshot.paint_targets if item_id in tree_items]
