import os
from PIL import Image
import xml.etree.ElementTree as ET

# 接受用户输入的文件夹地址和输出文件夹地址
input_dir = input("请输入文件夹地址:")
output_dir = input("请输入输出文件夹地址:")

# 遍历目录下的所有文件和文件夹
for filename in os.listdir(input_dir):
    # 判断当前文件是否为图片文件
    if filename.endswith(".jpg") or filename.endswith(".jpeg") or filename.endswith(".png"):
        # 构造对应的标注文件路径
        xml_file = os.path.join(input_dir, filename.replace(".jpg", ".xml").replace(".jpeg", ".xml").replace(".png", ".xml"))

        # 判断标注文件是否存在
        if not os.path.exists(xml_file):
            print(f"文件'{filename}'对应的标注文件不存在，将忽略该文件")
            continue

        # 解析XML文件，并对每个文字区域进行裁剪
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # 打开图像文件
        img_path = os.path.join(input_dir, filename)
        img = Image.open(img_path)

        # 统计每个标签的数量
        label_count = {}

        # 对每个文字区域进行裁剪
        for obj in root.iter('object'):
            # 获取文字区域的坐标
            bbox = obj.find('bndbox')
            xmin = int(bbox.find('xmin').text)
            ymin = int(bbox.find('ymin').text)
            xmax = int(bbox.find('xmax').text)
            ymax = int(bbox.find('ymax').text)

            # 裁剪图像
            text_img = img.crop((xmin, ymin, xmax, ymax))

            # 获取标签信息并设置保存文件名
            label = obj.find('name').text.split("_")[0]  # 仅使用第一个标签
            file_name_without_ext, ext = os.path.splitext(filename)

            # 计算当前标签已经出现的次数，并生成对应的文件名
            if label in label_count:
                label_count[label] += 1
            else:
                label_count[label] = 1
            save_name = f"{label}_{label_count[label]}_{file_name_without_ext}.png"

            # 保存裁剪后的图像
            save_path = os.path.join(output_dir, save_name)
            text_img.save(save_path)

            print(f"{filename}已完成")

print("所有任务已完成")