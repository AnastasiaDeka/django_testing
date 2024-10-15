from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from notes.models import Note

User = get_user_model()


class TestNoteCreationAndEditing(TestCase):
    NOTE_TEXT = 'Текст заметки'
    NEW_NOTE_TEXT = 'Обновленная заметка'
    NOTE_SLUG = 'slug-notes'

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
            text=cls.NOTE_TEXT,
            slug=cls.NOTE_SLUG
        )

        cls.create_url = reverse('notes:add')
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))

    def test_note_appears_in_user_list(self):
        response = self.client1.get(reverse('notes:list'))
        self.assertIn(self.note, response.context['object_list'])

    def test_note_does_not_appear_in_another_user_list(self):
        response = self.client2.get(reverse('notes:list'))
        self.assertNotIn(self.note, response.context['object_list'])

    def test_create_note_form_is_present(self):
        response = self.client1.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_edit_note_form_is_present(self):
        response = self.client1.get(self.edit_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_user_can_create_note(self):
        form_data = {
            'title': 'Новая заметка',
            'text': self.NEW_NOTE_TEXT,
            'slug': 'new-slug'
        }
        response = self.client1.post(self.create_url, data=form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertTrue(Note.objects.filter(text=self.NEW_NOTE_TEXT,
                                            author=self.user1).exists())

    def test_user_can_edit_note(self):
        form_data = {
            'title': 'Обновленный заголовок',
            'text': self.NEW_NOTE_TEXT
        }
        response = self.client1.post(self.edit_url, data=form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NEW_NOTE_TEXT)

    def test_user_cannot_edit_another_users_note(self):
        form_data = {
            'title': 'Новый заголовок',
            'text': self.NEW_NOTE_TEXT
        }
        response = self.client2.post(self.edit_url, data=form_data)
        self.assertEqual(response.status_code, 404)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NOTE_TEXT)
