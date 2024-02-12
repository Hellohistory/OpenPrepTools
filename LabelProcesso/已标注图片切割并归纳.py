from concurrent.futures import ThreadPoolExecutor
from PIL import Image
import xml.etree.ElementTree as ET
import os
import re
from tqdm import tqdm


def process_file(filename, input_dir, output_dir, progress_bar):
    try:
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

                # 在这里为每个标签创建一个文件夹，如果已存在则忽略错误
                label_dir = os.path.join(output_dir, label)
                os.makedirs(label_dir, exist_ok=True)  # 修改此处

                if label in label_count:
                    label_count[label] += 1
                else:
                    label_count[label] = 1

                file_name_without_ext, ext = os.path.splitext(filename)
                save_name = f"{label}_{label_count[label]}_{file_name_without_ext}.png"
                save_name = re.sub(r'[<>:"/\\|?*]', '', save_name)  # 移除文件名中的非法字符
                save_name = (save_name[:150] + '.png') if len(save_name) > 150 else save_name  # 限制文件名长度
                save_path = os.path.join(label_dir, save_name)
                text_img.save(save_path)
    except Exception as e:
        print(f"处理文件'{filename}'时出现错误: {e}")
    finally:
        progress_bar.update(1)  # 更新进度条


input_dir = r"G:\OCR数据集\数据集\文献通考_三百四十八卷_元_马端临撰_明嘉靖三年司礼监刊本_哈佛大学图书馆藏_黑白版"
output_dir = r"G:\OCR数据集\单字切割"
files = os.listdir(input_dir)

progress_bar = tqdm(total=len(files), desc="处理进度")

max_workers = 40
with ThreadPoolExecutor(max_workers=max_workers) as executor:
    futures = [executor.submit(process_file, filename, input_dir, output_dir, progress_bar) for filename in files]

# 等待所有任务完成，进度条会自动更新
progress_bar.close()  # 所有任务完成后关闭进度条
print("所有任务已完成")
