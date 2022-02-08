import shutil
import tempfile
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from ..models import Group, Post, Comment


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class CreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group_another = Group.objects.create(
            title='Другая группа',
            slug='another-slug',
            description='Другое описание'
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        another_small_gif = (
            b'GIF87a\x01\x00\x01\x00\x80\x01\x00'
            b'\x00\x00\x00ccc,\x00\x00\x00\x00\x01'
            b'\x00\x01\x00\x00\x02\x02D\x01\x00;'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.uploaded_rename = SimpleUploadedFile(
            name='rename_small.gif',
            content=small_gif,
            content_type='image/gif',
        )
        cls.uploaded_another = SimpleUploadedFile(
            name='another_small.gif',
            content=another_small_gif,
            content_type='image/gif',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Пятнадцать00000',
            image=cls.uploaded,
        )
        cls.form = CreateFormTests()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(CreateFormTests.user)

    def test_redirect_anonymous_on_login_page(self):
        """
        Страница по адресу /create/ перенаправит анонимного
        пользователя на страницу авторизации.
        """
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст для записи нового поста в БД',
            'group': self.group.id,
        }
        self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        response = self.guest_client.get(reverse('posts:post_create'))

        self.assertEqual(Post.objects.count(), posts_count, (
            'Ошибка. Создана новая запись в БД'))
        self.assertRedirects(response, ('{0}?next={1}'.format(
            reverse('users:login'), reverse('posts:post_create'))))

    def test_create_post(self):
        """
        При отправке валидной формы со страницы создания поста
        создаётся новая запись в базе данных
        """
        posts_count = Post.objects.count()

        form_data = {
            'text': 'Текст для записи нового поста в БД',
            'group': self.group.id,
            'image': CreateFormTests.uploaded_rename,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        last_created_post = Post.objects.order_by('pk').last()

        post_fields_check = {
            last_created_post.text: form_data['text'],
            last_created_post.group.id: form_data['group'],
            last_created_post.author: CreateFormTests.user,
            last_created_post.image.size: form_data['image'].size
        }

        self.assertEqual(Post.objects.count(), posts_count + 1, (
            'Ошибка. Новая запись в БД не создана'))

        for db_post_field_value, form_field_value in post_fields_check.items():
            with self.subTest(db_post_field_value=db_post_field_value):
                self.assertEqual(db_post_field_value, form_field_value, (
                    f'Ошибка. Несоответствие значения поля '
                    f'{db_post_field_value} '
                    f'значению указанному в форме создания поста.'))

    def test_edit_post(self):
        """
        При отправке валидной формы со страницы редактирования поста
        происходит изменение поста с post_id в базе данных. При изменении
        группы редактируемый пост не должен отображаться на странице
        группы, присвоенной до редактирования.
        """
        posts_count = Post.objects.count()

        form_data = {
            'text': 'Новый текст для сохранения отредактированного поста в БД',
            'group': self.group_another.id,
            'image': CreateFormTests.uploaded_another,
        }
        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={
                'post_id': f'{CreateFormTests.post.id}'}),
            data=form_data,
        )
        post_obj = Post.objects.get(pk=CreateFormTests.post.id)

        post_fields_check = {
            post_obj.text: form_data['text'],
            post_obj.group.id: form_data['group'],
            post_obj.author: CreateFormTests.user,
            post_obj.image.size: form_data['image'].size,
        }
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': CreateFormTests.group.slug}))

        self.assertEqual(Post.objects.count(), posts_count, (
            "Ошибка. Количество постов изменилось"))
        self.assertIsNot(post_obj, CreateFormTests.post, (
            "Ошибка. Содержание поста не изменилось"))
        self.assertNotIn(CreateFormTests.post, response.context['page_obj'], (
            f'Ошибка. Пост не должен отображаться на странице группы '
            f'{CreateFormTests.group}'))

        for db_post_field_value, form_field_value in post_fields_check.items():
            with self.subTest(db_post_field_value=db_post_field_value):
                self.assertEqual(db_post_field_value, form_field_value, (
                    f'Ошибка. Несоответствие значения поля '
                    f'{db_post_field_value} '
                    f'значению указанному в форме редактирования поста.'))

    def test_creat_comment_authorized_client(self):
        """
        При отправке авторизованным пользователем валидной формы создания
        комментария со страницы поста post_detail, новый комментарий создаётся
        в базе данных и отображается на странице поста post_detail.
        """
        comments_count = Comment.objects.count()

        form_data = {
            'text': 'Тестовый комментарий',
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={
                'post_id': CreateFormTests.post.id}),
            data=form_data,
        )
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={
                'post_id': CreateFormTests.post.id})
        )

        comment_on_page = response.context[
            'post_obj'].comments.order_by('pk').last()

        db_comment = Comment.objects.filter(
            post_id=CreateFormTests.post.id).order_by('pk').last()

        comment_fields_check = {
            form_data['text']: db_comment.text,
            comment_on_page.post: db_comment.post,
            comment_on_page.created: db_comment.created,
            comment_on_page.author: db_comment.author,
            comment_on_page.text: db_comment.text,
        }

        self.assertEqual(Comment.objects.count(), comments_count + 1, (
            'Ошибка. Количество постов не изменилось'))

        for context_values, db_values in comment_fields_check.items():
            with self.subTest(context_values=context_values):
                self.assertEqual(context_values, db_values, (
                    f'Ошибка. Несоответствие значения поля '
                    f'{context_values} значению, указанному в БД'))

    def test_creat_comment_guest_client(self):
        """
        При отправке неавторизованным пользователем валидной формы создания
        комментария со страницы поста post_detail, новый комментарий
        не создаётся в базе данных.
        """
        comments_count = Comment.objects.count()

        form_data = {
            'text': 'Тестовый комментарий',
        }
        self.guest_client.post(
            reverse('posts:add_comment', kwargs={
                'post_id': CreateFormTests.post.id}),
            data=form_data,
        )
        self.assertEqual(Comment.objects.count(), comments_count, (
            'Ошибка. Количество постов не должно было изменится'))
