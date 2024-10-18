import pytest
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from news.models import News, Comment

User = get_user_model()


@pytest.fixture
def author(db):
    """Создает пользователя-автора для тестов."""
    return User.objects.create_user(username='Автор', password='password')


@pytest.fixture
def not_author(db):
    """Создает пользователя, который не является автором."""
    return User.objects.create_user(username='Не автор', password='password')


@pytest.fixture
def news_detail(db):
    """Создает тестовую новость для использования в тестах."""
    return News.objects.create(title='Тестовая новость', text='Просто текст.')


@pytest.fixture
def pk_news(news):
    return (news.pk,)


@pytest.fixture
def comment(db, news_detail, author):
    """Создает тестовый комментарий для использования в тестах."""
    return Comment.objects.create(
        news=news_detail,
        author=author,
        text='Текст комментария'
    )


@pytest.fixture
def comments(db, news_detail):
    """Создает несколько тестовых комментариев для новости и возвращает их."""
    comments_list = [
        Comment(
            news=news_detail,
            author=User.objects.create_user(username=f'author{index}',
                                            password='testpassword'),
            text=f'Комментарий {index}',
            created=timezone.now() - timedelta(days=index)
        )
        for index in range(3)
    ]
    Comment.objects.bulk_create(comments_list)


@pytest.fixture
def news(db):
    """Создает тестовую новость и возвращает её."""
    return News.objects.create(title='Заголовок',
                               text='Текст новости')


@pytest.fixture
def author_client(client, author):
    """Фикстура для авторизованного пользователя."""
    client.force_login(author)
    return client


@pytest.fixture
def not_author_client(client, not_author):
    """Фикстура для пользователя, который не является автором."""
    client.force_login(not_author)
    return client


@pytest.fixture
def home_url():
    """Возвращает URL для главной страницы."""
    return reverse('news:home')


@pytest.fixture
def news_detail_url(news_detail):
    """Возвращает URL для детальной страницы новости."""
    return reverse('news:detail', args=[news_detail.id])


@pytest.fixture
def delete_comment_url(comment):
    """Возвращает URL для удаления комментария."""
    return reverse('news:delete', args=(comment.id,))


@pytest.fixture
def edit_comment_url(comment):
    """Возвращает URL для редактирования комментария."""
    return reverse('news:edit', args=(comment.id,))


@pytest.fixture
def comment_form_data():
    """Возвращает данные формы для создания нового комментария."""
    return {'text': 'Новый комментарий'}


@pytest.fixture
def login_url():
    """Возвращает URL для страницы логина."""
    return reverse('users:login')


@pytest.fixture
def logout_url():
    """Возвращает URL для страницы выхода."""
    return reverse('users:logout')


@pytest.fixture
def signup_url():
    """Возвращает URL для страницы регистрации."""
    return reverse('users:signup')
