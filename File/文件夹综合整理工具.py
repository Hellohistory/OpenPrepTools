import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import track
from rich.prompt import Prompt
from rich.text import Text
from rich.traceback import install

install()
console = Console()

GITHUB_URL = "https://gist.github.com/Hellohistory/54b529cfc4d53c3041f3d005785a8e77"
AUTHOR_NAME = "Hellohistory"


def display_script_info():
    """显示脚本信息"""
    header_markdown = Markdown(
        f"# 文件整理工具\n\n👤 作者: {AUTHOR_NAME}\n🔗 GitHub: [链接]({GITHUB_URL})\n\n[脚本信息] 这是一个用于文件整理的脚本，包括文件移动、文件夹重命名等功能。")
    console.print(Panel(header_markdown, title="[bold magenta]欢迎[/bold magenta]", expand=False, border_style="red"))


def display_footer():
    """显示程序尾部信息"""
    footer_text = Text.assemble(
        ("脚本由 ", "bold"),
        (AUTHOR_NAME, "bold green"),
        (" 编写 - ", "bold"),
        ("GitHub", "link " + GITHUB_URL),
        style="italic"
    )
    console.print(Panel(footer_text, style="green"))


def handle_duplicate_file(dest_file):
    """处理目标文件夹中的同名文件"""
    base, extension = os.path.splitext(dest_file)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    new_dest_file = f"{base}_{timestamp}{extension}"
    return new_dest_file


def move_file(src_file, dest_file):
    try:
        shutil.move(src_file, dest_file)
        console.log(f"文件 {src_file} 已移动到 {dest_file}")
    except Exception as e:
        console.log(f"无法移动文件 {src_file}: {e}")


def move_files():
    """移动文件的功能实现"""
    src_dir = Prompt.ask("请输入源文件夹路径", console=console)
    dest_dir = Prompt.ask("请输入目标文件夹路径", console=console)

    src_dir = os.path.abspath(src_dir)
    dest_dir = os.path.abspath(dest_dir)
    file_tasks = []

    for root, _, files in os.walk(src_dir):
        for name in files:
            src_file = os.path.join(root, name)
            dest_file = os.path.join(dest_dir, name)
            if os.path.exists(dest_file):
                dest_file = handle_duplicate_file(dest_file)
            file_tasks.append((src_file, dest_file))

    with ThreadPoolExecutor(max_workers=5) as executor:
        for src_file, dest_file in file_tasks:
            executor.submit(move_file, src_file, dest_file)


def rename_folders():
    """重命名文件夹的功能实现，去掉'_'和后续数字"""
    base_dir = Prompt.ask("请输入文件夹所在的基本路径", console=console)
    start_number_str = Prompt.ask("请输入文件夹编号起始数字", default="100", console=console)
    start_number = int(start_number_str)

    folders = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    for folder_name in track(sorted(folders), description="正在重命名文件夹..."):
        old_path = os.path.join(base_dir, folder_name)
        new_folder_name = f"{start_number:03d}"  # 去掉'_'和后续数字
        new_path = os.path.join(base_dir, new_folder_name)
        os.rename(old_path, new_path)
        console.log(f"文件夹 {old_path} 重命名为 {new_path}")
        start_number += 1


def select_log_level():
    """选择日志级别"""
    level = Prompt.ask("请选择日志级别 (1-简单, 2-详细)", choices=["1", "2"], default="1", console=console)
    if level == "1":
        console.log("已设置为简单日志级别")
    else:
        console.log("已设置为详细日志级别")


def backup_file(src_file, dest_file):
    try:
        shutil.copy2(src_file, dest_file)
        console.log(f"文件 {src_file} 已备份到 {dest_file}")
    except Exception as e:
        console.log(f"无法备份文件 {src_file}: {e}")


def backup_files():
    """备份文件的功能实现"""
    src_dir = Prompt.ask("请输入需要备份的源文件夹路径", console=console)
    dest_dir = Prompt.ask("请输入备份文件的目标文件夹路径", console=console)

    src_dir = os.path.abspath(src_dir)
    dest_dir = os.path.abspath(dest_dir)

    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
        console.log(f"已创建备份目标文件夹 {dest_dir}")

    file_tasks = []

    for root, _, files in os.walk(src_dir):
        for name in files:
            src_file = os.path.join(root, name)
            dest_file = os.path.join(dest_dir, name)
            if os.path.exists(dest_file):
                dest_file = handle_duplicate_file(dest_file)
            file_tasks.append((src_file, dest_file))

    with ThreadPoolExecutor(max_workers=5) as executor:
        for src_file, dest_file in file_tasks:
            executor.submit(backup_file, src_file, dest_file)


