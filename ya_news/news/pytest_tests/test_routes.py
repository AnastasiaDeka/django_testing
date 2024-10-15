import pytest
from http import HTTPStatus
from django.urls import reverse
from news.models import Comment, News
from pytest_django.asserts import assertRedirects


@pytest.mark.django_db
def test_pages_availability(client):
    """Проверка доступности страниц для анонимного пользователя."""
    news_item = News.objects.create(title='Заголовок', text='Текст')

    pages = [
        'news:home',
        'news:detail',
        'users:login',
        'users:logout',
        'users:signup',
    ]

    for name in pages:
        url = reverse(name,
                      args=(news_item.id,) if name == 'news:detail' else None)
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    'client_fixture, expected_status',
    [
        ('author_client', HTTPStatus.OK),
        ('reader_client', HTTPStatus.NOT_FOUND),
    ]
)
@pytest.mark.django_db
def test_availability_for_comment_edit_and_delete(request,
                                                  client_fixture,
                                                  expected_status):
    """Проверка доступности страниц редактирования и удаления комментариев."""
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
    """Проверка редиректа для анонимного клиента на страницы
    редактирования и удаления комментариев.
    """
    news_item = News.objects.create(title='Заголовок',
                                    text='Текст')
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
def test_anonymous_user_cannot_post_comment(client):
    """Анонимный пользователь не может отправить комментарий."""
    news_item = News.objects.create(title='Заголовок', text='Текст')
    url = reverse('news:detail', args=(news_item.id,))
    response = client.post(url, data={'text': 'Текст комментария'})
    assert response.status_code == HTTPStatus.FOUND


@pytest.mark.django_db
def test_authorized_user_can_post_comment(author_client):
    """Авторизованный пользователь может отправить комментарий."""
    news_item = News.objects.create(title='Заголовок',
                                    text='Текст')
    url = reverse('news:detail', args=(news_item.id,))
    response = author_client.post(url,
                                  data={'text': 'Текст комментария'})
    assert response.status_code == HTTPStatus.FOUND
    assert Comment.objects.filter(news=news_item,
                                  text='Текст комментария').exists()


@pytest.mark.django_db
def test_comment_contains_bad_words(author_client):
    """Если комментарий содержит запрещённые слова, он не будет опубликован."""
    news_item = News.objects.create(title='Заголовок', text='Текст')
    url = reverse('news:detail', args=(news_item.id,))
    response = author_client.post(url, data={'text': 'Ты редиска!'})
    assert response.status_code == HTTPStatus.OK
    assert not Comment.objects.filter(news=news_item,
                                      text='Ты редиска!').exists()


@pytest.mark.django_db
def test_author_can_edit_own_comment(author_client, author):
    """Авторизованный пользователь может редактировать свои комментарии."""
    news_item = News.objects.create(title='Заголовок',
                                    text='Текст')
    comment = Comment.objects.create(news=news_item,
                                     author=author,
                                     text='Текст комментария')
    url = reverse('news:edit', args=(comment.id,))
    response = author_client.post(
        url,
        data={'text': 'Обновленный текст комментария'}
    )
    assert response.status_code == HTTPStatus.FOUND
    comment.refresh_from_db()
    assert comment.text == 'Обновленный текст комментария'


@pytest.mark.django_db
def test_author_cannot_edit_other_comment(author_client,
                                          reader_client,
                                          reader):
    """Авторизованный пользователь не может редактировать
    чужие комментарии.
    """
    news_item = News.objects.create(title='Заголовок',
                                    text='Текст')
    comment = Comment.objects.create(news=news_item,
                                     author=reader,
                                     text='Текст комментария')

    response = author_client.post(reverse('news:edit', args=(comment.id,)),
                                  {'text': 'Измененный текст'})

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == (
        f'{reverse("news:detail", args=(news_item.id,))}#comments'
    )
