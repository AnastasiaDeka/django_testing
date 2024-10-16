import pytest
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings

from news.models import News, Comment

User = get_user_model()


@pytest.fixture
def news_detail(db):
    return News.objects.create(title='Тестовая новость', text='Просто текст.')


@pytest.fixture
def comment_author(db):
    return User.objects.create_user(username='Комментатор',
                                    password='password')


@pytest.fixture
def comments(news_detail, db):
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
    return Comment.objects.filter(news=news_detail)


@pytest.fixture
def news(db):
    today = timezone.now()
    news_items = [
        News(
            title=f'Новость {index}',
            text='Просто текст.',
            date=today - timedelta(days=index)
        )
        for index in range(settings.NEWS_COUNT_ON_HOME_PAGE)
    ]
    News.objects.bulk_create(news_items)
    return News.objects.all()


@pytest.fixture
def user_factory(db):
    def create_user(username):
        return User.objects.create_user(username=username, password='password')
    return create_user


@pytest.fixture
def author(user_factory):
    return user_factory('Автор')


@pytest.fixture
def not_author(user_factory):
    return user_factory('Не автор')


@pytest.fixture
def author_client(client, author):
    client.force_login(author)
    return client


@pytest.fixture
def not_author_client(client, not_author):
    client.force_login(not_author)
    return client


@pytest.fixture
def comment(db, news_detail, author):
    return Comment.objects.create(
        news=news_detail,
        author=author,
        text='Текст комментария'
    )


@pytest.fixture
def comment_form_data():
    return {
        'text': 'Новый комментарий'
    }


@pytest.fixture
def home_url():
    return reverse('news:home')


@pytest.fixture
def news_detail_url(news_detail):
    return reverse('news:detail', args=[news_detail.id])
