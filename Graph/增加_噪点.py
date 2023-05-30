# 经过实验发现在黑白图片上增加噪点，对于人眼识别有一定的积极作用，因此创建此文件来对图片进行噪点处理来增加辨识度。
import os
import random

from PIL import Image


def add_noise(image, noise_range):
    width, height = image.size
    pixels = image.load()
    for y in range(height):
        for x in range(width):
            pixel = pixels[x, y]
            noise = random.randint(-noise_range, noise_range)
            pixel = max(0, min(255, pixel + noise))
            pixels[x, y] = pixel
    return image

def distort_image(image, noise_range):
    image_low = image.copy()
    image_low = add_noise(image_low, noise_range)
    return image_low

def process_images(folder_path, noise_range):
    if not os.path.exists(folder_path):
        print("文件夹不存在。")
        return

    file_names = os.listdir(folder_path)

    for file_name in file_names:
        image_path = os.path.join(folder_path, file_name)
        if os.path.isfile(image_path):
            image = Image.open(image_path).convert('L')

            distorted_image = distort_image(image, noise_range)

            file_name_without_ext, ext = os.path.splitext(file_name)
            save_name = f"{file_name_without_ext}_noise{ext}"
            save_path = os.path.join(folder_path, save_name)
            distorted_image.save(save_path)

            print(f"处理完成的图像：{file_name}")

    print("图像处理完成。")

# 输入文件夹路径
folder_path = input("请输入文件夹路径：")

# 输入噪点范围
noise_range = int(input("请输入噪点范围（0-255之间的整数）：")) # 50

process_images(folder_path, noise_range)
