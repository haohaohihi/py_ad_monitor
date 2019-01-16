import json
import logging
from json import JSONDecodeError

from django.db import IntegrityError
from django.http import HttpResponse, JsonResponse

from ad.utils.decorators import need_login
from ..models import ChannelProgram

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
    programs = ChannelProgram.objects.filter(channel_id=channel_id, valid=1).order_by('weekday', 'start_time')
    data = []
    for c in programs:
        data.append({
            "scopeId": c.id,
            "weekDay": c.weekday,
            "name": c.name,
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
        exist_program = ChannelProgram.objects.filter(channel_id=data.get("channelId"), weekday=data.get("weekDay"),
                                                      name=data.get("name"), start_time=data.get("startTime"), valid=0)
        if exist_program:
            # 处理删除后创建新的，然后再删除时，由于unique约束导致的失败
            program = exist_program[0]
            program.valid = 1
        elif not (data.get("channelId") and data.get("weekDay") and data.get("name") and data.get("startTime") and data.get("endTime")):
            return JsonResponse(lack_param_error)
        else:
            program = ChannelProgram(channel_id=data.get("channelId"), weekday=data.get("weekDay"),
                                     name=data.get("name"), start_time=data.get("startTime"),
                                    end_time=data.get("endTime"), stage1=data.get("stage1"),
                                    stage2=data.get("stage2"), stage3=data.get("stage3"))

        program.save()
    except JSONDecodeError as e:
        logger.error(repr(e))
        return JsonResponse(json_format_error)
    except IntegrityError as e:
        logger.error(repr(e))
        if "Duplicate" in str(e):
            return JsonResponse(param_repeat_error)
        return JsonResponse(lack_param_error)
    return JsonResponse({
        "id": program.id,
        "status": 0,
        "msg": "创建数据成功"
    })


@need_login()
def update(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        idx = int(data["scopeId"])
        program = ChannelProgram.objects.filter(valid=1).get(id=idx)
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
    program.weekday = data.get("weekDay") or program.weekday
    program.name = data.get("name") or program.name
    program.start_time = data.get("startTime") or program.start_time
    program.end_time = data.get("endTime") or program.end_time
    program.stage1 = data.get("stage1") or program.stage1
    program.stage2 = data.get("stage2") or program.stage2
    program.stage3 = data.get("stage3") or program.stage3
    program.save()
    return JsonResponse({
        "status": 0,
        "msg": "更新数据成功",
        "id": program.id
    })


@need_login()
def delete(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        idxs = [int(i) for i in data.get("scopeIds")]
        programs = ChannelProgram.objects.filter(id__in=idxs, valid=1)
        result_idxs = []
        for c in programs:
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
