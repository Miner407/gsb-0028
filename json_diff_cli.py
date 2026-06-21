"""JSON 配置差异对比 CLI 工具"""

import argparse
import sys
import json
import os

from json_diff.comparator import JsonComparator, DiffResult
from json_diff.report import HtmlReport, MarkdownReport


def format_value(value) -> str:
    if value is None:
        return 'null'
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, str):
        return f'"{value}"'
    return str(value)


def print_console_report(result: DiffResult, file1: str, file2: str):
    print('=' * 60)
    print('  JSON 配置差异对比报告')
    print('=' * 60)
    print()

    if file1 or file2:
        print('对比文件:')
        if file1:
            print(f'  旧配置: {file1}')
        if file2:
            print(f'  新配置: {file2}')
        print()

    print('统计摘要:')
    print(f'  新增: {len(result.added)} 项')
    print(f'  删除: {len(result.removed)} 项')
    print(f'  修改: {len(result.modified)} 项')
    print(f'  类型变化: {len(result.type_changed)} 项')
    print(f'  总计: {result.total_changes} 项变化')
    print()

    if result.added:
        print('-' * 60)
        print('新增项:')
        print('-' * 60)
        for item in result.added:
            val = format_value(item.new_value)
            print(f'  + {item.path}')
            print(f'    值: {val} [{item.new_type}]')
        print()

    if result.removed:
        print('-' * 60)
        print('删除项:')
        print('-' * 60)
        for item in result.removed:
            val = format_value(item.old_value)
            print(f'  - {item.path}')
            print(f'    值: {val} [{item.old_type}]')
        print()

    if result.modified:
        print('-' * 60)
        print('修改项:')
        print('-' * 60)
        for item in result.modified:
            old_val = format_value(item.old_value)
            new_val = format_value(item.new_value)
            print(f'  ~ {item.path}')
            print(f'    旧值: {old_val}')
            print(f'    新值: {new_val}')
        print()

    if result.type_changed:
        print('-' * 60)
        print('类型变化:')
        print('-' * 60)
        for item in result.type_changed:
            old_val = format_value(item.old_value)
            new_val = format_value(item.new_value)
            print(f'  T {item.path}')
            print(f'    旧: {item.old_type} = {old_val}')
            print(f'    新: {item.new_type} = {new_val}')
        print()

    if not result.has_changes:
        print('✅ 两个配置文件完全相同，没有差异。')
        print()


def main():
    parser = argparse.ArgumentParser(
        description='JSON 配置差异对比工具 - 对比两个 JSON 文件的差异'
    )

    parser.add_argument('file1', help='旧版本 JSON 文件路径')
    parser.add_argument('file2', help='新版本 JSON 文件路径')

    parser.add_argument(
        '--ignore', '-i',
        action='append',
        default=[],
        help='忽略的路径模式 (支持通配符 *)，可多次指定'
    )

    parser.add_argument(
        '--no-sort',
        action='store_true',
        help='不按路径排序输出'
    )

    parser.add_argument(
        '--html',
        metavar='OUTPUT',
        help='导出 HTML 报告到指定文件'
    )

    parser.add_argument(
        '--markdown', '--md',
        metavar='OUTPUT',
        help='导出 Markdown 报告到指定文件'
    )

    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='静默模式，不在控制台输出'
    )

    parser.add_argument(
        '--summary-json',
        metavar='OUTPUT',
        help='将差异统计导出为 JSON 文件'
    )

    parser.add_argument(
        '--fail-on',
        metavar='TYPES',
        default='',
        help='指定触发非零返回码的变化类型，逗号分隔: added,removed,modified,type_changed。未指定时任意差异均返回 1'
    )

    args = parser.parse_args()

    valid_fail_types = {'added', 'removed', 'modified', 'type_changed'}
    fail_on_types = set()
    if args.fail_on:
        for t in args.fail_on.split(','):
            t = t.strip()
            if t:
                if t not in valid_fail_types:
                    print(f'错误: --fail-on 无效类型 "{t}"，有效值: {",".join(sorted(valid_fail_types))}', file=sys.stderr)
                    sys.exit(3)
                fail_on_types.add(t)

    if not os.path.exists(args.file1):
        print(f'错误: 文件不存在 - {args.file1}', file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(args.file2):
        print(f'错误: 文件不存在 - {args.file2}', file=sys.stderr)
        sys.exit(1)

    try:
        comparator = JsonComparator(
            ignore_paths=args.ignore,
            sort_paths=not args.no_sort
        )
        result = comparator.compare_files(args.file1, args.file2)

        if not args.quiet:
            print_console_report(result, args.file1, args.file2)

        if args.html:
            report = HtmlReport(result, args.file1, args.file2)
            report.save(args.html)
            if not args.quiet:
                print(f'HTML 报告已保存到: {args.html}')

        if args.markdown:
            report = MarkdownReport(result, args.file1, args.file2)
            report.save(args.markdown)
            if not args.quiet:
                print(f'Markdown 报告已保存到: {args.markdown}')

        if args.summary_json:
            summary_data = {
                'added_count': len(result.added),
                'removed_count': len(result.removed),
                'modified_count': len(result.modified),
                'type_changed_count': len(result.type_changed),
                'total_changes': result.total_changes,
                'has_changes': result.has_changes,
                'old_file': args.file1,
                'new_file': args.file2,
                'ignore_rules': args.ignore
            }
            with open(args.summary_json, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, ensure_ascii=False, indent=2)
            if not args.quiet:
                print(f'Summary JSON 已保存到: {args.summary_json}')

        if fail_on_types:
            should_fail = False
            if 'added' in fail_on_types and result.added:
                should_fail = True
            if 'removed' in fail_on_types and result.removed:
                should_fail = True
            if 'modified' in fail_on_types and result.modified:
                should_fail = True
            if 'type_changed' in fail_on_types and result.type_changed:
                should_fail = True
            sys.exit(0 if not should_fail else 1)
        else:
            sys.exit(0 if not result.has_changes else 1)

    except json.JSONDecodeError as e:
        print(f'错误: JSON 解析失败 - {e}', file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f'错误: {e}', file=sys.stderr)
        sys.exit(3)


if __name__ == '__main__':
    main()
