import json
import os
import re
import sys
import subprocess
import shutil
from datetime import datetime

# 设置UTF-8编码输出
sys.stdout.reconfigure(encoding='utf-8')

def find_xelatex():
    """查找 xelatex 可执行文件路径"""
    path = shutil.which("xelatex")
    if path:
        return path
    home = os.path.expanduser("~")
    candidates = [
        os.path.join(home, "AppData", "Local", "Programs", "MiKTeX", "miktex", "bin", "x64", "xelatex.exe"),
        r"C:\texlive\2025\bin\windows\xelatex.exe",
        r"C:\texlive\2024\bin\windows\xelatex.exe",
        r"C:\Program Files\MiKTeX\miktex\bin\x64\xelatex.exe",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None

def find_photo(photo_dir):
    """在指定目录中查找第一张图片（jpg/jpeg/png）"""
    if not os.path.isdir(photo_dir):
        return None
    for f in os.listdir(photo_dir):
        if f.lower().endswith(('.jpg', '.jpeg', '.png')):
            return os.path.join(photo_dir, f)
    return None

def read_config():
    """读取配置文件"""
    config_path = "config.json"
    if not os.path.exists(config_path):
        print(f"错误：配置文件 {config_path} 不存在")
        sys.exit(1)
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)

def save_data(user_data):
    """保存数据到文件"""
    data_file = ".resume_data.json"
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(user_data, f, ensure_ascii=False, indent=2)

def collect_single_field(field_name):
    """收集单个字段的数据"""
    config = read_config()
    field_config = config["required_fields"][field_name]
    required = " (必填)" if field_config.get("required", False) else " (可选)"
    prompt = field_config.get("prompt", f"请输入{field_name}")

    print(f"\n=== 请填写 {field_name} ===")
    print(f"{field_name}{required}")
    example = field_config.get("example", "")
    if example:
        print(f"  示例：{example}")
    print(f"  {prompt}: ", end="", flush=True)

    try:
        value = sys.stdin.readline().strip()
    except (EOFError, KeyboardInterrupt):
        print("\n输入已取消")
        return None

    if not value and field_config.get("required", False):
        print(f"  ⚠ 此项为必填，请重新输入")
        print(f"  {prompt}: ", end="", flush=True)
        try:
            value = sys.stdin.readline().strip()
        except (EOFError, KeyboardInterrupt):
            print("\n输入已取消")
            return None

    return value if value else None

