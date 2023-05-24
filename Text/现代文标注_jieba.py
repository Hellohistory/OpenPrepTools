import concurrent.futures
import os
import sys

import chardet
import jieba.posseg as pseg
from tqdm import tqdm

# 用户输入需要处理的文档的地址或文件夹的地址
path = input("请输入文档地址或文件夹地址:")

# 判断用户输入的是文件夹还是文件
if os.path.isfile(path):
    file_paths = [path]
else:
    file_paths = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith('.txt'):
                file_paths.append(os.path.join(root, file))

# 定义函数，用于对单个文件进行词性标注
def process_file(file_path):
    # 读取文件内容，并判断编码格式
    with open(file_path, 'rb') as f:
        content = f.read()
        encoding = chardet.detect(content)['encoding']

    # 如果不是utf-8编码的文件，转换为utf-8编码
    if encoding != 'utf-8':
        content = content.decode(encoding)
        content = content.encode('utf-8')
    else:
        content = content.decode('utf-8')

    # 分割文本为行，并逐行进行词性标注
    lines = content.split('\n')
    result = ''
    for line in lines:
        words = pseg.cut(line.strip())
        line_output = ''
        for word, flag in words:
            line_output += f'{word}[{flag}]'
        result += line_output + '\n'

        # 在每个句子结束后添加一个空行
        result += '\n'

    # 将结果输出到新的txt文件中
    output_file_path = os.path.splitext(file_path)[0] + '_output.txt'
    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write(result)

# 使用多线程进行处理
with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = [executor.submit(process_file, file_path) for file_path in file_paths]
    # 显示文件处理的总进度
    for _ in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc='Processing files', leave=False):
        pass

# 强制刷新标准输出缓冲区，将所有内容写入磁盘中
sys.stdout.flush()

print('词性标注完成！')
