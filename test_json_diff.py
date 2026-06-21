"""JSON 差异对比工具测试脚本"""

import json
import os
import sys
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from json_diff.comparator import JsonComparator, DiffResult
from json_diff.report import HtmlReport, MarkdownReport


EXAMPLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'examples')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_output')

os.makedirs(OUTPUT_DIR, exist_ok=True)


def test_basic_comparison():
    """测试 1: 基本对比功能"""
    print('=' * 60)
    print('测试 1: 基本对比功能')
    print('=' * 60)

    file1 = os.path.join(EXAMPLES_DIR, 'basic', 'config_v1.json')
    file2 = os.path.join(EXAMPLES_DIR, 'basic', 'config_v2.json')

    comparator = JsonComparator()
    result = comparator.compare_files(file1, file2)

    print(f'新增: {len(result.added)} 项')
    print(f'删除: {len(result.removed)} 项')
    print(f'修改: {len(result.modified)} 项')
    print(f'类型变化: {len(result.type_changed)} 项')
    print(f'总计: {result.total_changes} 项变化')
    print()

    added_paths = [item.path for item in result.added]
    modified_paths = [item.path for item in result.modified]

    assert 'api_key' in added_paths, '应该检测到新增的 api_key'
    assert 'database.database' in added_paths, '应该检测到新增的 database.database'
    assert 'version' in modified_paths, '应该检测到修改的 version'
    assert 'debug' in modified_paths, '应该检测到修改的 debug'
    assert 'database.host' in modified_paths, '应该检测到修改的 database.host'

    print('[OK] 基本对比测试通过')
    print()
    return True


def test_ignore_rules():
    """测试 2: 忽略路径规则"""
    print('=' * 60)
    print('测试 2: 忽略路径规则')
    print('=' * 60)

    file1 = os.path.join(EXAMPLES_DIR, 'ignore_rules', 'config_old.json')
    file2 = os.path.join(EXAMPLES_DIR, 'ignore_rules', 'config_new.json')

    comparator_no_ignore = JsonComparator()
    result_no_ignore = comparator_no_ignore.compare_files(file1, file2)
    print(f'不忽略时总变化数: {result_no_ignore.total_changes}')

    ignore_patterns = ['secrets.*', '*.password', 'database.username']
    comparator_with_ignore = JsonComparator(ignore_paths=ignore_patterns)
    result_with_ignore = comparator_with_ignore.compare_files(file1, file2)
    print(f'忽略后总变化数: {result_with_ignore.total_changes}')
    print()

    all_paths = [item.path for item in result_with_ignore.all_items()]
    for path in all_paths:
        assert 'secrets.' not in path, f'不应该包含 secrets 路径: {path}'
        assert not path.endswith('.password'), f'不应该包含 password 路径: {path}'
        assert path != 'database.username', f'不应该包含 database.username'

    assert result_with_ignore.total_changes < result_no_ignore.total_changes, \
        '忽略后变化数应该减少'

    print('[OK] 忽略规则测试通过')
    print()
    return True


def test_array_changes():
    """测试 3: 数组变化处理"""
    print('=' * 60)
    print('测试 3: 数组变化处理')
    print('=' * 60)

    file1 = os.path.join(EXAMPLES_DIR, 'arrays', 'config_v1.json')
    file2 = os.path.join(EXAMPLES_DIR, 'arrays', 'config_v2.json')

    comparator = JsonComparator()
    result = comparator.compare_files(file1, file2)

    print(f'新增: {len(result.added)} 项')
    print(f'删除: {len(result.removed)} 项')
    print(f'修改: {len(result.modified)} 项')
    print(f'类型变化: {len(result.type_changed)} 项')
    print()

    added_paths = [item.path for item in result.added]
    removed_paths = [item.path for item in result.removed]
    modified_paths = [item.path for item in result.modified]

    assert 'tags[3]' in added_paths, '应该检测到 tags 数组新增元素'
    assert 'servers[3]' in added_paths, '应该检测到 servers 数组新增元素'
    assert 'ports[2]' in removed_paths, '应该检测到 ports 数组删除元素'
    assert 'servers[1].status' in modified_paths, '应该检测到服务器状态修改'

    print('[OK] 数组变化测试通过')
    print()
    return True


def test_type_changes():
    """测试 4: 类型变化和空值处理"""
    print('=' * 60)
    print('测试 4: 类型变化和空值处理')
    print('=' * 60)

    file1 = os.path.join(EXAMPLES_DIR, 'type_changes', 'config_v1.json')
    file2 = os.path.join(EXAMPLES_DIR, 'type_changes', 'config_v2.json')

    comparator = JsonComparator()
    result = comparator.compare_files(file1, file2)

    print(f'新增: {len(result.added)} 项')
    print(f'删除: {len(result.removed)} 项')
    print(f'修改: {len(result.modified)} 项')
    print(f'类型变化: {len(result.type_changed)} 项')
    print()

    type_changed_paths = [item.path for item in result.type_changed]

    assert 'string_field' in type_changed_paths, '应该检测到 string_field 类型变化'
    assert 'number_field' in type_changed_paths, '应该检测到 number_field 类型变化'
    assert 'null_field' in type_changed_paths, '应该检测到 null_field 类型变化'
    assert 'array_field' in type_changed_paths, '应该检测到 array_field 类型变化'
    assert 'object_field' in type_changed_paths, '应该检测到 object_field 类型变化'

    print('[OK] 类型变化测试通过')
    print()
    return True


