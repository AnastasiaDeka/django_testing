import pytest
from http import HTTPStatus

from pytest_lazyfixture import lazy_fixture
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from news.models import Comment, News

@pytest.mark.django_db
@pytest.mark.parametrize(
    'name, args',
    [
        ('news:home', None),
        ('news:detail', pytest.lazy_fixture('pk_news')),
        ('users:login', None),
        ('users:logout', None),
        ('users:signup', None),
    ]
)
def test_pages_availability(client, name, args):
    """Проверка доступности страниц для анонимного пользователя."""
    url = reverse(name, args=args)
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    'url_fixture, client_fixture, expected_status',
    [
        (lazy_fixture('edit_comment_url'),
         lazy_fixture('author_client'), HTTPStatus.OK),
        (lazy_fixture('delete_comment_url'),
         lazy_fixture('author_client'), HTTPStatus.OK),
        (lazy_fixture('edit_comment_url'),
         lazy_fixture('not_author_client'), HTTPStatus.NOT_FOUND),
        (lazy_fixture('delete_comment_url'),
         lazy_fixture('not_author_client'), HTTPStatus.NOT_FOUND),
    ]
)
@pytest.mark.django_db
def test_availability_for_comment_edit_and_delete(url_fixture,
                                                  client_fixture,
                                                  expected_status):
    """Проверка доступности страниц редактирования и удаления комментариев."""
    url = url_fixture
    response = client_fixture.get(url)
    assert response.status_code == expected_status


@pytest.mark.parametrize('url_fixture',
                         ['edit_comment_url', 'delete_comment_url'])
@pytest.mark.django_db
def test_redirect_for_anonymous_client(client,
                                       request,
                                       url_fixture,
                                       comment,
                                       login_url):
    """Проверка редиректа для анонимного клиента
    на страницы редактирования и удаления комментариев.
    """
    url = request.getfixturevalue(url_fixture)
    expected_url = f'{login_url}?next={url}'
    response = client.get(url)
    assertRedirects(response, expected_url)
