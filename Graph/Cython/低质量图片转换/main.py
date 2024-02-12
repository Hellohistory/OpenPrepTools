import image_processing  # 导入我们的Cython扩展模块


def main():
    # 输入文件夹路径
    folder_path = input("请输入文件夹路径：")

    # 输入压缩比
    compression_ratio = float(input("请输入压缩比（0-1之间的小数）："))  # 0.5

    # 输入噪点范围
    noise_range = int(input("请输入噪点范围（0-255之间的整数）："))  # 50

    # 输入模糊半径
    blur_radius = float(input("请输入模糊半径（大于0的浮点数）："))  # 1.5

    # 输入污点数量
    num_stains = int(input("请输入污点数量（大于0的整数）："))  # 50

    # 输入污点尺寸范围
    stain_size_min = int(input("请输入污点尺寸范围下限（大于0的整数）："))  # 5
    stain_size_max = int(input("请输入污点尺寸范围上限（大于下限的整数）："))  # 20
    stain_size = (stain_size_min, stain_size_max)

    image_processing.process_images(folder_path, compression_ratio, noise_range, blur_radius, num_stains, stain_size)


if __name__ == "__main__":
    main()
