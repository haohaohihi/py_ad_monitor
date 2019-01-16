import json
import logging
from json import JSONDecodeError

from django.db import IntegrityError
from django.http import HttpResponse, JsonResponse

from ad.utils.decorators import need_login
from ..models import ChannelAdCharge

logger = logging.getLogger("ad")
from ..error_msg import *


# Create your views here.


@need_login()
def get(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        channel_id = int(data["channelId"])
    except JSONDecodeError as e:
        logger.error(repr(e))
        return JsonResponse(json_format_error)
    except KeyError as e:
        logger.error(repr(e))
        return JsonResponse(lack_param_error)
    except ValueError as e:
        logger.error(repr(e))
        return JsonResponse(param_format_error)
    charges = ChannelAdCharge.objects.filter(channel_id=channel_id, valid=1).order_by('-id')
    data = []
    for c in charges:
        data.append({
            "scopeId": c.id,
            "weekDay": c.weekday,
            "proBefore": c.pro_before,
            "proAfter": c.pro_after,
            "startTime": c.start_time,
            "endTime": c.end_time,
            "stage1": c.stage1,
            "stage2": c.stage2,
            "stage3": c.stage3
        })
    return JsonResponse({
        "status": 0,
        "msg": "success",
        "data": data
    })


def get_by_id(request):
    return HttpResponse("get by id")


@need_login()
def add(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        exist_charge = ChannelAdCharge.objects.filter(channel_id=data.get("channelId"), weekday=data.get("weekDay"),
                                                      start_time=data.get("startTime"), end_time=data.get("endTime"),
                                                      valid=0)
        if exist_charge:
            # 处理删除后创建新的，然后再删除时，由于unique约束导致的失败
            charge = exist_charge[0]
            charge.valid = 1
        else:
            charge = ChannelAdCharge(channel_id=data.get("channelId"), weekday=data.get("weekDay"),
                                     pro_before=data.get("proBefore"), pro_after=data.get("proAfter"),
                                     start_time=data.get("startTime"), end_time=data.get("endTime"),
                                     stage1=data.get("stage1"), stage2=data.get("stage2"),
                                     stage3=data.get("stage3"))
        charge.save()
    except JSONDecodeError as e:
        logger.error(repr(e))
        return JsonResponse(json_format_error)
    except IntegrityError as e:
        logger.error(repr(e))
        if "Duplicate" in str(e):
            return JsonResponse(param_repeat_error)
        return JsonResponse(lack_param_error)
    return JsonResponse({
        "id": charge.id,
        "status": 0,
        "msg": "创建数据成功"
    })


@need_login()
def update(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        idx = int(data["scopeId"])
        charge = ChannelAdCharge.objects.filter(valid=1).get(id=idx)
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
    charge.weekday = data.get("weekDay") or charge.weekday
    charge.pro_before = data.get("proBefore") or charge.pro_before
    charge.pro_after = data.get("proAfter") or charge.pro_after
    charge.start_time = data.get("startTime") or charge.start_time
    charge.end_time = data.get("endTime") or charge.end_time
    charge.stage1 = data.get("stage1") or charge.stage1
    charge.stage2 = data.get("stage2") or charge.stage2
    charge.stage3 = data.get("stage3") or charge.stage3
    charge.save()
    return JsonResponse({
        "status": 0,
        "msg": "更新数据成功",
        "id": charge.id
    })


@need_login()
def delete(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        idxs = [int(i) for i in data.get("scopeIds")]
        charges = ChannelAdCharge.objects.filter(id__in=idxs, valid=1)
        result_idxs = []
        for c in charges:
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
