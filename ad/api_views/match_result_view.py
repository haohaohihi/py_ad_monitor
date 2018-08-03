import os
import xlwt
import json
import logging
from datetime import datetime
from json import JSONDecodeError

import math
from django.db import IntegrityError
from django.http import HttpResponse, JsonResponse
from django.http import StreamingHttpResponse

from ..models import Ad, Firm, AdClass, Channel, ChannelAdCharge, MatchResult
from ..error_msg import *

download_dir = "download_files"
logger = logging.getLogger("ad")


# 根据ad对象，获取其分类list
def get_classes_by_ad(ad):
    catgs = []
    catg_id = ad.catg_id
    while catg_id != 0:
        cur_class = AdClass.objects.get(class_item_id=catg_id)
        catgs.append(cur_class.name)
        catg_id = cur_class.parent_id
    catgs.reverse()
    return catgs


def get_season(start_time):
    month = start_time.month
    if month in [1, 2, 3]:
        return "第一季度"
    elif month in [4, 5, 6]:
        return "第二季度"
    elif month in [7, 8, 9]:
        return "第三季度"
    else:
        return "第四季度"


def get_weekday(start_time):
    weekday = start_time.weekday()
    if weekday == 0:
        return "星期一"
    elif weekday == 1:
        return "星期二"
    elif weekday == 2:
        return "星期三"
    elif weekday == 3:
        return "星期四"
    elif weekday == 4:
        return "星期五"
    elif weekday == 5:
        return "星期六"
    elif weekday == 6:
        return "星期日"
    else:
        return ""


def get_ad_charge(channel_id, start_time, end_time):
    weekday = start_time.weekday() + 1
    ad_charge = ChannelAdCharge.objects.filter(channel_id=channel_id, weekday=weekday)
    temp_ad_charge = []
    for c in ad_charge:
        if start_time.time() >= c.start_time and end_time.time() <= c.end_time:
            temp_ad_charge.append(c)
    ad_charge = temp_ad_charge
    return ad_charge


def get_fee(ad_charge, seconds):
    if seconds <= 5:
        return ad_charge.stage1
    elif 5 < seconds <= 10:
        return ad_charge.stage2
    else:
        return ad_charge.stage3


def get_all_matched_in_ad_charge(ad_charge):
    match_result = MatchResult.objects.filter(channel_id=ad_charge.channel_id)
    temp_result = []
    for r in match_result:
        if r.start_time.weekday() == (ad_charge.weekday - 1) and r.start_time.time() > ad_charge.start_time and r.end_time.time() < ad_charge.end_time:
            temp_result.append(r)
    match_result = temp_result
    return match_result

