import shutil
import tempfile
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from ..models import Group, Post, Follow
from ..utils import POSTS_LIMIT


User = get_user_model()

OVER_POSTS_LIMIT = 1

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PaginatorViwesTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='paginator')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',)

        for post_num in range(POSTS_LIMIT + OVER_POSTS_LIMIT):
            cls.post = Post.objects.create(
                author=cls.user,
                group=cls.group,
                text=f'{post_num} One two three four five'
            )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViwesTest.user)

    def test_first_page_of_pages_with_posts_list_contains_ten_records(self):
        """
        Проверка количества постов на первых страницах проекта, на которых
        отображаются списки с постами. На главной странице, странице группы и
        профайла пользователя должно отображается POSTS_LIMIT пост(а)(ов).
        """
        group = PaginatorViwesTest.group
        author = PaginatorViwesTest.user

        address_list = [
            ('posts:index', None),
            ('posts:group_list', (group.slug,)),
            ('posts:profile', (author.username,)),
        ]
        for address, args in address_list:
            url = reverse(address, args=args)
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                first_object = response.context['page_obj']
                self.assertEqual(len(first_object), POSTS_LIMIT, (
                    f'Ошибка. Количество постов на первой странице {url} '
                    f'не равно {POSTS_LIMIT}'))

    def test_second_page_of_pages_with_posts_list_contains_ten_records(self):
        """
        Проверка количества постов на вторых страницах проекта, на которых
        отображаются списки с постами. На главной странице, странице группы и
        профайла пользователя должно отображается OVER_POSTS_LIMIT пост(а)(ов).
        """

        URL_ADD = '?page=2'

        group = PaginatorViwesTest.group
        author = PaginatorViwesTest.user

        address_list = [
            ('posts:index', None),
            ('posts:group_list', (group.slug,)),
            ('posts:profile', (author.username,)),
        ]
        for address, args in address_list:
            url = reverse(address, args=args) + URL_ADD
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                page_object = response.context['page_obj']
                self.assertEqual(len(page_object), OVER_POSTS_LIMIT, (
                    f'Ошибка. Количество постов на второй странице не равно'
                    f'{OVER_POSTS_LIMIT}'))


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.follower_user = User.objects.create_user(
            username='follower')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Пятнадцать00000',
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostViewsTests.user)
        self.follower_authorized_client = Client()
        self.follower_authorized_client.force_login(
            PostViewsTests.follower_user)

    def test_pages_uses_correct_template(self):
        """View-функция использует соответствубщий шаблон"""

        post = PostViewsTests.post
        group = PostViewsTests.group

        urls_list = [
            ('posts:index', 'posts/index.html', None),
            ('posts:group_list', 'posts/group_list.html', (group.slug,)),
            ('posts:profile', 'posts/profile.html', (post.author.username,)),
            ('posts:post_detail', 'posts/post_detail.html', (post.id,)),
            ('posts:post_edit', 'posts/create_post.html', (post.id,)),
            ('posts:post_create', 'posts/create_post.html', None),
        ]
        for url_name, template, args in urls_list:
            url = reverse(url_name, args=args)
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_pages_with_posts_lists_show_correct_context(self):
        """
        Проверка корректности контекста, переданного в шаблоны страниц
        с отображением списка постов.
        """

        post = PostViewsTests.post

        address_list = [
            ('posts:index', None),
            ('posts:group_list', (post.group.slug,)),
            ('posts:profile', (post.author.username,)),
        ]
        for address, args in address_list:
            url = reverse(address, args=args)
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                first_object = response.context['page_obj'][0]

                self.assertEqual(first_object.text, post.text, (
                    'Ошибка. Неверный контекст (поле text)'
                ))
                self.assertEqual(first_object.created, post.created, (
                    'Ошибка. Неверный контекст (поле created)'
                ))
                self.assertEqual(first_object.author, post.author, (
                    'Ошибка. Неверный контекст (поле author)'
                ))
                self.assertEqual(first_object.group.slug, post.group.slug, (
                    'Ошибка. Неверный контекст (поле group)'
                ))
                self.assertEqual(first_object.image, post.image, (
                    'Ошибка. Неверный контекст (поле image)'
                ))

    def test_post_detail_page_show_correct_context(self):
        """
        Проверка корректности контекста, переданного для формирования
        шаблона posts/post_detail.html.
        """
        post = PostViewsTests.post

        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': f'{post.id}'}))

        post_obj = response.context.get('post_obj')

        posts_count = response.context.get('posts_count')

        self.assertEqual(post_obj.text, post.text, (
            'Ошибка. Неверный контекст (поле text)'))
        self.assertEqual(post_obj.created, post.created, (
            'Ошибка. Неверный контекст (поле created)'))
        self.assertEqual(post_obj.author, post.author, (
            'Ошибка. Неверный контекст (поле author)'))
        self.assertEqual(post_obj.group, post.group, (
            'Ошибка. Неверный контекст (поле group)'))
        self.assertEqual(post_obj.image, post.image, (
            'Ошибка. Неверный контекст (поле image)'))
        self.assertEqual(posts_count, 1, (
            'Ошибка. Неверное количество постов'))

    def test_create_page_show_correct_context(self):
        """
        Проверка корректности контекста, переданного для формирования
        шаблона posts/create_post.html, и полей формы создания поста.
        """
        title = 'Добавить запись'
        group = PostViewsTests.group

        response = self.authorized_client.get(reverse('posts:post_create'))

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

        self.assertEqual(response.context.get('title'), title, (
            f'Ошибка. Значение title должно быть {title}'))
        self.assertEqual(response.context['group_option'].first(), group, (
            f'Ошибка. Значение группы должно быть {group}'))

    def test_edit_page_show_correct_context(self):
        """
        Проверка корректности контекста, переданного для формирования
        шаблона posts/create_post.html для редактирования поста
        """
        title = 'Редактировать запись'
        is_edit = True
        post = PostViewsTests.post

        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': f'{post.id}'}))

        form_object = response.context.get('form').instance
        title_context = response.context['title']
        is_edit_context = response.context['is_edit']
        post_id_context = response.context['post_id']

        self.assertEqual(form_object.text, post.text, (
            'Ошибка. Неверный контекст (поле text)'))
        self.assertEqual(form_object.group, post.group, (
            'Ошибка. Неверный контекст (поле group)'))
        self.assertEqual(title_context, title, (
            'Ошибка. Неверный контекст (title)'))
        self.assertEqual(is_edit_context, is_edit, (
            'Ошибка. Неверный контекст (is_edit)'))
        self.assertEqual(post_id_context, post.id, (
            'Ошибка. Неверный контекст (post_id)'))

    def test_post_in_main_group_slug_profile_pages(self):
        """
        Проверка отображения созданного поста с указанием группы
        на страницах, сформированных с помощью шаблонов posts/index.html,
        posts/group_list.html, 'posts/profile.html'. При создании поста он
        не должен попадать на страницу другой группы.
        """
        post = PostViewsTests.post

        # Создаем дополнительную группу только для этого теста,
        group_additional = Group.objects.create(
            title='Дополнительная группа',
            slug='additional-slug',
            description='Дополнительное тестовое описание',)

        address_list = [
            ('posts:index', None),
            ('posts:group_list', (post.group.slug,)),
            ('posts:profile', (post.author.username,)),
        ]
        for address, args in address_list:
            url = reverse(address, args=args)
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertIn(post, response.context['page_obj'], (
                    f'Ошибка. Пост не отображается на странице {url}'))

        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug':
                    f'{group_additional.slug}'}))
        self.assertNotIn(post, response.context['page_obj'], (
            'Ошибка. Пост не должен отображаться в Дополнительной группе'))

    def test_main_page_cache(self):
        """
        Проверка кеширования главной страницы. Логика теста:
        при удалении записи из базы, она остаётся в response.content
        главной страницы до тех пор, пока кэш не будет очищен принудительно.
        """
        response_main_before_post_delete = self.authorized_client.get(
            reverse('posts:index'))

        Post.objects.get(pk=PostViewsTests.post.id).delete()

        response_main_after_post_delete = self.authorized_client.get(
            reverse('posts:index'))

        cache.clear()

        response_main_after_cache_clear = self.authorized_client.get(
            reverse('posts:index'))

        self.assertEqual(response_main_after_post_delete.content, (
            response_main_before_post_delete.content), (
                'Ошибка до очистки кеша. response.content главной страницы '
                'до и после удаления поста не равны друг другу'))

        self.assertNotEqual(response_main_after_post_delete.content, (
            response_main_after_cache_clear), (
                'Ошибка после очистки кеша. response.content главной страницы '
                'после удаления поста и после очистки кеша не должны быть '
                'равны друг другу'))

    def test_create_follow_row_authorized_client(self):
        """
        Проверка возможности авторизованного пользователя
        подписываться на других пользователей.
        """
        post = PostViewsTests.post

        follows_count = Follow.objects.count()

        self.follower_authorized_client.get(reverse(
            'posts:profile_follow', kwargs={'username': f'{post.author}'}))

        follow = Follow.objects.last()

        self.assertEqual(
            follow.user_id, PostViewsTests.follower_user.id, (
                'Ошибка. В БД сохранился не корректный id пользователя'))
        self.assertEqual(follow.author_id, PostViewsTests.user.id, (
            'Ошибка. В БД сохранился не корректный id автора поста'))
        self.assertEqual(Follow.objects.count(), follows_count + 1, (
            'Ошибка. Количество подписок не увеличилось'))

    def test_delete_follow_row_authorized_client(self):
        """
        Проверка возможности авторизованного пользователя
        отписываться от других пользователей.
        """
        Follow.objects.get_or_create(
            user=PostViewsTests.follower_user,
            author=PostViewsTests.user
        )
        follows_count = Follow.objects.count()

        self.follower_authorized_client.get(reverse(
            'posts:profile_unfollow', kwargs={
                'username': f'{PostViewsTests.user}'}))

        self.assertEqual(Follow.objects.count(), follows_count - 1, (
            'Ошибка. Количество подписок не уменьшилось'))

    def test_new_post_in_followers_feeds(self):
        """
        Новая запись пользователя появляется в ленте тех,
        кто на него подписан.
        """
        user = PostViewsTests.user

        self.follower_authorized_client.get(reverse(
            'posts:profile_follow', kwargs={'username': f'{user}'}))

        self.new_post = Post.objects.create(
            author=PostViewsTests.user,
            group=PostViewsTests.group,
            text='Тестирование подписки'
        )
        response = self.follower_authorized_client.get(
            reverse('posts:follow_index'))

        page_obj = response.context['page_obj']

        self.assertIn(self.new_post, page_obj, (
            f'Ошибка. Новый пост автора отсутствует в ленте новых записей '
            f'подписчика {PostViewsTests.follower_user}'))
        self.assertEqual(page_obj[0].text, self.new_post.text, (
            'Ошибка. Неверный контекст (поле text)'))
        self.assertEqual(page_obj[0].group, self.new_post.group, (
            'Ошибка. Неверный контекст (поле group)'))
        self.assertEqual(page_obj[0].author, self.new_post.author, (
            'Ошибка. Неверный контекст (поле author)'))

    def test_new_post_not_in_unfollowers_feeds(self):
        """
        Новая запись пользователя не появляется в ленте тех,
        кто на него не подписан.
        """
        self.new_post = Post.objects.create(
            author=PostViewsTests.user,
            group=PostViewsTests.group,
            text='Тестирование подписки'
        )
        response = self.follower_authorized_client.get(
            reverse('posts:follow_index'))

        page_obj = response.context['page_obj']

        self.assertNotIn(self.new_post, page_obj, (
            f'Ошибка. Новый пост автора не должен отображается в ленте новых '
            f'записей неподписчика {PostViewsTests.follower_user}'))
