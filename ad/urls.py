from django.urls import path

from ad.api_views import config_view
from .api_views import ad_class_view, channel_view, charge_view, ad_view, firm_view, \
    rule_view, match_result_view, monitor_view, task_view, user_view, program_view

urlpatterns = [
    path('catg/get', ad_class_view.get),
    path('catg/get_by_id', ad_class_view.get_by_id),
    path('catg/add', ad_class_view.add),
    path('catg/update', ad_class_view.update),
    path('catg/delete', ad_class_view.delete),

    path('channel/get', channel_view.get),
    path('channel/get_by_id', channel_view.get_by_id),
    path('channel/add', channel_view.add),
    path('channel/update', channel_view.update),
    path('channel/delete', channel_view.delete),

    path('charge/get', charge_view.get),
    path('charge/get_by_id', charge_view.get_by_id),
    path('charge/add', charge_view.add),
    path('charge/update', charge_view.update),
    path('charge/delete', charge_view.delete),

    path('program/get', program_view.get),
    path('program/get_by_id', program_view.get_by_id),
    path('program/add', program_view.add),
    path('program/update', program_view.update),
    path('program/delete', program_view.delete),

    path('firm/get', firm_view.get),
    path('firm/add', firm_view.add),
    path('firm/update', firm_view.update),
    path('firm/delete', firm_view.delete),

    path('ad/get', ad_view.get),
    path('ad/get_by_id', ad_view.get_by_id),
    path('ad/add', ad_view.add),
    path('ad/update', ad_view.update),
    path('ad/delete', ad_view.delete),

    path('rule/get', rule_view.get),
    path('rule/add', rule_view.add),
    path('rule/update', rule_view.update),
    path('rule/delete', rule_view.delete),
    path('rule/hint', rule_view.hint),

    path('match_result/get', match_result_view.get),
    path('match_result/download', match_result_view.download),

    path('monitor/status', monitor_view.status),

    path('task/add', task_view.add),
    path('task/get', task_view.get),
    path('task/cancel', task_view.cancel),
    path('task/get_all_running', task_view.get_all_running),

    path('user/login', user_view.login),
    path('user/logout', user_view.logout),
    path('user/need_login', user_view.need_login_msg),
    path('user/add', user_view.add),
    path('user/delete', user_view.delete),
    path('user/get', user_view.get),
    path('user/get_by_id', user_view.get_by_id),
    path('user/update', user_view.update),
    path('user/access_error', user_view.access_error),
    path('user/change_password', user_view.change_password),

    path('config/get', config_view.get),
    path('config/update', config_view.update),
]
