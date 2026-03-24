from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """Default pagination for all API endpoints.

    Supports ``?page=N`` and ``?page_size=N`` (max 100).

    Translatable list endpoints (products, categories, suppliers, customers) also accept
    optional ``?language=CODE`` (e.g. ``fr``). See :mod:`api.language`.
    """

    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100
