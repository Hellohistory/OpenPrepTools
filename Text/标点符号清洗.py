import os
import re
import chardet


def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read()
    return chardet.detect(raw_data)['encoding']


def process_file(file_path, preserve_structure=True):
    # 检测文件编码格式
    encoding = detect_encoding(file_path)
    with open(file_path, 'r', encoding=encoding, errors='replace') as f:
        text = f.read()
    # 去除标点符号
    text = re.sub(r'[^\w\s\-\']', '', text)
    # 构建新的文件名和路径
    target_name = os.path.splitext(os.path.basename(file_path))[0] + '_无标点.txt'
    if preserve_structure:
        target_dir = os.path.dirname(file_path) + '_无标点'
        target_path = os.path.join(target_dir, target_name)
        os.makedirs(target_dir, exist_ok=True)
    else:
        target_path = os.path.join(os.path.dirname(file_path), target_name)
    # 将处理后的文本写入新文件
    with open(target_path, 'w', encoding=encoding) as f:
        f.write(text)
    print("处理完成，结果已保存到文件:", target_path)


def process_folder(folder_path, preserve_structure=True):
    global target_dir
    if preserve_structure:
        target_dir = folder_path + '_无标点'
        os.makedirs(target_dir, exist_ok=True)
    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            file_path = os.path.join(root, filename)
            process_file(file_path, preserve_structure=preserve_structure)
    if preserve_structure:
        print("处理完成，结果已保存到文件夹:", target_dir)
    else:
        print("处理完成，结果已保存到文件夹:", folder_path)


if __name__ == '__main__':
    # 获取用户输入的路径
    path = input("请输入文件夹路径:")

    # 判断是否保留文件夹结构
    preserve_structure = input("是否保留文件夹结构？（y/n）").lower() == 'y'

    # 处理文件夹
    if os.path.isdir(path):
        process_folder(path, preserve_structure=preserve_structure)
    # 处理单个文件
    elif os.path.isfile(path):
        process_file(path, preserve_structure=preserve_structure)
        print("处理完成，结果已保存到文件:", path)
    else:
        print("输入的路径不是文件或文件夹，请重新输入。")