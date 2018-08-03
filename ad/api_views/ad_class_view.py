import json
import logging
from json import JSONDecodeError

from django.db import IntegrityError
from django.http import HttpResponse, JsonResponse

from ..models import AdClass

logger = logging.getLogger("ad")

from ..error_msg import *

# Create your views here.


def get_second_children(parent_id):
    result = []
    third_classes = AdClass.objects.filter(level=2, parent_id=parent_id, is_using=1)
    for c in third_classes:
        result.append({
            "id": c.class_item_id,
            "name": c.name,
            "level": c.level + 1
        })
    return result


def get_first_children(parent_id):
    result = []
    second_classes = AdClass.objects.filter(level=1, parent_id=parent_id, is_using=1)
    for c in second_classes:
        result.append({
            "id": c.class_item_id,
            "name": c.name,
            "level": c.level + 1,
            "children": get_second_children(c.class_item_id)
        })
    return result

def get(request):
    query_result = []
    first_classes = AdClass.objects.filter(level=0, is_using=1)
    for c in first_classes:
        query_result.append({
            "id": c.class_item_id,
            "name": c.name,
            "level": c.level + 1,
            "children": get_first_children(c.class_item_id)
        })

    return JsonResponse({
        "status": 0,
        "msg": "success",
        "data": query_result
    })


def get_by_id(request):
    return HttpResponse("get by id")


def _create_three_catgs(first_catg, second_catg, third_catg):
    second_id = _create_two_catgs(first_catg, second_catg).get("id")
    ad_class = AdClass.objects.filter(level=2).filter(name=third_catg).filter(parent_id=second_id)
    if ad_class:
        third = ad_class[0]
        third.is_using = 1
    else:
        third = AdClass(level=2, parent_id=second_id, name=third_catg, is_using=1)
    third.save()
    return {
        "id": third.class_item_id
    }


def _create_two_catgs(first_catg, second_catg):
    first_id = _create_one_catg(first_catg).get("id")
    ad_class = AdClass.objects.filter(level=1).filter(name=second_catg).filter(parent_id=first_id)
    if ad_class:
        second = ad_class[0]
        second.is_using = 1
    else:
        second = AdClass(level=1, parent_id=first_id, name=second_catg, is_using=1)
    second.save()
    return {
        "id": second.class_item_id
    }


def _create_one_catg(first_catg):
    ad_class = AdClass.objects.filter(level=0).filter(name=first_catg)
    if ad_class:
        first = ad_class[0]
        first.is_using = 1
    else:
        first = AdClass(level=0, parent_id=0, name=first_catg, is_using=1)
    first.save()
    return {
        "id": first.class_item_id
    }


def add(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        first_catg, second_catg, third_catg = data.get("first_catg"), data.get("second_catg"), data.get("third_catg")
        if first_catg and second_catg and third_catg:
            result = _create_three_catgs(first_catg, second_catg, third_catg)
        elif first_catg and second_catg and not third_catg:
            result = _create_two_catgs(first_catg, second_catg)
        elif first_catg and not (second_catg or third_catg):
            result = _create_one_catg(first_catg)
        else:
            result = lack_param_error
    except JSONDecodeError as e:
        logger.error(repr(e))
        return JsonResponse(json_format_error)
    except IntegrityError as e:
        logger.error(repr(e))
        if "Duplicate" in str(e):
            return JsonResponse(param_repeat_error)
        return JsonResponse(lack_param_error)
    if "status" not in result.keys():
        result.update(success)
    return JsonResponse(result)


def update(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        idx = int(data["id"])
        ad_class = AdClass.objects.filter(is_using=1).get(class_item_id=idx)
        ad_class.name = data.get("name")
        ad_class.save()
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
        "msg": "更新数据成功",
        "id": ad_class.class_item_id
    })


def delete(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        idxs = [int(i) for i in data["ids"]]
        print(idxs)
        ad_classes = AdClass.objects.filter(class_item_id__in=idxs, is_using=1)
        result_idxs = []
        for ac in ad_classes:
            ac.is_using = 0
            ac.save()
            result_idxs.append(ac.class_item_id)
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

