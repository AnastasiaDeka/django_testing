from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.text import slugify

from notes.models import Note
from notes.forms import WARNING

User = get_user_model()


class TestNoteCreationAndEditing(TestCase):
    NOTE_TITLE = 'Заголовок заметки'
    NOTE_TEXT = 'Текст заметки'
    NOTE_SLUG = 'slug-notes'
    NEW_NOTE_TITLE = 'Новая заметка'
    NEW_NOTE_SLUG = 'new-slug'

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

        cls.create_url = reverse('notes:add')
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))

        cls.form_data = {
            'title': cls.NEW_NOTE_TITLE,
            'text': cls.NOTE_TEXT,
            'slug': cls.NEW_NOTE_SLUG
        }

    def test_user_can_create_note(self):
        """Проверка, что авторизованный пользователь может
        создать заметку.
        """
        response = self.client_author.post(self.create_url,
                                           data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 2)

        note = Note.objects.get(slug=self.form_data['slug'])
        self.assertEqual(note.title, self.form_data['title'])
        self.assertEqual(note.text, self.form_data['text'])
        self.assertEqual(note.author, self.user_author)

    def test_anonymous_user_cannot_create_note(self):
        """Проверка, что анонимный пользователь не может создать заметку."""
        self.client.logout()

        form_data = {
            'title': 'Анонимная заметка',
            'text': 'Текст заметки',
            'slug': 'anonymous-slug'
        }

        response = self.client.post(self.create_url, data=form_data)
        self.assertRedirects(
            response,
            f"{reverse('users:login')}?next={self.create_url}"
        )
        self.assertEqual(Note.objects.count(), 1)

    def test_user_cannot_create_note_with_duplicate_slug(self):
        """Проверка, что пользователь не может создать
        заметку с дублирующимся slug.
        """
        form_data = {
            'title': 'Новая заметка с дублирующимся slug',
            'text': 'Текст заметки',
            'slug': self.note.slug
        }

        response = self.client_author.post(self.create_url, data=form_data)
        self.assertFormError(
            response,
            'form',
            'slug',
            self.note.slug + WARNING
        )

    def test_slug_is_generated_automatically_if_not_provided(self):
        """Проверка автоматической генерации slug, если он не предоставлен."""
        self.client_author.force_login(self.user_author)

        title = 'Явный заголовок заметки'
        form_data = {
            'title': title,
            'text': 'Текст заметки',
        }

        form_data.pop('slug', None)

        notes_before = Note.objects.count()
        response = self.client_author.post(self.create_url, data=form_data)
        self.assertRedirects(response, reverse('notes:success'))

        notes_after = Note.objects.count()
        self.assertEqual(notes_after - notes_before, 1)

        new_note = Note.objects.latest('id')

        self.assertTrue(new_note.slug,
                        "Slug не был сгенерирован автоматически.")

        expected_slug = slugify(title)
        self.assertEqual(new_note.slug, expected_slug)

    def test_user_can_edit_note(self):
        """Проверка, что авторизованный пользователь может
        редактировать свою заметку.
        """
        form_data = {
            'title': 'Обновленный заголовок',
            'text': 'Обновлённая заметка',
            'slug': self.note.slug
        }

        response = self.client_author.post(self.edit_url, data=form_data)
        self.assertRedirects(response, reverse('notes:success'))

        note = Note.objects.get(id=self.note.id)
        self.assertEqual(note.title, form_data['title'])
        self.assertEqual(note.text, form_data['text'])
        self.assertEqual(note.slug, form_data['slug'])

    def test_user_can_delete_own_note(self):
        """Проверка, что авторизованный пользователь может
        удалить свою заметку.
        """
        response = self.client_author.post(self.delete_url)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertFalse(Note.objects.filter(id=self.note.id).exists())

    def test_user_cannot_delete_another_users_note_authenticated(self):
        """Проверка, что авторизованный пользователь не может
        удалить заметку другого пользователя.
        """
        response = self.client_other.post(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTrue(Note.objects.filter(id=self.note.id).exists())
