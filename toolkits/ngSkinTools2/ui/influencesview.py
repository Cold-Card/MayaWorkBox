# -*- coding: UTF-8 -*-
from ngSkinTools2 import signal
from ngSkinTools2.api import influence_names
from ngSkinTools2.api.influenceMapping import InfluenceInfo
from ngSkinTools2.api.layers import Layer
from ngSkinTools2.api.log import getLogger
from ngSkinTools2.api.pyside import QActionGroup, QtCore, QtGui, QtWidgets
from ngSkinTools2.api.target_info import list_influences
from ngSkinTools2.ui import actions, qt
from ngSkinTools2.ui.influence_locking import (
    apply_skin_cluster_influence_lock,
)
from ngSkinTools2.ui.influence_tree_state import (
    SearchTransition,
    apply_expansion_policy,
    capture_tree_snapshot,
    drop_duplicate_dag_paths,
    first_existing_target,
    is_branch_indicator_hit,
    is_recursive_toggle_request,
    prepare_display_records,
    resolve_unique_dag_paths,
    restore_tree_snapshot,
    reveal_item,
    sample_influence_reveal_state,
    set_branch_expanded,
)
from ngSkinTools2.ui.layout import scale_multiplier
from ngSkinTools2.ui.options import Config, config

log = getLogger("influencesView")
_ = Layer  # only imported for type reference


class RecursiveBranchToggleFilter(QtCore.QObject):
    """Handle Ctrl+Shift+left-click on a tree disclosure indicator."""

    def __init__(self, view):
        super(RecursiveBranchToggleFilter, self).__init__(view)
        self.view = view

    @staticmethod
    def item_depth(item):
        depth = 0
        parent_item = item.parent()
        while parent_item is not None:
            depth += 1
            parent_item = parent_item.parent()
        return depth

    @staticmethod
    def event_position(event):
        position = getattr(event, "position", None)
        if position is not None:
            return position().toPoint()
        return event.pos()

    def eventFilter(self, watched, event):
        if event.type() != QtCore.QEvent.MouseButtonPress:
            return QtCore.QObject.eventFilter(self, watched, event)

        if not is_recursive_toggle_request(
            event.button(),
            event.modifiers(),
            QtCore.Qt.LeftButton,
            QtCore.Qt.ControlModifier,
            QtCore.Qt.ShiftModifier,
        ):
            return QtCore.QObject.eventFilter(self, watched, event)

        position = self.event_position(event)
        item = self.view.itemAt(position)
        if item is None or item.childCount() == 0:
            return QtCore.QObject.eventFilter(self, watched, event)

        column_left = self.view.header().sectionViewportPosition(0)
        if not is_branch_indicator_hit(
            position.x(),
            self.item_depth(item),
            self.view.indentation(),
            column_left,
        ):
            return QtCore.QObject.eventFilter(self, watched, event)

        with qt.signals_blocked(self.view):
            set_branch_expanded(item, not item.isExpanded())

        self.view.viewport().update()
        event.accept()
        return True


def build_used_influences_action(parent):
    def toggle():
        config.influences_show_used_influences_only.set(not config.influences_show_used_influences_only())

    result = actions.define_action(
        parent,
        "只显示有权重的影响物",
        callback=toggle,
        tooltip="如果启用，“影响”视图将只显示当前层上具有权重的影响",
    )

    @signal.on(config.influences_show_used_influences_only.changed, qtParent=parent)
    def update():
        result.setChecked(config.influences_show_used_influences_only())

    result.setCheckable(True)
    update()
    return result


def build_set_influences_sorted_action(parent):
    from ngSkinTools2.ui import actions

    def toggle():
        new_value = Config.InfluencesSortDescending
        if config.influences_sort() == new_value:
            new_value = Config.InfluencesSortUnsorted
        config.influences_sort.set(new_value)

    result = actions.define_action(
        parent,
        "影响物排序 ( 按名称 )",
        callback=toggle,
        tooltip="按名称对影响进行排序",
    )

    @signal.on(config.influences_sort.changed, qtParent=parent)
    def update():
        result.setChecked(config.influences_sort() == Config.InfluencesSortDescending)

    result.setCheckable(True)
    update()
    return result


