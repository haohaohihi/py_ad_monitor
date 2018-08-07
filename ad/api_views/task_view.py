import json
import logging
import os
from json import JSONDecodeError

import math
import time
import datetime
from django.db import IntegrityError, transaction
from django.http import HttpResponse, JsonResponse
from ..models import Task, Monitor, Channel
from ..error_msg import *

logger = logging.getLogger("ad")


def get(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        date = data["date"]
    except JSONDecodeError as e:
        logger.error(repr(e))
        return JsonResponse(json_format_error)
    except KeyError as e:
        logger.error(repr(e))
        return JsonResponse(lack_param_error)
    tasks = Task.objects.all()
    valid_tasks = []
    for t in tasks:
        if t.create_time and time.strftime("%Y-%m-%d",
                                           time.localtime(int(t.create_time))) == date and t.type != "refclip":
            valid_tasks.append(t)
    data = []
    for t in valid_tasks:
        data.append({
            "id": t.id,
            "channel": Channel.objects.get(id=t.channel_id).name,
            "type": t.type,
            "is_running": t.is_running,
            "nas_Ip": t.nas_ip,
            "startTime": t.start_time,
            "endTime": t.end_time,
            "ts_ip": t.ts_ip,
            "port": t.ts_port
        })
    return JsonResponse({
        "status": 0,
        "msg": "success",
        "data": data
    })


def add(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        print(data)
        m_type = data.get("type")
        # 获取空闲的monitor
        monitors = Monitor.objects.filter(type=m_type, has_task=0)
        if not monitors:
            return JsonResponse(not_enough_monitor)
        monitor = monitors[0]

        # 获取任务的频道
        channels = Channel.objects.filter(name=data.get("channel"))
        if not channels:
            return JsonResponse(channel_not_found)
        channel = channels[0]

        with transaction.atomic():
            task = Task(is_running=0, channel_id=channel.id, monitor_id=monitor.id, type=m_type,
                        nas_ip=data.get("nas_Ip"), start_time=data.get("startTime"), end_time=data.get("endTime"),
                        ts_ip=data.get("ts_ip"), ts_port=data.get("port"), create_time=int(time.time()))
            monitor.channel = channel.name
            monitor.has_task = 1
            monitor.save()
            task.save()

    except JSONDecodeError as e:
        logger.error(repr(e))
        return JsonResponse(json_format_error)
    except IntegrityError as e:
        logger.error(repr(e))
        if "Duplicate" in str(e):
            return JsonResponse(param_repeat_error)
        return JsonResponse(lack_param_error)
    return JsonResponse({
        "id": task.id,
        "status": 0,
        "msg": "创建数据成功"
    })


def cancel(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        idx = int(data["id"])
        task = Task.objects.get(id=idx)
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
    task.is_running = 3
    task.save()
    return JsonResponse({
        "status": 0,
        "msg": "success",
        "id": task.id
    })
