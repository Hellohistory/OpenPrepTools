#### 本工具是一个基于 PyQt5 的桌面应用程序，专门用于生成2FA验证码  
  
#### 有时候我们会需要使用到基于时间的2FA验证码，通常情况下是使用谷歌，电脑上也有基于网页版的工具，但是我不太放心使用，因此这个基于Python的小工具就诞生了！
## 界面展示  

![软件运行界面](image/离线2FA验证工具运行界面.png)  

## 源代码与二次开发  

如你有兴趣对本工具进行二次开发，请先阅读 LICENSE 文件，遵守相关协议。本项目的核心逻辑位于 `totp_core.py` 文件中，已进行封装，二次开发时请重点关注此部分。 

## 自行编译教程

本项目采用`nuitka`进行打包，打包指令如下：

```angular2html
nuitka --standalone --mingw64 --output-dir=dist --enable-plugin=pyqt5 --windows-console-mode=disable --windows-icon-from-ico=icon.ico totp_gui.py 
```

## 项目链接  

- [GitHub 地址](https://github.com/Hellohistory/OpenPrepTools)  
- [Gitee 地址](https://gitee.com/Hellohistory/OpenPrepTools)  

## [技术原理说明](TechnicalPrinciples/TOTP%20算法与实现解析.md)
  
## 最后说明  

此密码无法恢复，无法找回，请务必牢记！！！！！！

## 下载地址

[百度网盘](https://pan.baidu.com/s/1vxFJF0bLLUYDSCT0SYIvnw?pwd=jg25)

[蓝奏云](https://xmy521.lanzn.com/i3OoR2lhw32d)
