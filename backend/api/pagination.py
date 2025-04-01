from rest_framework.pagination import PageNumberPagination


class CustomPageNumberPagination(PageNumberPagination):
    """Пагинация с настраиваемым лимитом"""
    page_size_query_param = 'limit'
    max_page_size = 40
    page_query_param = 'page'
