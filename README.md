# 简历生成器

编辑 `data.json` → `python main.py generate` → PDF 输出到 `outputs/`

## 环境准备

### Python 3.7+

```bash
python --version  # 检查是否已安装
```

未安装请前往 [python.org](https://www.python.org/downloads/) 下载，安装时勾选 "Add Python to PATH"。

### TeX Live（XeLaTeX + 中文支持）

本工具使用 XeLaTeX 编译 PDF，模板依赖 `ctex` 中文宏包。

| 平台 | 安装方式 |
|------|----------|
| Windows | 下载 [TeX Live](https://www.tug.org/texlive/acquire-netinstall.html) 完整安装（约 30 分钟） |
| macOS | `brew install --cask mactex` 或前往 [tug.org/mactex](https://tug.org/mactex/) |
| Linux | `sudo apt install texlive-full`（或精简安装 `texlive-xetex texlive-lang-chinese texlive-latex-extra`） |

安装后验证 `xelatex` 命令可用：

```bash
xelatex --version
```

Windows 如果找不到命令，需将 TeX Live 的 bin 目录（如 `C:\texlive\2025\bin\windows`）添加到系统 PATH。

### 中文字体

- Windows / macOS — 自带中文字体，无需操作
- Linux — 需手动安装：`sudo apt install fonts-wqy-microhei fonts-wqy-zenhei`

## 使用方法

1. 编辑 `data.json` 填写简历信息
2. （可选）在 `photos/` 中放入个人照片（任意 jpg/png，无照片也可正常生成）
3. 运行 `python main.py generate`
4. 生成的 PDF 在 `outputs/` 文件夹

### 其他命令

```bash
python main.py <字段名>   # 填写单个字段
python main.py help       # 查看帮助
```

### 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| name | ✓ | 姓名 |
| email | ✓ | 邮箱 |
| phone | ✓ | 电话 |
| age | ✓ | 年龄 |
| hometown | ✓ | 户籍/籍贯 |
| location | ✓ | 现所在地 |
| education | ✓ | 教育经历（格式：时间段 学校 专业 \| 学位） |
| courses | ✓ | 主修课程 |
| projects | ✓ | 项目经历（多个项目用 `---` 分隔） |
| honors | | 在校荣誉/获奖经历 |
| skills | ✓ | 关键技能 |
| self_evaluation | ✓ | 自我评价 |

## 扩写功能

生成简历时，程序会询问是否需要 Claude 扩写「项目经历」和「自我评价」。选择 `y` 后，将当前内容发给 Claude 进行润色扩写，然后将结果粘贴回终端即可。

适合在 Claude Code 或 Claude 网页版中使用，让 AI 帮你把项目描述写得更专业。
