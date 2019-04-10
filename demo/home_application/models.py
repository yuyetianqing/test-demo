# -*- coding: utf-8 -*-
from django.db import models


class Business(models.Model):
    """业务信息"""

    bk_biz_id = models.CharField(u'业务ID', max_length=16)
    bk_biz_name = models.CharField(u'业务名称', max_length=64)

    def __unicode__(self):
        return '{}.{}'.format(self.bk_biz_id,
                              self.bk_biz_name)

    class Meta:
        verbose_name = '业务信息'
        verbose_name_plural = '业务信息'


class Host(models.Model):
    """主机信息"""

    bk_biz_id = models.CharField(u'业务', max_length=16)
    bk_cloud_id = models.CharField(u'云区域', max_length=16)
    bk_os_type = models.CharField(u'系统类型', max_length=64, default='Linux')
    set_name = models.CharField(u'所属模块', max_length=64, blank=True, default='')
    module_name = models.CharField(u'所属模块', max_length=64, blank=True, default='')
    inner_ip = models.GenericIPAddressField(u'内网IP')
    add_at = models.DateTimeField(u'添加时间', auto_now_add=True)
    update_at = models.DateTimeField(u'更新时间', auto_now=True)
    auto_check = models.BooleanField(u'自动定时检查', default=False)

    def __unicode__(self):
        return '{}.{}.{}'.format(self.inner_ip,
                                 self.bk_biz_id,
                                 self.bk_cloud_id)

    class Meta:
        verbose_name = '主机信息'
        verbose_name_plural = '主机信息'


class Check(models.Model):
    """
    定时检查结果暂存
    """

    bk_biz_id = models.CharField(u'业务', max_length=16)
    bk_cloud_id = models.CharField(u'云区域', max_length=16)
    inner_ip = models.GenericIPAddressField(u'内网IP')
    mem_used = models.FloatField(u'mem')
    disk_used = models.FloatField(u'disk')
    cpu_used = models.FloatField(u'cpu')
    check_at = models.DateTimeField(u'time', auto_now_add=True)

    def __unicode__(self):
        return '{}.{}.{}.{}'.format(self.inner_ip,
                                    self.mem_used,
                                    self.disk_used,
                                    self.cpu_used)

    class Meta:
        verbose_name = '采集数据'
        verbose_name_plural = '采集数据'


class OptLog(models.Model):
    """操作记录信息"""
    operator = models.CharField(u'操作用户', max_length=128)
    bk_biz_id = models.CharField(u'业务', max_length=16)
    inner_ip = models.GenericIPAddressField(u'内网IP')
    opt_at = models.DateTimeField(u'操作时间', auto_now_add=True)
    opt_type = models.CharField(u'操作类型', max_length=64, choices=[
        ('check', '立即检查'),
        ('add_check', '加入自动检查'),
        ('remove_check', '取消自动检查'),
    ], default=0)

    def __unicode__(self):
        return '{}.{}.{}'.format(self.inner_ip,
                                 self.opt_type,
                                 self.opt_at)

    class Meta:
        verbose_name = '操作记录信息'
        verbose_name_plural = '操作记录信息'
