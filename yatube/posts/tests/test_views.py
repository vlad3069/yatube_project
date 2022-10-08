from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from ..models import Group, Post

User = get_user_model()


class PostTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Заголовок группы',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            id=20,
            group=cls.group,
        )
        cls.group2 = Group.objects.create(
            title='Заголовок группы2',
            slug='test-slug2',
            description='Тестовое описание',
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='test')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # АВТОР
        self.post_author = Client()
        self.author = PostTests.user
        self.post_author.force_login(self.author)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        post_id = PostTests.post.id
        templates_page_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': (
                reverse('posts:group_list', kwargs={'slug': 'test-slug'})),
            'posts/profile.html': (
                reverse('posts:profile', kwargs={'username': 'auth'})),
            'posts/post_detail.html': (
                reverse('posts:post_detail', kwargs={'post_id': post_id})),
            'posts/create_post.html': (
                reverse('posts:post_edit', kwargs={'post_id': post_id})),
            'posts/create_post.html': reverse('posts:post_create'),
        }
        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_list_page_show_correct_context(self):
        """Шаблон post_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_author_0 = first_object.author.username
        post_text_0 = first_object.text
        post_group_0 = first_object.group.title
        self.assertEqual(post_author_0, 'auth')
        self.assertEqual(post_text_0, 'Тестовый пост')
        self.assertEqual(post_group_0, 'Заголовок группы')

    def test_group_pages_show_correct_context(self):
        """Шаблон группы сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse
                                              ('posts:group_list',
                                               kwargs={'slug': 'test-slug'}))
        first_object = response.context['group']
        group_title_0 = first_object.title
        group_slug_0 = first_object.slug
        self.assertEqual(group_title_0, 'Заголовок группы')
        self.assertEqual(group_slug_0, 'test-slug')

    def test_profile_pages_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse
                                              ('posts:profile',
                                               kwargs={'username': 'auth'}))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        self.assertEqual(response.context['author'].username, 'auth')
        self.assertEqual(post_text_0, 'Тестовый пост')

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон поста сформирован с правильным контекстом."""
        post_id = PostTests.post.id
        response = self.authorized_client.get(reverse
                                              ('posts:post_detail',
                                               kwargs={'post_id': post_id}))
        first_object = response.context['post']
        post_text_0 = first_object.text
        self.assertEqual(post_text_0, 'Тестовый пост')

    def test_new_post_show_correct_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        post_id = PostTests.post.id
        response = self.post_author.get(reverse
                                        ('posts:post_edit',
                                         kwargs={'post_id': post_id}))
        first_object = response.context['post']
        post_text_0 = first_object.text
        self.assertEqual(post_text_0, 'Тестовый пост')
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_in_need_group(self):
        """Пост попал в куда надо"""
        reverse_name = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'auth'}),
        ]
        for name in reverse_name:
            with self.subTest(name=name):
                response = self.authorized_client.get(name)
                first_object = response.context['page_obj'][0]
                post_text_0 = first_object.text
                post_group_0 = first_object.group.title
                self.assertEqual(post_text_0, 'Тестовый пост')
                self.assertEqual(post_group_0, 'Заголовок группы')

    def test_post_another_group(self):
        """Пост не попал в другую группу"""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug2'}))
        self.assertFalse(response.context['page_obj'])


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Заголовок группы',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = []
        for i in range(13):
            cls.post.append(Post.objects.create(
                author=cls.user,
                text='Тестовый пост{i}',
                group=cls.group,)
            )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='test')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        list_reverse = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'auth'}),
        ]
        for url in list_reverse:
            response = self.client.get(url)
            self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        list_reverse = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'auth'}),
        ]
        for url in list_reverse:
            response = self.client.get(url + '?page=2')
            self.assertEqual(len(response.context['page_obj']), 3)