def get(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        page_idx = int(data["currentPageNum"])
        page_size = data.get("pageSize") or 8
        dates = data.get("date")
        weekdays = data.get("weekDay")
        cover_areas = data.get("coverArea")
        times = data.get("time")
        firm_names = data.get("manufactory")
        tags = data.get("tag")
        class_names = data.get("category")
        channel_names = data.get("channel")
        data = generate_match_data(channel_names, class_names, cover_areas, dates, firm_names, tags, times, weekdays)
        if data:
            return JsonResponse({
                "data": data,
                "status": 0,
                "msg": "success"
            })
        else:
            return JsonResponse(data_not_exist_error)
    except JSONDecodeError as e:
        logger.error(repr(e))
        return JsonResponse(json_format_error)
    except Exception as e:
        logger.error(repr(e))
        return JsonResponse(system_error)



def download(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        page_idx = int(data["currentPageNum"])
        page_size = data.get("pageSize") or 8
        dates = data.get("date")
        weekdays = data.get("weekDay")
        cover_areas = data.get("coverArea")
        times = data.get("time")
        firm_names = data.get("manufactory")
        tags = data.get("tag")
        class_names = data.get("category")
        channel_names = data.get("channel")
        data = generate_match_data(channel_names, class_names, cover_areas, dates, firm_names, tags, times, weekdays)
        if data:
            filename = generate_xls_file(data)
            response = StreamingHttpResponse(file_iterator(os.path.join(download_dir, filename)))  # 这里创建返回
            response['Content-Type'] = 'application/vnd.ms-excel'  # 注意格式
            response['Content-Disposition'] = 'attachment;filename="{0}"'.format(filename)  # 注意filename 这个是下载后的名字
            return response
        else:
            raise Exception
    except JSONDecodeError as e:
        logger.error(repr(e))
        return JsonResponse(json_format_error)
    except Exception as e:
        logger.error(repr(e))
        return JsonResponse(data_not_exist_error)


def generate_match_data(channel_names, class_names, cover_areas, dates, firm_names, tags, times, weekdays):
    # 过滤channels, 模糊过滤
    if channel_names:
        for n in channel_names:
            channels = Channel.objects.filter(name__contains=n, valid=1)
    else:
        channels = Channel.objects.filter(valid=1)
    # print(channels)
    # 过滤区域
    if cover_areas:
        channels = channels.filter(cover_area=cover_areas[0], cover_province=cover_areas[1], cover_city=cover_areas[1])
    # 根据频道id获取所有的匹配结果，再进行下一步的过滤
    channel_ids = [channel.id for channel in channels]
    match_results = MatchResult.objects.filter(channel_id__in=channel_ids, valid=1)
    # 过滤日期+时间
    # 只有日期
    if dates and not times:
        temp_match_result = []
        for r in match_results:
            # 先判断日期范围
            if dates[0] <= str(r.start_time.date()) <= dates[1]:
                temp_match_result.append(r)
        match_results = temp_match_result
    # 有日期也有时间
    elif dates and times:
        temp_match_result = []
        for r in match_results:
            # 先判断日期范围
            if dates[0] <= str(r.start_time.date()) <= dates[1]:
                if datetime.strptime(times[0], "%H:%M:%S").time() <= r.start_time.time() <= datetime.strptime(times[1],
                                                                                                              "%H:%M:%S").time():
                    temp_match_result.append(r)
        match_results = temp_match_result
    # 没有日期，只有时间
    elif not dates and times:
        temp_match_result = []
        cur_date = datetime.today()
        for r in match_results:
            if datetime.strptime(times[0], "%H:%M:%S").time() <= r.start_time.time() <= datetime.strptime(times[1],
                                                                                                          "%H:%M:%S").time():
                if (cur_date - r.start_time.replace(tzinfo=None)).days <= 30:
                    temp_match_result.append(r)
        match_results = temp_match_result
    else:
        print("lslslslsl")
        temp_match_result = []
        cur_date = datetime.today()
        for r in match_results:
            if (cur_date - r.start_time.replace(tzinfo=None)).days <= 30:
                temp_match_result.append(r)
        match_results = temp_match_result

    # 过滤星期几
    if weekdays:
        temp_match_result = []
        for r in match_results:
            # [bug fixed] datetime.weekday()起始为0
            if r.start_time.weekday() + 1 in weekdays:
                temp_match_result.append(r)
        match_results = temp_match_result

    # 过滤厂商
    if firm_names:
        temp_match_result = []
        for name in firm_names:
            for r in match_results:
                if Firm.objects.filter(id=Ad.objects.get(id=r.ad_id).firm_id, name__contains=name, valid=1):
                    temp_match_result.append(r)
        match_results = temp_match_result

    # 过滤标签
    if tags:
        temp_match_result = []
        for tag in tags:
            for r in match_results:
                if Ad.objects.filter(id=r.ad_id, tags__contains=tag, valid=1):
                    temp_match_result.append(r)
        match_results = temp_match_result

    # 过滤分类
    if class_names:
        # [bug fixed] 改成set，避免重复数据
        temp_match_result = set()
        for c_name in class_names:
            for r in match_results:
                ad = Ad.objects.get(id=r.ad_id)
                if c_name in get_classes_by_ad(ad):
                    temp_match_result.add(r)
        match_results = temp_match_result

    ## 组装数据
    data = []
    for r in match_results:
        ad = Ad.objects.get(id=r.ad_id)
        channel = Channel.objects.get(id=r.channel_id)
        ad_classes = get_classes_by_ad(ad)

        ad_charge = get_ad_charge(channel.id, r.start_time, r.end_time)
        if not ad_charge:
            continue
        ad_charge = ad_charge[0]

        all_matched_in_ad_charge = get_all_matched_in_ad_charge(ad_charge)
        cur_index = all_matched_in_ad_charge.index(r)
        last_result = None if cur_index == 0 else all_matched_in_ad_charge[cur_index - 1]
        last_ad = Ad.objects.get(id=last_result.ad_id) if last_result else None
        last_classes = get_classes_by_ad(last_ad) if last_ad else None

        next_result = None if cur_index == (len(all_matched_in_ad_charge) - 1) else all_matched_in_ad_charge[
            cur_index + 1]
        next_ad = Ad.objects.get(id=next_result.ad_id) if next_result else None
        next_classes = get_classes_by_ad(next_ad) if next_ad else None

        d = {
            "date": r.start_time.strftime("%Y-%m-%d"),
            "time": r.start_time.strftime("%H:%M:%S"),
            "season": get_season(r.start_time),
            "weekDay": get_weekday(r.start_time),
            "duration": (r.end_time - r.start_time).seconds,
            "channel": channel.name,
            "description": ad.pro_desc,
            "ver_description": ad.ver_desc,
            "majorClass": ad_classes[0],
            "mediumClass": ad_classes[1],
            "fineClass": ad_classes[2],
            "tags": " | ".join(eval(ad.tags)),
            "mainBrand": ad.brand,
            "manufactory": Firm.objects.get(id=ad.firm_id).name,

            "fee": get_fee(ad_charge, (r.end_time - r.start_time).seconds),
            "preDate": "",
            "proBefore": ad_charge.pro_before,
            "totalPos": len(all_matched_in_ad_charge),
            "pPos": cur_index + 1,
            "nPos": len(all_matched_in_ad_charge) - cur_index,
            "adBefore": last_ad.pro_desc if last_ad else None,
            "adBeforeType": "/".join(last_classes) if last_ad else None,
            "adAfter": next_ad.pro_desc if next_ad else None,
            "adAfterType": "/".join(next_classes) if next_ad else None,
            "proAfter": ad_charge.pro_after,

            "coverArea": channel.cover_area,
            "coverProvince": channel.cover_province,
            "coverCity": channel.cover_city,
            "mediaFile": ad.file_path,
            "nasIp": ad.nas_ip
        }
        data.append(d)
    return data


def generate_xls_file(data):
    filename = datetime.today().strftime("%Y_%m_%d_%H_%M_%S") + ".xls"
    xls = xlwt.Workbook()
    table = xls.add_sheet("result")

    table.write(0, 0, "区域")
    table.write(0, 1, "省份")
    table.write(0, 2, "城市")
    table.write(0, 3, "频道")

    table.write(0, 4, "大类")
    table.write(0, 5, "中类")
    table.write(0, 6, "小类")
    table.write(0, 7, "产品描述")
    table.write(0, 8, "版本描述")
    table.write(0, 9, "关键词")

    table.write(0, 10, "星期")
    table.write(0, 11, "匹配日期")
    table.write(0, 12, "匹配开始时间")
    table.write(0, 13, "匹配时间长度")
    table.write(0, 14, "季度")

    table.write(0, 15, "频道费用")

    table.write(0, 16, "品牌")
    table.write(0, 17, "厂商")

    table.write(0, 18, "首播日期")

    table.write(0, 19, "正排位置")
    table.write(0, 20, "倒排位置")
    table.write(0, 21, "总位置")
    table.write(0, 22, "前节目")
    table.write(0, 23, "前广告")
    table.write(0, 24, "前广告类型")
    table.write(0, 25, "后广告")
    table.write(0, 26, "后广告类型")
    table.write(0, 27, "后节目")

    table.write(0, 28, "媒体文件")

    i = 0
    for d in data:
        i += 1
        table.write(i, 0, d.get("coverArea"))
        table.write(i, 1, d.get("coverProvince"))
        table.write(i, 2, d.get("coverCity"))
        table.write(i, 3, d.get("channel"))

        table.write(i, 4, d.get("majorClass"))
        table.write(i, 5, d.get("mediumClass"))
        table.write(i, 6, d.get("fineClass"))
        table.write(i, 7, d.get("description"))
        table.write(i, 8, d.get("ver_description"))
        table.write(i, 9, d.get("tags"))

        table.write(i, 10, d.get("weekDay"))
        print(d.get("date"))
        table.write(i, 11, d.get("date"))
        table.write(i, 12, d.get("time"))
        table.write(i, 13, d.get("duration"))
        table.write(i, 14, d.get("season"))

        table.write(i, 15, d.get("fee"))

        table.write(i, 16, d.get("mainBrand"))
        table.write(i, 17, d.get("manufactory"))

        table.write(i, 18, d.get("preDate"))

        table.write(i, 19, d.get("pPos"))
        table.write(i, 20, d.get("nPos"))
        table.write(i, 21, d.get("totalPos"))
        table.write(i, 22, d.get("proBefore"))
        table.write(i, 23, d.get("adBefore"))
        table.write(i, 24, d.get("adBeforeType"))
        table.write(i, 25, d.get("adAfter"))
        table.write(i, 26, d.get("adAfterType"))
        table.write(i, 27, d.get("proAfter"))

        table.write(i, 28, d.get("mediaFile"))

    xls.save(os.path.join(download_dir, filename))
    return filename


def file_iterator(file_name, chunk_size=512):  # 用于形成二进制数据
    with open(file_name, 'rb') as f:
        while True:
            c = f.read(chunk_size)
            if c:
                yield c
            else:
                break
