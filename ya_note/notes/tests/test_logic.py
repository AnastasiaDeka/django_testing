from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from notes.models import Note
from notes.forms import WARNING
from pytils.translit import slugify

User = get_user_model()


class TestNoteCreation(TestCase):
    NOTE_TEXT = 'Текст заметки'
    NOTE_TITLE = 'Текст заголовка'
    NOTE_SLUG = 'unique-slug'

    URL_TO_ADD = reverse('notes:add')
    URL_TO_DONE = reverse('notes:success')
    URL_TO_LOGIN = reverse('users:login')

    EXPECTED_NOTES_INCREMENT = 1

    @classmethod
    def setUpTestData(cls):
        cls.notes_counts = Note.objects.count()
        cls.user = User.objects.create(username='Пользователь')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.form_data = {
            'text': cls.NOTE_TEXT,
            'title': cls.NOTE_TITLE,
            'slug': cls.NOTE_SLUG,
            'author': cls.auth_client
        }

    def test_user_can_create_note(self):
        self.form_data['slug'] = 'new-unique-slug'
        response = self.auth_client.post(self.URL_TO_ADD, data=self.form_data)
        self.assertRedirects(response, self.URL_TO_DONE)
        note_count = Note.objects.count()
        self.assertEqual(note_count,
                         self.notes_counts + self.EXPECTED_NOTES_INCREMENT)
        note = Note.objects.last()
        self.assertEqual(note.title, self.NOTE_TITLE)
        self.assertEqual(note.slug, 'new-unique-slug')
        self.assertEqual(note.text, self.NOTE_TEXT)
        self.assertEqual(note.author, self.user)

    def test_anonymous_user_cannot_create_note(self):
        """Проверка, что анонимный
        пользователь не может создать заметку.
        """
        self.client.logout()
        response = self.client.post(self.URL_TO_ADD, data=self.form_data)
        self.assertRedirects(response,
                             f"{self.URL_TO_LOGIN}?next={self.URL_TO_ADD}")
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, self.notes_counts)

    def test_slug_is_generated_automatically_if_not_provided(self):
        """Проверка, что slug генерируется
        автоматически, если не предоставлен.
        """
        self.form_data.pop('slug')
        response = self.auth_client.post(self.URL_TO_ADD, data=self.form_data)
        self.assertRedirects(response, self.URL_TO_DONE)
        self.assertEqual(Note.objects.count(),
                         self.notes_counts + self.EXPECTED_NOTES_INCREMENT)
        new_note = Note.objects.get()
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)


class TestNoteSlugDuplication(TestCase):
    NOTE_TEXT = 'Текст заметки'
    NOTE_TITLE = 'Текст заголовка'
    NOTE_SLUG = 'unique-slug'

    URL_TO_ADD = reverse('notes:add')
    WARNING = "Должен быть уникальным."

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Пользователь')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)

        cls.note = Note.objects.create(
            author=cls.user,
            title=cls.NOTE_TITLE,
            text=cls.NOTE_TEXT,
            slug=cls.NOTE_SLUG
        )

    def setUp(self):
        self.form_data = {
            'text': self.NOTE_TEXT,
            'title': self.NOTE_TITLE,
            'slug': self.NOTE_SLUG,
        }
        self.notes_counts = Note.objects.count()

    def test_user_cannot_create_note_with_duplicate_slug(self):
        """Проверка, что пользователь
        не может создать заметку с дублирующимся slug.
        """
        self.form_data['slug'] = self.note.slug
        response = self.auth_client.post(self.URL_TO_ADD,
                                         data=self.form_data)

        self.assertFormError(response, 'form', 'slug',
                             errors=(self.note.slug + WARNING))
        self.assertEqual(Note.objects.count(), self.notes_counts)


class TestNoteEditDelete(TestCase):
    UPDATED_NOTE_TITLE = 'Обновленный заголовок'
    UPDATED_NOTE_TEXT = 'Обновлённая заметка'
    NOTE_TITLE = 'Заголовок заметки'
    NOTE_TEXT = 'Текст заметки'
    NOTE_SLUG = 'slug-notes'

    @classmethod
    def setUpTestData(cls):
        """Создание тестовых данных для всех тестов."""
        cls.user_author = User.objects.create(username='Автор заметки')
        cls.user_other = User.objects.create(username='Другой пользователь')

        cls.client_author = Client()
        cls.client_author.force_login(cls.user_author)

        cls.client_other = Client()
        cls.client_other.force_login(cls.user_other)

        cls.note = Note.objects.create(
            author=cls.user_author,
            title=cls.NOTE_TITLE,
            text=cls.NOTE_TEXT,
            slug=cls.NOTE_SLUG
        )

        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))

        cls.form_data = {
            'title': cls.UPDATED_NOTE_TITLE,
            'text': cls.UPDATED_NOTE_TEXT,
            'slug': cls.NOTE_SLUG,
        }

    def test_user_can_edit_note(self):
        """Проверка, что авторизованный
        пользователь может редактировать свою заметку.
        """
        response = self.client_author.post(self.edit_url,
                                           data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))

        note = Note.objects.get(id=self.note.id)
        self.assertEqual(note.title, self.form_data['title'])
        self.assertEqual(note.text, self.form_data['text'])
        self.assertEqual(note.slug, self.form_data['slug'])

    def test_user_can_delete_own_note(self):
        """Проверка, что авторизованный
        пользователь может удалить свою заметку.
        """
        response = self.client_author.post(self.delete_url)
        self.assertRedirects(response, reverse('notes:success'))

        self.assertFalse(Note.objects.filter(id=self.note.id).exists())

    def test_user_cannot_delete_another_users_note_authenticated(self):
        """Проверка, что авторизованный пользователь не
        может удалить заметку другого пользователя.
        """
        response = self.client_other.post(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        self.assertTrue(Note.objects.filter(id=self.note.id).exists())
