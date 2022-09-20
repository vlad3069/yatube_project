from django.shortcuts import render, get_object_or_404
from .models import Post, Group

LIMIT = 10


def index(request):
    template = "posts/index.html"
    posts = Post.objects.select_related("group")[:LIMIT]
    context = {
        'posts': posts,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = "posts/group_list.html"
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()[:LIMIT]
    # posts = Post.objects.filter(group=group).order_by("-pub_date")[:limit]
    context = {
        'group': group,
        'posts': posts,
    }
    return render(request, template, context)
