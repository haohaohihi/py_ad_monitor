import base64
import logging

from django.http.response import JsonResponse

from ..error_msg import *
from ..models import AdminUser

logger = logging.getLogger("ad")


def login(request):
    try:
        username = request.POST['username']
        password = request.POST['password']
    except Exception as e:
        return JsonResponse(lack_param_error)

    username = base64.b64decode(username).decode("utf-8")
    password = base64.b64decode(password).decode("utf-8")
    print(username, password)

    try:
        user = AdminUser.objects.get(username=username, password=password)
    except Exception as e:
        print(e)
        return JsonResponse(user_not_found)

    request.session['user_id'] = user.id
    request.session.set_expiry(2 * 60 * 60)  # seesion有效期2个小时
    return JsonResponse({
        "status": 0,
        "msg": "success",
        "user": username
    })


def logout(request):
    try:
        del request.session["user_id"]
    except Exception as e:
        logger.error(repr(e))
    return JsonResponse(success)


def need_login_msg(request):
    return JsonResponse(user_not_login)
