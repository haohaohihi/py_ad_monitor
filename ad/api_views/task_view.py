import json
import logging
import time
from json import JSONDecodeError

from django.db import IntegrityError, transaction
from django.http import JsonResponse

from ..error_msg import *
from ..models import Task, Monitor, Channel
from ..utils.decorators import need_login

logger = logging.getLogger("ad")


@need_login()
def get(request):
    # print(request.session["user_id"])
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
        print(t.create_time)
        print(time.strftime("%Y-%m-%d", time.localtime(int(t.create_time))))
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
            "port": t.ts_port,
            "create_time": t.create_time
        })
    return JsonResponse({
        "status": 0,
        "msg": "success",
        "data": data
    })


@need_login()
def add(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        # print(data.get("startTime"))
        m_type = data.get("type")
        # print(m_type)
        # 获取空闲的monitor
        monitors = Monitor.objects.filter(type=m_type, has_task=0, problem=0)
        if not monitors:
            return JsonResponse(not_enough_monitor)
        monitor = monitors[0]

        # 获取任务的频道
        channels = Channel.objects.filter(name=data.get("channel"))
        if not channels:
            return JsonResponse(channel_not_found)
        channel = channels[0]

        existed_tasks = Task.objects.filter(channel_id=channel.id, type=m_type, nas_ip=data.get("nas_Ip"), is_running__in=[0, 1, 3, 6])

        if len(existed_tasks) > 0:
            return JsonResponse({
                "id": existed_tasks[0].id,
                "status": -401,
                "msg": "已有相同任务在处理中"
            })

        with transaction.atomic():
            task = Task(is_running=0, channel_id=channel.id, monitor_id=monitor.id, type=m_type,
                        nas_ip=data.get("nas_Ip") if data.get("nas_Ip") else None,
                        start_time=data.get("startTime") if m_type == "matchclip" and data.get("startTime") else None,
                        end_time=data.get("endTime") if m_type == "matchclip" and data.get("endTime") else None,
                        ts_ip=data.get("ts_ip") if data.get("ts_ip") else None,
                        ts_port=data.get("port") if data.get("port") else None,
                        create_time=int(time.time()))
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


@need_login()
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


# @need_login
def get_all_running(request):
    all = Task.objects.filter(is_running__in=[0, 1, 3, 6])
    data = []
    for t in all:
        data.append({
            "id": t.id,
            "channel": Channel.objects.get(id=t.channel_id).name,
            "type": t.type,
            "is_running": t.is_running,
            "nas_Ip": t.nas_ip,
            "startTime": t.start_time,
            "endTime": t.end_time,
            "ts_ip": t.ts_ip,
            "port": t.ts_port,
            "create_time": t.create_time
        })
    return JsonResponse({
        "status": 0,
        "msg": "success",
        "data": data
    })