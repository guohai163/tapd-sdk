# -*- coding: utf-8 -*-
import datetime
import re
import configparser
from export import ExportExcel

import log4p

from performance import Performance
from tapdsdk import Tapd

LOG = log4p.GetLogger('DOperating').logger


def compute_update_size(workspace_id, stories, iteration_id, tapd=None):
    """
    通过加载回来的得数计算AC+复杂度+规模
    :param iteration_id:
    :param tapd:
    :param workspace_id: 项目ID
    :param stories: 故事列表
    :return: 返回此迭代的总规模
    """
    size_sum = 0
    story_categories = tapd.get_story_categories(workspace_id)
    for story in stories:
        dev_num = 0
        s = story['Story']
        story_id = s['id']
        if s['category_id'] != '-1':
            category = [category['Category']['name'] for category in story_categories['data']
                        if category['Category']['id'] == s['category_id']]

            if category[0] == '单独打分任务':
                #  单独打分任务，分数全部直接给0
                tapd.set_stories_attribute(workspace_id, story_id, 'custom_field_81', 0)
                tapd.set_stories_attribute(workspace_id, story_id, 'custom_field_82', 0)
                tapd.set_stories_attribute(workspace_id, story_id, 'size', 0)
                continue
        ac_num = len(re.findall('ac-\d+\.', s['description']))
        if ac_num == 0:
            ac_num = len(re.findall('<div>\d+\.[^<]+</div>', s['description']))
        if ac_num == 0:
            ac_num = len(re.findall('<p>\d+\.[^<]+</p>', s['description']))
        if ac_num == 0:
            ac_num = len(re.findall('>?\d+\. [^<]+<?', s['description']))

        technical = re.search('技术复杂度[^0-9]+([0-9]+)', s['description'])
        tapd.set_stories_attribute(workspace_id, story_id, 'custom_field_81', ac_num)
        if technical is not None:
            dev_num = technical.group(1)
            tapd.set_stories_attribute(workspace_id, story_id, 'custom_field_82', dev_num)

        tapd.set_stories_attribute(workspace_id, story_id, 'size', ac_num + int(dev_num))
        size_sum += ac_num + int(dev_num)
    print('更新成功')
    compute_update_bug(workspace_id, size_sum, iteration_id, tapd)
    return size_sum


def compute_update_bug(workspace_id, size_sum, iteration_id, tapd=None):
    """
    计算BUG
    :param workspace_id:
    :param size_sum:
    :param iteration_id:
    :param tapd:
    :return:
    """
    bug_point = tapd.get_bug_count(workspace_id, iteration_id)

    result = tapd.set_iterate_attribute(workspace_id, iteration_id, 'custom_field_31', size_sum)
    result = tapd.set_iterate_attribute(workspace_id, iteration_id, 'custom_field_32', bug_point['data']['count'])


def crate_tapd_sdk():
    """
    初始化方法创建TAPD操作类
    :return:
    """
    config_base = configparser.ConfigParser()
    config_base.read('config.ini')
    tapd_user = config_base['base']['tapd_user']
    tapd_password = config_base['base']['tapd_password']
    return Tapd(tapd_user, tapd_password), config_base['base']['tapd_company_id']


def import_kpi(project, stories, iteration, kpi=None):
    """
    导入绩效体系
    :param project_name:
    :param kpi:
    :return:
    """
    if len(project[0]) == 0:
        return
    kpi.del_stories_from_version(iteration[0]['name'])
    project_info = kpi.query_project(project[0]['name'])
    po_code = kpi.query_user_code(stories[0]['Story']['creator'])
    # TODO 测试
    iteration_score = 0
    iteration_user = []
    for story in stories:
        story_code = kpi.add_new_stories(story, iteration[0]['name'], project[0]['name'], project_info.code,
                                         po_code)
        kpi.add_stories_task(story_code, story)
        iteration_score += int(story['Story']['size'])
        for task in story['Story']['owner'].split(';'):
            if task is None or task == '':
                continue
            if task not in iteration_user:
                iteration_user.append(task)
    kpi.del_finished_project_from_version(iteration[0]['name'], project_info.project_code)
    finish_month = datetime.datetime.strptime(iteration[0]['startdate'], "%Y-%m-%d").strftime('%Y-%m')
    project_content = [story['Story']['name'] for story in stories]
    iteration_start_date = datetime.datetime.strptime(iteration[0]['startdate'], "%Y-%m-%d")
    iteration_end_date = datetime.datetime.strptime(iteration[0]['enddate'], "%Y-%m-%d")
    # 计算天数，第1天也算为1 天，最后结果需要+1
    iteration_day = iteration_end_date.day - iteration_start_date.day + 1
    finished_project_code = kpi.add_project_finished_reoprt(finish_month, project_content, project_info, iteration,
                                                            po_code, iteration_score, iteration_day)
    kpi.add_project_finished_person(finished_project_code, iteration_user)


