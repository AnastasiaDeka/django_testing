from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()

URLS = {
    'home': 'notes:home',
    'login': 'users:login',
    'logout': 'users:logout',
    'signup': 'users:signup',
    'detail': 'notes:detail',
    'edit': 'notes:edit',
    'delete': 'notes:delete',
    'list': 'notes:list',
    'add': 'notes:add',
    'success': 'notes:success',
}


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='LeoTolstoy')
        cls.reader = User.objects.create(username='Reader')
        cls.note = Note.objects.create(
            title='Note Title',
            text='Note text content.',
            slug='note-slug',
            author=cls.author
        )

    def setUp(self):
        self.author_client = self.client_class()
        self.reader_client = self.client_class()
        self.author_client.force_login(self.author)
        self.reader_client.force_login(self.reader)

    def test_pages_availability(self):
        """Проверяет доступность страниц для анонимных пользователей."""
        urls = (URLS['home'], URLS['login'], URLS['logout'], URLS['signup'])
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_authors_and_readers(self):
        """Проверяет доступность страниц для авторов и читателей."""
        urls = (URLS['detail'], URLS['edit'], URLS['delete'])
        clients_statuses = (
            (self.author_client, HTTPStatus.OK),
            (self.reader_client, HTTPStatus.NOT_FOUND),
        )
        for client, status in clients_statuses:
            for name in urls:
                with self.subTest(client=client, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_pages_availability_for_auth_users(self):
        """Проверяет доступность страниц для авторизованных пользователей."""
        urls = (URLS['list'], URLS['add'], URLS['success'])
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.reader_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirects_for_anonymous_users(self):
        """Проверяет редиректы для анонимных пользователей."""
        login_url = reverse(URLS['login'])
        urls = (
            (URLS['list'], None),
            (URLS['add'], None),
            (URLS['success'], None),
            (URLS['detail'], (self.note.slug,)),
            (URLS['edit'], (self.note.slug,)),
            (URLS['delete'], (self.note.slug,)),
        )
        for name, args in urls:
            with self.subTest(name=name, args=args):
                url = reverse(name, args=args)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
