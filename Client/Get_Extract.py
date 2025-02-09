import requests
import jsonpath
import base64
import pandas as pd
from openpyxl import load_workbook
import os
import json
import sys

class IntellectExtractOcr(object):
    def __init__(self, app_id, secret_code):
        self._url =  "https://api.textin.com/ai/service/v1/entity_extraction"
        self._app_id = app_id
        self._secret_code = secret_code
        self.output_num = 0

    def _get_file_content(self, filePath):
        try:
            with open(filePath, 'rb') as fp:
                return fp.read()
        except IOError as e:
            print(f"\n文件读取错误:")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            print(f"错误位置: {os.path.basename(__file__)}:{sys.exc_info()[2].tb_lineno}")
            raise

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
        保存API响应的JSON数据到本地文件，并打印印章信息
        """
        try:
            # 保存JSON文件
            json_dir = os.path.join(output_dir, 'json_files')
            if not os.path.exists(json_dir):
                os.makedirs(json_dir)
            
            json_path = os.path.join(json_dir, f'{self.output_num}_response.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)
            print(f"JSON响应已保存到: {json_path}")
            
            # 处理印章信息
            try:
                stamps = jsonpath.jsonpath(json_data, '$.result.detail_structure[*].stamps[*]')
                print("\n印章信息:")
                if stamps:
                    for stamp in stamps:
                        color = stamp.get('color', 'N/A')
                        stamp_shape = stamp.get('stamp_shape', 'N/A')
                        stamp_type = stamp.get('type', 'N/A')
                        value = stamp.get('value', 'N/A')
                        page_number = stamp.get('page_number', 'N/A')
                        print(f"颜色: {color}, 形状: {stamp_shape}, 类型: {stamp_type}, "
                              f"内容: {value}, 页码: {page_number}")
                else:
                    print("无印章")
                print()  # 打印空行作为分隔
                
            except Exception as e:
                print(f"\n印章信息处理错误:")
                print(f"错误类型: {type(e).__name__}")
                print(f"错误信息: {str(e)}")
                print(f"错误位置: {os.path.basename(__file__)}:{sys.exc_info()[2].tb_lineno}")
                
        except IOError as e:
            print(f"\nJSON保存错误:")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            print(f"错误位置: {os.path.basename(__file__)}:{sys.exc_info()[2].tb_lineno}")
        except json.JSONDecodeError as e:
            print(f"\nJSON编码错误:")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            print(f"错误位置: {os.path.basename(__file__)}:{sys.exc_info()[2].tb_lineno}")

    def _handle_response_status(self, response_json, img_path, is_url=False):
        """
        处理API响应的状态信息，包括错误码和推理状态
        
        Args:
            response_json: API响应的JSON数据
            img_path: 文件路径或URL
            is_url: 是否为URL请求
            
        Returns:
            bool: 响应是否成功
        """
        try:
            # 错误码映射字典
            error_codes = {
                40101: "x-ti-app-id 或 x-ti-secret-code 为空",
                40102: "x-ti-app-id 或 x-ti-secret-code 无效，验证失败",
                40103: "客户端IP不在白名单",
                40003: "余额不足，请充值后再使用",
                40004: "参数错误，请查看技术文档，检查传参",
                40007: "机器人不存在或未发布",
                40008: "机器人未开通，请至市场开通后重试",
                40301: "图片类型不支持",
                40302: "上传文件大小不符，文件大小不超过 50M",
                40303: "文件类型不支持",
                40304: "图片尺寸不符，图像宽高须介于 20 和 10000（像素）之间",
                40305: "识别文件未上传",
                40306: "qps超过限制",
                40400: "无效的请求链接，请检查链接是否正确",
                30203: "基础服务故障，请稍后重试",
                500: "服务器内部错误"
            }
            
            # 检查响应中的错误码
            if response_json.get('code') != 200:
                error_code = response_json.get('code')
                error_message = error_codes.get(error_code, "未知错误")
                error_line = f"文件: {img_path if is_url else os.path.basename(img_path)}"
                print(f"\n错误信息:")
                print(f"错误码: {error_code}")
                print(f"错误描述: {error_message}")
                print(f"错误位置: {error_line}")
                print(f"详细信息: {response_json.get('message', '无详细信息')}\n")
                return False
            
            # 处理推理状态
            finish_reason = response_json.get('result', {}).get('finish_reason')
            if finish_reason:
                reason_messages = {
                    'stop': '正常推理结束',
                    'length': 'token超出限制而结束'
                }
                status_message = reason_messages.get(finish_reason, '未知的推理状态')
                print(f"\n推理状态: {status_message}")
                if finish_reason == 'length':
                    print("警告: 由于token限制，可能未能完全处理所有内容")
            
            return True
        except Exception as e:
            print(f"\n响应状态处理错误:")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            print(f"错误位置: {os.path.basename(__file__)}:{sys.exc_info()[2].tb_lineno}")
            return False

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
            response_json = result.json()
            
            # 使用新方法处理响应状态
            if not self._handle_response_status(response_json, img_path, is_url):
                return None, None
            
            # 保存JSON响应
            self._save_json_response(response_json, output_dir)
            
            return self._json_parser(response_json, fields_key, table_key, output_dir)
        
        except requests.exceptions.RequestException as e:
            print(f"\n网络请求错误:")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            print(f"错误位置: {os.path.basename(__file__)}:{sys.exc_info()[2].tb_lineno}\n")
            return None, None
        except Exception as e:
            print(f"\n程序执行错误:")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            print(f"错误位置: {os.path.basename(__file__)}:{sys.exc_info()[2].tb_lineno}\n")
            return None, None

    def _export_single_files(self, fields_df, table_cells_df, output_dir='./Output_Extract'):
        """
        导出单个文件的DataFrame到独立的Excel文件
        """
        try:
            single_files_dir = os.path.join(output_dir, 'single_files')
            if not os.path.exists(single_files_dir):
                os.makedirs(single_files_dir)
            
            # 导出fields_df
            if fields_df is not None and not fields_df.empty:
                try:
                    fields_output_path = os.path.join(single_files_dir, f'{self.output_num}_fields.xlsx')
                    fields_df.to_excel(fields_output_path, index=False)
                    print(f"Fields数据已导出到: {fields_output_path}")
                except Exception as e:
                    print(f"\nFields导出错误:")
                    print(f"错误类型: {type(e).__name__}")
                    print(f"错误信息: {str(e)}")
                    print(f"错误位置: {os.path.basename(__file__)}:{sys.exc_info()[2].tb_lineno}")
            
            # 导出table_cells_df
            if table_cells_df is not None and not table_cells_df.empty:
                try:
                    table_output_path = os.path.join(single_files_dir, f'{self.output_num}_table_cells.xlsx')
                    table_cells_df.to_excel(table_output_path, index=False)
                    print(f"Table Cells数据已导出到: {table_output_path}")
                except Exception as e:
                    print(f"\nTable Cells导出错误:")
                    print(f"错误类型: {type(e).__name__}")
                    print(f"错误信息: {str(e)}")
                    print(f"错误位置: {os.path.basename(__file__)}:{sys.exc_info()[2].tb_lineno}")
            
            # 增加计数器
            self.output_num += 1
        except Exception as e:
            print(f"\n文件导出错误:")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            print(f"错误位置: {os.path.basename(__file__)}:{sys.exc_info()[2].tb_lineno}")

    def _json_parser(self, json_data, fields_key=None, table_key=None, output_dir='./Output_Extract'):
        """
        解析JSON响应数据，按照指定的key顺序处理数据
        
        Args:
            json_data: API返回的JSON数据
            fields_key: 字段提取的关键字列表
            table_key: 表格提取的关键字列表
            output_dir: 输出目录
        
        Returns:
            tuple: (fields_df, table_cells_df)
        """
        try:
            # 解析印章信息
            self._parse_stamps(json_data)
            
            fields = jsonpath.jsonpath(json_data, '$.result.detail_structure[*].fields')
            table_cells = jsonpath.jsonpath(json_data, '$.result.detail_structure[*].tables_relationship[*].cells[*]')

            fields_df = None
            table_cells_df = None

            # 处理fields数据
            if fields and fields[0]:
                try:
                    # 收集所有可能的键
                    all_keys = set()
                    for field in fields:
                        all_keys.update(field.keys())
                    
                    # 如果提供了fields_key，使用它来过滤和排序键
                    if fields_key:
                        keys_to_use = [k for k in fields_key if k in all_keys]
                        # 添加未在fields_key中但存在的键
                        keys_to_use.extend([k for k in all_keys if k not in fields_key])
                    else:
                        keys_to_use = sorted(list(all_keys))
                    
                    # 创建数据字典
                    data = {key: [] for key in keys_to_use}
                    max_length = max(len(value_list) for field in fields for value_list in field.values())

                    # 按照指定顺序填充数据
                    for field in fields:
                        for key in keys_to_use:
                            value_list = field.get(key, [])
                            if value_list:
                                data[key].append(value_list[0]['value'])
                            else:
                                data[key].append(None)
                            # 填充到最大长度
                            while len(data[key]) < max_length:
                                data[key].append(None)

                    fields_df = pd.DataFrame(data)
                    
                except Exception as e:
                    print(f"\n字段数据解析错误:")
                    print(f"错误类型: {type(e).__name__}")
                    print(f"错误信息: {str(e)}")
                    print(f"错误位置: {os.path.basename(__file__)}:{sys.exc_info()[2].tb_lineno}")

            # 处理table_cells数据
            if table_cells and table_cells[0]:
                try:
                    # 收集所有可能的键
                    all_keys = set()
                    for cell in table_cells:
                        all_keys.update(cell.keys())
                    
                    # 如果提供了table_key，使用它来过滤和排序键
                    if table_key:
                        keys_to_use = [k for k in table_key if k in all_keys]
                        # 添加未在table_key中但存在的键
                        keys_to_use.extend([k for k in all_keys if k not in table_key])
                    else:
                        keys_to_use = sorted(list(all_keys))
                    
                    # 创建数据字典
                    cell_data = {key: [] for key in keys_to_use}
                    
                    # 按照指定顺序填充数据
                    for cell in table_cells:
                        for key in keys_to_use:
                            if key in cell:
                                cell_data[key].append(cell[key]['value'])
                            else:
                                cell_data[key].append(None)

                    table_cells_df = pd.DataFrame(cell_data)
                    
                    # 如果提供了table_key，确保列顺序匹配
                    if table_key:
                        # 获取实际存在的列
                        existing_cols = [col for col in table_key if col in table_cells_df.columns]
                        # 添加其他列
                        other_cols = [col for col in table_cells_df.columns if col not in table_key]
                        # 重新排序列
                        table_cells_df = table_cells_df[existing_cols + other_cols]
                    
                except Exception as e:
                    print(f"\n表格数据解析错误:")
                    print(f"错误类型: {type(e).__name__}")
                    print(f"错误信息: {str(e)}")
                    print(f"错误位置: {os.path.basename(__file__)}:{sys.exc_info()[2].tb_lineno}")

            return fields_df, table_cells_df
        
        except Exception as e:
            print(f"\nJSON解析错误:")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            print(f"错误位置: {os.path.basename(__file__)}:{sys.exc_info()[2].tb_lineno}")
            return None, None

    def _parse_stamps(self, json_data):
        """解析印章信息"""
        try:
            stamps = jsonpath.jsonpath(json_data, '$.result.detail_structure[*].stamps[*]')
            print("\n印章信息:")
            if stamps:
                for stamp in stamps:
                    color = stamp.get('color', 'N/A')
                    stamp_shape = stamp.get('stamp_shape', 'N/A')
                    stamp_type = stamp.get('type', 'N/A')
                    value = stamp.get('value', 'N/A')
                    page_number = stamp.get('page_number', 'N/A')
                    print(f"颜色: {color}, 形状: {stamp_shape}, 类型: {stamp_type}, "
                          f"内容: {value}, 页码: {page_number}")
            else:
                print("无印章")
            print()  # 打印空行作为分隔
        except Exception as e:
            print(f"\n印章信息处理错误:")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            print(f"错误位置: {os.path.basename(__file__)}:{sys.exc_info()[2].tb_lineno}")

    def _merge_dataframes_to_excel(self, dataframes, output_path, sheet_name='Sheet1'):
        try:
            # 检查是否有数据帧需要写入
            if not dataframes:
                print(f"没有数据可以写入到 {sheet_name} 表格中")
                return

            # 如果文件不存在，直接写入
            if not os.path.exists(output_path):
                try:
                    with pd.ExcelWriter(output_path, engine='openpyxl', mode='w') as writer:
                        pd.concat(dataframes, ignore_index=True).to_excel(
                            writer,
                            sheet_name=sheet_name,
                            index=False
                        )
                except Exception as e:
                    print(f"\nExcel写入错误:")
                    print(f"错误类型: {type(e).__name__}")
                    print(f"错误信息: {str(e)}")
                    print(f"错误位置: {os.path.basename(__file__)}:{sys.exc_info()[2].tb_lineno}")
            else:
                try:
                    with pd.ExcelWriter(output_path, engine='openpyxl', mode='a') as writer:
                        pd.concat(dataframes, ignore_index=True).to_excel(
                            writer,
                            sheet_name=sheet_name,
                            index=False
                        )
                except Exception as e:
                    print(f"\nExcel追加错误:")
                    print(f"错误类型: {type(e).__name__}")
                    print(f"错误信息: {str(e)}")
                    print(f"错误位置: {os.path.basename(__file__)}:{sys.exc_info()[2].tb_lineno}")
        except Exception as e:
            print(f"\nExcel处理错误:")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            print(f"错误位置: {os.path.basename(__file__)}:{sys.exc_info()[2].tb_lineno}")