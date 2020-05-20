# -*- coding: utf-8 -*-
import datetime
import re
import configparser
import sys

from export import ExportExcel
import getopt
import log4p

from jenkinsdata import JenkinsData
from performance import Performance
from tapdsdk import Tapd

LOG = log4p.GetLogger('DOperating').logger


def usage():
    print("""python main.py [option]
    --help       : 打印帮助
    --update-size: 更新本月迭代规模数
    --send-excel : 发送上周质量报告
    """)


def get_parm(parm):
    """
    获取启动参数
    :param parm:
    :return:
    """
    try:
        optlist, args = getopt.getopt(parm, 'h', ['update-size', 'send-excel', 'help', 'jenkins'])
    except getopt.GetoptError as err:
        print(str(err))
        sys.exit(1)
    for o, a in optlist:
        if o == '--help':
            usage()
            sys.exit()
        elif o == '--update-size':
            return 'update-size'
        elif o == '--send-excel':
            return 'send-excel'
        elif o == '--jenkins':
            return 'jenkins'


def send_weekly_report(workspaces, tapd=None, export=None, kpi=None):
    intrinsic_quality_data = []
    personnel_data = {}
    jenkins_server11 = JenkinsData()
    for work in workspaces:
        if work['Workspace']['description'] == '运营开发部':
            print('[{}]. {}'.format(work['Workspace']['id'], work['Workspace']['name']))
            iterations = tapd.get_iterate(work['Workspace']['id'])
            for iteration in iterations['data']:
                print('准备处理迭代{}'.format(iteration['Iteration']['name']))
                # 计算迭代是否在计算范围内
                iteration_start_date = datetime.datetime.strptime(iteration['Iteration']['startdate'],
                                                                  "%Y-%m-%d").date()
                iteration_end_date = datetime.datetime.strptime(iteration['Iteration']['enddate'], "%Y-%m-%d").date()
                now_date = datetime.date.today()
                if iteration_start_date >= (now_date - datetime.timedelta(days=10)) and iteration_end_date < now_date:
                    print(iteration['Iteration']['name'])
                    storie = tapd.get_stories(workspace_id=work['Workspace']['id'],
                                              iteration_id=iteration['Iteration']['id'])
                    story_categories = tapd.get_story_categories(work['Workspace']['id'])
                    size_sum = 0
                    for story in storie['data']:
                        s = story['Story']
                        if s['category_id'] != '-1':
                            category = [category['Category']['name'] for category in story_categories['data']
                                        if category['Category']['id'] == s['category_id']]
                            if category[0] == '单独打分任务':
                                continue
                        size_sum += len(re.findall('ac-\d', s['description'], re.IGNORECASE))
                        # 给人员增加故事点数
                        for person in story['Story']['owner'].split(';'):
                            if person is None or person == '':
                                continue
                            person_key = '{}|{}|{}'.format(person, work['Workspace']['id'],
                                                           iteration['Iteration']['id'])
                            if personnel_data.get(person_key) is None:
                                personnel_data[person_key] = [person, work['Workspace']['name'],
                                                              iteration['Iteration']['name'],
                                                              iteration['Iteration']['startdate'],
                                                              iteration['Iteration']['startdate'],
                                                              size_sum, 0, 0.0]
                            else:
                                personnel_data[person_key][5] = personnel_data[person_key][5] + size_sum

                    bug_sum = tapd.get_bug_count(work['Workspace']['id'], iteration['Iteration']['id'])['data']['count']
                    if size_sum == 0:
                        bug_raite = 0
                    else:
                        bug_raite = bug_sum / size_sum
                    # 准备为个人赋值BUG数
                    bug_list = tapd.get_bug(work['Workspace']['id'], iteration['Iteration']['id'])
                    for bug in bug_list['data']:
                        if bug['Bug']['current_owner'] is None:
                            continue
                        for person in bug['Bug']['current_owner'].split(';'):
                            if person is None or person == '':
                                continue
                            # person_info = kpi.query_user_info(person)
                            # if person_info[1] == 'TEST' or person_info[1] == 'PO':
                            #     continue
                            person_key = '{}|{}|{}'.format(person, work['Workspace']['id'],
                                                           iteration['Iteration']['id'])
                            if personnel_data.get(person_key) is None:
                                personnel_data[person_key] = [person, work['Workspace']['name'],
                                                              iteration['Iteration']['name'],
                                                              iteration['Iteration']['startdate'],
                                                              iteration['Iteration']['enddate'],
                                                              0, 1, 0.0]
                            else:
                                personnel_data[person_key][6] = personnel_data[person_key][6] + 1

                    # TODO: 通过Jenkins收集质量数据
                    build_data = kpi.query_build_relation_info(work['Workspace']['name'])
                    jenkins_data = {'sut': '', 'fut': '', 'cut': '',
                                    'ssq': '', 'fsq': '', 'csq': '',
                                    'sci': '', 'fci': '', 'cci': ''}
                    doc_url = ''
                    if len(build_data) > 0:
                        for build in build_data:
                            if build.type == 'server':
                                sq, ut, ci = jenkins_server11.get_intrinsic_quality(build.build_name)
                                jenkins_data['sut'] = ut
                                jenkins_data['ssq'] = sq
                                jenkins_data['sci'] = ci
                                doc_url = build.doc_url
                            elif build.type == 'web':
                                sq, ut, ci = jenkins_server11.get_intrinsic_quality(build.build_name)
                                jenkins_data['fut'] = ut
                                jenkins_data['fsq'] = sq
                                jenkins_data['fci'] = ci
                            elif build.type == 'client':
                                sq, ut, ci = jenkins_server11.get_intrinsic_quality(build.build_name)
                                jenkins_data['cut'] = '{}:{}\n{}'.format(build.build_name, jenkins_data['cut'], ut)
                                jenkins_data['csq'] = '{}:{}\n{}'.format(build.build_name, jenkins_data['csq'], sq)
                                jenkins_data['cci'] = '{}:{}\n{}'.format(build.build_name, jenkins_data['cci'], ci)



                    # 要保存的数据，项目名、版本号、版本开始时间、版本结束时间、单元测试、SQ、性能测试、是否可以使用集成环境、是否完善文档
                    intrinsic_quality_data.append((work['Workspace']['name'], iteration['Iteration']['name'],
                                                   iteration['Iteration']['startdate'],
                                                   iteration['Iteration']['enddate'],
                                                   jenkins_data['sut'], jenkins_data['fut'], jenkins_data['cut'],
                                                   jenkins_data['ssq'], jenkins_data['fsq'], jenkins_data['csq'],
                                                   '上一版本没有性能测试',
                                                   jenkins_data['sci'], jenkins_data['fci'], jenkins_data['cci'],
                                                   doc_url,
                                                   size_sum, bug_sum, bug_raite))
    if len(intrinsic_quality_data) > 0:
        result_path = export.intrinsic_quality(intrinsic_quality_data)
        print(result_path)
        bug_result_path = export.weekly_report_bug(personnel_data)
        print(bug_result_path)
    else:
        LOG.debug('没有需要导出的数据')


