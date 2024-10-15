import pytest
from django.urls import reverse
from news.forms import CommentForm
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db  # Добавляем маркер
def test_news_count(news, client):
    """Проверяем количество новостей на главной странице."""
    url = reverse('news:home')
    response = client.get(url)
    object_list = response.context['object_list']
    assert len(object_list) == settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db  # Добавляем маркер
def test_news_order(news, client):
    """Проверяем сортировку новостей от самой свежей к самой старой."""
    url = reverse('news:home')
    response = client.get(url)
    object_list = response.context['object_list']
    all_dates = [news_item.date for news_item in object_list]
    sorted_dates = sorted(all_dates, reverse=True)
    assert all_dates == sorted_dates


@pytest.mark.django_db  # Добавляем маркер
def test_comments_order(news_detail, comments, client):
    """Проверяем сортировку комментариев на странице отдельной новости."""
    url = reverse('news:detail', args=[news_detail.id])
    response = client.get(url)
    news = response.context['news']
    all_comments = news.comment_set.all()
    all_timestamps = [comment.created for comment in all_comments]
    sorted_timestamps = sorted(all_timestamps)
    assert all_timestamps == sorted_timestamps


@pytest.mark.django_db  # Добавляем маркер
def test_anonymous_client_has_no_form(news_detail, client):
    """Анонимный пользователь не должен видеть форму для комментариев."""
    url = reverse('news:detail', args=[news_detail.id])
    response = client.get(url)
    assert 'form' not in response.context


@pytest.mark.django_db  # Добавляем маркер
def test_authorized_client_has_form(news_detail, comments, client):
    """Авторизованный пользователь должен видеть форму для комментариев."""
    _, author = comments
    client.force_login(author)
    url = reverse('news:detail', args=[news_detail.id])
    response = client.get(url)
    assert 'form' in response.context
    assert isinstance(response.context['form'], CommentForm)
