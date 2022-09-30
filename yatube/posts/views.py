from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect, render, get_object_or_404

from .models import Post, Group, User
from .forms import PostForm

LIMIT = 10


def index(request):
    template = "posts/index.html"
    posts = Post.objects.select_related("group")
    paginator = Paginator(posts, LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = "posts/group_list.html"
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()[:LIMIT]
    paginator = Paginator(posts, LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required()
def post_create(request):
    form = PostForm(request.POST or None)
    template = "posts/create_post.html"
    context = {
        'form': form,
    }
    if not form.is_valid():
        return render(request, template, context)
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', username=request.user)


@login_required()
def post_edit(request,  post_id):
    post = get_object_or_404(Post, pk=post_id,
                             )
    form = PostForm(request.POST or None, instance=post)
    template = "posts/create_post.html"
    context = {
            "form": form,
            'post': post,
            "post_edit_flag": True
            }
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    template = "posts/profile.html"
    posts = author.posts.all()
    paginator = Paginator(posts, LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'author': author,
            }
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id,
                             )
    # Здесь код запроса к модели и создание словаря контекста
    context = {
        'post': post,
    }
    return render(request, 'posts/post_detail.html', context)
