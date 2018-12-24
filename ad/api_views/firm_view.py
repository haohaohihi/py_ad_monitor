import json
import logging
from json import JSONDecodeError

from django.db import IntegrityError
from django.http import JsonResponse

from ad.utils.decorators import need_login
from ..error_msg import *
from ..models import Firm

logger = logging.getLogger("ad")


@need_login()
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

    firms = Firm.objects.filter(name__contains=query_key, valid=1) if query_key else Firm.objects.filter(valid=1)
    # total = math.ceil(len(firms) / page_size)
    total = len(firms)
    firms = firms.order_by('-id')[(page_idx - 1) * page_size: page_idx * page_size]
    result = {
        "status": 0,
        "msg": "success",
        "total": total,
        "currentPageNum": page_idx,
        "pageSize": page_size,
        "data": [],
    }
    for firm in firms:
        result["data"].append({
            "id": firm.id,
            "name": firm.name
        })
    return JsonResponse(result)


@need_login()
def add(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        exist_firm = Firm.objects.filter(name=data.get("name"), valid=0)
        if exist_firm:
            # 处理删除后创建新的，然后再删除时，由于unique约束导致的失败
            firm = exist_firm[0]
            firm.valid = 1
        else:
            firm = Firm(name=data.get("name"))
        firm.save()
    except JSONDecodeError as e:
        logger.error(repr(e))
        return JsonResponse(json_format_error)
    except IntegrityError as e:
        logger.error(repr(e))
        if "Duplicate" in str(e):
            return JsonResponse(param_repeat_error)
        return JsonResponse(lack_param_error)
    return JsonResponse({
        "id": firm.id,
        "status": 0,
        "msg": "创建数据成功"
    })


@need_login()
def update(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        idx = int(data["id"])
        firm = Firm.objects.filter(valid=1).get(id=idx)
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
    firm.name = data.get("name") or firm.name
    firm.save()
    return JsonResponse({
        "status": 0,
        "msg": "更新数据成功",
        "id": firm.id
    })


@need_login()
def delete(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        idxs = [int(i) for i in data["ids"]]
        firms = Firm.objects.filter(id__in=idxs, valid=1)
        result_idxs = []
        for f in firms:
            f.valid = 0
            f.save()
            result_idxs.append(f.id)
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
