import os
import random
from PIL import Image, ImageFilter, ImageDraw

cpdef select_mode(image):
    if image.mode == "RGB" or image.mode == "RGBA":
        return image
    else:
        return image.convert('L')

cpdef add_noise(image, noise_range):
    width, height = image.size
    pixels = image.load()
    for y in range(height):
        for x in range(width):
            if image.mode == "RGB":
                r, g, b = pixels[x, y]
                noise = random.randint(-noise_range, noise_range)
                r = max(0, min(255, r + noise))
                g = max(0, min(255, g + noise))
                b = max(0, min(255, b + noise))
                pixels[x, y] = (r, g, b)
            else:  # For grayscale images
                pixel = pixels[x, y]
                noise = random.randint(-noise_range, noise_range)
                pixel = max(0, min(255, pixel + noise))
                pixels[x, y] = pixel
    return image

cpdef add_blur(image, blur_radius):
    blurred_image = image.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    return blurred_image

cpdef add_stains(image, int num_stains, tuple stain_size):
    width, height = image.size
    draw = ImageDraw.Draw(image)
    for _ in range(num_stains):
        x = random.randint(0, width)
        y = random.randint(0, height)
        size = random.randint(stain_size[0], stain_size[1])
        if image.mode == "RGB":
            color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        else:
            color = random.randint(0, 255)
        draw.ellipse([(x, y), (x+size, y+size)], fill=color)
    return image

cpdef distort_image(image, noise_range, blur_radius, num_stains, tuple stain_size):
    image_low_1 = image.copy()
    image_low_2 = image.copy()
    image_low_3 = image.copy()
    image_low_4 = image.copy()
    image_low_5 = image.copy()

    image_low_1 = add_noise(image_low_1, noise_range)
    image_low_2 = add_noise(image_low_2, noise_range)
    image_low_3 = add_noise(image_low_3, noise_range)

    image_low_2 = add_blur(image_low_2, blur_radius)
    image_low_3 = add_blur(image_low_3, blur_radius)
    image_low_4 = add_blur(image_low_4, blur_radius)

    image_low_3 = add_stains(image_low_3, num_stains, stain_size)
    image_low_4 = add_stains(image_low_4, num_stains, stain_size)
    image_low_5 = add_stains(image_low_5, num_stains, stain_size)

    return image_low_1, image_low_2, image_low_3, image_low_4, image_low_5

cpdef compress_image(image, compression_ratio):
    width, height = image.size
    new_width = int(width * compression_ratio)
    new_height = int(height * compression_ratio)
    compressed_image = image.resize((new_width, new_height), Image.LANCZOS)
    return compressed_image

cpdef process_images(folder_path, compression_ratio, noise_range, blur_radius, num_stains, tuple stain_size):
    if not os.path.exists(folder_path):
        print("文件夹不存在。")
        return

    file_names = os.listdir(folder_path)

    for file_name in file_names:
        image_path = os.path.join(folder_path, file_name)
        if os.path.isfile(image_path):
            image = Image.open(image_path)
            image = select_mode(image)

            compressed_image = compress_image(image, compression_ratio)
            distorted_images = distort_image(compressed_image, noise_range, blur_radius, num_stains, stain_size)

            for i, distorted_image in enumerate(distorted_images, start=1):
                file_name_without_ext, ext = os.path.splitext(file_name)
                save_name = f"{file_name_without_ext}_low{i}{ext}"
                save_path = os.path.join(folder_path, save_name)
                distorted_image.save(save_path)

            combined_image = compressed_image.copy()
            for distorted_image in distorted_images:
                combined_image = Image.blend(combined_image, distorted_image, 0.5)

            file_name_without_ext, ext = os.path.splitext(file_name)
            combined_save_name = f"{file_name_without_ext}_low_combined{ext}"
            combined_save_path = os.path.join(folder_path, combined_save_name)
            combined_image.save(combined_save_path)

            print(f"处理完成的图像：{file_name}")

    print("图像处理完成.")
