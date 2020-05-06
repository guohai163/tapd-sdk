# -*- coding: utf-8 -*-
import json

import requests
import log4p

LOG = log4p.GetLogger('DOperating').logger
API_BASE = 'https://api.tapd.cn'


class Tapd:
    _api_user = None
    _api_password = None

    def __init__(self, api_user, api_password):
        self._api_user = api_user
        self._api_password = api_password

    def _request_api_get(self, method, parms):
        """
        网络请求GET公共类
        :param method:
        :param parms:
        :return:
        """
        req = requests.get("{0}{1}?{2}".format(API_BASE, method, parms), auth=(self._api_user, self._api_password))
        return json.loads(req.content.decode('utf8'))

    def _subject_api_post(self, method, parms):
        """
        网络请求POST公共类
        :param method:
        :param parms:
        :return:
        """
        req = requests.post(url='{}{}'.format(API_BASE, method), data=parms, auth=(self._api_user, self._api_password))
        return json.loads(req.content.decode('utf8'))

    def get_projects(self, company_id):
        """
        获取公司项目列表
        :param company_id:公司ID
        :return:
        """
        method = '/workspaces/projects'
        parm = 'company_id={0}'.format(company_id)
        return self._request_api_get(method, parm)

    def get_iterate(self, workspace_id):
        """
        获取迭代列表
        :param workspace_id:项目ID
        :return:
        """
        method = '/iterations'
        parm = 'workspace_id={}&fields={}'.format(workspace_id, 'id,name,startdate,enddate,status,status')
        return self._request_api_get(method, parm)

    def get_stories(self, workspace_id, iteration_id):
        """
        获取需求列表
        :param workspace_id:项目ID
        :param iteration_id:迭代ID
        :return:
        """
        method = '/stories'
        parm = 'workspace_id={}&iteration_id={}&fields={}'.format(workspace_id, iteration_id,
                                                                  'id,name,status,size,category_id,type')
        return self._request_api_get(method, parm)
