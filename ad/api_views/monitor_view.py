from django.http import JsonResponse

from ad.utils.decorators import need_login
from ..models import Monitor


@need_login()
def status(request):
    monitors = Monitor.objects.all()
    data = []
    for m in monitors:
        data.append({
            "id": m.id,
            "type": m.type,
            "channel": m.channel,
            "problem": m.problem,
            "startTime": m.start_time.replace('_', ' ') if (m.start_time and "_" in m.start_time) else m.start_time,
            "lastTime": m.last_time.replace('_', ' ') if (m.last_time and "_" in m.last_time) else m.last_time,
            "task": m.has_task
        })
    return JsonResponse({
        "stats": 0,
        "msg": "success",
        "data": data
    })
