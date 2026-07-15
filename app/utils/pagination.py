"""Shared pagination helper for list endpoints."""


def paginate_query(query, page=1, per_page=20):
    page = max(int(page or 1), 1)
    per_page = min(max(int(per_page or 20), 1), 100)
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return items, {"page": page, "per_page": per_page, "total": total}
