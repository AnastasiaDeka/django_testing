import pytest
from django.utils import timezone
from datetime import timedelta
from news.models import News, Comment
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()


@pytest.fixture
def news_detail(db):
    """Создает тестовую новость для использования в тестах."""
    return News.objects.create(title='Тестовая новость',
                               text='Просто текст.')


@pytest.fixture
def comments(db, news_detail):
    """Создает тестовые комм-ии для тестирования функционала."""
    author = User.objects.create_user(username='Комментатор')
    now = timezone.now()
    comments = [
        Comment.objects.create(
            news=news_detail,
            author=author,
            text=f'Текст {index}',
            created=now + timedelta(days=index)
        )
        for index in range(10)
    ]
    return comments, author


@pytest.fixture
def news(db):
    """Создает тестовые новости для использования в тестах."""
    today = timezone.now()
    news_items = [
        News(
            title=f'Новость {index}',
            text='Просто текст.',
            date=today - timedelta(days=index)
        )
        for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
    ]
    News.objects.bulk_create(news_items)
    return News.objects.all()


@pytest.fixture
def user_factory(db):
    """Для создания пользователей."""
    def create_user(username):
        return User.objects.create_user(username=username, password='password')
    return create_user


@pytest.fixture
def author(user_factory):
    """Создает пользователя-автора для тестов."""
    return user_factory('Автор')


@pytest.fixture
def not_author(user_factory):
    """Создает пользователя, который не является автором."""
    return user_factory('Не автор')


@pytest.fixture
def reader(user_factory):
    """Создает пользователя-читателя для тестов."""
    return user_factory('Читатель')


@pytest.fixture
def author_client(client, author):
    """Фикстура для авторизованного пользователя."""
    client.force_login(author)
    return client


@pytest.fixture
def not_author_client(client, not_author):
    """Создает клиента, автори-ого под поль-ем, который не является автором."""
    client.force_login(not_author)
    return client


@pytest.fixture
def reader_client(client, reader):
    """Создает клиента, авторизованного под пользователем-читателем."""
    client.force_login(reader)
    return client


@pytest.fixture
def comment(db, news, author):
    """Создает тестовый комментарий для использования в тестах."""
    return Comment.objects.create(
        news=news[0],
        author=author,
        text='Текст комментария'
    )


@pytest.fixture
def comment_form_data():
    """Возвращает данные формы для создания нового комментария."""
    return {
        'text': 'Новый комментарий'
    }


@pytest.fixture
def bad_words_form_data():
    """Возвращает данные формы с недопустимыми словами."""
    return {
        'text': 'Ты редиска!'
    }


@pytest.fixture
def new_comment_form_data():
    """Возвращает данные формы для обновления комментария."""
    return {
        'text': 'Обновленный комментарий'
    }
