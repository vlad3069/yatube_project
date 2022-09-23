from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Post(models.Model):
    text = models.TextField()
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',)
    group = models.ForeignKey(
        'Group',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='posts',
        verbose_name='Сообщество',)

    class Meta:
        ordering = ['-pub_date']

    class Post:
        def __str__(self):
            return self.text


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name='Заголовок')
    slug = models.SlugField(
        null=False,
        unique=True,
        verbose_name='Адрес')
    description = models.TextField(
        verbose_name='Описание группы')

    def __str__(self):
        return f'Группа: {self.title}'
