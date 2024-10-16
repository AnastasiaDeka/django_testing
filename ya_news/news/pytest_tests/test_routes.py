import pytest
from http import HTTPStatus

from django.urls import reverse

from news.models import Comment, News
from pytest_django.asserts import assertRedirects


@pytest.mark.django_db
def test_pages_availability(client, news):
    pages = [
        'news:home',
        'news:detail',
        'users:login',
        'users:logout',
        'users:signup',
    ]

    first_news = news.first()

    for name in pages:
        url = reverse(name,
                      args=(first_news.id,) if name == 'news:detail' else None)
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    'client_fixture, expected_status',
    [
        ('author_client', HTTPStatus.OK),
        ('not_author_client', HTTPStatus.NOT_FOUND),
    ]
)
@pytest.mark.django_db
def test_availability_for_comment_edit_and_delete(request,
                                                  client_fixture,
                                                  expected_status):
    news_item = News.objects.create(title='Заголовок', text='Текст')
    author = request.getfixturevalue('author')
    comment = Comment.objects.create(news=news_item,
                                     author=author,
                                     text='Текст комментария')

    client = request.getfixturevalue(client_fixture)

    for name in ['edit', 'delete']:
        url = reverse(f'news:{name}', args=(comment.id,))
        response = client.get(url)
        assert response.status_code == expected_status


@pytest.mark.django_db
def test_redirect_for_anonymous_client(client, author):
    news_item = News.objects.create(title='Заголовок', text='Текст')
    comment = Comment.objects.create(news=news_item,
                                     author=author,
                                     text='Текст комментария')

    for name in ['news:edit', 'news:delete']:
        login_url = reverse('users:login')
        url = reverse(name, args=(comment.id,))
        expected_url = f'{login_url}?next={url}'
        response = client.get(url)
        assertRedirects(response, expected_url)


@pytest.mark.django_db
def test_author_cannot_edit_other_comment(author_client,
                                          not_author_client,
                                          author):
    news_item = News.objects.create(title='Заголовок', text='Текст')
    comment = Comment.objects.create(news=news_item,
                                     author=author,
                                     text='Текст комментария')

    response = not_author_client.get(reverse('news:edit',
                                             args=(comment.id,)))
    assert response.status_code == HTTPStatus.NOT_FOUND

    response = not_author_client.get(reverse('news:delete',
                                             args=(comment.id,)))
    assert response.status_code == HTTPStatus.NOT_FOUND
