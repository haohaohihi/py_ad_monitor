import json
import logging
from json.decoder import JSONDecodeError

from django.db import IntegrityError
from django.http import JsonResponse

from ad.utils.decorators import need_login
from ..error_msg import *
from ..models import Channel

logger = logging.getLogger("ad")


# Create your views here.

@need_login()
def get(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        page_idx = int(data["currentPageNum"])
        page_size = int(data["pageSize"])
    except JSONDecodeError as e:
        logger.error(repr(e))
        return JsonResponse(json_format_error)
    except KeyError as e:
        logger.error(repr(e))
        return JsonResponse(lack_param_error)
    except ValueError as e:
        logger.error(repr(e))
        return JsonResponse(param_format_error)

    # 在valide=1（表示存在）的数据中进行下一步过滤
    channels = Channel.objects.filter(valid=1).order_by('-id')
    if data.get("name") and data.get("name")[0]:
        channel_name = data.get("name")[0]
        channels = channels.filter(name__icontains=channel_name)
    if data.get("area"):
        channels = channels.filter(area__in=data.get("area"))
    if data.get("province"):
        channels = channels.filter(province__in=data.get("province"))
    if data.get("city"):
        channels = channels.filter(city__in=data.get("city"))
    if data.get("coverArea"):
        channels = channels.filter(cover_area__in=data.get("coverArea"))
    if data.get("coverProvince"):
        channels = channels.filter(cover_province__in=data.get("coverProvince"))
    if data.get("coverCity"):
        channels = channels.filter(cover_city__in=data.get("coverCity"))
    # total = math.ceil(len(channels) / page_size)
    total = len(channels)
    channels = channels.order_by('-id')[(page_idx - 1) * page_size: page_idx * page_size]
    result = {
        "status": 0,
        "msg": "success",
        "total": total,
        "currentPageNum": page_idx,
        "pageSize": page_size,
        "data": [],
    }

    for channel in channels:
        result["data"].append({
            "id": channel.id,
            "name": channel.name,
            "area": channel.area,
            "province": channel.province,
            "city": channel.city,
            "coverArea": channel.cover_area,
            "coverProvince": channel.cover_province,
            "coverCity": channel.cover_city
        })
    return JsonResponse(result)


@need_login()
def get_by_id(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        idx = int(data["id"])
        print(idx)
        channel = Channel.objects.filter(valid=1).get(id=idx)

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
        "data": {
            "id": channel.id,
            "name": channel.name,
            "area": channel.area,
            "province": channel.province,
            "city": channel.city,
            "coverArea": channel.cover_area,
            "coverProvince": channel.cover_province,
            "coverCity": channel.cover_city
        }
    })


@need_login()
def add(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        exist_channel = Channel.objects.filter(name=data.get("name"), valid=0)
        if exist_channel:
            # 处理删除后创建新的，然后再删除时，由于unique约束导致的失败
            channel = exist_channel[0]
            channel.valid = 1
        else:
            channel = Channel(name=data.get("name"), area=data.get("area"), province=data.get("province"),
                              city=data.get("city"), cover_area=data.get("coverArea"),
                              cover_province=data.get("coverProvince"), cover_city=data.get("coverCity"))
        channel.save()
    except JSONDecodeError as e:
        logger.error(repr(e))
        return JsonResponse(json_format_error)
    except IntegrityError as e:
        logger.error(repr(e))
        if "Duplicate" in str(e):
            return JsonResponse(param_repeat_error)
        return JsonResponse(lack_param_error)
    return JsonResponse({
        "id": channel.id,
        "status": 0,
        "msg": "创建数据成功"
    })


@need_login()
def update(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        idx = int(data["id"])
        channel = Channel.objects.filter(valid=1).get(id=idx)
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
    channel.name = data.get("name") or channel.name
    channel.area = data.get("area") or channel.area
    channel.province = data.get("province") or channel.province
    channel.city = data.get("city") or channel.city
    channel.cover_area = data.get("coverArea") or channel.cover_area
    channel.cover_province = data.get("coverProvince") or channel.cover_province
    channel.cover_city = data.get("coverCity") or channel.cover_city
    channel.save()
    return JsonResponse({
        "status": 0,
        "msg": "更新数据成功",
        "id": channel.id
    })


@need_login()
def delete(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        idxs = [int(i) for i in data["ids"]]
        channels = Channel.objects.filter(id__in=idxs, valid=1)
        result_idxs = []
        for c in channels:
            c.valid = 0
            c.save()
            result_idxs.append(c.id)
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
        "id": result_idxs
    })


def get_channel_dict(channel_id):
    try:
        channel = Channel.objects.get(id=channel_id)
        return {
            "id": channel.id,
            "name": channel.name,
        }
    except Exception as e:
        logger.error(repr(e))
        return None
