import pytest
from http import HTTPStatus

from pytest_lazyfixture import lazy_fixture


@pytest.mark.django_db
@pytest.mark.parametrize('url, pk, expected_status', [
    (lazy_fixture('home_url'), None, HTTPStatus.OK),
    (lazy_fixture('news_detail_url'), lazy_fixture('pk_news'), HTTPStatus.OK),
    (lazy_fixture('login_url'), None, HTTPStatus.OK),
    (lazy_fixture('logout_url'), None, HTTPStatus.OK),
    (lazy_fixture('signup_url'), None, HTTPStatus.OK),
])
def test_pages_availability(client, url, pk, expected_status):
    """Проверяет доступность страниц."""
    response = client.get(url)
    assert response.status_code == expected_status


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


@pytest.mark.django_db
@pytest.mark.parametrize(
    'url_fixture',
    [
        lazy_fixture('edit_comment_url'),
        lazy_fixture('delete_comment_url'),
    ]
)
def test_redirect_for_anonymous_client(client,
                                       url_fixture,
                                       login_url):
    """Проверка редиректа для анонимного клиента
    на страницы редактирования и удаления комментариев.
    """
    expected_url = f'{login_url}?next={url_fixture}'
    response = client.get(url_fixture)
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == expected_url
