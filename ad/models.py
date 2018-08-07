from django.db import models


class AdClass(models.Model):
    level = models.IntegerField()
    class_item_id = models.AutoField(primary_key=True)
    parent_id = models.IntegerField()
    name = models.CharField(max_length=50)
    is_using = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ad_classfication_tab'


class Ad(models.Model):
    id = models.BigAutoField(primary_key=True)
    catg_id = models.BigIntegerField()
    agent_id = models.BigIntegerField()
    firm_id = models.BigIntegerField()
    brand = models.CharField(max_length=1000, blank=True, null=True)
    pro_desc = models.CharField(max_length=1000, blank=True, null=True)
    ver_desc = models.CharField(max_length=1000, blank=True, null=True)
    lang = models.CharField(max_length=1000, blank=True, null=True)
    tags = models.CharField(max_length=1000, blank=True, null=True)
    file_path = models.CharField(max_length=800)
    nas_ip = models.CharField(max_length=200)
    valid = models.IntegerField(blank=True, null=True, default=1)

    class Meta:
        managed = False
        db_table = 'ad_info'
        unique_together = (('file_path', 'nas_ip'),)


class Agent(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=1000)
    valid = models.IntegerField(blank=True, null=True, default=1)

    class Meta:
        managed = False
        db_table = 'agent_info'


class Brand(models.Model):
    id = models.BigAutoField(primary_key=True)
    firm_id = models.BigIntegerField()
    name = models.CharField(max_length=500)
    valid = models.IntegerField(blank=True, null=True, default=1)

    class Meta:
        managed = False
        db_table = 'brand_info'
        unique_together = (('firm_id', 'name'),)


class ChannelAdCharge(models.Model):
    id = models.BigAutoField(primary_key=True)
    channel_id = models.BigIntegerField()
    weekday = models.IntegerField()
    pro_before = models.CharField(max_length=1000, blank=True, null=True)
    pro_after = models.CharField(max_length=1000, blank=True, null=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    stage1 = models.IntegerField(blank=True, null=True)
    stage2 = models.IntegerField(blank=True, null=True)
    stage3 = models.IntegerField(blank=True, null=True)
    valid = models.IntegerField(blank=True, null=True, default=1)

    class Meta:
        managed = False
        db_table = 'channel_ad_charge'
        unique_together = (('channel_id', 'weekday', 'start_time', 'end_time', 'valid'),)


class Channel(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=100)
    area = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    cover_area = models.CharField(max_length=100)
    cover_province = models.CharField(max_length=100)
    cover_city = models.CharField(max_length=100)
    valid = models.IntegerField(blank=True, null=True, default=1)

    class Meta:
        managed = False
        db_table = 'channel_info'


class Firm(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=255)
    valid = models.IntegerField(blank=True, null=True, default=1)

    class Meta:
        managed = False
        db_table = 'firm_info'


class FirstPlayDate(models.Model):
    id = models.BigAutoField(primary_key=True)
    ad_id = models.BigIntegerField()
    channel_id = models.BigIntegerField()
    play_date = models.DateField()
    valid = models.IntegerField(blank=True, null=True, default=1)

    class Meta:
        managed = False
        db_table = 'first_play_date'
        unique_together = (('ad_id', 'channel_id'),)


class MatchResult(models.Model):
    id = models.BigAutoField(primary_key=True)
    ad_id = models.BigIntegerField()
    channel_id = models.BigIntegerField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    valid = models.IntegerField(blank=True, null=True, default=1)

    class Meta:
        managed = False
        db_table = 'match_result'


class User(models.Model):
    userid = models.AutoField(primary_key=True)
    user_name = models.CharField(unique=True, max_length=20)
    passwd = models.CharField(max_length=20)
    name = models.CharField(max_length=20, blank=True, null=True)
    phone_number = models.CharField(max_length=200, blank=True, null=True)
    email = models.CharField(unique=True, max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'user_tab'


class Rule(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=255)
    update_date = models.DateField()
    weekdays = models.CharField(max_length=1000)
    times = models.CharField(max_length=1000)
    cover_areas = models.CharField(max_length=1000)
    firm_names = models.CharField(max_length=1000)
    class_names = models.CharField(max_length=1000)
    tags = models.CharField(max_length=1000)
    channel_names = models.CharField(max_length=1000)
    valid = models.IntegerField(blank=True, null=True, default=1)

    class Meta:
        managed = False
        db_table = 'rule'

class Monitor(models.Model):
    id = models.BigAutoField(primary_key=True)
    type = models.CharField(max_length=255)
    ip = models.CharField(max_length=255)
    has_task = models.IntegerField(db_column="task")
    channel = models.CharField(max_length=255, db_column='task_on')
    problem = models.IntegerField()
    start_time = models.CharField(max_length=255, db_column='starttime')
    last_time = models.CharField(max_length=255, db_column='lasttime')

    class Meta:
        managed = False
        db_table = 'monitor'


class Task(models.Model):
    id = models.BigAutoField(primary_key=True)
    is_running = models.IntegerField(null=False)
    channel_id = models.BigIntegerField(db_column="channelid", null=False)
    monitor_id = models.BigIntegerField(db_column="monitorid", null=False)
    type = models.CharField(max_length=255, null=False)
    nas_ip = models.CharField(max_length=255, null=False, db_column="nas_Ip")
    start_time = models.CharField(max_length=255, db_column='starttime')
    end_time = models.CharField(max_length=255, db_column='endtime')
    ts_ip = models.CharField(max_length=255, null=False, db_column="ts_ip")
    ts_port = models.IntegerField(db_column="port")
    create_time = models.CharField(max_length=255, db_column='create_time')

    class Meta:
        managed = False
        db_table = 'task'
