# -*- coding: utf-8 -*-
import datetime

import jenkinsapi
import pytz
from jenkinsapi.jenkins import Jenkins


# 需要修改jenkins工具的build.py文件 502行，修改返回的编码格式

class JenkinsData:
    _jenkins_conn = None

    def __init__(self):
        jenkins_server = 'http://192.168.6.11:8080'
        self._jenkins_conn = Jenkins(baseurl=jenkins_server, username='xieshuyu', password='xieshuyu', timeout=1000)

    def get_intrinsic_quality(self, job_name):
        """
        获取内部质量情况
        :param job_name:
        :return: sq,ut,ci
        """
        try:
            job = self._jenkins_conn.get_job(job_name)
        except jenkinsapi.custom_exceptions.UnknownJob as err:
            print(err)
            return '-', '-', '没有配置CI'

        # if iteration_start_date >= (now_date - datetime.timedelta(days=7)) and iteration_end_date < now_date:
        # TODO: 检查最后一次JOB的时间，如果不在上周，返回'上周未做'
        build = job.get_last_build()
        build_time = build.get_timestamp()
        now_date = datetime.datetime.now().replace(tzinfo=pytz.timezone('UTC'))
        if build_time < (now_date - datetime.timedelta(days=7)) or build_time > now_date:
            return '上周未做构建', '上周未做构建', '使用CI'

        console = build.get_console()
        if console.find('SonarQube质量检查未通过'):
            sq = '未通过'
        elif console.find('SonarQube质量检查通过'):
            sq = '通过'
        else:
            sq = '未使用'

        # TODO: 检查单元测试状态