def collect_user_data():
    """从文件读取或交互式收集用户数据"""
    data_file = ".resume_data.json"
    if os.path.exists(data_file):
        with open(data_file, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
        print(f"已从 {data_file} 读取用户数据")
        return user_data
    else:
        config = read_config()
        user_data = {}

        print("\n=== 请填写简历信息 ===")
        print("（每次只填写一个字段，完成后按回车继续下一个字段）\n")

        field_names = list(config["required_fields"].keys())

        for field_name in field_names:
            value = collect_single_field(field_name)

            if value:
                user_data[field_name] = value
                save_data(user_data)
                print(f"✓ {field_name} 已保存")
            else:
                if config["required_fields"][field_name].get("required", False):
                    print(f"⚠ {field_name} 是必填项，需要填写")
                    while True:
                        value = collect_single_field(field_name)
                        if value:
                            user_data[field_name] = value
                            save_data(user_data)
                            print(f"✓ {field_name} 已保存")
                            break
                else:
                    print(f"✗ {field_name} 已跳过")

            if field_name != field_names[-1]:
                print("\n按回车继续填写下一个字段，或输入 'done' 结束填写...")
                try:
                    continue_input = sys.stdin.readline().strip()
                    if continue_input.lower() == 'done':
                        break
                except (EOFError, KeyboardInterrupt):
                    break

        return user_data

def escape_latex(text):
    """转义 LaTeX 特殊字符"""
    if not text:
        return ""
    text = text.replace('\\', '\\textbackslash{}')
    text = text.replace('&', '\\&')
    text = text.replace('%', '\\%')
    text = text.replace('$', '\\$')
    text = text.replace('#', '\\#')
    text = text.replace('_', '\\_')
    text = text.replace('{', '\\{')
    text = text.replace('}', '\\}')
    text = text.replace('~', '\\textasciitilde{}')
    text = text.replace('^', '\\textasciicircum{}')
    return text

def format_projects_latex(projects_text):
    """将项目经历格式化为 LaTeX 列表项"""
    projects = [p.strip() for p in projects_text.split("---") if p.strip()]
    items = []
    for proj in projects:
        proj = escape_latex(proj)
        proj = proj.replace('\n', ' \\\\\n    ')
        items.append(f"  \\item {proj}")
    return "\n".join(items)

def format_skills_latex(skills_text):
    """将技能格式化为 LaTeX 列表项（由模板决定列表环境）"""
    skills = [s.strip() for s in re.split(r'[,，、]', skills_text) if s.strip()]
    if len(skills) <= 1:
        return escape_latex(skills_text)
    items = []
    for skill in skills:
        items.append(f"  \\item {escape_latex(skill)}")
    return "\n".join(items)

def ask_expand(field_name, content):
    """询问用户是否需要扩写某个字段，返回扩写后的内容或原内容"""
    print(f"\n{'='*50}")
    print(f"【{field_name}】当前内容：")
    print(content)
    print(f"{'='*50}")
    print("是否需要先让 Claude 扩写再生成？(y/n)")
    try:
        choice = input().strip().lower()
    except (EOFError, KeyboardInterrupt):
        return content
    if choice != 'y':
        return content

    print(f"\n请在 Claude 中要求扩写以下内容，然后将结果粘贴回来。")
    print(f"（直接按回车保持原内容）：\n")
    try:
        expanded = sys.stdin.read().strip()
    except (EOFError, KeyboardInterrupt):
        return content
    return expanded if expanded else content

def generate_resume(user_data):
    """生成简历文档（LaTeX → PDF）"""
    config = read_config()

    # 验证必填项
    for field_name, field_config in config["required_fields"].items():
        if field_config.get("required", False):
            if field_name not in user_data or not user_data[field_name]:
                print(f"✗ 必填项 '{field_name}' 未填写")
                return None

    # 扩写选项
    if user_data.get("projects") or user_data.get("self_evaluation"):
        print("\n=== 简历内容优化 ===")
        print("以下字段可以先让 Claude 扩写后再生成简历：")

        if user_data.get("projects"):
            user_data["projects"] = ask_expand("项目经历", user_data["projects"])
            save_data(user_data)

        if user_data.get("self_evaluation"):
            user_data["self_evaluation"] = ask_expand("自我评价", user_data["self_evaluation"])
            save_data(user_data)

    # 创建输出文件夹
    output_dir = config["output_dir"]
    os.makedirs(output_dir, exist_ok=True)

    # 读取 LaTeX 模板
    template_path = config["template_file"]
    if not os.path.exists(template_path):
        print(f"错误：模板文件 {template_path} 不存在")
        return None

    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    safe_name = user_data.get("name", "resume")
    safe_name = re.sub(r'[\\/*?:"<>|]', "", safe_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    photo_path = find_photo(config.get("photo_dir", "photos"))
    if photo_path:
        photo_path = photo_path.replace("\\", "/")

    photo_block = ""
    if photo_path:
        photo_block = (
            "\\begin{minipage}[c]{0.25\\textwidth}\n"
            "  \\raggedleft\n"
            f"  \\includegraphics[width=3cm]{{{photo_path}}}\n"
            "\\end{minipage}"
        )

    replacements = {
        "name": escape_latex(user_data.get("name", "")),
        "email": escape_latex(user_data.get("email", "")),
        "phone": escape_latex(user_data.get("phone", "")),
        "age": escape_latex(user_data.get("age", "")),
        "hometown": escape_latex(user_data.get("hometown", "")),
        "location": escape_latex(user_data.get("location", "")),
        "education": escape_latex(user_data.get("education", "")),
        "courses": escape_latex(user_data.get("courses", "")),
        "projects": format_projects_latex(user_data.get("projects", "")),
        "honors": escape_latex(user_data.get("honors", "")),
        "skills": format_skills_latex(user_data.get("skills", "")),
        "self_evaluation": escape_latex(user_data.get("self_evaluation", "")),
        "photo_block": photo_block,
    }

    tex_content = template
    for key, value in replacements.items():
        placeholder = "{{" + key + "}}"
        tex_content = tex_content.replace(placeholder, value)

    tex_path = os.path.join(output_dir, f"{safe_name}_{timestamp}.tex")
    with open(tex_path, 'w', encoding='utf-8') as f:
        f.write(tex_content)

    print(f"✓ LaTeX 文件已生成: {tex_path}")

    print("正在编译 PDF ...")
    xelatex_cmd = find_xelatex()
    if not xelatex_cmd:
        print("✗ 未找到 xelatex，请安装 TeX Live 或 MiKTeX")
        print(f"LaTeX 源文件已生成: {tex_path}")
        return tex_path
    try:
        result = subprocess.run(
            [xelatex_cmd, "-interaction=nonstopmode", "-output-directory", output_dir, tex_path],
            capture_output=True,
            timeout=60,
        )
        if result.returncode == 0:
            pdf_path = tex_path.replace(".tex", ".pdf")
            print(f"✓ PDF 编译成功: {pdf_path}")
            for ext in [".aux", ".log", ".out"]:
                aux_file = tex_path.replace(".tex", ext)
                if os.path.exists(aux_file):
                    os.remove(aux_file)
            return pdf_path
        else:
            print("✗ PDF 编译失败")
            output = result.stdout.decode("utf-8", errors="replace")
            for line in output.splitlines():
                if line.startswith("!") or "Error" in line or "error" in line:
                    print(f"  {line}")
            print(f"\nLaTeX 源文件保留于: {tex_path}")
            return tex_path
    except FileNotFoundError:
        print("✗ xelatex 执行失败，请检查安装")
        print(f"LaTeX 源文件已生成: {tex_path}")
        return tex_path
    except subprocess.TimeoutExpired:
        print("✗ 编译超时（60秒）")
        print(f"LaTeX 源文件保留于: {tex_path}")
        return tex_path

def generate_from_file(data_file):
    """从文件生成简历"""
    with open(data_file, 'r', encoding='utf-8') as f:
        user_data = json.load(f)

    print(f"已从 {data_file} 读取用户数据")

    print("\n正在生成简历...")
    output_path = generate_resume(user_data)
    if output_path:
        print(f"\n✓ 简历生成成功: {output_path}")
    else:
        print("\n✗ 简历生成失败")

def main():
    """主入口"""
    config = read_config()

    if len(sys.argv) > 1 and sys.argv[1] == "帮我生成简历":
        user_data = collect_user_data()
        print("\n正在生成简历...")
        output_path = generate_resume(user_data)
        if output_path:
            print(f"\n✓ 简历生成成功: {output_path}")
            if os.path.exists(".resume_data.json"):
                os.remove(".resume_data.json")
        else:
            print("\n✗ 简历生成失败")
        return

    if len(sys.argv) < 2:
        user_data = collect_user_data()
        print("\n正在生成简历...")
        output_path = generate_resume(user_data)
        if output_path:
            print(f"\n✓ 简历生成成功: {output_path}")
            if os.path.exists(".resume_data.json"):
                os.remove(".resume_data.json")
        else:
            print("\n✗ 简历生成失败")
        return

    command = sys.argv[1]

    if command in ["help", "-h", "--help"]:
        print("=== 简历生成器 ===\n")
        print("命令：")
        print("  python main.py 帮我生成简历    # 开始生成简历（逐字段填写）")
        print("  python main.py <字段名>      # 填写指定字段")
        print("  python main.py generate      # 从data.json生成简历")
        print("  python main.py help         # 帮助信息\n")
        print("可用字段：")
        for name, cfg in config["required_fields"].items():
            required = " (必填)" if cfg.get("required", False) else " (可选)"
            print(f"  {name}{required}")
    elif command == "generate":
        data_file = "data.json"
        if len(sys.argv) > 2:
            data_file = sys.argv[2]
        if not os.path.exists(data_file):
            print(f"错误：数据文件 {data_file} 不存在")
        else:
            generate_from_file(data_file)
    elif command in config["required_fields"]:
        field_name = command
        data_file = ".resume_data.json"
        user_data = {}
        if os.path.exists(data_file):
            with open(data_file, 'r', encoding='utf-8') as f:
                user_data = json.load(f)

        value = collect_single_field(field_name)
        if value:
            user_data[field_name] = value
            save_data(user_data)
            print(f"✓ {field_name} 已保存到 .resume_data.json")

            all_filled = True
            for name, cfg in config["required_fields"].items():
                if cfg.get("required", False) and name not in user_data:
                    all_filled = False
                    break

            if all_filled:
                print("\n所有必填项已完成！是否立即生成简历？(y/n)")
                try:
                    choice = sys.stdin.readline().strip().lower()
                    if choice == 'y':
                        print("\n正在生成简历...")
                        output_path = generate_resume(user_data)
                        if output_path:
                            print(f"\n✓ 简历生成成功: {output_path}")
                            if os.path.exists(".resume_data.json"):
                                os.remove(".resume_data.json")
                        else:
                            print("\n✗ 简历生成失败")
                except (EOFError, KeyboardInterrupt):
                    print("\n已保存数据，稍后可使用 'python main.py generate' 生成简历")
        else:
            print(f"✗ {field_name} 未保存")
    else:
        print("未知命令。运行 'python main.py help' 查看帮助。")

if __name__ == "__main__":
    main()
