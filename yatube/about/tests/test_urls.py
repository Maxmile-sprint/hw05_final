from django.test import TestCase, Client


class StaticURLTests(TestCase):
    def setUp(self):
        self.quest_client = Client()

    def test_aboutAuthorPage(self):
        response = self.quest_client.get('/about/author/')
        self.assertEqual(response.status_code, 200, 'Error')

    def test_aboutTechPage(self):
        response = self.quest_client.get('/about/tech/')
        self.assertEqual(response.status_code, 200, 'Error')
