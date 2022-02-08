from django.contrib.auth import get_user_model
from django.test import TestCase
from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Буря мглою небо кроет, вихри снежные крутя.'
        )

    def test_models_have_correct_object_names(self):
        """В моделях Post, Group корректно работает метод __str__."""

        post = PostModelTest.post
        group = PostModelTest.group

        model_objects = {
            post: post.text,
            group: group.title,
        }
        for unit, str_method in model_objects.items():
            with self.subTest(unit=unit):
                self.assertEqual(str_method[:Post.SYMBOLS_LIMIT], str(unit), (
                    f'Ошибка. В модели {type(unit).__name__} '
                    f'не корректно работает метод __str__'))

    def test_model_verbose_name(self):
        """verbose_name полей модели совпадает с ожидаемым."""

        post = PostModelTest.post

        verbose_names = {
            'text': 'Текст поста',
            'created': 'Дата создания',
            'author': 'Автор',
            'group': 'Группа по интересам'
        }
        for field_name, verbose_value in verbose_names.items():
            with self.subTest(field_name=field_name):
                verbose = post._meta.get_field(field_name).verbose_name
                self.assertEqual(verbose, verbose_value, (
                    f'Ошибка. Неправильное значение verbose_name '
                    f'поля {field_name} модели {type(post).__name__}'))
