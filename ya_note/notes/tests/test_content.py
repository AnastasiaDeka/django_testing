from django.test import TestCase
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

    def test_note_in_context_for_author(self):
        self.client.force_login(self.author_user)
        response = self.client.get(self.HOME_URL)
        object_list = response.context.get('object_list', [])
        self.assertIn(self.author_note, object_list)

    def test_note_in_context_for_other_user(self):
        self.client.force_login(self.other_user)
        response = self.client.get(self.HOME_URL)
        object_list = response.context.get('object_list', [])
        self.assertNotIn(self.author_note, object_list)


class TestNotePages(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='User')
        cls.note = Note.objects.create(
            title='Тестовая заметка',
            text='Просто текст заметки.',
            author=cls.user,
            slug='test-slug'
        )
        cls.create_url = reverse('notes:add')
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))

    def test_create_and_edit_pages_have_form(self):
        urls = [self.create_url, self.edit_url]
        self.client.force_login(self.user)

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)
