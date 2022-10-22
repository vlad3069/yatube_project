from django.test import TestCase, Client
from http import HTTPStatus

from posts.models import Group, Post, User
from posts.def_uls import (INDEX_URL, GROUP_URL, PROFILE_URL, POST_URL,
                           POST_EDIT_URL, POST_CREATE_URL, LOGIN_URL,
                           NONE_URL)


GROUP_TITLE = 'Тестовая группа'
GROUP_SLUG = 'test-slug'
GROUP_TEXT = 'Тестовое описание'
USER_NAME = 'test'
POST_TEXT = 'Тестовый пост'
POST_ID = 22


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text=POST_TEXT,
            id=POST_ID,
        )
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_TEXT,
        )

    def setUp(self):
        self.user = User.objects.create_user(username=USER_NAME)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post_author = Client()
        self.author = PostURLTests.user
        self.post_author.force_login(self.author)

    def test_public_urls(self):
        """Страница / доступна любому пользователю."""
        url_names = (
            INDEX_URL(),
            GROUP_URL(GROUP_SLUG=GROUP_SLUG),
            PROFILE_URL(USER_NAME=USER_NAME),
            POST_URL(POST_ID=POST_ID),
        )
        for url in url_names:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_not_found_urls(self):
        """Страница '/unexisting_page/' недоступна."""
        response = self.client.get(NONE_URL())
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_post_edit_for_auth_users(self):
        """Страница /create/ доступна только авторизованному пользователю."""
        response = self.authorized_client.get(POST_CREATE_URL())
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_for_author(self):
        """Страница posts/<int:post_id>/edit/ доступна только автору."""
        response = self.post_author.get(POST_URL(POST_ID=POST_ID))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.authorized_client.get(POST_EDIT_URL(POST_ID=POST_ID))
        self.assertRedirects(response, POST_URL(POST_ID=POST_ID))

    def test_post_edit_for_guest(self):
        """Страница posts/<int:post_id>/edit/ перенаправляет гостя на вход."""
        response = self.client.get(POST_EDIT_URL(POST_ID=POST_ID))
        self.assertRedirects(response,
                             LOGIN_URL() + POST_EDIT_URL(POST_ID=POST_ID))

    def test_post_create_for_guest(self):
        """Страница /create/ перенаправляет гостя на вход."""
        response = self.client.get(POST_CREATE_URL())
        self.assertRedirects(response, LOGIN_URL() + POST_CREATE_URL())

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            INDEX_URL(): 'posts/index.html',
            GROUP_URL(GROUP_SLUG=GROUP_SLUG): 'posts/group_list.html',
            PROFILE_URL(USER_NAME=USER_NAME): 'posts/profile.html',
            POST_URL(POST_ID=POST_ID): 'posts/post_detail.html',
            POST_EDIT_URL(POST_ID=POST_ID): 'posts/create_post.html',
            POST_CREATE_URL(): 'posts/create_post.html'
        }
        for url, template in templates_url_names.items():
            with self.subTest(addrurless=url):
                response = self.post_author.get(url)
                self.assertTemplateUsed(response, template)
