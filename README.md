# OpenPrepTools

OpenPrepTools 是一个旨在整合多种数据预处理工具的项目，以便于后续使用。项目中包含的工具涵盖了文件整理、MD5校验等多个方面，部分工具已被打包为可执行文件，便于直接使用。

## 项目说明

OpenPrepTools 项目提供了一系列工具，帮助用户高效进行数据预处理和文件管理。通过简化日常工作流程，用户可以节省时间，提高工作效率。

由于项目日渐扩大，编译后的软件版本越来越多，因此不再上传至github与gitee发行版仓库，改由云盘管理，您也可以选择自行编译！

### 工具列表

| 工具编号 | 工具名称        | 功能简介                        | 项目地址                                                            | 说明文件地址                                               | 最新版本下载                                        |
|------|-------------|-----------------------------|-----------------------------------------------------------------|------------------------------------------------------|-----------------------------------------------|
| 0001 | 文件夹综合整理工具   | 一个功能强大的文件整理工具，支持文件移动、备份等功能  | [文件夹综合整理工具.py](File/文件夹综合整理工具.py)                               | [文件夹综合整理工具.md](ExplanationDocument/文件夹综合整理工具.md)     | [下载](https://xmy521.lanzouy.com/i9QAt2uphqzg) |
| 0002 | MD5校验器      | 用于生成和校验文件MD5哈希值，确保文件完整性和一致性 | [md5校验_GUI.py](Other/md5校验_GUI.py)                              | [MD5校验器.md](ExplanationDocument/MD5校验器.md)           | [下载](https://xmy521.lanzouy.com/iaAgZ1o4m1oh) |
| 0003 | 伪文件生成       | 生成伪文件用来测试程序功能               | [生成伪文件.py](File/生成伪文件.py)                                       | [生成伪文件.md](ExplanationDocument/生成伪文件.md)             | [下载](https://xmy521.lanzouy.com/iaJsB2uphqkb) |
| 0004 | 一次性密码生成     | 用于生成一次性密码，并且实现检测密码强度        | [Safe_Code](Other/Safe_Code)                                    | [一次性密码生成.md](ExplanationDocument/一次性密码生成.md)         | [下载](https://xmy521.lanzouy.com/iMszB22cds8b) |
| 0005 | PDF转长图      | 用于将PDF文件转换为长图               | [PDF2Longimg.py](Graph/PDF2Longimg.py)                          | [PDF转长图.md](ExplanationDocument/PDF转长图.md)           | [下载](https://xmy521.lanzn.com/iYWhD27ok9pi)   |
| 0006 | 灰度图片转黑白图片   | 用于将灰度图片转换为黑白图片              | [Gray2BlackWhite](Graph/Convert2BlackWhite)                     | [灰度图片转黑白图片.md](ExplanationDocument/灰度图片转黑白图片.md)     | [下载](https://xmy521.lanzouy.com/il8h92upi8ze) |
| 0007 | 代码变量函数名翻译工具 | 翻译为常见命名规范                   | [CodeTranslation](Other/CodeTranslation)                        | [代码变量函数名翻译工具.md](ExplanationDocument/代码变量函数名翻译工具.md) | [下载](https://xmy521.lanzouy.com/iKP4H2uphqcd) |
| 0008 | 网易云单曲下载工具   | 下载网易云单曲                     | [163_music_download](Other/163_music_download)                  | [网易云单曲下载工具.md](ExplanationDocument/网易云单曲下载工具.md)     | [下载](https://xmy521.lanzn.com/iQi2r2g0854b)   |
| 0009 | 万能视频下载器     | 支持多种视频网站视频下载，支持批量下载         | [UniversalVideoDownloader](Downloader/UniversalVideoDownloader) | [万能视频下载器.md](ExplanationDocument/万能视频下载器.md)         | [下载](https://xmy521.lanzouy.com/icx4r2upi68f) |
| 0010 | 离线2FA验证工具   | 离线生成2FA验证码                  | [2FA_Tool](Other/2FA_Tool)                                      | [离线2FA验证工具.md](ExplanationDocument/离线2FA验证工具.md)     | [下载](https://xmy521.lanzn.com/iqCCY2uor3ah)   |
| 0011 | 中华甲子历史年表    | 中华甲子历史年表                    | [HistoryChronology](HistoryChronology)                          | [中华甲子历史年表.md](ExplanationDocument/中华甲子历史年表.md)       | [下载](https://xmy521.lanzn.com/iYl0o2ud4s6j)   |

### 使用说明

1. 根据需要选择并点击上述表格中的工具链接。
2. 阅读工具的详细说明文件，了解其功能和使用方法。
3. 根据说明文件中的指导下载并启动工具。

## 开发背景

随着数据处理需求的增长，高效的预处理工具变得越来越重要。OpenPrepTools 项目应运而生，旨在为广大用户提供一套易于使用的数据预处理和文件管理工具。

## 许可证

本项目整体采用 [Apache 2.0 许可证](LICENSE)。但是由于本项目部分项目使用 `QT` 作为UI库，其传染性因此亦采用 `GPL` 协议。因此使用 `OpenPrepTools` 项目中的工具时，请确保遵守相应的许可证条款。

## 一些说明

Windows7现在仍然被很多人使用，但是因为我的电脑是Windows11，所以你可能需要自己重新编译项目，Python项目使用Python3.8-32编译即可。

## 联系方式

如有问题或建议，请通过Issues联系即可。