def build_influences_display_mode_actions(parent):
    """Build an exclusive, persistent hierarchy/flat display mode pair."""

    group = QActionGroup(parent)
    group.setExclusive(True)

    hierarchy_action = actions.define_action(
        parent,
        "骨骼层级",
        callback=lambda: config.influences_display_mode.set(
            Config.InfluencesDisplayHierarchy
        ),
        tooltip="按照 Maya 骨骼父子关系显示影响物",
    )
    flat_action = actions.define_action(
        parent,
        "原版平铺",
        callback=lambda: config.influences_display_mode.set(
            Config.InfluencesDisplayFlat
        ),
        tooltip="按照 ngSkinTools2 原版方式平铺显示影响物",
    )

    for display_action in (hierarchy_action, flat_action):
        display_action.setCheckable(True)
        group.addAction(display_action)

    @signal.on(config.influences_display_mode.changed, qtParent=parent)
    def update():
        hierarchy_action.setChecked(
            config.influences_display_mode()
            == Config.InfluencesDisplayHierarchy
        )
        flat_action.setChecked(
            config.influences_display_mode() == Config.InfluencesDisplayFlat
        )

    update()
    return group, hierarchy_action, flat_action


icon_mask = QtGui.QIcon(":/blendColors.svg")
icon_dq = QtGui.QIcon(":/rotate_M.png")
icon_joint = QtGui.QIcon(":/joint.svg")
icon_joint_disabled = qt.image_icon("joint_disabled.png")
icon_transform = QtGui.QIcon(":/cube.png")
icon_transform_disabled = qt.image_icon("cube_disabled.png")


def _nearest_parent_influence_path(path, influence_paths):
    """Return the nearest Maya DAG ancestor that is also a skin influence."""
    if not path or "|" not in path:
        return None

    parent_path = path.rsplit("|", 1)[0]
    while parent_path:
        if parent_path in influence_paths:
            return parent_path
        parent_path = parent_path.rsplit("|", 1)[0]
    return None


def _resolve_maya_long_dag_paths(paths):
    """Resolve all influence paths with one Maya command round-trip."""
    paths = list(paths)
    query_paths = list(set([path for path in paths if path]))
    if not query_paths:
        return [None for _path in paths]
    try:
        from maya import cmds

        matches = cmds.ls(query_paths, long=True) or []
    except Exception as err:
        log.warning("failed to resolve influence DAG paths: %s", err)
        matches = [path for path in paths if path and path.startswith("|")]
    return drop_duplicate_dag_paths(resolve_unique_dag_paths(paths, matches))


