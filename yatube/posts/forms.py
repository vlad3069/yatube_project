from django.forms import ModelForm

from posts.models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post
        labels = {'group': 'Группа', 'text': 'Сообщение', 'image': 'Картинка'}
        help_texts = {'group': 'Выберите группу',
                      'text': 'Введите ссообщение',
                      'image': 'Добавьте изображение'}
        fields = ['group', 'text', 'image']


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        labels = {'text': 'Добавить комментарий'}
        help_texts = {'text': 'Текст комментария'}
        fields = ['text']
