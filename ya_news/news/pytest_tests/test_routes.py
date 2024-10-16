import pytest
from http import HTTPStatus

from django.urls import reverse
from pytest_django.asserts import assertRedirects

from news.models import Comment


@pytest.mark.django_db
@pytest.mark.parametrize('name', [
    'news:home',
    'news:detail',
    'users:login',
    'users:logout',
    'users:signup',
])
def test_pages_availability(client, name, news):
    """Проверка доступности страниц для анонимного пользователя."""
    kwargs = {'pk': news.id} if name == 'news:detail' else {}
    url = reverse(name, kwargs=kwargs)
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    'name, client_fixture, expected_status',
    [
        ('news:edit', 'author_client', HTTPStatus.OK),
        ('news:delete', 'author_client', HTTPStatus.OK),
        ('news:edit', 'not_author_client', HTTPStatus.NOT_FOUND),
        ('news:delete', 'not_author_client', HTTPStatus.NOT_FOUND),
    ]
)
@pytest.mark.django_db
def test_availability_for_comment_edit_and_delete(request, name,
                                                  client_fixture,
                                                  expected_status, comment):
    """Проверка доступности страниц
    редактирования и удаления комментариев.
    """
    client = request.getfixturevalue(client_fixture)
    url = reverse(name, args=(comment.id,))
    response = client.get(url)
    assert response.status_code == expected_status


@pytest.mark.parametrize('name', ['news:edit', 'news:delete'])
@pytest.mark.django_db
def test_redirect_for_anonymous_client(client, name, comment):
    """Проверка редиректа для анонимного клиента на
    страницы редактирования и удаления комментариев.
    """
    login_url = reverse('users:login')
    url = reverse(name, args=(comment.id,))
    expected_url = f'{login_url}?next={url}'
    response = client.get(url)
    assertRedirects(response, expected_url)


@pytest.mark.django_db
def test_anonymous_user_cannot_post_comment(client, news):
    """Анонимный пользователь не может отправить комментарий."""
    url = reverse('news:detail', args=(news.id,))
    response = client.post(url, data={'text': 'Текст комментария'})
    assert response.status_code == HTTPStatus.FOUND


@pytest.mark.django_db
def test_comment_contains_bad_words(author_client, news):
    """Если комментарий содержит запрещённые слова, он не будет опубликован."""
    url = reverse('news:detail', args=(news.id,))
    response = author_client.post(url, data={'text': 'Ты редиска!'})
    assert response.status_code == HTTPStatus.OK
    assert not Comment.objects.filter(news=news, text='Ты редиска!').exists()
