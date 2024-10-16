import pytest

from django.conf import settings
from django.contrib.auth import get_user_model

from news.forms import CommentForm


User = get_user_model()

CONTEXT_OBJECT_LIST = 'object_list'
CONTEXT_OBJECT_DETAIL = 'news'
CONTEXT_OBJECT_FORM = 'form'


@pytest.mark.django_db
def test_news_count(news, client, home_url):
    response = client.get(home_url)
    object_list = response.context.get(CONTEXT_OBJECT_LIST, [])

    assert len(object_list) <= settings.NEWS_COUNT_ON_HOME_PAGE

    if len(news) > settings.NEWS_COUNT_ON_HOME_PAGE:
        assert len(object_list) == settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_news_order(news, client, home_url):
    response = client.get(home_url)
    object_list = response.context.get(CONTEXT_OBJECT_LIST, [])
    all_dates = [news_item.date for news_item in object_list]
    sorted_dates = sorted([n.date for n in news], reverse=True)
    assert all_dates == sorted_dates


@pytest.mark.django_db
def test_comments_order(news_detail, comments, client, news_detail_url):
    response = client.get(news_detail_url)
    all_comments = response.context[CONTEXT_OBJECT_DETAIL].comment_set.all()
    all_timestamps = [comment.created for comment in all_comments]
    sorted_timestamps = sorted([c.created for c in comments])
    assert all_timestamps == sorted_timestamps


@pytest.mark.parametrize("is_authorized, expected", [
    (False, False),
    (True, True),
])
@pytest.mark.django_db
def test_comment_form_visibility(news_detail,
                                 comments,
                                 client,
                                 news_detail_url,
                                 is_authorized,
                                 expected):
    if is_authorized:
        author = comments.first().author
        client.force_login(author)

    response = client.get(news_detail_url)

    assert (('form' in response.context) == expected)

    if is_authorized:
        assert isinstance(response.context['form'], CommentForm)
