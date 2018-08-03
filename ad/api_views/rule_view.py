import json
import logging
import os
from json import JSONDecodeError

import math

import datetime
from django.db import IntegrityError
from django.http import HttpResponse, JsonResponse
from ..models import Rule, Firm, AdClass, Ad, Channel
from ..error_msg import *
logger = logging.getLogger("ad")


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
    rules = Rule.objects.filter(name__contains=query_key, valid=1) if query_key else Rule.objects.filter(valid=1)
    # total = math.ceil(len(rules) / page_size)
    total = len(rules)
    rules = rules.order_by('id')[(page_idx - 1) * page_size: page_idx * page_size]
    result = {
        "status": 0,
        "msg": "success",
        "total": total,
        "currentPageNum": page_idx,
        "pageSize": page_size,
        "data": [],
    }
    for rule in rules:
        result["data"].append({
            "id": rule.id,
            "name": rule.name,
            "date": rule.update_date,
            "weekDay": rule.weekdays,
            "time": rule.times,
            "coverArea": rule.cover_areas,
            "manufactory": rule.firm_names,
            "category": rule.class_names,
            "tag": rule.tags,
            "channel": rule.channel_names
        })
    return JsonResponse(result)


def add(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        print(data)
        exist_rule = Rule.objects.filter(name=data.get("name"), valid=0)
        if exist_rule:
            rule = exist_rule[0]
            rule.valid = 1
        else:
            rule = Rule(name=data.get("name"), update_date=datetime.date.today())
            if data.get("weekDay"):
                rule.weekdays = data.get("weekDay")
            if data.get("time"):
                rule.times = data.get("time")
            if data.get("coverArea"):
                rule.cover_areas = data.get("coverArea")
            if data.get("manufactory"):
                rule.firm_names = data.get("manufactory")
            if data.get("category"):
                rule.class_names = data.get("category")
            if data.get("tag"):
                rule.tags = data.get("tag")
            if data.get("channel"):
                rule.channel_names = data.get("channel")
        rule.save()
    except JSONDecodeError as e:
        logger.error(repr(e))
        return JsonResponse(json_format_error)
    except IntegrityError as e:
        logger.error(repr(e))
        if "Duplicate" in str(e):
            return JsonResponse(param_repeat_error)
        return JsonResponse(lack_param_error)
    return JsonResponse({
        "id": rule.id,
        "status": 0,
        "msg": "创建数据成功"
    })


def update(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        idx = int(data["id"])
        rule = Rule.objects.get(id=idx, valid=1)
        print(idx)
        changed = False
        if data.get("weekDay") and data.get("weekDay") != rule.weekdays:
            rule.weekdays = data.get("weekDay")
            changed = True
        if data.get("time") and data.get("time") != rule.times:
            rule.times = data.get("time")
            changed = True
        if data.get("coverArea") and data.get("coverArea") != rule.cover_areas:
            rule.cover_areas = data.get("coverArea")
            changed = True
        if data.get("manufactory") and data.get("manufactory") != rule.firm_names:
            rule.firm_names = data.get("manufactory")
            changed = True
        if data.get("category") and data.get("category") != rule.class_names:
            rule.class_names = data.get("category")
            changed = True
        if data.get("tag") and data.get("tag") != rule.tags:
            rule.tags = data.get("tag")
            changed = True
        if data.get("channel") and data.get("channel") != rule.channel_names:
            rule.channel_names = data.get("channel")
            changed = True
        if data.get("name") and data.get("name") != rule.channel_names:
            rule.name = data.get("name")
            changed = True
        rule.save()
    except JSONDecodeError as e:
        logger.error(repr(e))
        return JsonResponse(json_format_error)
    except KeyError as e:
        logger.error(repr(e))
        return JsonResponse(lack_param_error)
    except ValueError as e:
        logger.error(repr(e))
        return JsonResponse(param_format_error)
    except IntegrityError as e:
        logger.error(repr(e))
        if "Duplicate" in str(e):
            return JsonResponse(param_repeat_error)
        return JsonResponse(lack_param_error)
    except Exception as e:
        logger.error(repr(e))
        return JsonResponse(data_not_exist_error)
    if changed:
        rule.update_date = datetime.date.today()
    rule.save()
    return JsonResponse({
        "status": 0,
        "msg": "更新数据成功",
        "id": rule.id
    })


def delete(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        idxs = [int(i) for i in data["ids"]]
        rules = Rule.objects.filter(id__in=idxs, valid=1)
        result_idxs = []
        for r in rules:
            r.valid = 0
            r.save()
            result_idxs.append(r.id)
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


def hint(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        type = data["category"]
        query_word = data["query"]
    except JSONDecodeError as e:
        logger.error(repr(e))
        return JsonResponse(json_format_error)
    except KeyError as e:
        logger.error(repr(e))
        return JsonResponse(lack_param_error)
    data = []
    if "厂商" == type:
        firms = Firm.objects.filter(name__contains=query_word, valid=1)
        data = [f.name for f in firms]
    elif "标签" == type:
        ads = Ad.objects.filter(tags__contains=query_word, valid=1)
        print(ads)
        tags = set()
        for a in ads:
            tags = tags.union(eval(a.tags))
        data = list(tags)
    elif "类别" == type:
        ad_class = AdClass.objects.filter(name__contains=query_word, is_using=1)
        data = [c.name for c in ad_class]
    elif "频道" == type:
        channels = Channel.objects.filter(name__contains=query_word, valid=1)
        data = [c.name for c in channels]
    else:
        pass
    return JsonResponse({
        "status": 0,
        "msg": "success",
        "data": data
    })
