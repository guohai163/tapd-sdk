# -*- coding: utf-8 -*-
import uuid

import log4p
import xlsxwriter


LOG = log4p.GetLogger('Export').logger


class ExportExcel:
    _cache_path = None

    def __init__(self, cache_path):
        self._cache_path = cache_path

    def weekly_report_bug(self, data):
        """
        第周BUG统计
        :param data:
        :return:
        """
        xlsx_path = self._cache_path + '/' + str(uuid.uuid1()) + '.xlsx'
        workbook = xlsxwriter.Workbook(xlsx_path)
        title_fromat = workbook.add_format({'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter',
                                            'bg_color': 'yellow'})

        worksheet = workbook.add_worksheet('版本内部质量统计表')
        worksheet.merge_range('A1:I1', '每周每人BUG统计', title_fromat)

        worksheet.write('A2', '序号', title_fromat)
        worksheet.write('B2', '姓名', title_fromat)
        worksheet.write('C2', '项目名称', title_fromat)
        worksheet.write('D2', '版本号', title_fromat)
        worksheet.write('E2', '版本开始时间', title_fromat)
        worksheet.write('F2', '版本结束时间', title_fromat)
        worksheet.write('G2', '个人完成用户故事点数', title_fromat)
        worksheet.write('H2', '个人BUG数量', title_fromat)
        worksheet.write('I2', '个人BUG率', title_fromat)
        row_index = 0
        for row_data in data:
            worksheet.write(row_index + 2, 0, row_index + 1)
            for cell_index in range(len(data[row_data])):
                # TODO: 这里不严谨为了偷懒应该放在主方法里
                if cell_index == 7 and int(data[row_data][5]) != 0:
                    bug_ratio = float(data[row_data][6]) / float(data[row_data][5])
                    worksheet.write(row_index + 2, cell_index + 1, bug_ratio)
                else:
                    worksheet.write(row_index + 2, cell_index + 1, data[row_data][cell_index])
            row_index += 1

        workbook.close()
        print('weekly_report_bug文件[{}]书写成功'.format(xlsx_path))

    def intrinsic_quality(self, data):
        """
        内部质量存档
        :param data:
        :param mail:
        :return:
        """

        xlsx_path = self._cache_path + '/' + str(uuid.uuid1()) + '.xlsx'
        workbook = xlsxwriter.Workbook(xlsx_path)
        title_fromat = workbook.add_format({'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter',
                                            'bg_color': 'yellow'})

        worksheet = workbook.add_worksheet('版本内部质量统计表')
        # 写表头部分
        # worksheet.write('A1', '版本内部质量统计表', bold)
        worksheet.merge_range('A1:S1', '版本内部质量统计表', title_fromat)
        worksheet.merge_range('A2:A3', '序号', title_fromat)
        worksheet.merge_range('B2:B3', '项目名称', title_fromat)
        worksheet.merge_range('C2:C3', '版本号', title_fromat)
        worksheet.merge_range('D2:D3', '版本开始时间', title_fromat)
        worksheet.merge_range('E2:E3', '版本结束时间', title_fromat)
        worksheet.merge_range('F2:H2', '单元测试覆盖度', title_fromat)
        worksheet.write('F3', '服务器', title_fromat)
        worksheet.write('G3', '前  端', title_fromat)
        worksheet.write('H3', '客户端', title_fromat)
        worksheet.merge_range('I2:K2', 'SQ检查结果', title_fromat)
        worksheet.write('I3', '服务器', title_fromat)
        worksheet.write('J3', '前  端', title_fromat)
        worksheet.write('K3', '客户端', title_fromat)
        worksheet.merge_range('L2:L3', '性能测试是否通过', title_fromat)
        worksheet.merge_range('M2:O2', '是否使用持续集成环境', title_fromat)
        worksheet.write('M3', '服务器', title_fromat)
        worksheet.write('N3', '前  端', title_fromat)
        worksheet.write('O3', '客户端', title_fromat)
        worksheet.merge_range('P2:P3', '接口文档是否完善', title_fromat)
        worksheet.merge_range('Q2:Q3', '故事点数完成数量', title_fromat)
        worksheet.merge_range('R2:R3', 'BUG数', title_fromat)
        worksheet.merge_range('S2:S3', '版本BUG率', title_fromat)
        for row_index in range(len(data)):
            worksheet.write(row_index + 3, 0, row_index + 1)
            for cell_index in range(len(data[row_index])):
                worksheet.write(row_index + 3, cell_index + 1, data[row_index][cell_index])

        workbook.close()
        print('文件[{}]书写成功'.format(xlsx_path))

    def manual_scoring(self, data):
        """
        到处手工打分工作
        :param data:
        :return:
        """
        xlsx_path = self._cache_path + '/' + str(uuid.uuid1()) + '.xlsx'
        workbook = xlsxwriter.Workbook(xlsx_path)
        title_fromat = workbook.add_format({'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter',
                                            'bg_color': 'yellow'})

        worksheet = workbook.add_worksheet('需要手工打分任务')
        worksheet.write('A1', '项目名', title_fromat)
        worksheet.write('B1', '工作内容', title_fromat)
        worksheet.write('C1', '具体描述', title_fromat)
        worksheet.write('D1', '参与人员', title_fromat)
        worksheet.write('E1', '打分', title_fromat)
        for row_index in range(len(data)):
            for cell_index in range(len(data[row_index])):
                worksheet.write(row_index + 1, cell_index, data[row_index][cell_index])

        workbook.close()
        print('文件[{}]书写成功'.format(xlsx_path))
