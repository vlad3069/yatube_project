import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from http import HTTPStatus

from posts.models import Comment, Group, Post, User
from posts.def_uls import (INDEX_URL, POST_EDIT_URL,
                           POST_CREATE_URL, COMMENT_URL)


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
    b'\x0A\x00\x3B')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=AUTHOR_NAME)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_TEXT,
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=POST_TEXT,
            group=cls.group,
            id=POST_ID
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user(username=USER_NAME)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post_author = Client()
        self.author = PostCreateFormTests.user
        self.post_author.force_login(self.author)

    def post_create_test(self):
        """Валидная форма создаёт новую запись в базе данных."""
        posts_count = Post.objects.count()
        form_data = {
            'group': GROUP_TITLE,
            'text': POST_TEXT,
        }
        response = self.post_author.post(
            POST_CREATE_URL(),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, INDEX_URL())
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(text=POST_TEXT,).exists())
        self.assertEqual(PostCreateFormTests.post.text, POST_TEXT)
        self.assertEqual(PostCreateFormTests.post.username, AUTHOR_NAME)
        self.assertEqual(PostCreateFormTests.post.group, GROUP_TITLE)

    def test_authorized_edit_post(self):
        """При отправке валидной формы со страницы редактирования
        поста происходит изменение поста в базе данных.
        """
        form_data = {'text': 'Измененный текст'}
        response_edit = self.post_author.post(
            POST_EDIT_URL(POST_ID=POST_ID),
            data=form_data,
            follow=True,
        )
        post_2 = Post.objects.get(id=POST_ID)
        self.assertEqual(response_edit.status_code, HTTPStatus.OK)
        self.assertEqual(post_2.text, 'Измененный текст')
        self.assertIsNone(post_2.group)

    def test_post_with_image_creat(self):
        """Валидная форма с картинкой создаёт новую запись в базе данных."""
        posts_count = Post.objects.count()
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
            POST_CREATE_URL(),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(text=POST_TEXT,).exists())

    def test_add_comment(self):
        """Комментарий появляется на странице поста."""
        comment_count = Comment.objects.count()
        self.authorized_client.post(COMMENT_URL(POST_ID=POST_ID),
                                    {'text': COMMENT},
                                    follow=True)
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(Comment.objects.filter(
            text=COMMENT,).exists())
