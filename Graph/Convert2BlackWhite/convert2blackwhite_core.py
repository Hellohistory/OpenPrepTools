import fitz  # PyMuPDF
import cv2
import numpy as np
from fpdf import FPDF
from skimage.filters import threshold_sauvola
import os
import shutil


# 提取图片
def extract_images_from_pdf(pdf_path, temp_folder):
    pdf_document = fitz.open(pdf_path)
    image_counter = 0

    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)

        images = page.get_images(full=True)
        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            image_filename = f"image_{page_num:04d}_{img_index}.{image_ext}"
            image_path = os.path.join(temp_folder, image_filename)

            with open(image_path, "wb") as img_file:
                img_file.write(image_bytes)

            if not os.path.exists(image_path) or os.path.getsize(image_path) == 0:
                raise FileNotFoundError(f"图像提取失败或文件为空: {image_path}")

            image_counter += 1

    return image_counter


# 处理图像（黑白转换等）
def process_image(image_path, scale_percent, window_size, k):
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise FileNotFoundError(f"无法读取图像: {image_path}")

    # 缩放图像
    width = int(image.shape[1] * scale_percent / 100)
    height = int(image.shape[0] * scale_percent / 100)
    dim = (width, height)
    resized_image = cv2.resize(image, dim, interpolation=cv2.INTER_AREA)

    threshold_sauvola_val = threshold_sauvola(resized_image, window_size=window_size, k=k)
    binary_image = resized_image > threshold_sauvola_val
    binary_image = binary_image.astype(np.uint8) * 255

    return binary_image


# 生成PDF
def create_pdf_from_images(image_folder, output_pdf_path):
    pdf = FPDF()

    image_files = sorted(
        [f for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff'))])

    for filename in image_files:
        image_path = os.path.join(image_folder, filename)
        pdf.add_page()

        image = cv2.imread(image_path)
        if image is None:
            continue

        img_height, img_width = image.shape[:2]
        pdf_w, pdf_h = pdf.w, pdf.h

        ratio = min(pdf_w / img_width, pdf_h / img_height)
        img_w = img_width * ratio
        img_h = img_height * ratio

        x = (pdf_w - img_w) / 2
        y = (pdf_h - img_h) / 2

        pdf.image(image_path, x, y, img_w, img_h)

    pdf.output(output_pdf_path, "F")


# 清理临时文件夹
def clean_temp_folder(temp_folder):
    for filename in os.listdir(temp_folder):
        file_path = os.path.join(temp_folder, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
    os.rmdir(temp_folder)


# 核心处理函数
def process_pdf(input_pdf_path, output_pdf_path, scale_percent=75, window_size=25, k=0.08):
    temp_dir = "temp_images"
    os.makedirs(temp_dir, exist_ok=True)

    try:
        image_count = extract_images_from_pdf(input_pdf_path, temp_dir)
        if image_count == 0:
            print("没有提取到任何图片")
            return

        for image_file in os.listdir(temp_dir):
            image_path = os.path.join(temp_dir, image_file)
            processed_image = process_image(image_path, scale_percent, window_size, k)
            cv2.imwrite(image_path, processed_image)

        create_pdf_from_images(temp_dir, output_pdf_path)
        print(f"PDF生成完成: {output_pdf_path}")

    except FileNotFoundError as e:
        print(f"文件错误: {e}")
    except Exception as e:
        print(f"处理过程中发生错误: {e}")
    finally:
        # 清理临时文件夹
        if os.path.exists(temp_dir):
            clean_temp_folder(temp_dir)
            print(f"临时文件夹已清理: {temp_dir}")


# 在GUI中调用核心处理函数
def start_processing(input_pdf_path, output_pdf_path, scale_percent, window_size, k):
    process_pdf(input_pdf_path, output_pdf_path, scale_percent, window_size, k)
