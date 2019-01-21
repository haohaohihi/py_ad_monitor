#-*- coding:utf-8 -*-
import json
import math
import logging
import os
import os.path
from datetime import datetime
from json import JSONDecodeError

import xlwt
from django.http import JsonResponse
from django.http import StreamingHttpResponse

from ad.utils.decorators import need_login
from ..error_msg import *
from ..models import Ad, Firm, AdClass, Channel, ChannelAdCharge, MatchResult, ChannelProgram, AdminUser, UserChannel
from ..user_roles import *

download_dir = "download_files"
if not os.path.exists(download_dir):
    os.mkdir(download_dir)
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


def get_pre_aft_programs(channel_id, start_time, end_time):
    """
    查找一个广告的前后节目表
    :param channel_id: 频道id
    :param start_time: 广告开始时间，类型为datetime
    :param end_time: 广告结束时间，类型为datetime
    :return: pre, aft，两个ChannelProgram元素组成的元组
    """

    weekday = start_time.weekday() + 1
    programs = ChannelProgram.objects.filter(channel_id=channel_id).order_by('start_time')
    pre_programs = []
    aft_programs = []
    for p in programs:
        if p.end_time <= start_time.time():
            pre_programs.append(p)
        if p.start_time >= end_time.time():
            aft_programs.append(p)
    pre = pre_programs[-1] if pre_programs else None
    aft = aft_programs[0] if aft_programs else None
    return pre, aft

def get_all_results_in_stage(channel_id, start_date_time, end_date_time):
    """
    查找在两个时间点之间的所有匹配结果
    :param channel_id: 频道id
    :param start_date_time: 开始时间，类型为datetime
    :param end_date_time: 结束时间，类型为datetime
    :return:
    """
    if not start_date_time or not end_date_time:
        return None
    results = MatchResult.objects.filter(channel_id=channel_id).order_by('start_time')
    temp = []
    for r in results:
        if r.start_time.replace(tzinfo=None) >= start_date_time and r.end_time.replace(tzinfo=None) <= end_date_time:
            temp.append(r)
    return temp


def get_fee(ad_charge, seconds):
    if not ad_charge:
        return 0
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
        if r.start_time.weekday() == (
                ad_charge.weekday - 1) and r.start_time.time() > ad_charge.start_time and r.end_time.time() < ad_charge.end_time:
            temp_result.append(r)
    match_result = temp_result
    return match_result


@need_login()
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
        user_id = request.session["user_id"]
    except JSONDecodeError as e:
        logger.error(repr(e))
        return JsonResponse(json_format_error)
    except Exception as e:
        logger.error(repr(e))
        return JsonResponse(system_error)

    user = AdminUser.objects.get(id=user_id)
    print(user.role)
    if user.role >= USER_ADMIN:
        user_channel_ids = [c.id for c in Channel.objects.all()]
    else:
        user_channel_ids = [c.channel_id for c in UserChannel.objects.filter(user_id=user_id)]
    logger.info(user_channel_ids)

    data = generate_match_data(channel_names, class_names, cover_areas, dates, firm_names, tags, times, weekdays, user_channel_ids)

    if data:
        return JsonResponse({
            "data": data[page_size * (page_idx - 1): page_size * page_idx],
            "pageSize": page_size,
            "currentPageNum": page_idx,
            "total": len(data),
            "status": 0,
            "msg": "success"
        })
    else:
        return JsonResponse(data_not_exist_error)


