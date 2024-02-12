import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import hashlib
import json
import os
import webbrowser


class MD5CheckerApp:
    def __init__(self, root):
        self.root = root
        self.performance_check = tk.BooleanVar()
        self.performance_check.set(False)
        self.setup_ui()

    def setup_ui(self):
        """设置UI界面"""
        self.root.title('MD5校验器')
        self.root.geometry('600x600')

        # 主框架
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 文件操作框架
        file_frame = tk.Frame(main_frame)
        file_frame.pack(fill=tk.X, expand=False, pady=5)
        self.add_button = tk.Button(file_frame, text="添加文件MD5", command=self.add_file_md5)
        self.add_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.check_button = tk.Button(file_frame, text="校验文件MD5", command=self.check_file_md5)
        self.check_button.pack(side=tk.LEFT, padx=5, pady=5)

        # 性能设置框架
        performance_frame = tk.Frame(main_frame)
        performance_frame.pack(fill=tk.X, expand=False, pady=5)
        self.performance_checkbox = tk.Checkbutton(performance_frame, text="仅计算文件的前256KB",
                                                   variable=self.performance_check)
        self.performance_checkbox.pack(side=tk.LEFT, padx=5, pady=5)

        # 输出显示框架
        output_frame = tk.Frame(main_frame)
        output_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.output_text = scrolledtext.ScrolledText(output_frame, height=20, width=70)
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 进度条框架
        progress_frame = tk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, expand=False, pady=5)
        self.progress = ttk.Progressbar(progress_frame, orient="horizontal", length=200, mode="determinate")
        self.progress.pack(fill=tk.X, expand=True, padx=5, pady=5)

        # 链接访问框架
        self.setup_links(main_frame)

    def setup_links(self, main_frame):
        """设置底部链接"""
        link_frame = tk.Frame(main_frame)
        link_frame.pack(fill=tk.X, expand=False, pady=5)
        links = {
            "源码（GitHub）": "https://gist.github.com/Hellohistory/32af2c9eba1ebce32e48b6d8516eb988",
            "源码（Gitee）": "https://gitee.com",
            "更多项目（GitHub）": "https://github.com",
            "更多项目（Gitee）": "https://gitee.com",
        }
        for i, (text, url) in enumerate(links.items()):
            link_label = tk.Label(link_frame, text=text, fg="blue", cursor="hand2")
            link_label.pack(side=tk.LEFT, padx=10, pady=5)
            link_label.bind("<Button-1>", lambda e, url=url: self.open_url(url))

    def calculate_md5(self, file_path):
        """计算并返回文件的MD5哈希值，根据性能提升选项决定计算方式"""
        with open(file_path, 'rb') as file:
            file_hash = hashlib.md5()
            if self.performance_check.get():
                chunk = file.read(262144)  # 读取前256KB
                file_hash.update(chunk)
            else:
                while chunk := file.read(8192):
                    file_hash.update(chunk)
        return file_hash.hexdigest()

    def write_to_json(self, file_path, md5_hash):
        """将文件名、MD5哈希值和是否仅计算了前256KB的MD5写入JSON文件"""
        data = {}
        if os.path.exists('md5_data.json'):
            with open('md5_data.json', 'r') as f:
                data = json.load(f)
        data[file_path] = {'md5': md5_hash, 'partial': self.performance_check.get()}
        with open('md5_data.json', 'w') as f:
            json.dump(data, f, indent=4)

    def add_file_md5(self):
        """选择多个文件，计算MD5并写入JSON"""
        file_paths = filedialog.askopenfilenames(filetypes=self.file_types)
        total_files = len(file_paths)
        if file_paths:
            for i, file_path in enumerate(file_paths, start=1):
                md5_hash = self.calculate_md5(file_path)
                self.write_to_json(file_path, md5_hash)
                self.insert_output(f"{os.path.basename(file_path)}: {md5_hash}\n", "match")
                self.progress['value'] = (i / total_files) * 100
                self.root.update_idletasks()
            messagebox.showinfo("成功", "所选文件的MD5已全部写入")
        self.progress['value'] = 0

    def check_file_md5(self):
        """选择多个文件，计算MD5并与JSON中的值比较"""
        file_paths = filedialog.askopenfilenames(filetypes=self.file_types)
        total_files = len(file_paths)
        if file_paths:
            if not os.path.exists('md5_data.json'):
                messagebox.showwarning("警告", "MD5数据文件不存在，请先添加文件MD5。")
                return
            with open('md5_data.json', 'r') as f:
                data = json.load(f)
            for i, file_path in enumerate(file_paths, start=1):
                md5_hash = self.calculate_md5(file_path)
                file_info = data.get(file_path)
                if file_info and file_info['md5'] == md5_hash and file_info['partial'] == self.performance_check.get():
                    self.insert_output(f"匹配: {os.path.basename(file_path)}\n", "match")
                else:
                    self.insert_output(f"不匹配: {os.path.basename(file_path)}\n", "nomatch")
                self.progress['value'] = (i / total_files) * 100
                self.root.update_idletasks()
        self.progress['value'] = 0

    def insert_output(self, text, tag):
        """向输出文本框插入文本，并根据标签使用不同颜色"""
        self.output_text.insert(tk.END, text)
        if tag == "match":
            self.output_text.tag_add(tag, "end-1c linestart", "end-1c")
            self.output_text.tag_configure(tag, foreground="green")
        elif tag == "nomatch":
            self.output_text.tag_add(tag, "end-1c linestart", "end-1c")
            self.output_text.tag_configure(tag, foreground="red")

    def open_url(self, url):
        """打开给定的URL"""
        webbrowser.open(url)


if __name__ == "__main__":
    root = tk.Tk()
    app = MD5CheckerApp(root)
    root.mainloop()
