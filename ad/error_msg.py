json_format_error = {
    "status": -200,
    "msg": "传入json格式错误"
}

lack_param_error = {
    "status": -300,
    "msg": "缺少参数"
}
param_format_error = {
    "status": -301,
    "msg": "参数格式错误"
}

param_repeat_error = {
    "status": -401,
    "msg": "数据重复"
}
data_not_exist_error = {
    "status": -402,
    "msg": "未查找到数据"
}

not_enough_monitor = {
    "status": -403,
    "msg": "没有可用的monitor"
}

channel_not_found = {
    "status": -405,
    "msg": "没有找到频道，请确认频道名"
}

user_not_found = {
    "status": -406,
    "msg": "用户名不存在或密码错误"
}

system_error = {
    "status": -500,
    "msg": "系统错误"
}

user_not_login = {
    "status": -600,
    "msg": "用户未登陆"
}

user_access_error = {
    "status": -601,
    "msg": "没有权限"
}

success = {
    "status": 0,
    "msg": "success"
}
