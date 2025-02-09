import requests
import json
import base64
import pandas as pd
import os
import traceback
import sys

class CommonTableOcr(object):
    def __init__(self, x_ti_app_id, x_ti_secret_code):
        # 通用表格识别
        self._url = 'https://api.textin.com/ai/service/v2/recognize/table/multipage'
        self._app_id = x_ti_app_id
        self._secret_code = x_ti_secret_code

        self.output_num = 0  # 如果上传的是url，就编号为0 1 2 3 输出

        self.test_count=0# 临时测试用的，为了输出json数据编码

    def handle_error_code(self, code):
        """处理API返回的错误码"""
        error_codes = {
            40101: "x-ti-app-id 或 x-ti-secret-code 为空",
            40102: "x-ti-app-id 或 x-ti-secret-code 无效，验证失败",
            40103: "客户端IP不在白名单",
            40003: "余额不足，请充值后再使用",
            40004: "参数错误，请查看技术文档，检查传参",
            40007: "机器人不存在或未发布",
            40008: "机器人未开通，请至市场开通后重试",
            40301: "图片类型不支持",
            40302: "上传文件大小不符，文件大小不超过 10M",
            40303: "文件类型不支持",
            40304: "图片尺寸不符，图像宽高须介于 20 和 10000（像素）之间",
            40305: "识别文件未上传",
            40400: "无效的请求链接，请检查链接是否正确",
            30203: "基础服务故障，请稍后重试",
            500: "服务器内部错误"
        }
        error_msg = error_codes.get(code, f"未知错误码: {code}")
        print(f"\nAPI错误响应:")
        print(f"错误类型: API错误码")
        print(f"错误信息: {error_msg}")
        print(f"错误位置: {os.path.basename(__file__)}:{sys.exc_info()[2].tb_lineno}")
        return error_msg

    def _get_file_content(self, filePath):
        try:
            with open(filePath, 'rb') as fp:
                return fp.read()
        except Exception as e:
            print(f"\n文件读取错误:")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            print(f"错误位置: {os.path.basename(__file__)}:{sys.exc_info()[2].tb_lineno}")
            return None

    def recognize(self, file_paths, urls, output_dir='./Output_table', output_order="perpendicula"):# 这个order见API文档
        try:
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
        except Exception as e:
            print(f"处理识别请求时发生错误: {str(e)}")
            print(f"位置: {traceback.extract_stack()[-1][1]}")

    def _recognize_one(self, img_path, output_dir, is_url=False, output_order="perpendicula"):
        try:
            head = {
                'x-ti-app-id': self._app_id,
                'x-ti-secret-code': self._secret_code
            }
            params = {
                "excel": 1,
                "output_order": output_order
            }

            if is_url:
                head['Content-Type'] = 'text/plain'
                body = img_path
            else:
                image = self._get_file_content(img_path)
                if image is None:
                    return None
                head['Content-Type'] = 'application/octet-stream'
                body = image

            response = requests.post(self._url, data=body, params=params, headers=head)
            json_data = response.json()

            # 检查错误码
            if 'code' in json_data and json_data['code'] != 200 :
                self.handle_error_code(json_data['code'])
                return None

            self._save_json_to_tmp(json_data, output_dir)
            return self.json_parser(json_data)

        except requests.exceptions.RequestException as e:
            print(f"\n网络请求错误:")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            print(f"错误位置: {os.path.basename(__file__)}:{sys.exc_info()[2].tb_lineno}")
            return None
        except json.JSONDecodeError as e:
            print(f"\nJSON解析错误:")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            print(f"错误位置: {os.path.basename(__file__)}:{sys.exc_info()[2].tb_lineno}")
            return None
        except Exception as e:
            print(f"\n处理请求时发生错误:")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            print(f"错误位置: {os.path.basename(__file__)}:{sys.exc_info()[2].tb_lineno}")
            return None

    def json_parser(self, json_data):
        try:
            if json_data is not None and 'result' in json_data and 'excel' in json_data['result']:
                excel_base64_str = json_data['result']['excel']
                return base64.b64decode(excel_base64_str)
            return None
        except Exception as e:
            print(f"\nJSON解析错误:")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            print(f"错误位置: {os.path.basename(__file__)}:{sys.exc_info()[2].tb_lineno}")
            return None

    def _save_to_excel(self, path, data, output_dir, is_url):
        try:
            if is_url:
                file_name = f"url_{self.output_num}.xlsx"
                self.output_num += 1
            else:
                file_name = f"{os.path.splitext(os.path.basename(path))[0]}.xlsx"
            
            file_path = os.path.join(output_dir, file_name)
            os.makedirs(output_dir, exist_ok=True)

            with open(file_path, "wb") as file:
                file.write(data)
            print(f"文件已成功保存至 {file_path}")
        except Exception as e:
            print(f"\n保存Excel文件错误:")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            print(f"错误位置: {os.path.basename(__file__)}:{sys.exc_info()[2].tb_lineno}")

    def _save_json_to_tmp(self, json_data, output_dir='./Output_Table'):
        """
        保存API响应的JSON数据到本地文件
        """
        try:
            json_dir = os.path.join(output_dir, 'Table_json')
            if not os.path.exists(json_dir):
                os.makedirs(json_dir)
            
            file_path = os.path.join(json_dir, f"{self.test_count}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)
            
            print(f"{self.test_count}.json 已成功保存")
            self.test_count += 1
        except Exception as e:
            print(f"\n保存JSON文件错误:")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            print(f"错误位置: {os.path.basename(__file__)}:{sys.exc_info()[2].tb_lineno}")




