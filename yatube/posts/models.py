from core.models import CreatedModel
from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Group(models.Model):

    title = models.CharField(max_length=200,)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(CreatedModel):

    SYMBOLS_LIMIT = 15

    text = models.TextField(verbose_name='Текст поста',)
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='posts_usr')
    group = models.ForeignKey(
        Group,
        verbose_name='Группа по интересам',
        on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='posts_grp',)
    image = models.ImageField(
        verbose_name='Картинка',
        upload_to='posts/',
        blank=True,)

    class Meta:
        ordering = ["-created"]
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:self.SYMBOLS_LIMIT]


class Comment(CreatedModel):
    post = models.ForeignKey(
        Post,
        related_name='comments',
        on_delete=models.CASCADE)
    author = models.ForeignKey(
        User,
        related_name='comments',
        on_delete=models.CASCADE)
    text = models.TextField()

    class Meta:
        ordering = ["-created"]
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комметарии'

    def __str__(self):
        return self.text[:50]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        related_name='follower',
        verbose_name='Подписчик',
        on_delete=None
    )
    author = models.ForeignKey(
        User,
        related_name='following',
        verbose_name='Блогер',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
