import xml.etree.ElementTree as ET
import os


def process_xml(input_file, output_file):
    tree = ET.parse(input_file)
    root = tree.getroot()

    # 处理XML内容，这里只是打印了每个目标对象的名称和边界框坐标
    for obj in root.iter('object'):
        name = obj.find('name').text
        bbox = obj.find('bndbox')
        xmin = int(bbox.find('xmin').text)
        ymin = int(bbox.find('ymin').text)
        xmax = int(bbox.find('xmax').text)
        ymax = int(bbox.find('ymax').text)

    # 生成新的输出文件路径
    output_dir = os.path.dirname(output_file)
    output_filename = os.path.basename(input_file)
    output_filename = os.path.splitext(output_filename)[0] + '_new.xml'
    output_path = os.path.join(output_dir, output_filename)

    # 创建一个新的ElementTree对象并写入文件
    new_tree = ET.ElementTree(root)
    new_tree.write(output_path)

    print('处理结果已保存到:', output_path)


# 指定输入XML文件路径和输出目录
input_xml_file = 'K:\OCR训练集\新建文件夹 (2)\诗经通论_一_03.xml'
output_dir = 'K:\OCR训练集\新建文件夹 (2)'

# 生成输出XML文件路径
output_xml_file = os.path.join(output_dir, os.path.basename(input_xml_file))

# 调用函数处理XML文件，并保存到新的XML文件
process_xml(input_xml_file, output_xml_file)
