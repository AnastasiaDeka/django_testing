from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note
from notes.forms import WARNING
from pytils.translit import slugify


User = get_user_model()


class TestNoteCreationAndEditing(TestCase):
    NOTE_SLUG = 'slug-notes'
    NOTE_TITLE = 'Заголовок заметки'

    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create(username='Пользователь 1')
        cls.user2 = User.objects.create(username='Пользователь 2')

        cls.client1 = Client()
        cls.client1.force_login(cls.user1)

        cls.client2 = Client()
        cls.client2.force_login(cls.user2)

        cls.note = Note.objects.create(
            author=cls.user1,
            title=cls.NOTE_TITLE,
            text='Текст заметки',
            slug=cls.NOTE_SLUG
        )

        cls.create_url = reverse('notes:add')
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))

    def test_user_can_create_note(self):
        form_data = {
            'title': 'Новая заметка',
            'text': 'Обновлённая заметка',
            'slug': 'new-slug'
        }
        response = self.client1.post(self.create_url, data=form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 2)
        note = Note.objects.get(slug='new-slug')
        self.assertEqual(note.title, form_data['title'])
        self.assertEqual(note.text, form_data['text'])
        self.assertEqual(note.author, self.user1)

    def test_anonymous_user_cannot_create_note(self):
        self.client1.logout()
        form_data = {
            'title': 'Анонимная заметка',
            'text': 'Текст заметки'
        }
        response = self.client1.post(self.create_url, data=form_data)
        self.assertRedirects(
            response,
            f"{reverse('users:login')}?next={self.create_url}"
        )

    def test_user_cannot_create_note_with_duplicate_slug(self):
        form_data = {
            'title': 'Заголовок для дубликата',
            'text': 'Текст дубликата',
            'slug': self.note.slug
        }
        response = self.client1.post(self.create_url, data=form_data)
        self.assertFormError(
            response,
            'form',
            'slug',
            errors=(self.note.slug + WARNING)
        )

    def test_slug_is_generated_automatically_if_not_provided(self):
        form_data = {
            'title': 'Новая заметка',
            'text': 'Текст заметки'
        }
        response = self.client1.post(self.create_url, data=form_data)
        self.assertRedirects(response, reverse('notes:success'))
        note = Note.objects.get(title=form_data['title'])
        expected_slug = slugify(form_data['title'])
        self.assertEqual(note.slug, expected_slug)

    def test_user_can_edit_note(self):
        form_data = {
            'title': 'Обновленный заголовок',
            'text': 'Обновлённая заметка'
        }
        response = self.client1.post(self.edit_url, data=form_data)
        self.assertRedirects(response, reverse('notes:success'))
        note = Note.objects.get(id=self.note.id)
        self.assertEqual(note.title, form_data['title'])
        self.assertEqual(note.text, form_data['text'])

    def test_user_can_delete_own_note(self):
        response = self.client1.post(self.delete_url)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertFalse(Note.objects.filter(id=self.note.id).exists())

    def test_user_cannot_delete_another_users_note(self):
        response = self.client2.post(self.delete_url)
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Note.objects.filter(id=self.note.id).exists())
