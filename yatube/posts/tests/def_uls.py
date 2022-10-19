from django.urls import reverse


def INDEX_URL():
    return reverse('posts:index')


def GROUP_URL(GROUP_SLUG):
    return reverse('posts:group_list', kwargs={'slug': GROUP_SLUG})


def PROFILE_URL(USER_NAME):
    return reverse('posts:profile', kwargs={'username': USER_NAME})


def POST_URL(POST_ID):
    return reverse('posts:post_detail', kwargs={'post_id': POST_ID})


def POST_EDIT_URL(POST_ID):
    return reverse('posts:post_edit', kwargs={'post_id': POST_ID})


def POST_CREATE_URL():
    return reverse('posts:post_create')


def LOGIN_URL():
    return reverse('login') + '?next='


def NONE_URL():
    return '/unexisting_page/'


def COMMENT_URL(POST_ID):
    return reverse('posts:add_comment', kwargs={'post_id': POST_ID})


def FOLLOW_INDEX_URL():
    return reverse('posts:follow_index')


def FOLLOW_URL(USER_NAME):
    return reverse('posts:profile_follow', kwargs={'username': USER_NAME})


def UNFOLLOW_URL(USER_NAME):
    return reverse('posts:profile_unfollow', kwargs={'username': USER_NAME})