def test_nested_objects():
    """测试 5: 深层嵌套对象"""
    print('=' * 60)
    print('测试 5: 深层嵌套对象')
    print('=' * 60)

    file1 = os.path.join(EXAMPLES_DIR, 'type_changes', 'config_v1.json')
    file2 = os.path.join(EXAMPLES_DIR, 'type_changes', 'config_v2.json')

    comparator = JsonComparator()
    result = comparator.compare_files(file1, file2)

    type_changed_paths = [item.path for item in result.type_changed]
    modified_paths = [item.path for item in result.modified]

    assert 'mixed.value' in type_changed_paths, '应该检测到深层嵌套类型变化'
    assert 'deep.level1.level2.value' in type_changed_paths, '应该检测到深层嵌套值类型变化'
    assert 'deep.level1.level2.items' in type_changed_paths, '应该检测到深层数组转对象'

    print(f'检测到的类型变化路径:')
    for path in type_changed_paths:
        print(f'  - {path}')
    print()

    print('[OK] 深层嵌套测试通过')
    print()
    return True


def test_sort_paths():
    """测试 6: 路径排序功能"""
    print('=' * 60)
    print('测试 6: 路径排序功能')
    print('=' * 60)

    file1 = os.path.join(EXAMPLES_DIR, 'basic', 'config_v1.json')
    file2 = os.path.join(EXAMPLES_DIR, 'basic', 'config_v2.json')

    comparator_sorted = JsonComparator(sort_paths=True)
    result_sorted = comparator_sorted.compare_files(file1, file2)

    comparator_unsorted = JsonComparator(sort_paths=False)
    result_unsorted = comparator_unsorted.compare_files(file1, file2)

    added_paths_sorted = [item.path for item in result_sorted.added]
    assert added_paths_sorted == sorted(added_paths_sorted), '排序后的路径应该有序'

    print(f'排序后的新增路径: {added_paths_sorted}')
    print()
    print('[OK] 路径排序测试通过')
    print()
    return True


def test_html_report():
    """测试 7: HTML 报告导出"""
    print('=' * 60)
    print('测试 7: HTML 报告导出')
    print('=' * 60)

    file1 = os.path.join(EXAMPLES_DIR, 'basic', 'config_v1.json')
    file2 = os.path.join(EXAMPLES_DIR, 'basic', 'config_v2.json')

    comparator = JsonComparator()
    result = comparator.compare_files(file1, file2)

    report = HtmlReport(result, file1, file2)
    output_path = os.path.join(OUTPUT_DIR, 'basic_diff_report.html')
    report.save(output_path)

    assert os.path.exists(output_path), 'HTML 报告文件应该存在'
    assert os.path.getsize(output_path) > 0, 'HTML 报告文件不应该为空'

    with open(output_path, 'r', encoding='utf-8') as f:
        content = f.read()

    assert '<html' in content, '应该包含 HTML 标签'
    assert '</html>' in content, '应该包含闭合 HTML 标签'
    assert 'JSON 配置差异对比报告' in content, '应该包含报告标题'

    print(f'HTML 报告已生成: {output_path}')
    print(f'文件大小: {os.path.getsize(output_path)} bytes')
    print()
    print('[OK] HTML 报告测试通过')
    print()
    return True


def test_markdown_report():
    """测试 8: Markdown 报告导出"""
    print('=' * 60)
    print('测试 8: Markdown 报告导出')
    print('=' * 60)

    file1 = os.path.join(EXAMPLES_DIR, 'basic', 'config_v1.json')
    file2 = os.path.join(EXAMPLES_DIR, 'basic', 'config_v2.json')

    comparator = JsonComparator()
    result = comparator.compare_files(file1, file2)

    report = MarkdownReport(result, file1, file2)
    output_path = os.path.join(OUTPUT_DIR, 'basic_diff_report.md')
    report.save(output_path)

    assert os.path.exists(output_path), 'Markdown 报告文件应该存在'
    assert os.path.getsize(output_path) > 0, 'Markdown 报告文件不应该为空'

    with open(output_path, 'r', encoding='utf-8') as f:
        content = f.read()

    assert '# JSON 配置差异对比报告' in content, '应该包含报告标题'
    assert '## 统计摘要' in content, '应该包含统计摘要'

    print(f'Markdown 报告已生成: {output_path}')
    print(f'文件大小: {os.path.getsize(output_path)} bytes')
    print()
    print('[OK] Markdown 报告测试通过')
    print()
    return True


