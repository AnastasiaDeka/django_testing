from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from notes.models import Note
from notes.forms import NoteForm

User = get_user_model()


class TestHomePage(TestCase):
    HOME_URL = reverse('notes:list')

    @classmethod
    def setUpTestData(cls):
        cls.author_user = User.objects.create(username='AuthorUser')
        cls.other_user = User.objects.create(username='OtherUser')

        cls.author_note = Note.objects.create(
            title='Заметка автора',
            text='Текст заметки.',
            author=cls.author_user,
            slug='slug-author'
        )

        cls.client_author = Client()
        cls.client_author.force_login(cls.author_user)

        cls.client_other = Client()
        cls.client_other.force_login(cls.other_user)

    def test_note_in_context(self):
        """Проверка, что автор видит свои заметки,
        а другие пользователи — нет.
        """
        clients = [
            (self.client_author, True),
            (self.client_other, False)
        ]

        for client, expected in clients:
            with self.subTest(client=client):
                response = client.get(self.HOME_URL)
                object_list = response.context.get('object_list', [])
                self.assertIs(
                    self.author_note in object_list,
                    expected
                )


class TestNotePages(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_author = User.objects.create(username='UserAuthor')

        cls.note = Note.objects.create(
            title='Тестовая заметка',
            text='Просто текст заметки.',
            author=cls.user_author,
            slug='test-slug'
        )
        cls.create_url = reverse('notes:add')
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))

        cls.client_author = Client()
        cls.client_author.force_login(cls.user_author)

    def test_create_and_edit_pages_have_form(self):
        """Проверка, что страницы создания и редактирования имеют форму."""
        urls = [self.create_url, self.edit_url]

        for url in urls:
            with self.subTest(url=url):
                response = self.client_author.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)
