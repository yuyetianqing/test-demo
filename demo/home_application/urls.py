# -*- coding: utf-8 -*-

from django.conf.urls import patterns

urlpatterns = patterns(
    'home_application.views',
    (r'^$', 'home'),
    (r'^get_host/$', 'get_host'),
    (r'^check_host/$', 'check_host'),
    (r'^add_check_host/$', 'add_check_host'),
    (r'^remove_check_host/$', 'remove_check_host'),
    (r'^host_stat/$', 'host_stat'),
    (r'^get_host_stat/$', 'get_host_stat'),
    (r'^history/$', 'history'),
)

# expose api
urlpatterns += patterns(
    'home_application.views',
    # (r'^api/get_test_data/$', 'get_test_data'),
)