def build_view(parent, actions, session, filter):
    """
    :param parent: ui parent
    :type actions: ngSkinTools2.ui.actions.Actions
    :type session: ngSkinTools2.ui.session.Session
    :type filter: InfluenceNameFilter
    """

    icon_locked = QtGui.QIcon(":/Lock_ON.png")
    icon_unlocked = QtGui.QIcon(":/Lock_OFF_grey.png")

    id_role = QtCore.Qt.UserRole + 1
    hierarchy_key_role = QtCore.Qt.UserRole + 2
    search_text_role = QtCore.Qt.UserRole + 3
    item_size_hint = QtCore.QSize(25 * scale_multiplier, 25 * scale_multiplier)

    def get_item_id(item):
        if item is None:
            return None
        return item.data(0, id_role)

    tree_items = {}
    hierarchy_items = {}
    search_state = SearchTransition()
    dag_path_cache = {"key": None, "paths": None}
    hierarchy_expanded_keys = set()
    last_display_mode = {"value": config.influences_display_mode()}

    def build_items(view, items, layer):
        # type: (QtWidgets.QTreeWidget, list[InfluenceInfo], Layer) -> None
        is_group_layer = layer is not None and layer.num_children != 0

        def rebuild_buttons(item, item_id, buttons):
            bar = QtWidgets.QToolBar(parent=parent)
            bar.setMovable(False)
            bar.setIconSize(QtCore.QSize(13 * scale_multiplier, 13 * scale_multiplier))

            def add_or_remove(input_list, items, should_add):
                if should_add:
                    return list(input_list) + list(items)
                return [i for i in input_list if i not in items]

            def lock_unlock_handler(lock):
                def handler():
                    targets = layer.paint_targets
                    if item_id not in targets:
                        targets = (item_id,)

                    layer.locked_influences = add_or_remove(layer.locked_influences, targets, lock)
                    log.info("updated locked influences to %r", layer.locked_influences)
                    session.events.influencesListUpdated.emit()

                return handler

            if "unlocked" in buttons:
                a = bar.addAction(icon_unlocked, "Toggle locked/unlocked")
                qt.on(a.triggered)(lock_unlock_handler(True))

            if "locked" in buttons:
                a = bar.addAction(icon_locked, "Toggle locked/unlocked")
                qt.on(a.triggered)(lock_unlock_handler(False))

            view.setItemWidget(item, 1, bar)

        selected_ids = []
        if session.state.currentLayer.layer:
            selected_ids = session.state.currentLayer.layer.paint_targets
        current_id = None if not selected_ids else selected_ids[0]

        with qt.signals_blocked(view):
            tree_items.clear()
            hierarchy_items.clear()
            tree_root = view.invisibleRootItem()

            expanded_keys = set(hierarchy_expanded_keys)
            had_items = tree_root.childCount() != 0

            def collect_expanded(parent_item):
                for child_index in range(parent_item.childCount()):
                    child = parent_item.child(child_index)
                    hierarchy_key = child.data(0, hierarchy_key_role)
                    if hierarchy_key and child.isExpanded():
                        expanded_keys.add(hierarchy_key)
                    collect_expanded(child)

            if last_display_mode["value"] == Config.InfluencesDisplayHierarchy:
                expanded_keys.clear()
                collect_expanded(tree_root)
                hierarchy_expanded_keys.clear()
                hierarchy_expanded_keys.update(expanded_keys)
            view.clear()

            visible_items = list(wanted_tree_items(
                items=items,
                include_dq_item=session.state.skin_cluster_dq_channel_used,
                is_group_layer=is_group_layer,
                layer=layer,
                config=config,
                filter=None,
            ))

            influences_by_id = {influence.logicalIndex: influence for influence in items}
            raw_paths = [
                None if influences_by_id.get(item_id) is None else influences_by_id[item_id].path
                for item_id, _display_name, _icon, _buttons in visible_items
            ]
            cache_key = tuple(raw_paths)
            if dag_path_cache["key"] != cache_key:
                dag_path_cache["key"] = cache_key
                dag_path_cache["paths"] = _resolve_maya_long_dag_paths(raw_paths)

            records = []
            for visible_item, dag_path in zip(visible_items, dag_path_cache["paths"]):
                item_id, display_name, icon, buttons = visible_item
                influence = influences_by_id.get(item_id)
                records.append(
                    {
                        "id": item_id,
                        "display_name": display_name,
                        "icon": icon,
                        "buttons": buttons,
                        "dag_path": dag_path,
                        "search_text": None if influence is None else influence.path_name(),
                    }
                )

            searching = bool(filter.currentFilterString)
            hierarchy_enabled = (
                config.influences_display_mode()
                == Config.InfluencesDisplayHierarchy
            )
            records = prepare_display_records(
                records,
                hierarchy_enabled=hierarchy_enabled,
                is_match=filter.is_match if searching else None,
            )

            records_by_path = {record["dag_path"]: record for record in records if record["dag_path"]}
            influence_paths = set(records_by_path.keys())
            created_records = {}

            def create_record(record):
                record_key = record["dag_path"] or "special:{0}".format(record["id"])
                if record_key in created_records:
                    return created_records[record_key]

                parent_item = tree_root
                label = record["display_name"]
                if record["dag_path"] and hierarchy_enabled:
                    parent_path = record.get("display_parent_path")
                    if not searching:
                        parent_path = _nearest_parent_influence_path(
                            record["dag_path"],
                            influence_paths,
                        )
                    if parent_path is not None:
                        parent_item = create_record(records_by_path[parent_path])
                    label = record["dag_path"].rsplit("|", 1)[-1]

                item = QtWidgets.QTreeWidgetItem([label])
                item.setData(0, hierarchy_key_role, record_key)
                item.setData(0, id_role, record["id"])
                item.setData(0, search_text_role, record["search_text"])
                item.setIcon(0, record["icon"])
                item.setSizeHint(0, item_size_hint)
                if record["dag_path"]:
                    item.setToolTip(0, record["dag_path"])
                parent_item.addChild(item)

                tree_items[record["id"]] = item
                if record["id"] == current_id:
                    view.setCurrentItem(item, 0, QtCore.QItemSelectionModel.NoUpdate)
                item.setSelected(record["id"] in selected_ids)
                rebuild_buttons(item, record["id"], record["buttons"])

                created_records[record_key] = item
                return item

            for record in records:
                create_record(record)

            hierarchy_items.update(created_records)

            if hierarchy_enabled:
                apply_expansion_policy(
                    view,
                    created_records,
                    had_items,
                    filter.currentFilterString,
                    expanded_keys,
                )
            last_display_mode["value"] = config.influences_display_mode()

    view = QtWidgets.QTreeWidget(parent)
    view.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
    view.setUniformRowHeights(True)
    view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
    view.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
    actions.addInfluencesActions(view)
    from ngSkinTools2.ui import actions as actions_module

    view.addAction(actions.separator(parent, "锁定管理"))

    def set_all_skin_influences_locked(lock):
        layer = session.state.currentLayer.layer
        skin_cluster = session.state.currentLayer.selectedSkinCluster
        if (
            layer is None
            or skin_cluster is None
            or getattr(layer, "num_children", 0) != 0
        ):
            return

        influences = list_influences(skin_cluster)
        scroll_value = view.verticalScrollBar().value()
        if not apply_skin_cluster_influence_lock(layer, influences, lock):
            return

        log.info(
            "%s all influences for skinCluster %r",
            "locked" if lock else "unlocked",
            skin_cluster,
        )
        session.events.influencesListUpdated.emit()

        def restore_scroll_position():
            view.verticalScrollBar().setValue(scroll_value)

        QtCore.QTimer.singleShot(0, restore_scroll_position)

    lock_all_action = actions_module.define_action(
        view,
        "锁定全部蒙皮影响物",
        callback=lambda: set_all_skin_influences_locked(True),
        tooltip="锁定当前 skinCluster 中的全部影响物",
    )
    unlock_all_action = actions_module.define_action(
        view,
        "解锁全部蒙皮影响物",
        callback=lambda: set_all_skin_influences_locked(False),
        tooltip="解锁当前 skinCluster 中的全部影响物",
    )
    view.addAction(lock_all_action)
    view.addAction(unlock_all_action)

    def update_bulk_lock_actions_enabled():
        layer = session.state.currentLayer.layer
        enabled = (
            layer is not None
            and session.state.currentLayer.selectedSkinCluster is not None
            and getattr(layer, "num_children", 0) == 0
        )
        lock_all_action.setEnabled(enabled)
        unlock_all_action.setEnabled(enabled)

    update_bulk_lock_actions_enabled()
    view.addAction(actions.separator(parent, "显示设置"))
    view.addAction(actions.show_used_influences_only)
    view.addAction(actions.set_influences_sorted)
    view.addAction(actions.separator(parent, "骨骼层级"))

    expand_all_action = actions_module.define_action(view, "展开全部", callback=view.expandAll)
    collapse_all_action = actions_module.define_action(view, "折叠全部", callback=view.collapseAll)
    view.addAction(expand_all_action)
    view.addAction(collapse_all_action)
    hierarchy_actions_enabled = (
        config.influences_display_mode()
        == Config.InfluencesDisplayHierarchy
    )
    expand_all_action.setEnabled(hierarchy_actions_enabled)
    collapse_all_action.setEnabled(hierarchy_actions_enabled)
    view.setIndentation(10 * scale_multiplier)
    view.header().setStretchLastSection(False)
    view.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)

    view.setHeaderLabels(["影响物", ""])
    view.header().setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
    view.setColumnWidth(1, 25 * scale_multiplier)
    view.recursive_branch_toggle_filter = RecursiveBranchToggleFilter(view)
    view.viewport().installEventFilter(view.recursive_branch_toggle_filter)

    # view.setHeaderHidden(True)
    def refresh_items():
        items = list_influences(session.state.currentLayer.selectedSkinCluster)

        def sort_func(a):
            """
            :type a: InfluenceInfo
            """
            return a.name

        # items = sorted(items, key=sort_func)
        build_items(view, items, session.state.currentLayer.layer)

    @signal.on(
        config.influences_show_used_influences_only.changed,
        config.influences_sort.changed,
        config.influences_display_mode.changed,
        session.events.influencesListUpdated,
    )
    def influence_list_changed():
        update_bulk_lock_actions_enabled()
        hierarchy_actions_enabled = (
            config.influences_display_mode()
            == Config.InfluencesDisplayHierarchy
        )
        expand_all_action.setEnabled(hierarchy_actions_enabled)
        collapse_all_action.setEnabled(hierarchy_actions_enabled)
        refresh_items()

    @signal.on(filter.changed)
    def filter_changed():
        layer = session.state.currentLayer.layer
        skin_cluster = session.state.currentLayer.selectedSkinCluster
        layer_id = None if layer is None else layer.id

        if filter.currentFilterString and search_state.snapshot is None and layer is not None:
            search_state.enter(
                filter.currentFilterString,
                capture_tree_snapshot(
                    view,
                    hierarchy_items,
                    get_item_id,
                    skin_cluster,
                    layer_id,
                    layer.paint_targets,
                ),
            )

        snapshot = search_state.leave(filter.currentFilterString)
        refresh_items()

        if snapshot is None or layer is None or not snapshot.matches(skin_cluster, layer_id):
            return

        with qt.signals_blocked(view):
            restored_targets = restore_tree_snapshot(
                view,
                hierarchy_items,
                tree_items,
                snapshot,
            )

        if list(layer.paint_targets) != restored_targets:
            layer.paint_targets = restored_targets

        def restore_scroll_position():
            view.verticalScrollBar().setValue(snapshot.scroll_value)

        QtCore.QTimer.singleShot(0, restore_scroll_position)

    @signal.on(session.events.currentLayerChanged, qtParent=view)
    def current_layer_changed():
        update_bulk_lock_actions_enabled()
        snapshot = search_state.snapshot
        skin_cluster = session.state.currentLayer.selectedSkinCluster
        layer = session.state.currentLayer.layer
        layer_id = None if layer is None else layer.id
        if snapshot is not None and not snapshot.matches(skin_cluster, layer_id):
            search_state.clear()

        if not session.state.currentLayer.layer:
            build_items(view, [], None)
        else:
            log.info("current layer changed to %s", session.state.currentLayer.layer)
            refresh_items()
            current_influence_changed()

    @signal.on(session.events.currentInfluenceChanged, qtParent=view)
    def current_influence_changed():
        if session.state.currentLayer.layer is None:
            return

        log.info("current influence changed - updating item selection")
        with qt.signals_blocked(view):
            targets = session.state.currentLayer.layer.paint_targets
            should_reveal = sample_influence_reveal_state.should_reveal()
            for tree_item in tree_items.values():
                selected = get_item_id(tree_item) in targets
                tree_item.setSelected(selected)

            target_item = first_existing_target(tree_items, targets)
            if target_item is not None:
                view.setCurrentItem(target_item, 0, QtCore.QItemSelectionModel.NoUpdate)
                if should_reveal:
                    reveal_item(
                        view,
                        target_item,
                        QtWidgets.QAbstractItemView.PositionAtCenter,
                        set_current=False,
                    )

    @qt.on(view.currentItemChanged)
    def current_item_changed(curr, prev):
        if curr is None:
            return

        if session.state.selectedSkinCluster is None:
            return

        if not session.state.currentLayer.layer:
            return

        log.info("focused item changed: %r", get_item_id(curr))
        sync_paint_targets_to_selection()

    @qt.on(view.itemSelectionChanged)
    def sync_paint_targets_to_selection():
        log.info("syncing paint targets")
        selected_ids = [get_item_id(item) for item in view.selectedItems()]
        selected_ids = [i for i in selected_ids if i is not None]

        current_item = view.currentItem()
        if current_item and current_item.isSelected():
            # move id of current item to front, if it's selected
            item_id = get_item_id(current_item)
            selected_ids.remove(item_id)
            selected_ids = [item_id] + selected_ids

        if session.state.currentLayer.layer:
            session.state.currentLayer.layer.paint_targets = selected_ids

    current_layer_changed()

    return view


