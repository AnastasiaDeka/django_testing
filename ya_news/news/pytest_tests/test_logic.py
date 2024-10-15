import pytest
from http import HTTPStatus
from django.urls import reverse
from news.models import Comment


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(client, news, comment_form_data):
    """Анонимный пользователь не может отправить комментарий."""
    url = reverse('news:detail', args=(news.first().id,))
    response = client.post(url, data=comment_form_data)
    assert Comment.objects.count() == 0
    assert response.status_code in [HTTPStatus.FOUND, HTTPStatus.OK]


@pytest.mark.django_db
def test_authorized_user_can_create_comment(author_client,
                                            news,
                                            comment_form_data):
    """Авторизованный пользователь может отправить комментарий."""
    url = reverse('news:detail', args=(news.first().id,))
    response = author_client.post(url, data=comment_form_data)
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == f'{url}#comments'
    assert Comment.objects.count() == 1
    comment = Comment.objects.get()
    assert comment.text == comment_form_data['text']


@pytest.mark.django_db
def test_user_cant_use_bad_words(author_client, news, bad_words_form_data):
    """Если комментарий содержит запрещённые слова, он не будет опубликован."""
    url = reverse('news:detail', args=(news.first().id,))
    response = author_client.post(url, data=bad_words_form_data)

    assert 'form' in response.context
    if 'form' in response.context:
        assert 'text' in response.context['form'].errors
        assert response.context['form'].errors['text'] == ['Не ругайтесь!']
    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_author_can_edit_comment(author_client,
                                 comment,
                                 new_comment_form_data):
    """Авторизованный пользователь может редактировать свои комментарии."""
    author_client.force_login(comment.author)
    url = reverse('news:edit', args=(comment.id,))
    response = author_client.post(url, data=new_comment_form_data)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == (
        f'{reverse("news:detail", args=(comment.news.id,))}#comments'
    )

    comment.refresh_from_db()
    assert comment.text == new_comment_form_data['text']


@pytest.mark.django_db
def test_author_can_delete_comment(author_client, comment):
    """Авторизованный пользователь может удалять свои комментарии."""
    author_client.force_login(comment.author)
    url = reverse('news:delete', args=(comment.id,))
    news_detail_url = reverse('news:detail',
                              args=(comment.news.id,)) + '#comments'

    comments_before = Comment.objects.count()
    response = author_client.post(url)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == news_detail_url

    with pytest.raises(Comment.DoesNotExist):
        Comment.objects.get(pk=comment.id)

    comments_after = Comment.objects.count()
    assert comments_after == comments_before - 1


@pytest.mark.django_db
def test_user_cant_edit_comment_of_another_user(not_author_client,
                                                comment,
                                                new_comment_form_data):
    """Авторизованный пользователь не может редактировать чужие комментарии."""
    url = reverse('news:edit', args=(comment.id,))
    response = not_author_client.post(url, data=new_comment_form_data)
    assert response.status_code in [HTTPStatus.FORBIDDEN, HTTPStatus.NOT_FOUND]
    comment.refresh_from_db()
    assert comment.text == 'Текст комментария'


@pytest.mark.django_db
def test_user_cant_delete_comment_of_another_user(not_author_client, comment):
    """Авторизованный пользователь не может удалять чужие комментарии."""
    url = reverse('news:delete', args=(comment.id,))
    response = not_author_client.post(url)
    assert response.status_code in [HTTPStatus.FORBIDDEN, HTTPStatus.NOT_FOUND]
    assert Comment.objects.count() == 1
