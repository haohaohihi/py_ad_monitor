import logging

from django.http import HttpResponseRedirect

logger = logging.getLogger("ad")


def need_login(func, redirect_url="/api/user/need_login"):
    def wrapper(*args, **kwargs):
        try:
            print(args)
            user_id = args[0].session["user_id"]
            print(user_id)
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(repr(e))
            return HttpResponseRedirect(redirect_url)

    return wrapper