def move_subfolder_files_to_parent():
    """将子文件夹内的文件移动到父文件夹"""
    parent_dir = Prompt.ask("请输入父文件夹路径", console=console)
    parent_dir = os.path.abspath(parent_dir)

    if not os.path.isdir(parent_dir):
        console.log(f"指定的路径不是一个文件夹: {parent_dir}")
        return

    file_tasks = []

    subfolders = [d for d in os.listdir(parent_dir) if os.path.isdir(os.path.join(parent_dir, d))]
    for folder in subfolders:
        folder_path = os.path.join(parent_dir, folder)
        for root, _, files in os.walk(folder_path):
            for name in files:
                src_file = os.path.join(root, name)
                dest_file = os.path.join(parent_dir, name)
                if os.path.exists(dest_file):
                    dest_file = handle_duplicate_file(dest_file)
                file_tasks.append((src_file, dest_file))

    with ThreadPoolExecutor(max_workers=5) as executor:
        for src_file, dest_file in file_tasks:
            executor.submit(move_file, src_file, dest_file)


def split_folder(folder_path, subfolder_count):
    """将文件夹中的文件均匀分配到指定数量的子文件夹中"""
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    total_files = len(files)
    files_per_subfolder, remainder = divmod(total_files, subfolder_count)

    current_file_index = 0
    for i in range(subfolder_count):
        subfolder_path = os.path.join(folder_path, f"{i + 1}")
        os.makedirs(subfolder_path, exist_ok=True)
        for j in range(files_per_subfolder + (1 if i < remainder else 0)):
            shutil.move(os.path.join(folder_path, files[current_file_index]), subfolder_path)
            current_file_index += 1
    console.log("文件移动完成！")


def move_all_files(source_folder, destination_folder):
    """将源文件夹中的所有文件移动到目标文件夹，包括子文件夹中的文件"""
    files = os.listdir(source_folder)
    for filename in files:
        file_path = os.path.join(source_folder, filename)
        if os.path.isfile(file_path):
            shutil.move(file_path, destination_folder)
        elif os.path.isdir(file_path):
            move_all_files(file_path, destination_folder)
    console.log("文件移动完成！")


def main():
    display_script_info()
    console.print("文件整理工具", style="bold green")

    menu_options = {
        "1": ("移动文件", move_files),
        "2": ("重命名文件夹", rename_folders),
        "3": ("选择日志级别", select_log_level),
        "4": ("备份文件", backup_files),
        "5": ("将子文件夹内的文件移动到父文件夹", move_subfolder_files_to_parent),
        "6": ("文件夹中文件平均分配到子文件夹", lambda: split_folder_prompt()),
        "7": ("移动源文件夹中的所有文件到目标文件夹", lambda: move_all_files_prompt())
    }

    while True:
        console.print(Panel("[bold yellow]菜单选项[/bold yellow]", expand=False))
        for key, (desc, _) in menu_options.items():
            console.print(Text.assemble((f"{key}: ", "bold cyan"), (desc, "bold white")))
        console.print("0: 退出", style="bold red")

        choice = Prompt.ask("请选择一个选项", choices=list(menu_options.keys()) + ["0"], console=console)
        if choice == "0":
            break
        else:
            func = menu_options[choice][1]
            func()

    display_footer()


def split_folder_prompt():
    folder_path = Prompt.ask("请输入需要分配的文件夹路径", console=console)
    subfolder_count = int(Prompt.ask("请输入子文件夹数量", console=console))
    split_folder(folder_path, subfolder_count)


def move_all_files_prompt():
    source_folder = Prompt.ask("请输入源文件夹路径", console=console)
    destination_folder = Prompt.ask("请输入目标文件夹路径", console=console)
    move_all_files(source_folder, destination_folder)


if __name__ == "__main__":
    main()
