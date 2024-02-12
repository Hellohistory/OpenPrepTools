from concurrent.futures import ThreadPoolExecutor
from PIL import Image
import xml.etree.ElementTree as ET
import os
import re
from tqdm import tqdm


def process_file(filename, input_dir, output_dir):
    if filename.endswith(".jpg") or filename.endswith(".jpeg") or filename.endswith(".png"):
        xml_file = os.path.join(input_dir,
                                filename.replace(".jpg", ".xml").replace(".jpeg", ".xml").replace(".png", ".xml"))
        if not os.path.exists(xml_file):
            print(f"文件'{filename}'对应的标注文件不存在，将忽略该文件")
            return  # 如果标注文件不存在，则返回

        tree = ET.parse(xml_file)
        root = tree.getroot()
        img_path = os.path.join(input_dir, filename)
        img = Image.open(img_path)
        label_count = {}

        for obj in root.iter('object'):
            bbox = obj.find('bndbox')
            xmin = int(bbox.find('xmin').text)
            ymin = int(bbox.find('ymin').text)
            xmax = int(bbox.find('xmax').text)
            ymax = int(bbox.find('ymax').text)
            text_img = img.crop((xmin, ymin, xmax, ymax))
            label = obj.find('name').text.split("_")[0]
            # 在这里为每个标签创建一个文件夹
            label_dir = os.path.join(output_dir, label)
            if not os.path.exists(label_dir):
                os.makedirs(label_dir)  # 如果文件夹不存在，则创建文件夹

            if label in label_count:
                label_count[label] += 1
            else:
                label_count[label] = 1
            file_name_without_ext, ext = os.path.splitext(filename)
            save_name = f"{label}_{label_count[label]}_{file_name_without_ext}.png"
            save_name = re.sub(r'[<>:"/\\|?*]', '', save_name)
            save_name = (save_name[:150] + '.png') if len(save_name) > 150 else save_name
            save_path = os.path.join(label_dir, save_name)
            try:
                text_img.save(save_path)
            except Exception as e:
                print(f"保存文件时出错: {e}")


input_dir = input("请输入文件夹地址:")
output_dir = input("请输入输出文件夹地址:")

files = os.listdir(input_dir)
# 使用进度条封装文件列表
files_with_progress = tqdm(files, desc="处理进度")

# 设置线程池的最大线程数，例如10
max_workers = 10

with ThreadPoolExecutor(max_workers=max_workers) as executor:
    # 使用executor.map来并行处理文件
    list(executor.map(process_file, files_with_progress, [input_dir] * len(files), [output_dir] * len(files)))

print("所有任务已完成")
