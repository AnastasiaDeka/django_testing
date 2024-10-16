from http import HTTPStatus

import pytest
from django.urls import reverse

from news.models import Comment

COMMENT_TEXT = 'Текст комментария'
NEW_COMMENT_TEXT = 'Обновлённый комментарий'
BAD_WORDS = ('редиска', 'негодяй')
WARNING = 'Не ругайтесь!'
COMMENTS_REDIRECT = '#comments'
FORM_DATA = {'text': COMMENT_TEXT}
NEW_FORM_DATA = {'text': NEW_COMMENT_TEXT}
BAD_WORDS_FORM_DATA = {'text': BAD_WORDS[0]}

pytestmark = pytest.mark.django_db


def test_anonymous_user_cant_create_comment(client, news_detail_url):
    """Проверяем, что анонимный пользователь не может создать комментарий."""
    response = client.post(news_detail_url, data=FORM_DATA)

    assert Comment.objects.count() == 0
    assert response.status_code == HTTPStatus.FOUND


def test_authorized_user_can_create_comment(author, author_client, news):
    """Авторизованный пользователь может отправить комментарий."""
    url = reverse('news:detail', args=(news.id,))
    comments_before = Comment.objects.count()
    response = author_client.post(url, data=FORM_DATA)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == f'{url}{COMMENTS_REDIRECT}'

    comments_after = Comment.objects.count()
    assert (comments_after - comments_before) == 1

    comment = Comment.objects.last()
    assert comment.text == COMMENT_TEXT
    assert comment.author == author
    assert comment.news == news
    assert comment.created is not None


@pytest.mark.parametrize("bad_word", BAD_WORDS)
def test_user_cant_use_bad_words(author_client,
                                 news_detail_url, bad_word):
    """Проверяем, что пользователь не может
    использовать запрещенные слова в комментарии.
    """
    form_data = {'text': f'Текст с {bad_word}'}
    response = author_client.post(news_detail_url, data=form_data)

    assert 'form' in response.context
    assert 'text' in response.context['form'].errors
    assert response.context['form'].errors['text'] == [WARNING]
    assert Comment.objects.count() == 0


def test_author_can_edit_comment(author_client, comment):
    """Проверяем, что автор комментария может его редактировать."""
    url = reverse('news:edit', args=(comment.id,))
    response = author_client.post(url, data=NEW_FORM_DATA)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == (
        f'{reverse("news:detail", args=(comment.news.id,))}'
        f'{COMMENTS_REDIRECT}'
    )

    comment.refresh_from_db()
    assert comment.text == NEW_COMMENT_TEXT


def test_author_can_delete_comment(author_client, comment):
    """Проверяем, что автор комментария может его удалить."""
    url = reverse('news:delete', args=(comment.id,))
    response = author_client.post(url)

    assert response.status_code == HTTPStatus.FOUND
    assert Comment.objects.filter(pk=comment.id).count() == 0


def test_user_cant_edit_comment_of_another_user(not_author_client, comment):
    """Проверяем, что пользователь не может
    редактировать комментарий другого пользователя.
    """
    old_text = comment.text
    url = reverse('news:edit', args=(comment.id,))
    response = not_author_client.post(url, data=NEW_FORM_DATA)

    assert response.status_code == HTTPStatus.NOT_FOUND
    comment.refresh_from_db()
    assert comment.text == old_text


def test_user_cant_delete_comment_of_another_user(not_author_client, comment):
    """Проверяем, что пользователь не может
    удалить комментарий другого пользователя.
    """
    url = reverse('news:delete', args=(comment.id,))
    response = not_author_client.post(url)

    assert response.status_code == HTTPStatus.NOT_FOUND
