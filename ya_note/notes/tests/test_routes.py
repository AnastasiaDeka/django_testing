from http import HTTPStatus

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from notes.models import Note

User = get_user_model()

NAMES = (
    'notes:add',
    'notes:edit',
    'notes:detail',
    'notes:delete',
    'notes:list',
    'notes:success'
)


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Создаем тестового пользователя и заметку
        cls.author = User.objects.create(username='Лев Толстой')
        cls.note_author = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='zagolovok',
            author=cls.author
        )

    def test_pages_availability(self):
        # Проверяем доступность страниц для анонимных пользователей
        urls = (
            ('notes:home', None),
            ('users:login', None),
            ('users:logout', None),
            ('users:signup', None),
        )

        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_notes_add_edit_delete(self):
        # Проверяем доступность страниц для авторов и анонимных пользователей
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (None, HTTPStatus.FOUND),
        )

        for user, status in users_statuses:
            if user:
                self.client.force_login(user)
            else:
                self.client.logout()

            for name in NAMES:
                with self.subTest(user=user, name=name):
                    if name in ['notes:add', 'notes:list', 'notes:success']:
                        url = reverse(name)
                    else:
                        url = reverse(name, args=(self.note_author.slug,))
                    response = self.client.get(url)

                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_user(self):
        # Проверяем редирект для анонимных пользователей
        login_url = reverse('users:login')

        for name in NAMES:
            with self.subTest(name=name):
                if name in ['notes:add', 'notes:list', 'notes:success']:
                    url = reverse(name)
                else:
                    url = reverse(name, args=(self.note_author.slug,))
                response = self.client.get(url)
                expected_url = f"{login_url}?next={url}"

                self.assertRedirects(response, expected_url)
