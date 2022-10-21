from django.contrib.auth.mixins import LoginRequiredMixin

from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.views.generic import (ListView, CreateView, DeleteView,
                                  DetailView, UpdateView, View)

from posts.tests.def_uls import (PROFILE_URL, POST_URL,
                                 POST_EDIT_URL, POST_CREATE_URL, LOGIN_URL)

from .models import Follow, Post, Group, User, Comment
from .forms import PostForm, CommentForm


LIMIT = 10


class Index(ListView):
    model = Post
    template_name: str = 'posts/index.html'
    paginate_by: int = LIMIT


class GroupPost(ListView, LoginRequiredMixin):
    model = Group
    template_name: str = 'posts/group_list.html'
    paginate_by: int = LIMIT
    context_object_name: str = 'group'

    def get_queryset(self):
        return get_object_or_404(
            self.model,
            slug=self.kwargs.get('slug')
        ).posts.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['group'] = get_object_or_404(
            self.model,
            slug=self.kwargs.get('slug')
        )
        return context


class PostCreate(CreateView, LoginRequiredMixin):
    form_class = PostForm
    template_name: str = 'posts/create_post.html'

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_anonymous:
            return redirect(LOGIN_URL() + POST_CREATE_URL())
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form = form.save(commit=False)
        form.author = self.request.user
        form.save()
        return redirect(PROFILE_URL(self.request.user))


class PostEdit(UpdateView, LoginRequiredMixin):
    model = Post
    form_class = PostForm
    template_name: str = 'posts/create_post.html'
    pk_url_kwarg: str = 'post_id'
    context_object_name: str = 'post'
    extra_context = {'post_edit_flag': True}

    def dispatch(self, request, *args, **kwargs):
        obj = super().get_object()
        if (obj.author != self.request.user and
           self.request.user.is_authenticated):
            return redirect(POST_URL(self.kwargs['post_id']))
        if self.request.user.is_anonymous:
            return redirect(LOGIN_URL() +
                            POST_EDIT_URL(self.kwargs['post_id']))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.save()
        return redirect(POST_URL(self.kwargs['post_id']))


class DeletePost(DeleteView, LoginRequiredMixin):
    model = Post
    success_url = '/'
    pk_url_kwarg = 'post_id'


class Profile(ListView):
    model = Post
    template_name: str = 'posts/profile.html'
    paginate_by: int = LIMIT
    user = None

    def get_queryset(self):
        return get_object_or_404(
            get_user_model(),
            username=self.kwargs.get('username')
        ).posts.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        author = get_object_or_404(
            User,
            username=self.kwargs.get('username')
        )
        context['author'] = author
        if self.request.user.is_authenticated:
            context['following'] = Follow.objects.filter(
                user=self.request.user,
                author=author).exists()
        context['page_obj'] = context.pop('page_obj')
        return context


class PostDetail(DetailView):
    form_class = CommentForm
    model = Post
    template_name: str = 'posts/post_detail.html'
    context_object_name: str = 'post'
    pk_url_kwarg: str = 'post_id '

    def get_object(self):
        return get_object_or_404(self.model, pk=self.kwargs.get('post_id'))

    def get_queryset(self):
        return get_object_or_404(
            self.model,
            pk=self.kwargs.get('post_id')
        ).comments.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post'] = get_object_or_404(
            self.model,
            pk=self.kwargs.get('post_id')
        )
        context['form'] = CommentForm(self.request.POST or None)
        context['comments'] = Comment.objects.filter(post=context['post']).all()
        return context
        

class AddComment(DetailView, LoginRequiredMixin):
    model = Post
    pk_url_kwarg: str = 'post_id'
    form_class = CommentForm
    context_object_name = 'post'

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_anonymous:
            return redirect(LOGIN_URL())
        if request.user.is_authenticated:
            self.user = request.user
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = self.form_class(self.request.POST)
        comment = form.save(commit=False)
        comment.author = self.request.user
        comment.post = get_object_or_404(Post, id=self.kwargs['post_id'])
        comment.save()
        return redirect(POST_URL(self.kwargs['post_id']))


class FollowIndex(ListView, LoginRequiredMixin):
    model = Post
    template_name: str = 'posts/follow.html'
    paginate_by: int = LIMIT
    user = None

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_anonymous:
            return redirect(LOGIN_URL())
        if request.user.is_authenticated:
            self.user = request.user
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Post.objects.filter(author__following__user=self.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_obj'] = context.pop('page_obj')
        return context


class ProfileFollow(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        author = get_object_or_404(
            get_user_model(),
            username=self.kwargs['username']
        )
        if request.user != author:
            Follow.objects.get_or_create(user=request.user, author=author)
        return redirect(PROFILE_URL(self.kwargs['username']))


class ProfileUnfollow(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        author = get_object_or_404(
            get_user_model(),
            username=self.kwargs['username']
        )
        if request.user != author:
            Follow.objects.filter(user=request.user, author=author).delete()
        return redirect(PROFILE_URL(self.kwargs['username']))
