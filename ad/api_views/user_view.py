import base64
import logging

import json
from json import JSONDecodeError

from django.db.utils import IntegrityError
from django.http.response import JsonResponse

from ..error_msg import *
from ..models import AdminUser, UserChannel
from ..utils.decorators import *
from .channel_view import get_channel_dict

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
        "username": username,
        "id": user.id,
        "role": user.role
    })


def logout(request):
    try:
        del request.session["user_id"]
    except Exception as e:
        logger.error(repr(e))
    return JsonResponse(success)


@need_login()
@need_access()
def get(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        page_idx = int(data["currentPageNum"])
        page_size = int(data["pageSize"])
        query_key = data.get("key")
    except JSONDecodeError as e:
        logger.error(repr(e))
        return JsonResponse(json_format_error)
    except KeyError as e:
        logger.error(repr(e))
        return JsonResponse(lack_param_error)
    except ValueError as e:
        logger.error(repr(e))
        return JsonResponse(param_format_error)
    if not query_key:
        users = AdminUser.objects.all()
    else:
        users = AdminUser.objects.filter(username__contains=query_key)
    total = len(users)
    users = users.order_by('-id')[(page_idx - 1) * page_size: page_idx * page_size]
    result = {
        "status": 0,
        "msg": "success",
        "total": total,
        "currentPageNum": page_idx,
        "pageSize": page_size,
        "data": [],
    }
    for u in users:
        result["data"].append({
            "id": u.id,
            "name": u.username,
            "role": u.role,
            "channels":[get_channel_dict(uc.channel_id) for uc in UserChannel.objects.filter(user_id=u.id)],
        })
    return JsonResponse(result)


@need_login()
@need_access()
def get_by_id(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        idx = int(data["user_id"])
        print(idx)
        user = AdminUser.objects.get(id=idx)
    except JSONDecodeError as e:
        logger.error(repr(e))
        return JsonResponse(json_format_error)
    except KeyError as e:
        logger.error(repr(e))
        return JsonResponse(lack_param_error)
    except ValueError as e:
        logger.error(repr(e))
        return JsonResponse(param_format_error)
    except Exception as e:
        logger.error(repr(e))
        return JsonResponse(data_not_exist_error)

    return JsonResponse({
        "status": 0,
        "msg": "success",
        "user_id": idx,
        "role": user.role,
        "channels": [get_channel_dict(uc.channel_id) for uc in UserChannel.objects.filter(user_id=user.id)]
    })


@need_login()
@need_access()
def add(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        print(data)
        username = data.get("username")
        password = data.get("password")
        role = data.get("role")
        channel_ids = [int(i) for i in data["channel_ids"]]
        username = base64.b64decode(username).decode("utf-8")
        password = base64.b64decode(password).decode("utf-8")
        print("get data")

    except JSONDecodeError as e:
        logger.error(repr(e))
        return JsonResponse(json_format_error)
    except KeyError as e:
        logger.error(repr(e))
        return JsonResponse(lack_param_error)
    except ValueError as e:
        logger.error(repr(e))
        return JsonResponse(param_format_error)
    except Exception as e:
        logger.error(repr(e))
        return JsonResponse(param_repeat_error)

    if username and password and role:
        try:
            id = _create_user(username, password, role)
        except IntegrityError as e:
            logger.error(repr(e))
            return JsonResponse(param_repeat_error)
        if channel_ids:
            _create_user_channel(id, channel_ids)
    else:
        return JsonResponse(lack_param_error)

    return JsonResponse({
        "status": 0,
        "msg": "创建用户成功",
        "user_id": id
    })


@need_login()
@need_access()
def delete(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        idxs = [int(i) for i in data["ids"]]
        AdminUser.objects.filter(id__in=idxs).delete()
        UserChannel.objects.filter(user_id__in=idxs).delete()

    except JSONDecodeError as e:
        logger.error(repr(e))
        return JsonResponse(json_format_error)
    except KeyError as e:
        logger.error(repr(e))
        return JsonResponse(lack_param_error)
    except ValueError as e:
        logger.error(repr(e))
        return JsonResponse(param_format_error)
    except Exception as e:
        logger.error(repr(e))
        return JsonResponse(data_not_exist_error)
    return JsonResponse({
        "status": 0,
        "msg": "删除数据成功",
    })

@need_login()
@need_access()
def update(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        idx = int(data["user_id"])
        ch_ids = [int(i) for i in data["channel_ids"]]
    except JSONDecodeError as e:
        logger.error(repr(e))
        return JsonResponse(json_format_error)
    except KeyError as e:
        logger.error(repr(e))
        return JsonResponse(lack_param_error)
    except ValueError as e:
        logger.error(repr(e))
        return JsonResponse(param_format_error)
    except Exception as e:
        logger.error(repr(e))
        return JsonResponse(data_not_exist_error)

    # 增加没有的频道
    _create_user_channel(idx, ch_ids)
    # 删除不需要的频道
    UserChannel.objects.filter(user_id=idx).exclude(channel_id__in=ch_ids).delete()

    return JsonResponse({
        "status": 0,
        "msg": "更新数据成功",
        "user_id": idx
    })


def _create_user(username, password, role):
    user = AdminUser(username=username, password=password, role=role)
    user.save()
    return user.id


def _create_user_channel(user_id, channel_ids):
    for c in channel_ids:
        try:
            uc = UserChannel(user_id=user_id, channel_id=c)
            uc.save()
        except IntegrityError as e:
            logger.debug(e)


def access_error(request):
    return JsonResponse(
        user_access_error
    )


def need_login_msg(request):
    return JsonResponse(user_not_login)
