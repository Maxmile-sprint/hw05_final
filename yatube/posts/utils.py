from django.core.paginator import Paginator


POSTS_LIMIT = 10


def get_page_obj(queryset, request):

    paginator = Paginator(queryset, POSTS_LIMIT)
    page_number = request.GET.get('page')

    return paginator.get_page(page_number)
