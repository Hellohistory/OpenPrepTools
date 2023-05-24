import os

def convert_to_utf8(folder_path):
    for filename in os.listdir(folder_path):
        filepath = os.path.join(folder_path, filename)
        if os.path.isfile(filepath):
            with open(filepath, 'rb') as f:
                content = f.read()
                try:
                    decoded_content = content.decode('utf-8')
                except UnicodeDecodeError:
                    decoded_content = content.decode('gbk', 'ignore')
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(decoded_content)

if __name__ == '__main__':
    folder_path = input("请输入文件夹路径：")
    convert_to_utf8(folder_path)
    print("处理完成！")