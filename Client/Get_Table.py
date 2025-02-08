import requests
import json
import base64
import pandas as pd
import os

class CommonTableOcr(object):
    def __init__(self, x_ti_app_id, x_ti_secret_code):
        # 通用表格识别
        self._url = 'https://api.textin.com/ai/service/v2/recognize/table/multipage'
        self._app_id = x_ti_app_id
        self._secret_code = x_ti_secret_code

        self.output_num = 0  # 如果上传的是url，就编号为0 1 2 3 输出

        self.test_count=2# 临时测试用的，为了输出json数据编码

    def _get_file_content(self, filePath):
        with open(filePath, 'rb') as fp:
            return fp.read()

    def recognize(self, file_paths, urls, output_dir='./Output_table', output_order="perpendicula"):# 这个order见API文档
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        for file_path in file_paths:
            result = self._recognize_one(file_path, output_dir, output_order=output_order)
            if result:
                self._save_to_excel(file_path, result, output_dir, is_url=False)
        for url in urls:
            result = self._recognize_one(url, output_dir, is_url=True, output_order=output_order)
            if result:
                self._save_to_excel(url, result, output_dir, is_url=True)

    def _recognize_one(self, img_path, output_dir, is_url=False, output_order="perpendicula"):
        head = {}
        params = {
            "excel": 1,
            "output_order": output_order
        }
        try:
            head['x-ti-app-id'] = self._app_id
            head['x-ti-secret-code'] = self._secret_code
            if is_url:
                head['Content-Type'] = 'text/plain'
                body = img_path
            else:
                image = self._get_file_content(img_path)
                head['Content-Type'] = 'application/octet-stream'
                body = image
            result = requests.post(self._url, data=body, params=params, headers=head)
            json_data = result.json()

            self._save_json_to_tmp(json_data, output_dir)  # 传入output_dir参数

            return self.json_parser(json_data)
        except Exception as e:
            print(e)  # 后续可以想办法记录日志
            return None

    def json_parser(self, json_data):
        if json_data is not None:
            excel_base64_str = json_data['result']['excel']
            # Decode Base64
            binary_data = base64.b64decode(excel_base64_str)
            return binary_data
        return None

    def _save_to_excel(self, path, data, output_dir, is_url):
        if is_url:
            file_name = f"url_{self.output_num}.xlsx"
            self.output_num += 1
        else:
            file_name = f"{os.path.splitext(os.path.basename(path))[0]}.xlsx"
        file_path = os.path.join(output_dir, file_name)

        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Write data to Excel file
        with open(file_path, "wb") as file:
            file.write(data)

        print(f"File successfully saved as {file_path}")

    def _save_json_to_tmp(self, json_data, output_dir='./Output_Table'):
        """
        保存API响应的JSON数据到本地文件
        """
        json_dir = os.path.join(output_dir, 'Table_json')
        if not os.path.exists(json_dir):
            os.makedirs(json_dir)
        file_path = os.path.join(json_dir, f"{self.test_count}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)
        print(f"{self.test_count}.json was successfully saved")
        self.test_count += 1




