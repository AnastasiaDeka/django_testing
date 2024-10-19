from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestNoteCreation(TestCase):
    URL_TO_ADD = reverse('notes:add')
    URL_TO_DONE = reverse('notes:success')
    URL_TO_LOGIN = reverse('users:login')

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Пользователь')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.form_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': 'new-slug'
        }

    def setUp(self):
        self.note = Note.objects.create(
            author=self.user,
            title='Текст заголовка',
            text='Текст заметки',
            slug='unique-slug'
        )

    def test_user_can_create_note(self):
        """Проверка, что авторизованный
        пользователь может создать заметку.
        """
        response = self.auth_client.post(self.URL_TO_ADD, data=self.form_data)
        self.assertRedirects(response, self.URL_TO_DONE)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 2)
        note = Note.objects.last()
        self.assertEqual(note.title, self.form_data['title'])
        self.assertEqual(note.slug, self.form_data['slug'])
        self.assertEqual(note.text, self.form_data['text'])
        self.assertEqual(note.author, self.user)

    def test_anonymous_user_cannot_create_note(self):
        """Проверка, что анонимный пользователь
        не может создать заметку.
        """
        self.client.logout()
        response = self.client.post(self.URL_TO_ADD, data=self.form_data)
        self.assertRedirects(response,
                             f"{self.URL_TO_LOGIN}?next={self.URL_TO_ADD}")
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_slug_is_generated_automatically_if_not_provided(self):
        """Проверка, что slug генерируется автоматически,
        если не был указан пользователем.
        """
        form_data_without_slug = self.form_data.copy()
        form_data_without_slug.pop('slug')
        response = self.auth_client.post(self.URL_TO_ADD,
                                         data=form_data_without_slug)
        self.assertRedirects(response, self.URL_TO_DONE)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 2)
        new_note = Note.objects.last()
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)

    def test_user_cannot_create_note_with_duplicate_slug(self):
        """Проверка, что пользователь не
        может создать заметку с дублирующимся slug.
        """
        self.form_data['slug'] = self.note.slug
        response = self.auth_client.post(self.URL_TO_ADD, data=self.form_data)

        self.assertFormError(response, 'form', 'slug',
                             errors=(self.note.slug + WARNING))
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)


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

    def test_user_cannot_edit_or_delete_another_users_note(self):
        """Проверка, что авторизованный пользователь не может
        редактировать или удалять заметку другого пользователя.
        """
        response = self.client_other.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        note = Note.objects.get(id=self.note.id)
        self.assertEqual(note.title, self.NOTE_TITLE)
        self.assertEqual(note.text, self.NOTE_TEXT)
        self.assertEqual(note.slug, self.NOTE_SLUG)

        response = self.client_other.post(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        self.assertTrue(Note.objects.filter(id=self.note.id).exists())
