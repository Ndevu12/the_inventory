"""Helpers for stock location materialized-path trees (treebeard MP_Node)."""


def stock_location_parent_id_map(locations):
    """Resolve ``parent_id`` for a page of locations with one extra DB query.

    ``get_parent()`` per row would N+1; ancestors share a deterministic
    ``path`` prefix per `treebeard`.
    """
    if not locations:
        return {}
    model = locations[0].__class__
    steplen = getattr(model, "steplen", 4) or 4
    tenant_id = locations[0].tenant_id
    need_paths = set()
    for loc in locations:
        depth = getattr(loc, "depth", None) or 1
        path = getattr(loc, "path", "") or ""
        if depth > 1 and path:
            need_paths.add(path[:-steplen])
    if not need_paths:
        return {loc.pk: None for loc in locations}

    id_by_path = dict(
        model.objects.filter(
            tenant_id=tenant_id,
            path__in=need_paths,
        ).values_list("path", "id"),
    )
    out = {}
    for loc in locations:
        depth = getattr(loc, "depth", None) or 1
        path = getattr(loc, "path", "") or ""
        if depth <= 1 or not path:
            out[loc.pk] = None
        else:
            out[loc.pk] = id_by_path.get(path[:-steplen])
    return out
