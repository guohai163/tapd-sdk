# -*- coding: utf-8 -*-
import json
import time

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
        time.sleep(1)
        req = requests.get("{0}{1}?{2}".format(API_BASE, method, parms), auth=(self._api_user, self._api_password))
        return json.loads(req.content.decode('utf8'))

    def _subject_api_post(self, method, parms):
        """
        网络请求POST公共类
        :param method:
        :param parms:
        :return:
        """
        time.sleep(1)
        req = requests.post('{}{}'.format(API_BASE, method), parms, auth=(self._api_user, self._api_password))
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
        parm = 'workspace_id={}'.format(workspace_id)
        return self._request_api_get(method, parm)

    def get_stories(self, workspace_id, iteration_id):
        """
        获取需求列表
        :param workspace_id:项目ID
        :param iteration_id:迭代ID
        :return:
        """
        method = '/stories'
        parm = 'workspace_id={}&iteration_id={}'.format(workspace_id, iteration_id)
                                                                  # 'id,name,status,size,category_id,type,description')
        return self._request_api_get(method, parm)

    # def get_stories(self, workspace_id, name):
    #     method = '/stories'
    #     parm = 'workspace_id={}&name={}&fields={}'.format(workspace_id, name, 'id,name,status,size,category_id,type')
    #     return self._request_api_get(method, parm)

    def set_stories_attribute(self, workspace_id, stories_id, attribute, value):
        """
        更新属性
        :param workspace_id:
        :param stories_id:
        :param attribute:
        :param value:
        :return:
        """
        method = '/stories'
        parm = {'workspace_id': workspace_id, 'id': stories_id, attribute: value}
        return self._subject_api_post(method, parm)

    def set_iterate_attribute(self, workspace_id, iteration_id, attribute, value):
        """
        更新指定迭代的属性
        :param workspace_id:
        :param iteration_id:
        :param attribute:
        :param value:
        :return:
        """
        method = '/iterations'
        parm = {'workspace_id': workspace_id, 'id': iteration_id, 'current_user': 'guohai', attribute: value}
        return self._subject_api_post(method, parm)

    def get_bug_count(self, workspace_id, iteration_id):
        """
        计算符合查询条件的缺陷数量并返回
        :param workspace_id:
        :param iteration_id:
        :return:
        """
        method = '/bugs/count'
        parm = 'workspace_id={}&iteration_id={}'.format(workspace_id, iteration_id)
        return self._request_api_get(method, parm)

    def get_bug(self, workspace_id, iteration_id):
        """
        返回符合查询条件的所有缺陷
        :param workspace_id:
        :return:
        """
        method = '/bugs'
        parm = 'workspace_id={}&iteration_id={}'.format(workspace_id, iteration_id)
        return self._request_api_get(method, parm)

    def get_story_categories(self, workspace_id):
        """
        获取指定项目的需求分类
        :param workspace_id:
        :return:
        """
        method = '/story_categories'
        parm = 'workspace_id={}'.format(workspace_id)
        return self._request_api_get(method, parm)
