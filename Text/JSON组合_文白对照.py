import os
import json

# 指定你的文件夹路径
dir_path = input("请输入文件夹路径:")

# 获取所有文件名
files = os.listdir(dir_path)

# 将文件按前缀进行分组
file_groups = {}
for file in files:
    prefix, filetype = file.rsplit('_', 1)
    if prefix not in file_groups:
        file_groups[prefix] = {}
    file_groups[prefix][filetype] = file

# 对每个分组进行处理
for prefix, group in file_groups.items():
    result = []
    # 检查是否有标点和翻译文件
    if '标点.txt' in group and '翻译.txt' in group:
        with open(os.path.join(dir_path, group['标点.txt']), 'r', encoding='utf-8') as f_punc, \
             open(os.path.join(dir_path, group['翻译.txt']), 'r', encoding='utf-8') as f_trans:
            punc_lines = f_punc.readlines()
            trans_lines = f_trans.readlines()

            # 确保两种类型的数据行数相同
            assert len(punc_lines) == len(trans_lines)

            # 将数据保存到 JSON 结构中
            for i in range(len(punc_lines)):
                result.append({
                    "name": prefix,
                    "with_punctuation": punc_lines[i].strip(),
                    "translation": trans_lines[i].strip(),
                })

        # 将结果保存到 JSON 文件中
        with open(os.path.join(dir_path, f'{prefix}.json'), 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)