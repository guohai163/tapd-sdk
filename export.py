# -*- coding: utf-8 -*-
import uuid

import log4p
import xlsxwriter

LOG = log4p.GetLogger('Export').logger


class ExportExcel:
    _cache_path = None

    def __init__(self, cache_path):
        self._cache_path = cache_path

    def intrinsic_quality(self, data, mail):
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
        worksheet.merge_range('A1:R1', '版本内部质量统计表', title_fromat)
        worksheet.merge_range('A2:A3', '序号', title_fromat)
        worksheet.merge_range('B2:B3', '项目名称', title_fromat)
        worksheet.merge_range('C2:C3', '版本号', title_fromat)
        worksheet.merge_range('D2:D3', '版本开始时间', title_fromat)
        worksheet.merge_range('E2:E3', '版本结束时间', title_fromat)
        worksheet.merge_range('F2:H2', '单元测试覆盖度', title_fromat)
        worksheet.write('F3', '服务器', title_fromat)
        worksheet.write('G3', '客户端', title_fromat)
        worksheet.write('H3', '前  端', title_fromat)
        worksheet.merge_range('I2:K2', 'SQ检查结果', title_fromat)
        worksheet.write('I3', '服务器', title_fromat)
        worksheet.write('J3', '客户端', title_fromat)
        worksheet.write('K3', '前  端', title_fromat)
        worksheet.merge_range('L2:L3', '性能测试是否通过', title_fromat)
        worksheet.merge_range('M2:O2', '是否使用持续集成环境', title_fromat)
        worksheet.write('M3', '服务器', title_fromat)
        worksheet.write('N3', '客户端', title_fromat)
        worksheet.write('O3', '前  端', title_fromat)
        worksheet.merge_range('P2:P3', '接口文档是否完善', title_fromat)
        worksheet.merge_range('Q2:Q3', '故事点数完成数量', title_fromat)
        worksheet.merge_range('R2:R3', '版本BUG率', title_fromat)
        workbook.close()
        print('文件[{}]书写成功'.format(xlsx_path))