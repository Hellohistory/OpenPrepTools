import hashlib
import logging
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor

import cv2
import fitz  # PyMuPDF
import numpy as np
from fpdf import FPDF
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress
from skimage.filters import threshold_sauvola

logging.basicConfig(level="INFO", format="%(message)s", handlers=[RichHandler()])
logger = logging.getLogger("rich")

console = Console()


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


def process_image(image_path, output_folder, scale_percent=75, window_size=25, k=0.08):
    try:
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise FileNotFoundError(f"无法读取图像: {image_path}")

        width = int(image.shape[1] * scale_percent / 100)
        height = int(image.shape[0] * scale_percent / 100)
        dim = (width, height)
        resized_image = cv2.resize(image, dim, interpolation=cv2.INTER_AREA)

        threshold_sauvola_val = threshold_sauvola(resized_image, window_size=window_size, k=k)
        binary_image = resized_image > threshold_sauvola_val
        binary_image = binary_image.astype(np.uint8) * 255

        filename = os.path.splitext(os.path.basename(image_path))[0]
        png_output_path = os.path.join(output_folder, f"{filename}.png")

        cv2.imwrite(png_output_path, binary_image, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    except Exception as e:
        logger.error(f"处理图像时发生错误: {e}")


def create_pdf_from_images(image_folder, output_pdf_path):
    pdf = FPDF()
    for filename in sorted(os.listdir(image_folder)):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
            image_path = os.path.join(image_folder, filename)
            pdf.add_page()
            pdf.image(image_path, 0, 0, 210, 297)  # A4尺寸
    pdf.output(output_pdf_path)


def process_pdf(pdf_path, output_folder, scale_percent=75, window_size=25, k=0.08):
    input_pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    short_name = input_pdf_name[:10]
    unique_id = hashlib.md5(input_pdf_name.encode()).hexdigest()[:6]

    output_pdf_path = os.path.join(output_folder, f'{input_pdf_name}_processed.pdf')

    logger.info(f"开始处理PDF文件: {pdf_path}")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_image_folder = os.path.join(temp_dir, 'temp_images')
        processed_folder = os.path.join(temp_dir, 'processed_images')

        os.makedirs(temp_image_folder, exist_ok=True)
        os.makedirs(processed_folder, exist_ok=True)

        logger.info("开始提取图片...")
        image_count = extract_images_from_pdf(pdf_path, temp_image_folder)
        logger.info(f"提取了 {image_count} 张图片。")

        logger.info("开始处理图片...")
        image_files = [f for f in os.listdir(temp_image_folder) if
                       f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff'))]

        with Progress() as progress:
            task = progress.add_task("[green]处理图片...", total=len(image_files))
            with ThreadPoolExecutor() as executor:
                futures = []
                for filename in image_files:
                    image_path = os.path.join(temp_image_folder, filename)
                    future = executor.submit(process_image, image_path, processed_folder, scale_percent, window_size, k)
                    futures.append(future)
                    progress.update(task, advance=1)

        logger.info("图片处理完成，开始生成PDF...")
        create_pdf_from_images(processed_folder, output_pdf_path)
        logger.info(f"PDF生成完成: {output_pdf_path}")


def process_multiple_pdfs(pdf_files, output_folder, scale_percent=75, window_size=25, k=0.08):
    for pdf_file in pdf_files:
        process_pdf(pdf_file, output_folder, scale_percent, window_size, k)


def process_folder(pdf_folder, output_folder, scale_percent=75, window_size=25, k=0.08):
    pdf_files = [os.path.join(pdf_folder, f) for f in os.listdir(pdf_folder) if f.lower().endswith('.pdf')]
    process_multiple_pdfs(pdf_files, output_folder, scale_percent, window_size, k)


if __name__ == '__main__':
    mode = input("请选择模式 (1-单个PDF, 2-多个PDF, 3-文件夹模式): ")

    if mode == '1':
        pdf_path = input("请输入PDF文件路径: ")
        output_folder = input("请输入输出文件夹路径: ")
        scale_percent = int(input("请输入缩放比例（默认75）: ") or 75)
        window_size = int(input("请输入窗口大小（默认25）: ") or 25)
        k = float(input("请输入k值（默认0.08）: ") or 0.08)
        process_pdf(pdf_path, output_folder, scale_percent, window_size, k)

    elif mode == '2':
        pdf_files = input("请输入多个PDF文件路径，使用逗号分隔: ").split(',')
        output_folder = input("请输入输出文件夹路径: ")
        scale_percent = int(input("请输入缩放比例（默认75）: ") or 75)
        window_size = int(input("请输入窗口大小（默认25）: ") or 25)
        k = float(input("请输入k值（默认0.08）: ") or 0.08)
        pdf_files = [pdf_file.strip() for pdf_file in pdf_files]
        process_multiple_pdfs(pdf_files, output_folder, scale_percent, window_size, k)

    elif mode == '3':
        pdf_folder = input("请输入PDF文件夹路径: ")
        output_folder = input("请输入输出文件夹路径: ")
        scale_percent = int(input("请输入缩放比例（默认75）: ") or 75)
        window_size = int(input("请输入窗口大小（默认25）: ") or 25)
        k = float(input("请输入k值（默认0.08）: ") or 0.08)
        process_folder(pdf_folder, output_folder, scale_percent, window_size, k)

    else:
        logger.error("无效模式选择，请选择 1, 2 或 3。")
