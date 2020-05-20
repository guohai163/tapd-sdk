# -*- coding: utf-8 -*-
import pyodbc
import configparser
import log4p

LOG = log4p.GetLogger('Performance').logger


class Performance:
    _db_conn = None

    def __init__(self):
        db_config = configparser.ConfigParser()
        db_config.read('config.ini')
        db_ip = db_config['database']['sql_ip']
        db_user = db_config['database']['sql_user']
        db_pass = db_config['database']['sql_password']
        self._db_conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=' + db_ip +
                                       ';DATABASE=DevelopProjectManaDB;UID=' + db_user + ';PWD=' + db_pass)

    def query_project(self, project_name):
        """
        通过项目名获得项目编号
        :param project_name:
        :return:
        """
        sql = 'SELECT * FROM project_dev_manage_tb WHERE project_name=?'
        cursor = self._db_conn.cursor()
        row = cursor.execute(sql, project_name).fetchone()
        project = row
        cursor.close()
        return project

    def query_user_code(self, chinese_name):
        """
        通过中文名字查用户ID
        :param chinese_name:
        :return:
        """
        sql = 'SELECT user_id FROM user_relation_tb WHERE chinese_name=?'
        cursor = self._db_conn.cursor()
        row = cursor.execute(sql, chinese_name).fetchone()
        user_code = row.user_id
        cursor.close()
        return user_code

    def query_user_info(self, chinese_name):
        """
        通过用户中文名字取出用户岗位和编号
        :param chinese_name:
        :return:
        """
        sql = 'SELECT [user_code],[user_name],[type] FROM [project_personnel_type_tb] where [user_name]=?'
        cursor = self._db_conn.cursor()
        row = cursor.execute(sql, chinese_name).fetchone()
        user_code = row.user_code
        user_type = row.type
        cursor.close()
        return user_code, user_type

    def query_build_relation_info(self, project_name):
        """
        通过项目查询构建任务名
        :return:
        """
        sql = 'SELECT [code],[project_code],[project_name],[build_name],[type],doc_url FROM [tapd_build_relation_tb] ' \
              'WHERE project_name=?'
        cursor = self._db_conn.cursor()
        row = cursor.execute(sql, project_name).fetchall()
        cursor.close()
        return row

    def add_new_stories_many(self, stories, version, project_name, project_code, po_code):
        """
        批量增加故事
        :param stories:
        :param version:
        :param project_name:
        :param project_code:
        :param po_code:
        :return:
        """
        sql = 'INSERT INTO [user_stories_tb]([stories_no],[system_name],[content],[ac_num],[create_user],' \
              '[create_user_code],[create_time],[update_time],[system_code],[status],[is_del],[weight],[summary],' \
              '[version_num],[sn])VALUES(?,?,?,?,?,?,getdate(),getdate(),?,70,0,1,\'未分类\',?,?) '
        sql_parm = []
        for store in stories:
            sql_parm.append((store['Story']['id'], project_name, store['Story']['name'],
                             store['Story']['custom_field_81'], store['Story']['creator'], po_code, project_code,
                             version, store['Story']['size']))
        cursor = self._db_conn.cursor()
        try:
            self._db_conn.autocommit = False
            cursor.executemany(sql, sql_parm)
        except pyodbc.DatabaseError as err:
            self._db_conn.rollback()
        else:
            self._db_conn.commit()
        finally:
            self._db_conn.autocommit = True
            cursor.close()

    def add_new_stories(self, store, version, project_name, project_code, po_code):
        """
        插入一条故事记录，并返回插入的编号
        :param store:
        :param version:
        :param project_name:
        :param project_code:
        :param po_code:
        :return:
        """
        sql = 'INSERT INTO [user_stories_tb]([stories_no],[system_name],[content],[ac_num],[create_user],' \
              '[create_user_code],[create_time],[update_time],[system_code],[status],[is_del],[weight],[summary],' \
              '[version_num],[sn])VALUES(?,?,?,?,?,?,getdate(),getdate(),?,70,0,1,\'未分类\',?,?)'
        cursor = self._db_conn.cursor()
        self._db_conn.autocommit = True
        cursor.execute(sql, (store['Story']['id'], project_name, store['Story']['name'],
                             store['Story']['custom_field_81'], store['Story']['creator'], po_code, project_code,
                             version, store['Story']['size']))
        stories_code = cursor.execute('select @@IDENTITY as \'stories_code\'').fetchone()
        cursor.close()
        return int(stories_code.stories_code)

    def del_stories_from_version(self, version):
        """
        删除已经存在的故事
        :param version:
        :return:
        """
        cursor = self._db_conn.cursor()
        self._db_conn.autocommit = True
        sql = 'DELETE FROM user_stories_task_tb WHERE ' \
              'user_stories_code in (SELECT code FROM [user_stories_tb] WHERE [version_num]=?)'
        cursor.execute(sql, version)
        sql = 'DELETE FROM [user_stories_tb] WHERE [version_num]=?'
        cursor.execute(sql, version)
        cursor.close()

    def del_finished_project_from_version(self, version, project_code):
        """
        按版本删除
        :param project_code:
        :param version:
        :return:
        """
        cursor = self._db_conn.cursor()
        self._db_conn.autocommit = True
        sql = 'DELETE FROM finished_project_person_relation_tb WHERE ' \
              'project_code in (SELECT code FROM finished_project_report_tb WHERE project_version=? AND project_code=?)'
        cursor.execute(sql, version, project_code)
        sql = 'DELETE FROM finished_project_report_tb WHERE project_version=? AND project_code=?'
        cursor.execute(sql, version, project_code)
        cursor.close()

    def add_stories_task(self, story_code, story):
        """
        为故事增加任务
        :return:
        """
        sql = 'INSERT INTO [user_stories_task_tb]([user_stories_code],[create_user],[create_user_code],' \
              '[create_time],[status],[type],[is_del],[begin_time])VALUES(?,?,?,getdate(),20,?,0,getdate())'
        sql_parm = [(story_code, story['Story']['creator'], self.query_user_code(story['Story']['creator']), 'PO')]
        for task in story['Story']['owner'].split(';'):
            if task is None or task == '':
                continue
            user_code, user_type = self.query_user_info(task)
            sql_parm.append((story_code, task, user_code, user_type))
        print(sql_parm)
        cursor = self._db_conn.cursor()
        try:
            self._db_conn.autocommit = False
            cursor.executemany(sql, sql_parm)
        except pyodbc.DatabaseError as err:
            self._db_conn.rollback()
        else:
            self._db_conn.commit()
        finally:
            self._db_conn.autocommit = True
            cursor.close()

    def add_project_finished_reoprt(self, finish_month, project_content, project_info, iteration, po_id,
                                    iteration_score, iteration_day):
        """
        插入finished_project_report_tb表
        :param finish_month:
        :param project_content:
        :param project_info:
        :param iteration:
        :param po_id:
        :param iteration_score:
        :param iteration_day:
        :return:
        """
        sql = 'INSERT INTO finished_project_report_tb([finish_month],[project_content],[project_collection_code],' \
              '[project_code],[project_version],[plan_start_time],[plan_end_time],[practical_start_time],' \
              '[practical_end_time],[po_id],[po_name],[project_score],[project_score_person_id],' \
              '[project_level],[project_level_person_id],[project_level_time],[story_point],[work_overtime_hour],' \
              '[severe_bug_flag],[project_create_time],[project_create_persion_id],[delete_flag],[practical_days],' \
              '[cost_name],[project_level_desc],[value_point],[effect_create_time],[story_point2],[jsfzd_zy],' \
              '[syjz_zy],[kf_value],[plan_userstory_point],[real_userstory_point],[test_case])VALUES' \
              '(?,?,?,?,?,?,?,?,?,?,?,0,0,\'B\',3,getdate(),?,0,0,?,0,0,?,\'自动导入\',\'\',\'\',?,?,0,0,?,?,?,?)'
        sql_parm = (finish_month, ','.join(project_content), project_info.project_collection_code,
                    project_info.project_code, iteration[0]['name'], iteration[0]['startdate'],
                    iteration[0]['enddate'], iteration[0]['startdate'], iteration[0]['enddate'],
                    po_id, iteration[0]['creator'], iteration_score, iteration[0]['created'], iteration_day,
                    iteration[0]['created'], iteration_score, iteration_score, iteration_score, iteration_score,
                    iteration_score)

        cursor = self._db_conn.cursor()
        self._db_conn.autocommit = True
        cursor.execute(sql, sql_parm)
        finished_project_code = cursor.execute('select @@IDENTITY as \'finished_project_code\'').fetchone()
        cursor.close()
        return int(finished_project_code.finished_project_code)

    def add_project_finished_person(self, finished_project_code, iteration_user):
        sql = 'INSERT INTO [finished_project_person_relation_tb]([project_code],[person_id],[person_name_and_id])' \
              'VALUES(?,?,?)'
        sql_parm = []
        for task in iteration_user:
            if task is None or task == '':
                continue
            user_code, user_type = self.query_user_info(task)
            sql_parm.append((finished_project_code, user_code, '{}({})'.format(task, user_code)))
        cursor = self._db_conn.cursor()
        try:
            self._db_conn.autocommit = False
            cursor.executemany(sql, sql_parm)
        except pyodbc.DatabaseError as err:
            self._db_conn.rollback()
        else:
            self._db_conn.commit()
        finally:
            self._db_conn.autocommit = True
            cursor.close()
