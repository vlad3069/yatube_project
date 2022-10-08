from django.contrib.auth import get_user_model
from posts.models import Group, Post
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


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

    def test_authorized_edit_post(self):
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
        self.assertEqual(response_edit.status_code, 200)
        self.assertEqual(post_2.text, 'Измененный текст')
