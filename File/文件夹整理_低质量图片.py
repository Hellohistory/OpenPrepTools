import os
import shutil

def organize_files(folder_path):
    # 获取文件夹中的所有文件
    files = os.listdir(folder_path)

    # 创建一个字典，用于存储前缀和对应的文件列表
    file_dict = {}

    # 遍历文件列表
    for file in files:
        # 提取文件名和前缀
        file_name, ext = os.path.splitext(file)
        # 如果文件名中包含下划线，则将其分割为前缀和文件名
        prefix_parts = file_name.split("_", 2)[:2]
        if len(prefix_parts) >= 2:
            prefix = f"{prefix_parts[0]}_{prefix_parts[1]}"
        else:
            prefix = file_name

        # 如果前缀不存在于字典中，则将其添加为键，并将文件名添加到对应的值中作为列表
        if prefix not in file_dict:
            file_dict[prefix] = [file]
        else:
            file_dict[prefix].append(file)

    # 遍历字典，为每个前缀创建一个文件夹，并将对应的文件移动到该文件夹中
    for prefix, files in file_dict.items():
        # 创建文件夹
        folder_name = os.path.join(folder_path, prefix)
        os.makedirs(folder_name, exist_ok=True)

        # 移动文件到文件夹
        for file in files:
            file_path = os.path.join(folder_path, file)
            new_file_path = os.path.join(folder_name, file)
            if file_path != new_file_path:
                shutil.move(file_path, new_file_path)

# 指定文件夹路径
folder_path = input("请输入文件夹地址:")

# 调用函数进行文件夹归类
organize_files(folder_path)

print(f"已全部完成！")