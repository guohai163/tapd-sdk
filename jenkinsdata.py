# -*- coding: utf-8 -*-
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
        :return:
        """
        # TODO: 需要增加try检查
        job = self._jenkins_conn.get_job(job_name)
        # TODO: 检查最后一次JOB的时间，如果不在上周，返回'上周未做'
        build = job.get_last_build()
        console = build.get_console()
        if console.find('SonarQube质量检查未通过'):
            sq = '未通过'
        elif console.find('SonarQube质量检查通过'):
            sq = '通过'
        else:
            sq = '未使用'

        # TODO: 检查单元测试状态
