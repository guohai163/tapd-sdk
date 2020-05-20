# -*- coding: utf-8 -*-
import datetime
import json
import re

import jenkinsapi
import pytz
import requests
from jenkinsapi.jenkins import Jenkins
import ramlfications


# 需要修改jenkins工具的build.py文件 502行，修改返回的编码格式

class JenkinsData:
    _jenkins_conn = None
    _sonarqube_server = 'http://192.168.6.8:9000'

    def __init__(self):
        jenkins_server = 'http://192.168.6.11:8080'
        self._jenkins_conn = Jenkins(baseurl=jenkins_server, username='xieshuyu', password='xieshuyu', timeout=1000)

    def _get_sonarqube_data(self, project_key):
        """
        通过SQ取代码质量
        :param project_key:
        :return:
        """
        req = requests.get("{}/api/measures/component?additionalFields=metrics,"
                           "periods&componentKey={}&metricKeys=alert_status,quality_gate_details,"
                           "bugs,new_bugs,reliability_rating,new_reliability_rating,vulnerabilities,"
                           "new_vulnerabilities,security_rating,new_security_rating,code_smells,new_code_smells,"
                           "sqale_rating,new_maintainability_rating,sqale_index,new_technical_debt,coverage,"
                           "new_coverage,new_lines_to_cover,tests,duplicated_lines_density,new_duplicated_lines_density,"
                           "duplicated_blocks,ncloc,ncloc_language_distribution,projects"
                           .format(self._sonarqube_server, project_key))
        sonarquebe_json = json.loads(req.content.decode('utf8'))

        bugs = [s['value'] for s in sonarquebe_json['component']['measures'] if s['metric'] == 'bugs'][0]
        code_smells = [s['value'] for s in sonarquebe_json['component']['measures'] if s['metric'] == 'code_smells'][0]
        vulnerabilities = [s['value'] for s in sonarquebe_json['component']['measures'] if s['metric'] == 'vulnerabilities'][0]
        return bugs, vulnerabilities, code_smells

    def get_raml_data(self, url):
        api = ramlfications.parse('http://git.gyyx.cn/doc/raml-apis/raw/master/cospower/external-gateway/bak-cos-power-account.raml')
        print(api)


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
        # 检查最后一次JOB的时间，如果不在上周，返回'上周未做'
        build = job.get_last_build()
        build_time = build.get_timestamp()
        now_date = datetime.datetime.now().replace(tzinfo=pytz.timezone('UTC'))
        if build_time < (now_date - datetime.timedelta(days=7)) or build_time > now_date:
            return '上周未做构建', '上周未做构建', '使用CI'

        console = build.get_console()
        if console.find('SonarQube质量检查未通过') > 0:
            sq = '未通过'
            sq_result = re.search('/dashboard/index/(.+)', console).group(1)
            print(sq_result)
            bugs, vulnerabilities, code_smells = self._get_sonarqube_data(sq_result)
            sq = '未通过，BUG:{},漏洞:{},坏味道:{}'.format(bugs, vulnerabilities, code_smells)
        elif console.find('SonarQube质量检查通过') > 0:
            sq = '通过'
            sq_result = re.search('/dashboard/index/(.+)', console).group(1)
            print(sq_result)
            bugs, vulnerabilities, code_smells = self._get_sonarqube_data(sq_result)
            sq = '通过，BUG:{},漏洞:{},坏味道:{}'.format(bugs, vulnerabilities, code_smells)
        else:
            sq = '未使用'

        # TODO: 检查单元测试状态
        if console.find('单元测试阶段被跳过') > 0:
            ut = '单元测试阶段被跳过'
        elif console.find('覆盖率统计') > 0:
            # 进行了单元测试
            ut_result = re.search('Overall coverage: (.+)', console).group(1)
            ut = '使用了单元测试，{}'.format(ut_result)
        else:
            ut = '未配置单元测试'

        return sq, ut, '使用了CI'
