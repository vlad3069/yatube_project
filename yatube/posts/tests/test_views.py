import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from posts.models import Group, Post
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.core.cache import cache

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
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
            image=uploaded,
        )
        cls.group2 = Group.objects.create(
            title='Заголовок группы2',
            slug='test-slug2',
            description='Тестовое описание',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

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
            reverse('posts:index'): 'posts/index.html',
            (reverse('posts:group_list',
                     kwargs={'slug': 'test-slug'})): 'posts/group_list.html',
            (reverse('posts:profile',
                     kwargs={'username': 'auth'})): 'posts/profile.html',
            (reverse('posts:post_detail',
                     kwargs={'post_id': post_id})): 'posts/post_detail.html',
            (reverse('posts:post_edit',
                     kwargs={'post_id': post_id})): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.post_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_list_page_show_correct_context(self):
        """Шаблон post_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.group, self.post.group)

    def test_group_pages_show_correct_context(self):
        """Шаблон группы сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse
                                              ('posts:group_list',
                                               kwargs={'slug': 'test-slug'}))
        first_object = response.context['group']
        self.assertEqual(first_object.title, self.group.title)
        self.assertEqual(first_object.slug, self.group.slug)

    def test_profile_pages_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse
                                              ('posts:profile',
                                               kwargs={'username': 'auth'}))
        first_object = response.context['page_obj'][0]
        self.assertEqual(response.context['author'].username, 'auth')
        self.assertEqual(first_object.text, self.post.text)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон поста сформирован с правильным контекстом."""
        post_id = PostTests.post.id
        response = self.authorized_client.get(reverse
                                              ('posts:post_detail',
                                               kwargs={'post_id': post_id}))
        first_object = response.context['post']
        self.assertEqual(first_object.text, self.post.text)

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
        self.assertEqual(first_object.text, self.post.text)
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
                self.assertEqual(first_object.author, self.post.author)
                self.assertEqual(first_object.text, self.post.text)
                self.assertEqual(first_object.group, self.post.group)

    def test_post_another_group(self):
        """Пост не попал в другую группу"""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug2'}))
        self.assertFalse(response.context['page_obj'])

    def test_post_with_image_creat_to_need(self):
        """Пост с картинкой выводиться на на главную страницу,
        на страницу профайла, на страницу группы
        """
        reverse_name = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'auth'}),
        ]
        for name in reverse_name:
            with self.subTest(name=name):
                response = self.authorized_client.get(name)
                self.assertEqual(
                    response.context['page_obj'][0].image,
                    self.post.image
                )

    def test_add_auth_client_comment(self):
        """Комментировать посты может только авторизованный пользователь"""
        post_id = PostTests.post.id
        self.authorized_client.post(reverse('posts:add_comment',
                                    kwargs={'post_id': post_id}),
                                    {'text': "Авторизованный комментарий"},
                                    follow=True)
        response = self.authorized_client.get(reverse
                                              ('posts:post_detail',
                                               kwargs={'post_id': post_id}))
        self.assertContains(response, 'Авторизованный комментарий')
        self.guest_client.post(reverse('posts:add_comment',
                               kwargs={'post_id': post_id}),
                               {'text': "Гостевой комментарий"},
                               follow=True)
        response = self.guest_client.get(reverse('posts:post_detail',
                                         kwargs={'post_id': post_id}))
        self.assertNotContains(response, 'Гостевой комментарий')

    def test_cashe_index_page(self):
        """Проверка кэша главной страницы"""
        first_page = self.authorized_client.get(reverse('posts:index'))
        post = first_page.context['page_obj'][0]
        post.delete()
        second_page = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(second_page.content, first_page.content)
        cache.clear()
        third_page = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(third_page.content, first_page.content)


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
        cls.posts = []
        for i in range(13):
            cls.posts.append(Post(
                author=cls.user,
                text='Тестовый пост{i}',
                group=cls.group,)
            )
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='test')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        """Тест первой страницы пажинатора"""
        list_reverse = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'auth'}),
        ]
        for url in list_reverse:
            response = self.client.get(url)
            self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        """Тест второй страницы пажинатора"""
        list_reverse = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'auth'}),
        ]
        for url in list_reverse:
            response = self.client.get(url + '?page=2')
            self.assertEqual(len(response.context['page_obj']), 3)
