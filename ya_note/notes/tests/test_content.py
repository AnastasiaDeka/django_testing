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
        cls.user1 = User.objects.create(username='User1')
        cls.user2 = User.objects.create(username='User2')

        cls.note1 = Note.objects.create(
            title='Заметка User1',
            text='Текст заметки User1.',
            author=cls.user1,
            slug='slug-user1'
        )
        cls.note2 = Note.objects.create(
            title='Заметка User2',
            text='Текст заметки User2.',
            author=cls.user2,
            slug='slug-user2'
        )

    def test_note_in_context(self):
        self.client.force_login(self.user1)

        response = self.client.get(self.HOME_URL)
        object_list = response.context.get('object_list', [])

        self.assertIn(self.note1, object_list)
        self.assertNotIn(self.note2, object_list)

    def test_notes_order(self):
        self.client.force_login(self.user1)
        response = self.client.get(self.HOME_URL)
        object_list = response.context.get('object_list', [])

        self.assertEqual(
            [note.slug for note in object_list],
            [self.note1.slug]
        )


class TestNotePages(TestCase):
    HOME_URL = reverse('notes:list')

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
        cls.edit_url = reverse('notes:edit',
                               args=(cls.note.slug,))

    def test_create_page_has_form(self):
        self.client.force_login(self.user)
        response = self.client.get(self.create_url)
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], NoteForm)

    def test_edit_page_has_form(self):
        self.client.force_login(self.user)
        response = self.client.get(self.edit_url)
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], NoteForm)

    def test_user_sees_only_own_notes(self):
        other_user = User.objects.create(username='OtherUser')
        Note.objects.create(
            title='Заметка другого пользователя',
            text='Текст заметки другого пользователя.',
            author=other_user,
            slug='other-slug'
        )

        self.client.force_login(self.user)
        response = self.client.get(self.HOME_URL)
        object_list = response.context.get('object_list', [])

        self.assertIn(self.note, object_list)
        self.assertNotIn('Заметка другого пользователя',
                         [note.title for note in object_list])
