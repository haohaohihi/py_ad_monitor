import logging
from functools import wraps

from django.http import HttpResponseRedirect
from ..models import AdminUser, Channel
from ..user_roles import USER_ADMIN

logger = logging.getLogger("ad")


def need_login(redirect_url="/api/user/need_login"):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                user_id = args[0].session["user_id"]
                print("need_login", user_id)
                return func(*args, **kwargs)
            except KeyError as e:
                logger.error(repr(e))
                return HttpResponseRedirect(redirect_url)
        return wrapper
    return decorator

# def need_login(func, redirect_url="/api/user/need_login"):
#     def wrapper(*args, **kwargs):
#         try:
#             user_id = args[0].session["user_id"]
#             print("need_login", user_id)
#             return func(*args, **kwargs)
#         except Exception as e:
#             logger.error(repr(e))
#             return HttpResponseRedirect(redirect_url)
#
#     return wrapper



def need_access(redirect_url="/api/user/access_error", user_role=USER_ADMIN):
    def decorator(func):
        def wrapper(*args, **kwargs):
            user_id = args[0].session["user_id"]
            print("need_access", user_id)
            user = AdminUser.objects.get(id=user_id)
            if user.role >= user_role:
                return func(*args, **kwargs)
            else:
                return HttpResponseRedirect(redirect_url)
        return wrapper
    return decorator