def test_cli_basic():
    """测试 9: CLI 基本功能"""
    print('=' * 60)
    print('测试 9: CLI 基本功能')
    print('=' * 60)

    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'json_diff_cli.py')
    file1 = os.path.join(EXAMPLES_DIR, 'basic', 'config_v1.json')
    file2 = os.path.join(EXAMPLES_DIR, 'basic', 'config_v2.json')

    result = subprocess.run(
        [sys.executable, script_path, file1, file2],
        capture_output=True
    )

    stdout = result.stdout.decode(sys.stdout.encoding or 'utf-8', errors='replace')

    print(f'返回码: {result.returncode}')
    print(f'输出行数: {len(stdout.splitlines())}')

    assert 'JSON' in stdout and '差异' in stdout, 'CLI 输出应该包含报告标题'
    assert result.returncode == 1, '有差异时应该返回 1'

    print()
    print('[OK] CLI 基本功能测试通过')
    print()
    return True


def test_cli_reports():
    """测试 10: CLI 报告导出功能"""
    print('=' * 60)
    print('测试 10: CLI 报告导出功能')
    print('=' * 60)

    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'json_diff_cli.py')
    file1 = os.path.join(EXAMPLES_DIR, 'arrays', 'config_v1.json')
    file2 = os.path.join(EXAMPLES_DIR, 'arrays', 'config_v2.json')
    html_output = os.path.join(OUTPUT_DIR, 'cli_array_report.html')
    md_output = os.path.join(OUTPUT_DIR, 'cli_array_report.md')

    result = subprocess.run(
        [sys.executable, script_path, file1, file2,
         '--html', html_output,
         '--markdown', md_output,
         '--quiet'],
        capture_output=True,
        text=True,
        encoding='utf-8'
    )

    assert result.returncode == 1, '有差异时应该返回 1'
    assert os.path.exists(html_output), 'HTML 报告文件应该存在'
    assert os.path.exists(md_output), 'Markdown 报告文件应该存在'

    print(f'HTML 报告: {html_output}')
    print(f'Markdown 报告: {md_output}')
    print()
    print('[OK] CLI 报告导出测试通过')
    print()
    return True


def test_cli_ignore():
    """测试 11: CLI 忽略参数"""
    print('=' * 60)
    print('测试 11: CLI 忽略参数')
    print('=' * 60)

    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'json_diff_cli.py')
    file1 = os.path.join(EXAMPLES_DIR, 'ignore_rules', 'config_old.json')
    file2 = os.path.join(EXAMPLES_DIR, 'ignore_rules', 'config_new.json')

    result_full = subprocess.run(
        [sys.executable, script_path, file1, file2, '--quiet'],
        capture_output=True,
        text=True,
        encoding='utf-8'
    )

    result_ignored = subprocess.run(
        [sys.executable, script_path, file1, file2,
         '-i', 'secrets.*',
         '-i', '*.password',
         '--quiet'],
        capture_output=True,
        text=True,
        encoding='utf-8'
    )

    result_full_count = result_full.stdout.count('\n') if result_full.stdout else 0
    result_ignored_count = result_ignored.stdout.count('\n') if result_ignored.stdout else 0

    print(f'完整对比返回码: {result_full.returncode}')
    print(f'忽略后对比返回码: {result_ignored.returncode}')

    assert result_full.returncode == 1, '有差异时应该返回 1'
    assert result_ignored.returncode == 1, '有差异时应该返回 1'

    print()
    print('[OK] CLI 忽略参数测试通过')
    print()
    return True


def test_no_changes():
    """测试 12: 无差异场景"""
    print('=' * 60)
    print('测试 12: 无差异场景')
    print('=' * 60)

    file1 = os.path.join(EXAMPLES_DIR, 'basic', 'config_v1.json')

    comparator = JsonComparator()
    result = comparator.compare_files(file1, file1)

    assert not result.has_changes, '相同文件应该没有差异'
    assert result.total_changes == 0, '差异数应该为 0'

    report = HtmlReport(result, file1, file1)
    html_content = report.generate()
    assert '完全相同' in html_content, '报告应该显示完全相同'

    print('[OK] 无差异场景测试通过')
    print()
    return True


def main():
    """运行所有测试"""
    print()
    print('开始运行 JSON 差异对比工具测试')
    print()

    tests = [
        ('基本对比', test_basic_comparison),
        ('忽略规则', test_ignore_rules),
        ('数组变化', test_array_changes),
        ('类型变化', test_type_changes),
        ('深层嵌套', test_nested_objects),
        ('路径排序', test_sort_paths),
        ('HTML 报告', test_html_report),
        ('Markdown 报告', test_markdown_report),
        ('CLI 基本功能', test_cli_basic),
        ('CLI 报告导出', test_cli_reports),
        ('CLI 忽略参数', test_cli_ignore),
        ('无差异场景', test_no_changes),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f'[FAIL] 测试失败: {name}')
            print(f'   错误: {e}')
            import traceback
            traceback.print_exc()
            failed += 1
            print()

    print('=' * 60)
    print('测试结果汇总')
    print('=' * 60)
    print(f'总测试数: {len(tests)}')
    print(f'通过: {passed}')
    print(f'失败: {failed}')
    print()

    if failed == 0:
        print('[PASS] 所有测试通过！')
    else:
        print(f'[WARN]  有 {failed} 个测试失败')

    print()

    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
