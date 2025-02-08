from Get_Table import CommonTableOcr
from Get_Extract import IntellectExtractOcr
import os

x_ti_app_id = ""
x_ti_secret_code = ""

def get_all_file_paths(directory):#得到所有文件的路径
    file_paths = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_paths.append(os.path.join(root, file))
    return file_paths

def process_with_common_table_ocr(): # 通用表格识别
    test_table_dir = './Test_table'
    output_dir = './Output'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    file_paths = get_all_file_paths(test_table_dir)
    urls = []  # 你也可以加一些图片或者文档的url 具体的文件的限制可以参考API文档

    ocr = CommonTableOcr(x_ti_app_id, x_ti_secret_code)
    ocr.recognize(file_paths, urls)

def process_with_intellect_extract_ocr(): # 智能提取识别
    test_table_dir = './Test_Extract'
    output_dir = './Output_Extract'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    file_paths = get_all_file_paths(test_table_dir) 
    urls = []  # Assuming no URLs to process
    #table_key = ['乘车人', '开车日期',"车次","出发站","到达站","座位类型","总票价"]
    fields_key=[]
    table_key=["校名","分数排名","最低分_归一均值","档次定义","江苏分数"]
    ocr = IntellectExtractOcr(x_ti_app_id, x_ti_secret_code)
    ocr.recognize(file_paths, urls, table_key=table_key,  output_dir=output_dir, output_filename='combined.xlsx')

if __name__ == "__main__":
    # Uncomment the function you want to use
    # process_with_common_table_ocr()
    process_with_intellect_extract_ocr()
