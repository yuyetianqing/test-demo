# -*- coding: utf-8 -*-
"""
celery 任务示例

本地启动celery命令: python  manage.py  celery  worker  --settings=settings
周期性任务还需要启动celery调度命令：python  manage.py  celerybeat --settings=settings
"""
import time
import base64
import datetime

import os
from celery import task
from celery.schedules import crontab
from celery.task import periodic_task
from django.conf import settings

from blueking.component.shortcuts import get_client_by_user
from common.log import logger
from home_application.models import Check, Host


@periodic_task(run_every=crontab(minute='*/1', hour='*', day_of_week="*"))
def check_task():
    bk_biz_list = Host.objects.values_list('bk_biz_id', flat=True).distinct()
    for bk_biz_id in bk_biz_list:
        check_biz_task(bk_biz_id)


def check_biz_task(bk_biz_id):
    """
    定义一个 celery 异步任务
    """

    print 'check: %s' % bk_biz_id

    cmd = """
#!/bin/bash
MEMORY=$(free -m | awk 'NR==2{printf "%.2f%%", $3*100/$2 }')
DISK=$(df -h | awk '$NF=="/"{printf "%s", $5}')
CPU=$(top -bn1 | grep load | awk '{printf "%.2f%%", $(NF-2)}')
DATE=$(date "+%Y-%m-%d %H:%M:%S")
echo -e "$DATE|$MEMORY|$DISK|$CPU"
    """
    content = base64.b64encode(cmd)

    ip_list = [
        {
            "bk_cloud_id": host.bk_cloud_id,
            "ip": host.inner_ip,
        }
        for host in Host.objects.filter(bk_biz_id=bk_biz_id, auto_check=True)
    ]

    # APP信息app_code, app_secret如未提供，从环境配置获取
    client = get_client_by_user('admin')
    client.set_bk_api_ver('v2')
    # job_template = client.job.get_job_detail({'bk_biz_id': 2, 'bk_job_id': 1000})
    kwargs = {
        "bk_biz_id": bk_biz_id,
        "script_content": content,
        "script_type": 1,
        "script_param": base64.b64encode(""),
        "script_timeout": 10,
        "ip_list": ip_list,
        # 账号可以手动输入或者从cmdb拿
        "account": "root",
    }
    res = client.job.fast_execute_script(kwargs)
    if not res.get('result'):
        print res
        logger.error('start job failed: %s' % res.get('message'))
        return False

    # 查询状态
    retries = 0
    MAX_RETRY = 30
    task_id = res.get('data').get('job_instance_id')
    print 'check task_id is: %s' % task_id
    while not client.job.get_job_instance_status({
        'bk_biz_id': bk_biz_id,
        'job_instance_id': task_id,
    }).get('data').get('is_finished') and retries < MAX_RETRY:
        retries += 1
        logger.info('(%s/%s)waiting job finished...' % (retries, MAX_RETRY))
        time.sleep(2)

    # 查看日志
    res = client.job.get_job_instance_log({
        'bk_biz_id': bk_biz_id,
        'job_instance_id': task_id
    })

    # 分析每个ip的日志
    ip_logs = res['data'][0]['step_results'][0]['ip_logs']
    for ip_log in ip_logs:
        print 'check result: %s' % ip_log
        log_content = ip_log['log_content']
        bk_cloud_id = ip_log['bk_cloud_id']
        inner_ip = ip_log['ip']

        check_time, mem, disk, cpu = log_content.rstrip().split('|')
        check_time = datetime.datetime.strptime(check_time, '%Y-%m-%d %H:%M:%S')
        mem, disk, cpu = float(mem[:-1]), float(disk[:-1]), float(cpu[:-1])

        # 数据入库
        Check.objects.create(
            bk_biz_id=bk_biz_id,
            check_at=check_time,
            bk_cloud_id=bk_cloud_id,
            inner_ip=inner_ip,
            mem_used=mem,
            disk_used=disk,
            cpu_used=cpu,
        )


# @task
# def distribute_job(cmd="pwd", ip="192.168.1.17"):
#     bk_biz_id = 2
#     client = get_client_by_user('admin')
#     content = base64.b64encode(cmd)
#     ip_list = [{"ip": ip, "bk_cloud_id": "0"}]
#     kwargs = {
#         "bk_biz_id": bk_biz_id,
#         "script_content": base64.b64encode(content),
#         "script_type": 1,
#         "script_param": base64.b64encode(""),
#         "script_timeout": 3,
#         "ip_list": ip_list,
#         "account": "root",
#     }
#     job_id = client.job.fast_execute_script(kwargs)['data']['job_instance_id']
#     status_args = {"bk_biz_id": 2, "job_instance_id": job_id}
#     while True:
#         is_finished = client.job.get_job_job_instance_status(status_args)['data']['is_finished']
#         if is_finished:
#             break
#         time.sleep(0.5)
#     response = client.job.get_job_job_instance_log(status_args)
#     return response['data'][0]['step_results'][0]['ip_logs'][0]['log_content']
#
#
# @task()
# def async_task(x, y):
#     """
#     定义一个 celery 异步任务
#     """
#     logger.error(u"celery 定时任务执行成功，执行结果：{:0>2}:{:0>2}".format(x, y))
#     return x + y
#
#
# def execute_task():
#     """
#     执行 celery 异步任务
#
#     调用celery任务方法:
#         task.delay(arg1, arg2, kwarg1='x', kwarg2='y')
#         task.apply_async(args=[arg1, arg2], kwargs={'kwarg1': 'x', 'kwarg2': 'y'})
#         delay(): 简便方法，类似调用普通函数
#         apply_async(): 设置celery的额外执行选项时必须使用该方法，如定时（eta）等
#                       详见 ：http://celery.readthedocs.org/en/latest/userguide/calling.html
#     """
#     now = datetime.datetime.now()
#     logger.error(u"celery 定时任务启动，将在60s后执行，当前时间：{}".format(now))
#     # 调用定时任务
#     async_task.apply_async(args=[now.hour, now.minute], eta=now + datetime.timedelta(seconds=60))
#
#
# @periodic_task(run_every=crontab(minute='*/5', hour='*', day_of_week="*"))
# def get_time():
#     """
#     celery 周期任务示例
#
#     run_every=crontab(minute='*/5', hour='*', day_of_week="*")：每 5 分钟执行一次任务
#     periodic_task：程序运行时自动触发周期任务
#     """
#     execute_task()
#     now = datetime.datetime.now()
#     logger.error(u"celery 周期任务调用成功，当前时间：{}".format(now))
