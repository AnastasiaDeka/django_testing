from http import HTTPStatus

import pytest
from pytest_django.asserts import assertRedirects
from pytest_django.asserts import assertFormError

from news.forms import BAD_WORDS, WARNING
from news.models import Comment

COMMENT_TEXT = 'Текст комментария'
NEW_COMMENT_TEXT = 'Обновлённый комментарий'
COMMENTS_REDIRECT = '#comments'
FORM_DATA = {'text': COMMENT_TEXT}
NEW_FORM_DATA = {'text': NEW_COMMENT_TEXT}

pytestmark = pytest.mark.django_db


def test_anonymous_user_cant_create_comment(client, news_detail_url):
    """Проверяем, что анонимный
    пользователь не может создать комментарий.
    """
    response = client.post(news_detail_url, data=FORM_DATA)

    assert Comment.objects.count() == 0
    assert response.status_code == HTTPStatus.FOUND


def test_authorized_user_can_create_comment(author,
                                            author_client,
                                            news_detail_url,
                                            news_detail):
    """Авторизованный пользователь может отправить комментарий."""
    comments_before = Comment.objects.count()
    response = author_client.post(news_detail_url, data=FORM_DATA)

    assert response.status_code == HTTPStatus.FOUND
    assertRedirects(response, f'{news_detail_url}{COMMENTS_REDIRECT}')
    comments_after = Comment.objects.count()
    assert (comments_after - comments_before) == 1

    comment = Comment.objects.last()

    assert comment.text == FORM_DATA['text']
    assert comment.author == author
    assert comment.news == news_detail


@pytest.mark.parametrize("bad_word", BAD_WORDS)
def test_user_cant_use_bad_words(author_client,
                                 news_detail_url,
                                 bad_word):
    """Проверяем, что пользователь не может
    использовать запрещенные слова в комментарии.
    """
    form_data = {'text': f'Текст с {bad_word}'}
    response = author_client.post(news_detail_url, data=form_data)

    assertFormError(response, 'form', 'text', WARNING)
    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_author_can_edit_comment(author_client,
                                 comment,
                                 edit_comment_url,
                                 news_detail_url):
    """Проверяем, что автор комментария может его редактировать."""
    response = author_client.post(edit_comment_url, data=NEW_FORM_DATA)

    expected_url = f'{news_detail_url}#comments'
    assertRedirects(response, expected_url)

    comment.refresh_from_db()

    assert comment.text == NEW_FORM_DATA['text']


def test_author_can_delete_comment(author_client,
                                   delete_comment_url,
                                   comment):
    """Проверяем, что автор комментария может его удалить."""
    response = author_client.post(delete_comment_url)

    assert response.status_code == HTTPStatus.FOUND
    assert Comment.objects.count() == 0


def test_user_cant_edit_comment_of_another_user(not_author_client,
                                                edit_comment_url,
                                                comment):
    """Проверяем, что пользователь не может редактировать
    комментарий другого пользователя.
    """
    old_text = comment.text
    response = not_author_client.post(edit_comment_url, data=NEW_FORM_DATA)

    assert response.status_code == HTTPStatus.NOT_FOUND
    comment.refresh_from_db()
    assert comment.text == old_text


def test_user_cant_delete_comment_of_another_user(not_author_client,
                                                  delete_comment_url,
                                                  comment):
    """Проверяем, что пользователь не может
    удалить комментарий другого пользователя.
    """
    comments_before = Comment.objects.count()
    response = not_author_client.post(delete_comment_url)

    assert response.status_code == HTTPStatus.NOT_FOUND
    comments_after = Comment.objects.count()
    assert comments_before == comments_after
