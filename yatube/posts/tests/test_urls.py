from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='test')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # АВТОР
        self.post_author = Client()
        self.author = PostURLTests.user
        self.post_author.force_login(self.author)

    def test_public_urls(self):
        """Страница / доступна любому пользователю."""
        post_id = PostURLTests.post.id
        url_names = (
            '/',
            '/group/test-slug/',
            '/profile/test/',
            '/posts/' + str(post_id) + '/',
        )
        for url in url_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEquals(response.status_code, HTTPStatus.OK)
                response = self.authorized_client.get(url)
                self.assertEquals(response.status_code, HTTPStatus.OK)

    def test_not_found_urls(self):
        """Страница '/unexisting_page/' недоступна"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEquals(response.status_code, HTTPStatus.NOT_FOUND)

    def test_post_edit_for_auth_users(self):
        """Страница /create/ доступна только авторизованному пользователю"""
        response = self.authorized_client.get('/create/')
        self.assertEquals(response.status_code, HTTPStatus.OK)

    def test_post_edit_for_author(self):
        """Страница posts/<int:post_id>/edit/ доступна только автору"""
        post_id = PostURLTests.post.id
        response = self.post_author.get('/posts/' + str(post_id) + '/')
        self.assertEquals(response.status_code, HTTPStatus.OK)
        response = self.authorized_client.get(
            '/posts/' + str(post_id) + '/edit/', follow=True)
        self.assertRedirects(
            response, '/posts/' + str(post_id) + '/'
        )

    def test_post_edit_for_guest(self):
        """Страница posts/<int:post_id>/edit/ перенаправляет гостя на вход"""
        post_id = PostURLTests.post.id
        response = self.guest_client.get(
            '/posts/' + str(post_id) + '/edit/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/posts/' + str(post_id) + '/edit/'
        )

    def test_post_create_for_guest(self):
        """Страница /create/ перенаправляет гостя на вход"""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        post_id = PostURLTests.post.id
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/test/': 'posts/profile.html',
            '/posts/' + str(post_id) + '/': 'posts/post_detail.html',
            '/posts/' + str(post_id) + '/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html'
        }
        for url, template in templates_url_names.items():
            with self.subTest(addrurless=url):
                response = self.post_author.get(url)
                self.assertTemplateUsed(response, template)