@need_login()
def download(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        dates = data.get("date")
        weekdays = data.get("weekDay")
        cover_areas = data.get("coverArea")
        times = data.get("time")
        firm_names = data.get("manufactory")
        tags = data.get("tag")
        class_names = data.get("category")
        channel_names = data.get("channel")
        user_id = request.session["user_id"]

        user = AdminUser.objects.get(id=user_id)
        print(user.role)
        if user.role >= USER_ADMIN:
            user_channel_ids = [c.id for c in Channel.objects.all()]
        else:
            user_channel_ids = [c.channel_id for c in UserChannel.objects.filter(user_id=user_id)]
        logger.info(user_channel_ids)

        data = generate_match_data(channel_names, class_names, cover_areas, dates, firm_names, tags, times, weekdays, user_channel_ids)
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


def generate_match_data(channel_names, class_names, cover_areas, dates, firm_names, tags, times, weekdays, user_channel_ids):
    # 过滤channels, 模糊过滤
    if channel_names and channel_names[0]:
        channels = Channel.objects.filter(name__in=channel_names, valid=1, id__in=user_channel_ids)
    else:
        channels = Channel.objects.filter(valid=1, id__in=user_channel_ids)
    # print(channels)

    # 过滤区域
    if cover_areas and cover_areas[0] and cover_areas[1] and cover_areas[2]:
        channels = channels.filter(cover_area=cover_areas[0], cover_province=cover_areas[1], cover_city=cover_areas[2])
    # print(channels)
    # 根据频道id获取所有的匹配结果，再进行下一步的过滤
    channel_ids = [channel.id for channel in channels]
    logger.info(channel_ids)
    # print(channel_ids)
    match_results = MatchResult.objects.filter(channel_id__in=channel_ids, valid=1).order_by('channel_id', 'start_time')
    # logger.info(match_results)
    # print(match_results)
    # 过滤日期+时间
    # logger.info(dates)
    # logger.info(times)
    data_time_null = ["", ""]
    # 只有日期
    if dates and dates != data_time_null and (not times or times == data_time_null):
        temp_match_result = []
        for r in match_results:
            # 先判断日期范围
            if dates[0] <= str(r.start_time.date()) <= dates[1]:
                temp_match_result.append(r)
        match_results = temp_match_result
    # 有日期也有时间
    elif dates and dates != data_time_null and times and times != data_time_null:
        temp_match_result = []
        for r in match_results:
            # 先判断日期范围
            if dates[0] <= str(r.start_time.date()) <= dates[1]:
                if datetime.strptime(times[0], "%H:%M:%S").time() <= r.start_time.time() <= datetime.strptime(times[1],
                                                                                                              "%H:%M:%S").time():
                    temp_match_result.append(r)
        match_results = temp_match_result
    # 没有日期，只有时间
    elif (not dates or dates == data_time_null) and times and times != data_time_null:
        temp_match_result = []
        cur_date = datetime.today()
        for r in match_results:
            if datetime.strptime(times[0], "%H:%M:%S").time() <= r.start_time.time() <= datetime.strptime(times[1],
                                                                                                          "%H:%M:%S").time():
                if (cur_date - r.start_time.replace(tzinfo=None)).days <= 30:
                    temp_match_result.append(r)
        match_results = temp_match_result
    # 都没有
    else:
        temp_match_result = []
        cur_date = datetime.today()
        for r in match_results:
            if (cur_date - r.start_time.replace(tzinfo=None)).days <= 30:
                temp_match_result.append(r)
        match_results = temp_match_result
    # logger.info(match_results)
    # 过滤星期几
    if weekdays:
        temp_match_result = []
        for r in match_results:
            # [bug fixed] datetime.isoweekday() 为1-7，1表示周一，7表示周日
            # 请求数据为0表示周日，1表示周一
            logger.info(r.start_time.weekday())
            logger.info(weekdays)
            if r.start_time.isoweekday() % 7 in weekdays:
                temp_match_result.append(r)
        match_results = temp_match_result
    # logger.info(match_results)
    # 过滤厂商
    if firm_names:
        temp_match_result = []
        for name in firm_names:
            for r in match_results:
                if Firm.objects.filter(id=Ad.objects.get(id=r.ad_id).firm_id, name__contains=name, valid=1):
                    temp_match_result.append(r)
        match_results = temp_match_result
    # logger.info(match_results)
    # 过滤标签
    if tags:
        temp_match_result = []
        for tag in tags:
            for r in match_results:
                if Ad.objects.filter(id=r.ad_id, tags__contains=tag, valid=1):
                    temp_match_result.append(r)
        match_results = temp_match_result
    # logger.info(match_results)
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
    # logger.info(match_results)
    ## 组装数据
    data = []
    for r in match_results:
        ad = Ad.objects.get(id=r.ad_id)
        channel = Channel.objects.get(id=r.channel_id)

        ad_classes = get_classes_by_ad(ad)
        logger.info(ad_classes)

        d = {
            "date": r.start_time.strftime("%Y-%m-%d"),
            "time": r.start_time.strftime("%H:%M:%S"),
            "season": get_season(r.start_time),
            "weekDay": get_weekday(r.start_time),
            "duration": (r.end_time - r.start_time).seconds,
            "channel": channel.name,
            "description": ad.pro_desc,
            "ver_description": ad.ver_desc,
            "majorClass": ad_classes[0] if ad_classes else None,
            "mediumClass": ad_classes[1] if len(ad_classes) > 1 else None,
            "fineClass": ad_classes[2] if len(ad_classes) > 2 else None,
            "tags": " | ".join(eval(ad.tags)) if ad.tags else None,
            "mainBrand": ad.brand,
            "manufactory": Firm.objects.get(id=ad.firm_id).name if ad.firm_id else None,
            "coverArea": channel.cover_area,
            "coverProvince": channel.cover_province,
            "coverCity": channel.cover_city,
            "mediaFile": ad.file_path,
            "nasIp": ad.nas_ip
        }

        # logger.info(r.start_time, r.end_time)
        pre_program, aft_program = get_pre_aft_programs(channel.id, r.start_time, r.end_time)
        # logger.info("pre", pre_program.name, pre_program.start_time, pre_program.end_time)
        # logger.info("aft", aft_program.name, aft_program.start_time, aft_program.end_time)
        stage_start_time = pre_program.end_time if pre_program else r.start_time.time().replace(0,0,0,0)        # 类型为datetime.time()
        stage_end_time = aft_program.start_time if aft_program else r.end_time.time().replace(23,59,59,999999)
        # logger.info(stage_start_time, stage_end_time)
        # 查询在两个节目间的所有广告结果（已经排好序）
        all_results_in_stage = get_all_results_in_stage(channel.id, datetime.combine(r.start_time.date(), stage_start_time), datetime.combine(r.start_time.date(), stage_end_time))
        # logger.info(len(all_results_in_stage))
        cur_index = all_results_in_stage.index(r)

        # 查找同一阶段前后广告信息
        pre_result = None if cur_index == 0 else all_results_in_stage[cur_index - 1]
        pre_ad = Ad.objects.get(id=pre_result.ad_id) if pre_result else None
        pre_classes = get_classes_by_ad(pre_ad) if pre_ad else None
        next_result = None if cur_index == (len(all_results_in_stage) - 1) else all_results_in_stage[ cur_index + 1]
        next_ad = Ad.objects.get(id=next_result.ad_id) if next_result else None
        next_classes = get_classes_by_ad(next_ad) if next_ad else None

        d.update({
            "fee": get_fee(pre_program, (r.end_time - r.start_time).seconds) if pre_program else None,
            "preDate": "",
            "proBefore": pre_program.name if pre_program else None,
            "totalPos": len(all_results_in_stage),
            "pPos": cur_index + 1,
            "nPos": len(all_results_in_stage) - cur_index,
            "adBefore": pre_ad.pro_desc if pre_ad else None,
            "adBeforeType": "/".join(pre_classes) if pre_classes else None,
            "adAfter": next_ad.pro_desc if next_ad else None,
            "adAfterType": "/".join(next_classes) if next_ad else None,
            "proAfter": aft_program.name if aft_program else None,
        })

        data.append(d)
        # logger.info(data)
    return data


# def weekday_chinese

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
