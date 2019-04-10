# -*- coding: utf-8 -*-
import base64

import os
import time
import datetime

from django.conf import settings

from common.log import logger
from common.mymako import render_mako_context, render_json, render_mako_tostring
from blueking.component.shortcuts import get_client_by_request, get_client_by_user
from home_application.models import Host, OptLog, Check


def history(request):
    """
    操作历史
    """
    client = get_client_by_request(request)
    client.set_bk_api_ver('v2')

    # 查询业务
    res = client.cc.search_business()
    bk_biz_list = res.get('data').get('info')

    opt_list = OptLog.objects.order_by('-opt_at')
    return render_mako_context(request,
                               '/home_application/history.html', {
                                   'opt_list': opt_list,
                                   'bk_biz_list': bk_biz_list,
                               })


def home(request):
    """
    首页
    """
    client = get_client_by_request(request)
    client.set_bk_api_ver('v2')
    # 查询业务
    res = client.cc.search_business()

    if res.get('result', False):
        bk_biz_list = res.get('data').get('info')
    else:
        logger.error(u"请求业务列表失败：%s" % res.get('message'))
        bk_biz_list = []

    # 查询IP
    res = client.cc.search_host({
        "page": {"start": 0, "limit": 5, "sort": "bk_host_id"},
        "ip": {
            "flag": "bk_host_innerip|bk_host_outerip",
            "exact": 1,
            "data": []
        },
        "condition": [
            {
                "bk_obj_id": "host",
                "fields": [
                    # "bk_cloud_id",
                    # "bk_host_id",
                    # "bk_host_name",
                    # "bk_os_name",
                    # "bk_os_type",
                    # "bk_host_innerip",
                ],
                "condition": []
            },
            {"bk_obj_id": "module", "fields": [], "condition": []},
            {"bk_obj_id": "set", "fields": [], "condition": []},
            {
                "bk_obj_id": "biz",
                "fields": [
                    "default",
                    "bk_biz_id",
                    "bk_biz_name",
                ],
                "condition": [
                    {
                        "field": "bk_biz_id",
                        "operator": "$eq",
                        "value": 2
                    }
                ]
            }
        ]
    })

    if res.get('result', False):
        bk_host_list = res.get('data').get('info')
    else:
        bk_host_list = []
        logger.error(u"请求主机列表失败：%s" % res.get('message'))

    # print bk_host_list

    bk_host_list = [
        {
            'bk_host_innerip': host['host']['bk_host_innerip'],
            'bk_host_name': host['host']['bk_host_name'],
            'bk_host_id': host['host']['bk_host_id'],
            'bk_os_type': host['host']['bk_os_type'],
            'bk_os_name': host['host']['bk_os_name'],
            'bk_cloud_id': host['host']['bk_cloud_id'][0]['bk_inst_id'],
            'bk_cloud_name': host['host']['bk_cloud_id'][0]['bk_inst_name'],
            'bk_set_name': ' '.join(map(lambda x: x['bk_set_name'], host['set'])[:1]),
            'bk_module_name': ' '.join(map(lambda x: x['bk_module_name'], host['module'])[:1]),
        }
        for host in bk_host_list
    ]

    return render_mako_context(request,
                               '/home_application/home.html', {
                                   'bk_biz_list': bk_biz_list,
                                   'bk_host_list': bk_host_list
                               })


def get_host(request):
    """
    查询主机
    """

    bk_biz_id = int(request.GET.get('bk_biz_id'))
    ip_filter = request.GET.get('ip_filter')

    client = get_client_by_request(request)
    client.set_bk_api_ver('v2')

    # 查询IP
    res = client.cc.search_host({
        "page": {"start": 0, "limit": 5, "sort": "bk_host_id"},
        "ip": {
            "flag": "bk_host_innerip|bk_host_outerip",
            "exact": 1,
            "data": []
        },
        "condition": [
            {
                "bk_obj_id": "host",
                "fields": [
                    # "bk_cloud_id",
                    # "bk_host_id",
                    # "bk_host_name",
                    # "bk_os_name",
                    # "bk_os_type",
                    # "bk_host_innerip",
                ],
                "condition": []
            },
            {"bk_obj_id": "module", "fields": [], "condition": []},
            {"bk_obj_id": "set", "fields": [], "condition": []},
            {
                "bk_obj_id": "biz",
                "fields": [
                    "default",
                    "bk_biz_id",
                    "bk_biz_name",
                ],
                "condition": [
                    {
                        "field": "bk_biz_id",
                        "operator": "$eq",
                        "value": bk_biz_id
                    }
                ]
            }
        ]
    })

    bk_host_list = [
        {
            'bk_host_innerip': i['host']['bk_host_innerip'],
            'bk_host_name': i['host']['bk_host_name'],
            'bk_host_id': i['host']['bk_host_id'],
            'bk_os_type': i['host']['bk_os_type'],
            'bk_os_name': i['host']['bk_os_name'],
            'bk_cloud_id': i['host']['bk_cloud_id'][0]['bk_inst_id'],
            'bk_cloud_name': i['host']['bk_cloud_id'][0]['bk_inst_name'],
            'bk_set_name': ' '.join(map(lambda x: x['bk_set_name'], i['set'])[:1]),
            'bk_module_name': ' '.join(map(lambda x: x['bk_module_name'], i['module'])[:1]),
        }
        for i in res.get('data').get('info')
    ]

    if ip_filter:
        bk_host_list = filter(lambda host: ip_filter in host['bk_host_innerip'], bk_host_list)

    data = render_mako_tostring('/home_application/tbody-ip.html', {
        'bk_host_list': bk_host_list
    })

    return render_json({
        'result': True,
        'data': data
    })


