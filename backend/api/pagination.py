from rest_framework.pagination import PageNumberPagination


class LimitPageNumberPagination(PageNumberPagination):
    """Пагинация с настраиваемым лимитом"""
    page_size_query_param = 'limit'
