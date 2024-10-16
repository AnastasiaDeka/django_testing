import pytest

from django.conf import settings
from django.contrib.auth import get_user_model

from news.forms import CommentForm

User = get_user_model()

CONTEXT_OBJECT_LIST = 'object_list'
CONTEXT_OBJECT_DETAIL = 'news'
CONTEXT_OBJECT_FORM = 'form'

pytestmark = pytest.mark.django_db


def test_news_count(news, client, home_url):
    """Количество новостей на главной странице — не более 10."""
    response = client.get(home_url)
    object_list = response.context.get(CONTEXT_OBJECT_LIST, [])
    assert object_list is not None
    news_count = object_list.count()
    assert news_count <= settings.NEWS_COUNT_ON_HOME_PAGE


def test_news_order(news, client, home_url):
    """Новости отсортированы от самой свежей к самой старой."""
    response = client.get(home_url)
    object_list = response.context.get(CONTEXT_OBJECT_LIST, [])
    assert object_list is not None
    all_dates = [news_item.date for news_item in object_list]
    sorted_dates = sorted(all_dates, reverse=True)
    assert all_dates == sorted_dates


def test_comments_order(news_detail, comments, client, news_detail_url):
    """Комментарии на странице отдельной новости отсортированы в
    хронологическом порядке: старые в начале списка, новые — в конце.
    """
    response = client.get(news_detail_url)
    assert CONTEXT_OBJECT_DETAIL in response.context
    news = response.context[CONTEXT_OBJECT_DETAIL]
    all_comments = news.comment_set.all()
    all_timestamps = [comment.created for comment in all_comments]
    sorted_timestamps = sorted(all_timestamps)
    assert all_timestamps == sorted_timestamps


def test_anonymous_client_has_no_form(news_detail,
                                      client,
                                      news_detail_url):
    """Анонимному пользователю недоступна форма для
    отправки комментария на странице отдельной новости.
    """
    response = client.get(news_detail_url)
    assert CONTEXT_OBJECT_FORM not in response.context


def test_authorized_client_has_form(author_client, news_detail,
                                    news_detail_url):
    """Авторизованному пользователю доступна форма
    для отправки комментария на странице отдельной новости.
    """
    response = author_client.get(news_detail_url)
    assert CONTEXT_OBJECT_FORM in response.context
    assert isinstance(response.context[CONTEXT_OBJECT_FORM], CommentForm)
