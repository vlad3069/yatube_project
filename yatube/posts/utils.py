from django.core.paginator import Paginator


def pagin(posts, request):
    LIMIT = 10
    paginator = Paginator(posts, LIMIT)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