def check_host(request):
    """立刻检查"""

    bk_biz_id = int(request.POST.get('bk_biz_id'))
    bk_host_innerip = request.POST.get('bk_host_innerip')
    bk_cloud_id = request.POST.get('bk_cloud_id')

    start = time.time()

    # 创建操作记录
    OptLog.objects.create(
        operator=request.user.username,
        bk_biz_id=bk_biz_id,
        inner_ip=bk_host_innerip,
        opt_type='check'
    )

    client = get_client_by_request(request)
    client.set_bk_api_ver('v2')

    with open(os.path.join(settings.PROJECT_ROOT, 'stat.sh'), 'r') as script:
        script_content = script.read()

    res = client.job.fast_execute_script({
        'bk_biz_id': bk_biz_id,
        'ip_list': [{
            "bk_cloud_id": bk_cloud_id,
            "ip": bk_host_innerip
        }],
        'account': 'root',
        'script_type': 1,
        'script_content': base64.b64encode(script_content),
        'script_param': '',
    })

    if not res.get('result'):
        return render_json(res)

    task_id = res.get('data').get('job_instance_id')
    while not client.job.get_job_instance_status({
        'bk_biz_id': bk_biz_id,
        'job_instance_id': task_id,
    }).get('data').get('is_finished'):
        print 'waiting job finished...'
        time.sleep(1.2)

    res = client.job.get_job_instance_log({
        'bk_biz_id': bk_biz_id,
        'job_instance_id': task_id
    })

    log_content = res['data'][0]['step_results'][0]['ip_logs'][0]['log_content']

    return render_json({
        'result': True,
        'data': {
            'time': datetime.datetime.now().strftime('%Y/%m/%d/%H:%M:%S'),
            'log': log_content
        },
        'message': '%s: elapsed %ss' % (res.get('message'), round(time.time() - start, 2))
    })


def host_stat(request):
    """主机状态"""
    client = get_client_by_request(request)
    client.set_bk_api_ver('v2')

    # 查询业务
    res = client.cc.search_business()
    bk_biz_list = res.get('data').get('info')

    return render_mako_context(request, '/home_application/host_stat.html', {
        'bk_biz_list': bk_biz_list,
    })


def add_check_host(request):
    bk_biz_id = request.POST.get('bk_biz_id')
    bk_host_innerip = request.POST.get('bk_host_innerip')
    bk_cloud_id = request.POST.get('bk_cloud_id')

    # 创建操作记录
    OptLog.objects.create(
        operator=request.user.username,
        bk_biz_id=bk_biz_id,
        inner_ip=bk_host_innerip,
        opt_type='add_check'
    )

    obj, updated = Host.objects.update_or_create(
        defaults={
            'auto_check': True
        },
        bk_biz_id=bk_biz_id,
        bk_cloud_id=bk_cloud_id,
        inner_ip=bk_host_innerip
    )

    return render_json({
        'result': True,
        'data': updated,
        'message': 'add success'
    })


def remove_check_host(request):
    bk_biz_id = request.POST.get('bk_biz_id')
    bk_host_innerip = request.POST.get('bk_host_innerip')
    bk_cloud_id = request.POST.get('bk_cloud_id')

    # 创建操作记录
    OptLog.objects.create(
        operator=request.user.username,
        bk_biz_id=bk_biz_id,
        inner_ip=bk_host_innerip,
        opt_type='remove_check'
    )

    obj, updated = Host.objects.update_or_create(
        defaults={
            'auto_check': False
        },
        bk_biz_id=bk_biz_id,
        bk_cloud_id=bk_cloud_id,
        inner_ip=bk_host_innerip
    )

    return render_json({
        'result': True,
        'data': updated,
        'message': 'remove success'
    })


def get_host_stat(request):
    """获取主机状态"""

    time_since = datetime.datetime.now() - datetime.timedelta(minutes=10)
    checks = Check.objects.filter(check_at__gte=time_since)
    check_ip_list = checks.values_list('inner_ip', flat=True).distinct()

    data = []
    for ip in check_ip_list:
        checks_ip = checks.filter(inner_ip=ip)
        x_axis, cpu, mem, disk = [], [], [], []

        for check in checks_ip:
            x_axis.append(check.check_at.strftime('%H:%M:%S'))
            cpu.append(check.cpu_used)
            mem.append(check.mem_used)
            disk.append(check.disk_used)

        data.append({
            'ip': ip,
            'x_axis': x_axis,
            'series': [
                {
                    'name': 'cpu',
                    'type': 'line',
                    'data': cpu
                },
                {
                    'name': 'mem',
                    'type': 'line',
                    'data': mem
                },
                {
                    'name': 'disk',
                    'type': 'line',
                    'data': disk
                },

            ],
        })

    return render_json({
        'result': True,
        'data': data
    })
