import os
from PIL import Image
import questionary
from rich.console import Console
from rich.prompt import Prompt
from rich import print as rprint
from rich.table import Table

console = Console()


def display_intro():
    table = Table(title="程序介绍")

    table.add_column("项目", justify="right", style="cyan", no_wrap=True)
    table.add_column("信息(按下Ctrl后点击链接访问)", style="magenta")

    table.add_row("程序名称", "ICO生成")
    table.add_row("开发者", "Hellohistory")
    table.add_row("项目源码(Github)", "https://gist.github.com/Hellohistory/f9c6dc2380cadc60ccf261a47ece958c")
    table.add_row("更多项目(Github)", "https://github.com/Hellohistory/OpenPrepTools")
    table.add_row("更多项目(Gitee)", "https://gitee.com/Hellohistory/OpenPrepTools")

    console.print(table)


def check_supported_format(file_path):
    supported_formats = ['png', 'jpg', 'jpeg', 'tif', 'bmp']
    ext = os.path.splitext(file_path)[-1].lower().strip('.')
    return ext in supported_formats


def check_file_existence(file_path):
    return os.path.isfile(file_path)


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
    while True:
        display_intro()
        input_path = Prompt.ask("[bold magenta]请输入图片文件路径[/]")
        target_directory = Prompt.ask("[bold magenta]请输入ICO文件保存的目录[留空则使用源文件所在目录]:", default="")
        sizes = select_icon_sizes()
        convert_image_to_multiple_icos(input_path, target_directory, sizes)

        continue_choice = Prompt.ask("[bold cyan]继续使用请输入'y'，退出请输入任意其他键[/]", default="n")
        if continue_choice.lower() != 'y':
            break


if __name__ == "__main__":
    main()
