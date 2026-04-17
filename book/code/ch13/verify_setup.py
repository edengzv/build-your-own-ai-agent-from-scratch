# MiniAgent 环境检查脚本
# 运行: python miniagent/verify_setup.py

import sys

def main():
    print("=== MiniAgent 环境检查 ===\n")

    # Python 版本
    v = sys.version_info
    py_ok = v >= (3, 10)
    print(f"Python 版本: {v.major}.{v.minor}.{v.micro} {'✓' if py_ok else '✗ (需要 3.10+)'}")

    # anthropic 库
    try:
        import anthropic
        print(f"anthropic 库: {anthropic.__version__} ✓")
    except ImportError:
        print("anthropic 库: 未安装 ✗")
        print("  → 运行: pip install anthropic")

    # API Key
    import os
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if key:
        print(f"ANTHROPIC_API_KEY: 已设置 (***{key[-4:]}) ✓")
    else:
        print("ANTHROPIC_API_KEY: 未设置 ✗")
        print("  → 运行: export ANTHROPIC_API_KEY='your-key-here'")

    print("\n=== 检查完成 ===")


if __name__ == "__main__":
    main()
