from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class UserFormTest(TestCase):

    def setUp(self):

        self.guest_client = Client()

    def test_signup(self):
        """Валидная форма создает новый пост."""

        users_count = User.objects.count()

        form_data = {
            'first_name': 'Darth',
            'last_name': 'Vader',
            'username': 'darth',
            'email': 'DarthVader@evel.com',
            'password1': 'ObiWanKenobi01',
            'password2': 'ObiWanKenobi01',
        }
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:index'))
        self.assertEqual(User.objects.count(), users_count + 1)

        self.assertTrue(
            User.objects.filter(
                first_name='Darth',
                last_name='Vader',
                username='darth',
                email='DarthVader@evel.com',
            ).exists()
        )
