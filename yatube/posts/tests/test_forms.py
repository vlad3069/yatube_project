import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from posts.models import Comment, Group, Post
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from http import HTTPStatus

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
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
        self.author = PostCreateFormTests.user
        self.post_author.force_login(self.author)

    def post_create_test(self):
        """Валидная форма создаёт новую запись в базе данных"""
        posts_count = Post.objects.count()
        form_data = {
            'group': 'Тестовая группа',
            'text': 'Тестовый пост',
        }
        response = self.post_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:index'))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(text='Тестовый пост',).exists())
        self.assertEqual(PostCreateFormTests.post.text, 'Тестовый пост')
        self.assertEqual(PostCreateFormTests.post.username, 'auth')
        self.assertEqual(PostCreateFormTests.post.group, 'Тестовая группа')

    def test_authorized_edit_post(self):
        """При отправке валидной формы со страницы редактирования
        поста происходит изменение поста в базе данных
        """
        post_id = PostCreateFormTests.post.id
        form_data = {
            'text': 'Измененный текст',
        }
        response_edit = self.post_author.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': post_id}),
            data=form_data,
            follow=True,
        )
        post_2 = Post.objects.get(id=post_id)
        self.assertEqual(response_edit.status_code, HTTPStatus.OK)
        self.assertEqual(post_2.text, 'Измененный текст')
        self.assertIsNone(post_2.group)

    def test_post_with_image_creat(self):
        """Валидная форма с картинкой создаёт новую запись в базе данных"""
        posts_count = Post.objects.count()
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
        form_data = {
            'text': 'Пост с картинкой',
            'group': self.group.id,
            'image': uploaded
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(text='Тестовый пост',).exists())

    def test_add_comment(self):
        """Комментарий появляется на странице поста"""
        post_id = PostCreateFormTests.post.id
        comment_count = Comment.objects.count()
        self.authorized_client.post(reverse('posts:add_comment',
                                    kwargs={'post_id': post_id}),
                                    {'text': "Авторизованный комментарий"},
                                    follow=True)
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(Comment.objects.filter(
            text='Авторизованный комментарий',).exists())
