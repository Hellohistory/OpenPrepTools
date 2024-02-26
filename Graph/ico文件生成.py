import os
from PIL import Image
import questionary
from rich.console import Console
from rich.prompt import Prompt
from rich import print as rprint

# 创建Rich控制台实例
console = Console()


# 检查文件格式是否支持
def check_supported_format(file_path):
    supported_formats = ['png', 'jpg', 'jpeg', 'tif', 'bmp']
    ext = os.path.splitext(file_path)[-1].lower().strip('.')
    return ext in supported_formats


# 检查文件是否存在
def check_file_existence(file_path):
    return os.path.isfile(file_path)


# 选择图标尺寸
def select_icon_sizes():
    sizes = questionary.checkbox(
        "选择要生成的ICO图标尺寸:",
        choices=[
            questionary.Choice('16x16'),
            questionary.Choice('24x24'),
            questionary.Choice('32x32'),
            questionary.Choice('48x48'),
            questionary.Choice('64x64'),
            questionary.Choice('72x72'),
            questionary.Choice('80x80'),
            questionary.Choice('96x96', checked=True),
            questionary.Choice('128x128'),
            questionary.Choice('256x256'),
        ],
    ).ask()
    return [(int(size.split('x')[0]), int(size.split('x')[1])) for size in sizes]


# 将图片转换为多个尺寸的ICO图标
def convert_image_to_multiple_icos(input_path, target_directory=None, sizes=None):
    if not check_supported_format(input_path):
        rprint("[bold red]不支持的图片格式，请输入PNG、JPEG、TIFF、BMP格式的图片。[/]")
        return

    if not check_file_existence(input_path):
        rprint("[bold red]指定的文件不存在，请检查路径。[/]")
        return

    if not target_directory:
        target_directory = os.path.dirname(os.path.abspath(input_path))
    else:
        target_directory = os.path.abspath(target_directory)

    try:
        with Image.open(input_path) as image:
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            for size in sizes:
                icon_path = os.path.join(target_directory, f"{base_name}_{size[0]}x{size[1]}.ico")
                image.save(icon_path, format='ICO', sizes=[size])
                rprint(f"[bold green]已保存:[/] {icon_path}")

    except Exception as e:
        rprint(f"[bold red]转换过程中发生错误[/] {e}")


def main():
    input_path = Prompt.ask("[bold magenta]请输入图片文件路径[/]")
    target_directory = Prompt.ask("[bold magenta]请输入ICO文件保存的目录[留空则使用源文件所在目录]:", default="")
    sizes = select_icon_sizes()
    convert_image_to_multiple_icos(input_path, target_directory, sizes)


if __name__ == "__main__":
    main()
