#!/usr/bin/env python3
"""analyze_complexity.py — 分析代码文件的复杂度指标

用法: python analyze_complexity.py <file-path>
stdout: JSON 分析结果
stderr: 状态信息

支持: Python (.py), JavaScript/TypeScript (.js/.ts/.jsx/.tsx)
"""

import sys
import json
import re
from pathlib import Path


def count_indentation_depth(lines):
    """计算最大嵌套深度"""
    max_depth = 0
    for line in lines:
        stripped = line.rstrip()
        if not stripped:
            continue
        indent = len(line) - len(line.lstrip())
        # 假设 4 空格或 1 tab = 1 级
        depth = indent // 4 if '\t' not in line else line.count('\t')
        max_depth = max(max_depth, depth)
    return max_depth


def detect_functions(lines, ext):
    """检测函数定义及其行范围"""
    functions = []

    if ext == '.py':
        pattern = re.compile(r'^(\s*)def\s+(\w+)\s*\(')
    elif ext in ('.js', '.ts', '.jsx', '.tsx'):
        pattern = re.compile(
            r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(|(\w+)\s*\([^)]*\)\s*\{)'
        )
    else:
        return functions

    for i, line in enumerate(lines):
        match = pattern.search(line)
        if match:
            name = next((g for g in match.groups() if g), 'anonymous')
            functions.append({
                'name': name,
                'start_line': i + 1,
                'indent': len(line) - len(line.lstrip())
            })

    # 估算函数结束行
    for idx, func in enumerate(functions):
        if idx + 1 < len(functions):
            func['end_line'] = functions[idx + 1]['start_line'] - 1
        else:
            func['end_line'] = len(lines)
        func['line_count'] = func['end_line'] - func['start_line'] + 1

    return functions


def estimate_cyclomatic_complexity(lines):
    """估算圈复杂度（简化版：计算分支关键词）"""
    complexity = 1  # 基础路径
    branch_keywords = ['if', 'elif', 'else if', 'case', 'for', 'while',
                       'catch', 'except', '&&', '||', '?']
    for line in lines:
        stripped = line.strip()
        for kw in branch_keywords:
            if kw in stripped:
                complexity += stripped.count(kw) if kw in ('&&', '||') else 1
                break
    return complexity


def find_duplicates(lines, min_length=3):
    """检测重复代码块（简化版）"""
    blocks = {}
    duplicates = []
    for i in range(len(lines) - min_length + 1):
        block = tuple(line.strip() for line in lines[i:i + min_length])
        if all(b for b in block):  # 忽略空行
            key = block
            if key in blocks:
                duplicates.append({
                    'lines': f'{blocks[key] + 1}-{blocks[key] + min_length}',
                    'duplicate_at': f'{i + 1}-{i + min_length}',
                    'content_preview': block[0][:60]
                })
            else:
                blocks[key] = i
    return duplicates[:5]  # 最多返回 5 个


def main():
    if len(sys.argv) < 2:
        print("用法: python analyze_complexity.py <file-path>", file=sys.stderr)
        sys.exit(1)

    filepath = Path(sys.argv[1])
    if not filepath.exists():
        print(f"Error: 文件不存在: {filepath}", file=sys.stderr)
        sys.exit(1)

    print(f"正在分析: {filepath}", file=sys.stderr)

    content = filepath.read_text(encoding='utf-8', errors='replace')
    lines = content.splitlines()
    ext = filepath.suffix

    # 文件级分析
    total_lines = len(lines)
    max_depth = count_indentation_depth(lines)
    duplicates = find_duplicates(lines)

    # 函数级分析
    functions = detect_functions(lines, ext)
    func_results = []
    for func in functions:
        func_lines = lines[func['start_line'] - 1:func['end_line']]
        cc = estimate_cyclomatic_complexity(func_lines)
        depth = count_indentation_depth(func_lines)
        status = '🟢' if cc <= 5 else ('🟡' if cc <= 10 else '🔴')
        func_results.append({
            'name': func['name'],
            'start_line': func['start_line'],
            'end_line': func['end_line'],
            'line_count': func['line_count'],
            'cyclomatic_complexity': cc,
            'max_nesting_depth': depth,
            'status': status
        })

    result = {
        'file': str(filepath),
        'total_lines': total_lines,
        'max_nesting_depth': max_depth,
        'functions': func_results,
        'duplicates': duplicates,
        'summary': {
            'total_functions': len(func_results),
            'high_complexity': len([f for f in func_results if f['cyclomatic_complexity'] > 10]),
            'medium_complexity': len([f for f in func_results if 5 < f['cyclomatic_complexity'] <= 10]),
            'low_complexity': len([f for f in func_results if f['cyclomatic_complexity'] <= 5])
        }
    }

    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    print(f"\n分析完成: {len(func_results)} 个函数", file=sys.stderr)


if __name__ == '__main__':
    main()
