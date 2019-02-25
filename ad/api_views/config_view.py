import json
import logging

from django.http import JsonResponse

from ad.utils.decorators import need_login
from ..error_msg import *
from ..models import Config

logger = logging.getLogger("ad")


def config_detail_dict(config):
    return {
        "id": config.id,
        "auto_delete_day_interval_days": config.auto_delete_day_interval_days
    }


@need_login()
def get(request):
    try:
        config = Config.objects.get(id=1)
        return JsonResponse(config_detail_dict(config))
    except Exception as e:
        config = Config(id=1, auto_delete_day_interval_days=30)
        config.save()
        return JsonResponse(config_detail_dict(config))

@need_login()
def update(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception as e:
        logger.error(repr(e))
        return JsonResponse(json_format_error)
    try:
        config = Config.objects.get(id=1)
        config.auto_delete_day_interval_days = data.get("auto_delete_day_interval_days") if data.get("auto_delete_day_interval_days") else config.auto_delete_day_interval_days
        config.save()
        return JsonResponse(config_detail_dict(config))
    except Exception as e:
        config = Config(id=1,
                        auto_delete_day_interval_days=data.get("auto_delete_day_interval_days") if data.get("auto_delete_day_interval_days") else 30)
        config.save()
        return JsonResponse(config_detail_dict(config))
