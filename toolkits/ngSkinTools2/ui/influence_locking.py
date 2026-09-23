# -*- coding: UTF-8 -*-


def update_locked_influences(existing_ids, skin_influence_ids, lock):
    """Return locked influence ids after applying one skinCluster-wide action."""
    existing = list(existing_ids or [])
    targets = list(skin_influence_ids or [])

    if lock:
        result = list(existing)
        for influence_id in targets:
            if influence_id not in result:
                result.append(influence_id)
        return result

    targets = set(targets)
    return [
        influence_id
        for influence_id in existing
        if influence_id not in targets
    ]


def apply_skin_cluster_influence_lock(layer, influences, lock):
    """Update one ngSkinTools layer from a skinCluster influence list."""
    if layer is None:
        return False

    updated = update_locked_influences(
        layer.locked_influences,
        [
            influence.logicalIndex
            for influence in (influences or [])
        ],
        lock,
    )
    if list(layer.locked_influences or []) == updated:
        return False

    layer.locked_influences = updated
    return True
