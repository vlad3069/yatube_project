from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect, render, get_object_or_404

from .models import Follow, Post, Group, User
from .forms import PostForm, CommentForm


LIMIT = 10


def pagin(posts, request):
    paginator = Paginator(posts, LIMIT)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def index(request):
    template = 'posts/index.html'
    posts = Post.objects.select_related('group')
    page_obj = pagin(posts, request)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = pagin(posts, request)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required()
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    template = 'posts/create_post.html'
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
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id,)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    template = 'posts/create_post.html'
    context = {
        'form': form,
        'post': post,
        'post_edit_flag': True
    }
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    template = 'posts/profile.html'
    posts = author.posts.all()
    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user, author=author)
    else:
        following = False
    page_obj = pagin(posts, request)
    context = {
        'page_obj': page_obj,
        'author': author,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id,)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id,)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    follow = Post.objects.filter(author__following__user=request.user)
    page_obj = pagin(follow, request)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = User.objects.get(username=username)
    follow = Follow.objects.filter(user=user, author=author)
    if user != author and not follow:
        Follow.objects.create(user=user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    user = request.user
    author = User.objects.get(username=username)
    follow = Follow.objects.filter(user=user, author=author)
    if user != author and follow:
        follow.delete()
    return redirect('posts:profile', username=username)
