# main.py

import image_processing

def main():
    # 输入文件夹路径
    folder_path = input("请输入文件夹路径：")

    # 输入噪点范围
    noise_range = int(input("请输入噪点范围（0-255之间的整数）：")) #50

    image_processing.process_images(folder_path, noise_range)

if __name__ == "__main__":
    main()