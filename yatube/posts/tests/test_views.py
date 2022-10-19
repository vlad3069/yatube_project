import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from posts.models import Group, Post, Follow
from django.test import Client, TestCase, override_settings
from django import forms
from django.core.cache import cache

from posts.tests.def_uls import (INDEX_URL, GROUP_URL, PROFILE_URL, POST_URL,
                                 POST_EDIT_URL, POST_CREATE_URL, COMMENT_URL,
                                 FOLLOW_INDEX_URL, FOLLOW_URL, UNFOLLOW_URL)

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

GROUP_TITLE = 'Тестовая группа'
GROUP_SLUG = 'test-slug'
GROUP_TEXT = 'Тестовое описание'
USER_NAME = 'test'
AUTHOR_NAME = 'auth'
POST_TEXT = 'Тестовый пост'
POST_ID = 22
COMMENT = 'Авторизованный комментарий'

small_gif = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
    )


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username=AUTHOR_NAME)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_TEXT,
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=POST_TEXT,
            id=POST_ID,
            group=cls.group,
            image=uploaded,
        )
        cls.group2 = Group.objects.create(
            title='Заголовок группы2',
            slug='test-slug2',
            description='Тестовое описание2',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username=USER_NAME)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post_author = Client()
        self.author = PostTests.user
        self.post_author.force_login(self.author)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            INDEX_URL(): 'posts/index.html',
            GROUP_URL(GROUP_SLUG=GROUP_SLUG): 'posts/group_list.html',
            PROFILE_URL(USER_NAME=AUTHOR_NAME): 'posts/profile.html',
            POST_URL(POST_ID=POST_ID): 'posts/post_detail.html',
            POST_EDIT_URL(POST_ID=POST_ID): 'posts/create_post.html',
            POST_CREATE_URL(): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.post_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_list_page_show_correct_context(self):
        """Шаблон post_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(INDEX_URL())
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.group, self.post.group)

    def test_group_pages_show_correct_context(self):
        """Шаблон группы сформирован с правильным контекстом."""
        response = self.authorized_client.get(GROUP_URL(
                                              GROUP_SLUG=GROUP_SLUG))
        first_object = response.context['group']
        self.assertEqual(first_object.title, self.group.title)
        self.assertEqual(first_object.slug, self.group.slug)

    def test_profile_pages_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(PROFILE_URL(
                                              USER_NAME=AUTHOR_NAME))
        first_object = response.context['page_obj'][0]
        self.assertEqual(response.context['author'].username, AUTHOR_NAME)
        self.assertEqual(first_object.text, self.post.text)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон поста сформирован с правильным контекстом."""
        response = self.authorized_client.get(POST_URL(POST_ID=POST_ID))
        first_object = response.context['post']
        self.assertEqual(first_object.text, self.post.text)

    def test_new_post_show_correct_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(POST_CREATE_URL())
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
        response = self.post_author.get(POST_EDIT_URL(POST_ID=POST_ID))
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
            INDEX_URL(),
            GROUP_URL(GROUP_SLUG=GROUP_SLUG),
            PROFILE_URL(USER_NAME=AUTHOR_NAME),
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
        response = self.authorized_client.get(GROUP_URL(
                                              GROUP_SLUG='test-slug2'))
        self.assertFalse(response.context['page_obj'])

    def test_post_with_image_creat_to_need(self):
        """Пост с картинкой выводиться не на главную страницу,
        на страницу профайла, на страницу группы
        """
        reverse_name = [
            INDEX_URL(),
            GROUP_URL(GROUP_SLUG=GROUP_SLUG),
            PROFILE_URL(USER_NAME=AUTHOR_NAME),
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
        self.authorized_client.post(COMMENT_URL(POST_ID=POST_ID),
                                    {'text': 'Авторизованный комментарий'},
                                    follow=True)
        response = self.authorized_client.get(POST_URL(POST_ID=POST_ID))
        self.assertContains(response, 'Авторизованный комментарий')
        self.guest_client.post(COMMENT_URL(POST_ID=POST_ID),
                               {'text': "Гостевой комментарий"},
                               follow=True)
        response = self.guest_client.get(POST_URL(POST_ID=POST_ID))
        self.assertNotContains(response, 'Гостевой комментарий')

    def test_cashe_index_page(self):
        """Проверка кэша главной страницы"""
        first_page = self.authorized_client.get(INDEX_URL())
        post = first_page.context['page_obj'][0]
        post.delete()
        second_page = self.authorized_client.get(INDEX_URL())
        self.assertEqual(second_page.content, first_page.content)
        cache.clear()
        third_page = self.authorized_client.get(INDEX_URL())
        self.assertNotEqual(third_page.content, first_page.content)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=AUTHOR_NAME)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_TEXT,
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
        self.user = User.objects.create_user(username=USER_NAME)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        """Тест первой страницы пажинатора"""
        list_reverse = [
            INDEX_URL(),
            GROUP_URL(GROUP_SLUG=GROUP_SLUG),
            PROFILE_URL(USER_NAME=AUTHOR_NAME),
        ]
        for url in list_reverse:
            response = self.client.get(url)
            self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        """Тест второй страницы пажинатора"""
        list_reverse = [
            INDEX_URL(),
            GROUP_URL(GROUP_SLUG=GROUP_SLUG),
            PROFILE_URL(USER_NAME=AUTHOR_NAME),
        ]
        for url in list_reverse:
            response = self.client.get(url + '?page=2')
            self.assertEqual(len(response.context['page_obj']), 3)


class FollowViewsTest(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized = User.objects.create_user(username='authorized')
        self.authorized_client.force_login(self.authorized)
        self.follower_client = Client()
        self.follower = User.objects.create_user(username='follower')
        self.follower_client.force_login(self.follower)
        self.following_client = Client()
        self.following = User.objects.create_user(username='following')
        self.following_client.force_login(self.following)
        self.post = Post.objects.create(
            author=self.following,
            text='Тестовая запись'
        )

    def test_auth_follow(self):
        """Зарегестрированный пользователь может подписаться"""
        username = self.following.username
        following_count = Follow.objects.count()
        self.follower_client.get(FOLLOW_URL(USER_NAME=username))
        self.assertEqual(Follow.objects.count(), following_count + 1)

    def test_guest_follow(self):
        """Незарегестрированный пользователь несможет подписаться"""
        username = self.following.username
        following_count = Follow.objects.count()
        self.guest_client.get(FOLLOW_URL(USER_NAME=username))
        self.assertEqual(Follow.objects.count(), following_count)

    def test_auth_unfollow(self):
        """Подписаный пользователь может отписаться"""
        username = self.following.username
        self.follower_client.get(FOLLOW_URL(USER_NAME=username))
        following_count = Follow.objects.count()
        self.follower_client.get(UNFOLLOW_URL(USER_NAME=username))
        self.assertEqual(Follow.objects.count(), following_count - 1)

    def test_followers_feed(self):
        """Запись появляется только в ленте подписчиков"""
        username = self.following.username
        self.follower_client.get(FOLLOW_URL(USER_NAME=username))
        response_follower = self.follower_client.get(FOLLOW_INDEX_URL())
        self.assertEqual(len(response_follower.context['page_obj']), 1)
        response_authorized = self.authorized_client.get(FOLLOW_INDEX_URL())
        self.assertEqual(len(response_authorized.context['page_obj']), 0)
