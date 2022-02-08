from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse
from http import HTTPStatus
from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')

        cls.user_another = User.objects.create_user(username='another')
        cls.authorized_client_another = Client()
        cls.authorized_client_another.force_login(cls.user_another)

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Пятнадцать00000',
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)

    def test_urls_exists_at_desired_location(self):
        """
        Проверка доступности страниц неавторизованному пользователю.
        """
        group = PostURLTests.group
        post = PostURLTests.post

        urls_list = [
            ('posts:index', None),
            ('posts:group_list', (group.slug,)),
            ('posts:profile', (post.author,)),
            ('posts:post_detail', (post.id,)),
            ('about:author', None),
            ('about:tech', None),
        ]
        for url, args in urls_list:
            with self.subTest(url=url):
                response = self.guest_client.get(reverse(url, args=args))
                self.assertEqual(response.status_code, HTTPStatus.OK, (
                    f'Ошибка. Страница {url} недоступна'))

    def test_unexisting_page(self):
        """
        Страница /unexisting_page/ недоступна всем пользователям.
        Ошибка 404 отображается пользователям с помощью
        кастомного шаблона
        """
        response1 = self.guest_client.get('/unexisting_page/')
        response2 = self.authorized_client.get('/unexisting_page/')
        self.assertEqual(response1.status_code, HTTPStatus.NOT_FOUND, (
            'Ошибка. Страница /unexisting_page/ не может быть доступна.'))
        self.assertEqual(response2.status_code, HTTPStatus.NOT_FOUND, (
            'Ошибка. Страница /unexisting_page/ не может быть доступна.'))

        self.assertTemplateUsed(response1, 'core/404.html', (
            'Ошибка. /unexisting_page/ использует несоответствующий шаблон'))
        self.assertTemplateUsed(response2, 'core/404.html', (
            'Ошибка. /unexisting_page/ использует несоответствующий шаблон'))

    def test_create_url_exists_at_desire_location_authorized(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertEqual(response.status_code, HTTPStatus.OK, (
            'Ошибка. /create не доступна для авторизованного пользователя'))

    def test_create_url_redirect_anonymous_on_admin_login(self):
        """
        Страница по адресу /create/ перенаправит анонимного
        пользователя на страницу авторизации.
        """
        response = self.guest_client.get(reverse('posts:post_create'))
        self.assertRedirects(response, ('{0}?next={1}'.format(
            reverse('users:login'), reverse('posts:post_create'))))

    def test_comment_add_url_redirect_anonymous_on_admin_login(self):
        """
        Страница по адресу posts/post_id/comment/ перенаправит анонимного
        пользователя на страницу авторизации.
        """
        response = self.guest_client.get(
            reverse('posts:add_comment', kwargs={
                'post_id': f'{PostURLTests.post.id}'}))
        self.assertRedirects(response, ('{0}?next={1}'.format(
            reverse('users:login'), reverse(
                'posts:add_comment', kwargs={
                    'post_id': f'{PostURLTests.post.id}'}))))

    def test_post_edit_redirect_no_author(self):
        """
        Неавтор не допускается на страницу редактирования поста
        /posts/post_id/edit/ и перенаправляется на страницу /posts/post_id/'.
        """
        post = PostURLTests.post

        response = PostURLTests.authorized_client_another.get(
            reverse('posts:post_edit', kwargs={'post_id': f'{post.id}'}))
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': f'{post.id}'}))

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        group = PostURLTests.group
        post = PostURLTests.post

        urls_list = [
            ('posts:index', 'posts/index.html', None),
            ('posts:group_list', 'posts/group_list.html', (group.slug,)),
            ('posts:profile', 'posts/profile.html', (post.author.username,)),
            ('posts:post_detail', 'posts/post_detail.html', (post.id,)),
            ('posts:post_edit', 'posts/create_post.html', (post.id,)),
            ('posts:post_create', 'posts/create_post.html', None),
            ('about:author', 'about/author.html', None),
            ('about:tech', 'about/tech.html', None),
        ]
        for url_name, template, args in urls_list:
            url = reverse(url_name, args=args)
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template, (
                    f'Ошибка. URL {url} использует несоответствубщий шаблон'))
