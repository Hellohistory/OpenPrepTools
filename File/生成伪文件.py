import os
import random
from rich.console import Console
from rich.table import Table
from rich.progress import track


def display_intro():
    table = Table(title="程序介绍")

    table.add_column("项目", justify="right", style="cyan", no_wrap=True)
    table.add_column("信息(按下Ctrl后点击链接访问)", style="magenta")

    table.add_row("程序名称", "伪文件生成")
    table.add_row("开发者", "Hellohistory")
    table.add_row("项目源码(Github)", "https://gist.github.com/Hellohistory/d38ebe4730a2235f40a465652090145b")
    table.add_row("更多项目(Github)", "https://github.com/Hellohistory/OpenPrepTools")
    table.add_row("更多项目(Gitee)", "https://gitee.com/Hellohistory/OpenPrepTools")

    console.print(table)


def generate_random_name(base_text, max_length, existing_names):
    while True:
        random_name = ''.join(random.choice(base_text) for _ in range(random.randint(1, max_length)))
        if random_name not in existing_names:
            return random_name


def create_fake_files(directory, file_details, use_random_names=False, base_text="", max_length=10):
    if not os.path.exists(directory):
        os.makedirs(directory)

    total_files = sum(file_details.values())
    existing_names = set()

    for ext, num_files in file_details.items():
        for i in track(range(num_files), description=f"正在创建 .{ext} 文件..."):
            if use_random_names:
                random_name = generate_random_name(base_text, max_length, existing_names)
                filename = f"{random_name}.{ext}"
                existing_names.add(random_name)
            else:
                filename = f"fake_file_{i + 1}.{ext}"
            filepath = os.path.join(directory, filename)
            with open(filepath, 'w') as f:
                f.write("This is a fake file.")
    console.print(f"[green]{total_files} 个伪文件已成功创建在 {directory} 中。[/green]")


if __name__ == "__main__":
    console = Console()
    display_intro()

    while True:
        directory = console.input("请输入要创建文件的目录路径：")
        use_random_names = console.input("是否使用随机文件名？(y/n)：").lower() == 'y'
        base_text = ""
        max_length = 10
        if use_random_names:
            base_text = console.input("请输入用于生成文件名的文字：")
            max_length = int(console.input("请输入文件名的最大长度："))

        extensions_input = console.input("请输入文件的扩展名（用逗号分隔）：")
        if extensions_input.strip() == "":
            file_details = {"txt": 1000}
        else:
            extensions = [ext.strip() for ext in extensions_input.replace("，", ",").split(",")]
            file_details = {}
            for ext in extensions:
                num_input = console.input(f"请输入要为 .{ext} 文件创建的数量[默认为1000]：")
                num_files = int(num_input) if num_input.strip() != "" else 1000
                file_details[ext] = num_files

        create_fake_files(directory, file_details, use_random_names, base_text, max_length)

        continue_choice = console.input("是否继续创建文件？(y/n)：")
        if continue_choice.lower() != "y":
            console.print("[bold magenta]程序已退出。[/bold magenta]")
            break
