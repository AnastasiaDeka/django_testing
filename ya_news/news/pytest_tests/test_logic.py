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


def test_anonymous_user_cant_create_comment(client, news):
    url = reverse('news:detail', args=(news.first().id,))
    response = client.post(url, data=FORM_DATA)

    assert Comment.objects.count() == 0
    assert response.status_code == HTTPStatus.FOUND


def test_authorized_user_can_create_comment(author_client, news):
    url = reverse('news:detail', args=(news.first().id,))
    response = author_client.post(url, data=FORM_DATA)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == f'{url}{COMMENTS_REDIRECT}'
    assert Comment.objects.count() == 1

    comment = Comment.objects.get()
    assert comment.text == COMMENT_TEXT


@pytest.mark.parametrize("bad_word", BAD_WORDS)
def test_user_cant_use_bad_words(author_client, news, bad_word):
    form_data = {'text': f'Текст с {bad_word}'}
    url = reverse('news:detail', args=(news.first().id,))
    response = author_client.post(url, data=form_data)

    assert 'form' in response.context
    assert 'text' in response.context['form'].errors
    assert response.context['form'].errors['text'] == [WARNING]
    assert Comment.objects.count() == 0


def test_author_can_edit_comment(author_client, comment):
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
    url = reverse('news:delete', args=(comment.id,))
    news_detail_url = (
        f'{reverse("news:detail", args=(comment.news.id,))}'
        f'{COMMENTS_REDIRECT}'
    )

    comments_before = Comment.objects.count()
    response = author_client.post(url)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == news_detail_url

    with pytest.raises(Comment.DoesNotExist):
        Comment.objects.get(pk=comment.id)

    assert Comment.objects.count() == comments_before - 1


def test_user_cant_edit_comment_of_another_user(not_author_client, comment):
    url = reverse('news:edit', args=(comment.id,))
    response = not_author_client.post(url, data=NEW_FORM_DATA)

    assert response.status_code == HTTPStatus.NOT_FOUND
    comment.refresh_from_db()
    assert comment.text == COMMENT_TEXT


def test_user_cant_delete_comment_of_another_user(not_author_client, comment):
    url = reverse('news:delete', args=(comment.id,))
    response = not_author_client.post(url)

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert Comment.objects.count() == 1
