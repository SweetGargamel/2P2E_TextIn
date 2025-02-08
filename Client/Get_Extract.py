import requests
import jsonpath
import base64
import pandas as pd
from openpyxl import load_workbook
import os
import json

class IntellectExtractOcr(object):
    def __init__(self, app_id, secret_code):
        self._url =  "https://api.textin.com/ai/service/v1/entity_extraction"
        self._app_id = app_id
        self._secret_code = secret_code
        self.output_num = 0

    def _get_file_content(self, filePath):
        with open(filePath, 'rb') as fp:
            return fp.read()

    def recognize(self, file_paths, urls, fields_key=[], table_key=[], 
                  output_dir=r'./Output_Extract', output_filename='combined.xlsx'):
        # Ensure the directory exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        all_fields_dfs = []
        all_table_cells_dfs = []
        print("开始处理文件")
        # 处理文件路径
        for path in file_paths:
            fields_df, table_cells_df = self._recognize_onefile(fields_key, table_key, path)
            if fields_df is not None and not fields_df.empty:
                all_fields_dfs.append(fields_df)
            if table_cells_df is not None and not table_cells_df.empty:
                all_table_cells_dfs.append(table_cells_df)

        # 处理URL
        for url in urls:
            fields_df, table_cells_df = self._recognize_onefile(fields_key, table_key, url, is_url=True)
            if fields_df is not None and not fields_df.empty:
                all_fields_dfs.append(fields_df)
            if table_cells_df is not None and not table_cells_df.empty:
                all_table_cells_dfs.append(table_cells_df)

        output_path = os.path.join(output_dir, output_filename)
        # 只在有数据时写入Excel
        if all_fields_dfs:
            self._merge_dataframes_to_excel(all_fields_dfs, output_path, sheet_name='Fields')
        if all_table_cells_dfs:
            self._merge_dataframes_to_excel(all_table_cells_dfs, output_path, sheet_name='TableCells')
        print("处理完成,文件已经保存在: ", output_dir)

    def _save_json_response(self, json_data, output_dir='./Output_Extract'):
        """
        保存API响应的JSON数据到本地文件
        """
        json_dir = os.path.join(output_dir, 'json_files')
        if not os.path.exists(json_dir):
            os.makedirs(json_dir)
        
        json_path = os.path.join(json_dir, f'{self.output_num}_response.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)
        print(f"JSON响应已保存到: {json_path}")

    def _recognize_onefile(self, fields_key, table_key, img_path, is_url=False, output_dir='./Output_Extract'):
        headers = {
            "x-ti-app-id": self._app_id,
            "x-ti-secret-code": self._secret_code,
        }
        params = {}
        if fields_key:
            params["key"] = ",".join(fields_key)

        if table_key:
            params["table_header"] = ",".join(table_key)
        print(f"params={params}")
        try:
            if is_url:
                headers['Content-Type'] = 'text/plain'
                img = img_path
            else:
                headers['Content-Type'] = 'application/octet-stream'
                img = self._get_file_content(img_path)

            result = requests.post(self._url, data=img, headers=headers, params=params)
            
            # 保存JSON响应
            self._save_json_response(result.json(), output_dir)
            
            return self._json_parser(result.json(), output_dir)
        
        except Exception as e:
            print(e)
            return None, None

    def _export_single_files(self, fields_df, table_cells_df, output_dir='./Output_Extract'):
        """
        导出单个文件的DataFrame到独立的Excel文件
        """
        single_files_dir = os.path.join(output_dir, 'single_files')
        if not os.path.exists(single_files_dir):
            os.makedirs(single_files_dir)
        
        # 导出fields_df
        if fields_df is not None and not fields_df.empty:
            fields_output_path = os.path.join(single_files_dir, f'{self.output_num}_fields.xlsx')
            fields_df.to_excel(fields_output_path, index=False)
            print(f"Fields数据已导出到: {fields_output_path}")
        
        # 导出table_cells_df
        if table_cells_df is not None and not table_cells_df.empty:
            table_output_path = os.path.join(single_files_dir, f'{self.output_num}_table_cells.xlsx')
            table_cells_df.to_excel(table_output_path, index=False)
            print(f"Table Cells数据已导出到: {table_output_path}")
        
        # 增加计数器
        self.output_num += 1

    def _json_parser(self, json_data, output_dir='./Output_Extract'):
        fields = jsonpath.jsonpath(json_data, '$.result.detail_structure[*].fields')
        table_cells = jsonpath.jsonpath(json_data, '$.result.detail_structure[*].tables_relationship[*].cells[*]')

        fields_df = None
        table_cells_df = None

        if fields[0]:
            data = {key: [] for key in fields[0].keys()}
            max_length = max(len(value_list) for field in fields for value_list in field.values())

            for field in fields:
                for key, value_list in field.items():
                    for value_dict in value_list:
                        data[key].append(value_dict['value'])
                    while len(data[key]) < max_length:
                        data[key].append(None)

            fields_df = pd.DataFrame(data)

        if table_cells:
            cell_data = {key: [] for key in table_cells[0].keys()}

            for cell in table_cells:
                for key, value in cell.items():
                    cell_data[key].append(value['value'])

            table_cells_df = pd.DataFrame(cell_data)

        # 调用新的导出函数
        #self._export_single_files(fields_df, table_cells_df)
        
        return fields_df, table_cells_df

    def _merge_dataframes_to_excel(self, dataframes, output_path, sheet_name='Sheet1'):
        # 检查是否有数据帧需要写入
        if not dataframes:
            print(f"没有数据可以写入到 {sheet_name} 表格中")
            return
        # # for df in dataframes:
        #     print(df)
        #     print("---------_merge_dataframes_to_excel---------")
        # 如果文件不存在，直接写入
        if not os.path.exists(output_path):
            with pd.ExcelWriter(output_path, engine='openpyxl', mode='w') as writer:
                pd.concat(dataframes, ignore_index=True).to_excel(
                    writer,
                    sheet_name=sheet_name,
                    index=False
                )
        else:
            # 如果文件已存在，使用追加模式
            with pd.ExcelWriter(output_path, engine='openpyxl', mode='a') as writer:
                pd.concat(dataframes, ignore_index=True).to_excel(
                    writer,
                    sheet_name=sheet_name,
                    index=False
                )