def get_icon(influence, is_joint):
    if influence.used:
        return icon_joint if is_joint else icon_transform
    return icon_joint_disabled if is_joint else icon_transform_disabled


def wanted_tree_items(
    layer,
    config,
    is_group_layer,
    include_dq_item,
    filter,
    items,
):
    """

    :type items: list[InfluenceInfo]
    """

    if layer is None:
        return

    # calculate "used" regardless as we're displaying it visually even if "show used influences only" is toggled off
    used = set((layer.get_used_influences() or []))
    locked = set((layer.locked_influences or []))
    for i in items:
        i.used = i.logicalIndex in used
        i.locked = i.logicalIndex in locked

    if config.influences_show_used_influences_only() and layer is not None:
        items = [i for i in items if i.used]

    if is_group_layer:
        items = []

    yield "mask", "[Mask]", icon_mask, []
    if not is_group_layer and include_dq_item:
        yield "dq", "[DQ Weights]", icon_dq, []

    names = influence_names.unique_names([i.path_name() for i in items])
    for i, name in zip(items, names):
        i.unique_name = name

    if config.influences_sort() == Config.InfluencesSortDescending:
        items = list(sorted(items, key=lambda i: i.unique_name))

    for i in items:
        is_joint = i.path is not None
        if filter is None or filter.is_match(i.path_name()):
            yield i.logicalIndex, i.unique_name, get_icon(i, is_joint), ["locked" if i.locked else "unlocked"]