def compute_update_size(workspace_id, stories, iteration_id=None, tapd=None):
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
        ac_num = len(re.findall('ac-\d', s['description'], re.IGNORECASE))
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
    # compute_update_bug(workspace_id, size_sum, iteration_id, tapd)
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
                    compute_update_size(work['Workspace']['id'], storie['data'], tapd=tapd)


def main():
    """
    主方法
    :return:
    """
    start_parm = get_parm(sys.argv[1:])
    tapd, tapd_company_id = crate_tapd_sdk()
    workspaces = tapd.get_projects(tapd_company_id)
    export = ExportExcel('/tmp/')
    # 初始化KPI操作对象
    kpi = Performance()
    if workspaces['status'] != 1:
        print('返回数据错误{}'.format(workspaces))
        return
    if start_parm == 'update-size':
        update_all_size(workspaces['data'], tapd)
        return
    elif start_parm == 'send-excel':
        print('===============\n准备制作每周报表\n===============\n')
        send_weekly_report(workspaces['data'], tapd, export, kpi)
        return

    if workspaces['status'] == 1:
        print('请选择你要进入的项目')
        for work in workspaces['data']:
            if work['Workspace']['description'] == '运营开发部':
                print('[{}]. {}'.format(work['Workspace']['id'], work['Workspace']['name']))
        print('输入字母\n[e]导出内在质量\n=======')
        input_workspace_id = input('请输入项目编号: ')

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