def update_all_size(workspaces, tapd=None):
    """
    批量更新 所有迭代的规模
    :param workspaces:
    :param tapd:
    :return:
    """
    for work in workspaces:
        if work['Workspace']['description'] == '运营开发部':

            iterations = tapd.get_iterate(work['Workspace']['id'])
            print('准备处理项目{},迭代数{}'.format(work['Workspace']['name'], len(iterations['data'])))
            if len(iterations['data']) == 0:
                print(iterations)
            for iteration in iterations['data']:
                print('\t准备处理迭代{}'.format(iteration['Iteration']['name']))
                iteration_date = datetime.datetime.strptime(iteration['Iteration']['startdate'], "%Y-%m-%d")
                now_date = datetime.date.today()
                if iteration_date.year == now_date.year and iteration_date.month == now_date.month:
                    print(iteration)
                    storie = tapd.get_stories(workspace_id=work['Workspace']['id'],
                                              iteration_id=iteration['Iteration']['id'])
                    compute_update_size(work['Workspace']['id'], storie['data'], tapd)


def main():
    kpi = Performance()
    tapd, tapd_company_id = crate_tapd_sdk()
    workspaces = tapd.get_projects(tapd_company_id)
    if workspaces['status'] == 1:
        print('请选择你要进入的项目')
        for work in workspaces['data']:
            if work['Workspace']['description'] == '运营开发部':
                print('[{}]. {}'.format(work['Workspace']['id'], work['Workspace']['name']))
        print('输入字母\n[a]开始更新所有本月故事的规模。\n[e]导出内在质量\n=======')
        input_workspace_id = input('请输入项目编号: ')
        # 准备遍历所有项目更新 规模
        if input_workspace_id == 'a':
            update_all_size(workspaces['data'], tapd)
            return
        if input_workspace_id == 'e':
            export = ExportExcel('/tmp/')
            export.intrinsic_quality('', '')
            return
        iterations = tapd.get_iterate(input_workspace_id)

        if iterations['status'] == 1 and len(iterations['data']) > 0:
            while True:
                print('======\n请选择迭代')
                for iteration in iterations['data']:
                    print('{}\t{}\t{}\t{}'.format(iteration['Iteration']['id'], iteration['Iteration']['name'],
                                                  iteration['Iteration']['startdate'],
                                                  iteration['Iteration']['status']))
                input_iteration_id = input('请输入迭代ID: ')

                while True:
                    storie = tapd.get_stories(workspace_id=input_workspace_id, iteration_id=input_iteration_id)
                    for sotry in storie['data']:
                        print('{}\t{}'.format(sotry['Story']['name'], sotry['Story']['size']))
                    print('======\n1. 更新项目规模\n2. 导出本迭代到xlsx\n3. 导出故事点数到绩效系统\n4. 更新BUG率\nb. 返回上一级\n0. 退出')
                    input_select_id = input('======\n请选择您要进行的操作：')
                    if input_select_id == '1':
                        compute_update_size(input_workspace_id, storie['data'], input_iteration_id, tapd)
                    elif input_select_id == '3':
                        project_name = [work['Workspace'] for work in workspaces['data'] if
                                        work['Workspace']['id'] == input_workspace_id]
                        version_num = [iteration['Iteration'] for iteration in iterations['data'] if
                                       iteration['Iteration']['id'] == input_iteration_id]
                        import_kpi(project_name, storie['data'], version_num, kpi)
                    elif input_select_id == '4':
                        compute_update_bug(input_workspace_id, storie['data'], input_iteration_id, tapd)
                    elif input_select_id == 'b':
                        break
                    elif input_select_id == '0':
                        return
        else:
            print('该项目无迭代存在')


if __name__ == '__main__':
    main()
