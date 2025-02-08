# TextIn API 调用 Demo

## 使用方法
1. 获取API密钥
   - 访问 TextIn 控制台: https://www.textin.com/console/dashboard/setting
   - 获取 x-ti-app-id 和 x-ti-secret-code
   - 在 Client/Client_main.py 中填入这些密钥
   - 注意: 需要先开通以下两个服务:
     - [表格识别服务](https://www.textin.com/document/recognize_table_multipage?from=toolstextin-seo-pc)
     - [智能文档提取服务](https://www.textin.com/document/open_kie_vlm_engine)

2. 安装依赖
   ```shell
   pip install jsonpath pandas requests
   ```

3. 运行程序
   ```shell
   python Client/Client_main.py
   ```

## 目录结构

主要的代码都在Clinet文件夹里面

- Client_main.py 主函数
- Client_Extract.py 智能文档提取
- Client_Recognize.py 表格识别
- GUI 待完成


Client_Recognize.py 是可以设置导出excel的三种方法的，你可以具体去看API的说明

多说一下智能提取，就是这里面的fields_key是如果你的一个图片或者一整个文档只有一个字段的一个信息话，你可以用来提取；然后table_key是如果你的一个图片或者一整个文档有一个字段的多个信息话，你可以用来提取。或者你可以直接上他的体验管你就知道是干啥的了（两个可以指定一个即可，也可以都指定） https://www.textin.com/console/recognition/robot_document_extract?service=open_kie_vlm_engine



- 在我目前的代码里面，默认所有的都会合并，所有的fields_key提取的合并到一起，所有的table_key的信息放到一起

![体验馆](image.png)

- 测试智能提取用的图片在Test_Extract和Test_Extract_Tickets文件夹下面，前者的输出在Output_Extract下面。Output里面的是每个图片的单独的输出结果
- 测试表格识别用的图片在Test_Table文件夹下面，输出在OutPut_Table里面
- 中间我有些调试的用来输出json的代码我注释掉了，你想要看的话可以解开
## 目前的问题
- 没有做各种鲁棒性的处理，比如API限制文件大小和格式，我没有检查，也没有处理API返回的错误码

- 确实需要图片预处理，果然CAC说的是对的，当图片有水印、结构不够工整、图片不清晰、图片里面的信息过于庞大的时候，识别效果会很差（可以参考Test_Extract文件夹下面的图片）



## 需要的改进
1. 做图片的预处理，比如去水印或者增加清晰度。其实只用到时候把处理好的图片的信息传给我的OCR类就行了
2. 可以考虑把pdf和word拆成一张张图片传，然后把大图片想办法拆开了传？（不知道可行不可行）。因为如果pdf过大的话或者过长，一个是准确度会下降，再一个就是他API本身就有长度的限制。
3. API-key的信息应该用配置信息来储存，不应该直接写在代码里。当然后续应该做前后端分离的。

> By SweetGargamel 