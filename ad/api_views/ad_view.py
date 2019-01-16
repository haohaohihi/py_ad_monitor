import json
import logging
from json import JSONDecodeError

from django.db import IntegrityError
from django.http import HttpResponse, JsonResponse

from ad.utils.decorators import need_login
from ..error_msg import *
from ..models import Ad, AdClass, Firm

logger = logging.getLogger("ad")


# Create your views here.

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
    if not query_key:
        ads = Ad.objects.filter(valid=1).order_by('-id')
    else:
        # 按照品牌过滤
        q_ads_1 = Ad.objects.filter(brand__contains=query_key, valid=1)
        # 按照描述过滤
        q_ads_2 = Ad.objects.filter(pro_desc__contains=query_key, valid=1)
        # 按照小类过滤
        third_catgs = AdClass.objects.filter(name__contains=query_key, is_using=1)
        third_catg_ids = [c.class_item_id for c in third_catgs]
        q_ads_3 = Ad.objects.filter(catg_id__in=third_catg_ids, valid=1)
        # 按照厂商名过滤
        firms = Firm.objects.filter(name__contains=query_key, valid=1)
        firm_ids = [f.id for f in firms]
        q_ads_4 = Ad.objects.filter(firm_id__in=firm_ids)

        ads = (q_ads_1 | q_ads_2 | q_ads_3 | q_ads_4).distinct()
    # ads = Ad.objects.filter(brand__contains=query_key, valid=1) if query_key else Ad.objects.filter(valid=1)
    # total = math.ceil(len(ads) / page_size)

    total = len(ads)
    ads = ads.order_by('-id')[(page_idx - 1) * page_size: page_idx * page_size]
    result = {
        "status": 0,
        "msg": "success",
        "total": total,
        "currentPageNum": page_idx,
        "pageSize": page_size,
        "data": [],
    }
    print("ads: ", ads)
    for ad in ads:
        catgs = []
        catg_id = ad.catg_id
        while catg_id != 0:
            cur_class = AdClass.objects.get(class_item_id=catg_id)
            catgs.append(cur_class.name)
            catg_id = cur_class.parent_id
        result["data"].append({
            "id": ad.id,
            "fineClass": catgs[0] if catgs else None,
            "nasIp": ad.nas_ip,
            "lamdaFileAddr": ad.file_path,
            "mainBrand": ad.brand,
            "manufacturer": Firm.objects.get(id=ad.firm_id).name if ad.firm_id else None,
            "description": ad.pro_desc,
            "tags": ad.tags if ad.tags else "[]"
        })
    return JsonResponse(result)


def get_by_id(request):
    return HttpResponse("get by id")


@need_login()
def add(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        exist_ad = Ad.objects.filter(file_path=data.get("lambdaFileAddr"), nas_ip=data.get("nasIp"), valid=0)
        if exist_ad:
            ad = exist_ad[0]
            ad.valid = 1
        else:
            ad = Ad(catg_id=data.get("catgId"), agent_id=data.get("agentId"), firm_id=data.get("manufacturerId"),
                    brand=data.get("mainBrand"), file_path=data.get("lambdaFileAddr"), nas_ip=data.get("nasIp"),
                    ver_desc=data.get("verDescription"), lang=data.get("lang"), pro_desc=data.get("description"),
                    tags=data.get("tags"))
        ad.save()
    except JSONDecodeError as e:
        logger.error(repr(e))
        return JsonResponse(json_format_error)
    except IntegrityError as e:
        logger.error(repr(e))
        if "Duplicate" in str(e):
            return JsonResponse(param_repeat_error)
        return JsonResponse(lack_param_error)
    return JsonResponse({
        "id": ad.id,
        "status": 0,
        "msg": "创建数据成功"
    })


@need_login()
def update(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        idx = int(data["id"])
        ad = Ad.objects.get(id=idx, valid=1)
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
    ad.catg_id = data.get("catgId") or ad.catg_id
    ad.agent_id = data.get("agentId") or ad.agent_id
    ad.firm_id = data.get("manufacturerId") or ad.firm_id
    ad.brand = data.get("mainBrand")
    ad.file_path = data.get("lambdaFileAddr") or ad.file_path
    ad.nas_ip = data.get("nasIp") or ad.nas_ip
    ad.ver_desc = data.get("verDescription") or ad.ver_desc
    ad.lang = data.get("lang") or ad.lang
    ad.pro_desc = data.get("description")
    ad.tags = data.get("tags")
    ad.save()
    return JsonResponse({
        "status": 0,
        "msg": "更新数据成功",
        "id": ad.id
    })


@need_login()
def delete(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        idxs = [int(i) for i in data["ids"]]
        ads = Ad.objects.filter(id__in=idxs, valid=1)
        result_idxs = []
        for a in ads:
            a.valid = 0
            a.save()
            result_idxs.append(a.id)
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
