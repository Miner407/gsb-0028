"""报告导出模块"""

import json
from .comparator import DiffResult, DiffItem


class BaseReport:
    """报告基类"""

    def __init__(self, result: DiffResult, file1: str = '', file2: str = ''):
        self.result = result
        self.file1 = file1
        self.file2 = file2

    @staticmethod
    def _format_value(value) -> str:
        if value is None:
            return 'null'
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False, indent=2)
        if isinstance(value, bool):
            return 'true' if value else 'false'
        if isinstance(value, str):
            return f'"{value}"'
        return str(value)


class MarkdownReport(BaseReport):
    """Markdown 报告生成器"""

    def generate(self) -> str:
        lines = []
        lines.append('# JSON 配置差异对比报告')
        lines.append('')

        if self.file1 or self.file2:
            lines.append('## 对比文件')
            lines.append('')
            if self.file1:
                lines.append(f'- **旧配置**: `{self.file1}`')
            if self.file2:
                lines.append(f'- **新配置**: `{self.file2}`')
            lines.append('')

        lines.append('## 统计摘要')
        lines.append('')
        lines.append(f'- 新增: **{len(self.result.added)}** 项')
        lines.append(f'- 删除: **{len(self.result.removed)}** 项')
        lines.append(f'- 修改: **{len(self.result.modified)}** 项')
        lines.append(f'- 类型变化: **{len(self.result.type_changed)}** 项')
        lines.append(f'- **总计: {self.result.total_changes} 项变化**')
        lines.append('')

        if self.result.added:
            lines.append('## 新增项')
            lines.append('')
            lines.append('| 路径 | 值 | 类型 |')
            lines.append('|------|-----|------|')
            for item in self.result.added:
                val = self._format_value(item.new_value)
                val = val.replace('\n', '<br>')
                lines.append(f'| `{item.path}` | {val} | {item.new_type} |')
            lines.append('')

        if self.result.removed:
            lines.append('## 删除项')
            lines.append('')
            lines.append('| 路径 | 值 | 类型 |')
            lines.append('|------|-----|------|')
            for item in self.result.removed:
                val = self._format_value(item.old_value)
                val = val.replace('\n', '<br>')
                lines.append(f'| `{item.path}` | {val} | {item.old_type} |')
            lines.append('')

        if self.result.modified:
            lines.append('## 修改项')
            lines.append('')
            lines.append('| 路径 | 旧值 | 新值 |')
            lines.append('|------|------|------|')
            for item in self.result.modified:
                old_val = self._format_value(item.old_value)
                new_val = self._format_value(item.new_value)
                old_val = old_val.replace('\n', '<br>')
                new_val = new_val.replace('\n', '<br>')
                lines.append(f'| `{item.path}` | {old_val} | {new_val} |')
            lines.append('')

        if self.result.type_changed:
            lines.append('## 类型变化')
            lines.append('')
            lines.append('| 路径 | 旧类型 | 新类型 | 旧值 | 新值 |')
            lines.append('|------|--------|--------|------|------|')
            for item in self.result.type_changed:
                old_val = self._format_value(item.old_value)
                new_val = self._format_value(item.new_value)
                old_val = old_val.replace('\n', '<br>')
                new_val = new_val.replace('\n', '<br>')
                lines.append(f'| `{item.path}` | {item.old_type} | {item.new_type} | {old_val} | {new_val} |')
            lines.append('')

        if not self.result.has_changes:
            lines.append('## 结果')
            lines.append('')
            lines.append('✅ 两个配置文件完全相同，没有差异。')
            lines.append('')

        return '\n'.join(lines)

    def save(self, filepath: str):
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.generate())


class HtmlReport(BaseReport):
    """HTML 报告生成器"""

    def generate(self) -> str:
        html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>JSON 配置差异对比报告</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background: #f5f7fa;
    color: #333;
    line-height: 1.6;
    padding: 20px;
}
.container {
    max-width: 1200px;
    margin: 0 auto;
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.1);
    padding: 30px;
}
h1 {
    color: #2c3e50;
    border-bottom: 3px solid #3498db;
    padding-bottom: 10px;
    margin-bottom: 20px;
}
h2 {
    color: #34495e;
    margin-top: 30px;
    margin-bottom: 15px;
    padding-left: 10px;
    border-left: 4px solid #3498db;
}
.summary {
    display: flex;
    gap: 20px;
    margin: 20px 0;
    flex-wrap: wrap;
}
.summary-card {
    flex: 1;
    min-width: 150px;
    padding: 20px;
    border-radius: 8px;
    text-align: center;
    background: #f8f9fa;
}
.summary-card .count {
    font-size: 32px;
    font-weight: bold;
    margin-bottom: 5px;
}
.summary-card .label {
    font-size: 14px;
    color: #666;
}
.summary-card.added { background: #e8f5e9; }
.summary-card.added .count { color: #2e7d32; }
.summary-card.removed { background: #ffebee; }
.summary-card.removed .count { color: #c62828; }
.summary-card.modified { background: #fff3e0; }
.summary-card.modified .count { color: #e65100; }
.summary-card.type-changed { background: #f3e5f5; }
.summary-card.type-changed .count { color: #6a1b9a; }
.summary-card.total { background: #e3f2fd; }
.summary-card.total .count { color: #1565c0; }
.file-info {
    background: #f8f9fa;
    padding: 15px;
    border-radius: 6px;
    margin-bottom: 20px;
}
.file-info p { margin: 5px 0; }
.file-info code {
    background: #e9ecef;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: "Consolas", "Monaco", monospace;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin: 15px 0;
    font-size: 14px;
}
th, td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid #e0e0e0;
    vertical-align: top;
}
th {
    background: #f5f7fa;
    font-weight: 600;
    color: #555;
}
tr:hover { background: #fafafa; }
.path {
    font-family: "Consolas", "Monaco", monospace;
    color: #1976d2;
    font-size: 13px;
}
pre {
    background: #f5f5f5;
    padding: 10px;
    border-radius: 4px;
    overflow-x: auto;
    font-family: "Consolas", "Monaco", monospace;
    font-size: 12px;
    margin: 0;
    white-space: pre-wrap;
    word-break: break-all;
}
.type-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 500;
    background: #e0e0e0;
    color: #555;
}
.type-badge.object { background: #bbdefb; color: #1565c0; }
.type-badge.array { background: #c8e6c9; color: #2e7d32; }
.type-badge.string { background: #fff9c4; color: #f57f17; }
.type-badge.integer, .type-badge.number { background: #d1c4e9; color: #4527a0; }
.type-badge.boolean { background: #ffccbc; color: #bf360c; }
.type-badge.null { background: #e0e0e0; color: #616161; }
.no-changes {
    text-align: center;
    padding: 40px;
    font-size: 18px;
    color: #2e7d32;
}
.section { margin-bottom: 30px; }
</style>
</head>
<body>
<div class="container">
'''

        html += '<h1>JSON 配置差异对比报告</h1>'

        if self.file1 or self.file2:
            html += '<div class="file-info">'
            if self.file1:
                html += f'<p><strong>旧配置:</strong> <code>{self.file1}</code></p>'
            if self.file2:
                html += f'<p><strong>新配置:</strong> <code>{self.file2}</code></p>'
            html += '</div>'

        html += '<div class="summary">'
        html += f'''
<div class="summary-card added">
    <div class="count">{len(self.result.added)}</div>
    <div class="label">新增</div>
</div>
<div class="summary-card removed">
    <div class="count">{len(self.result.removed)}</div>
    <div class="label">删除</div>
</div>
<div class="summary-card modified">
    <div class="count">{len(self.result.modified)}</div>
    <div class="label">修改</div>
</div>
<div class="summary-card type-changed">
    <div class="count">{len(self.result.type_changed)}</div>
    <div class="label">类型变化</div>
</div>
<div class="summary-card total">
    <div class="count">{self.result.total_changes}</div>
    <div class="label">总计</div>
</div>
'''
        html += '</div>'

        if self.result.added:
            html += self._render_added_section()

        if self.result.removed:
            html += self._render_removed_section()

        if self.result.modified:
            html += self._render_modified_section()

        if self.result.type_changed:
            html += self._render_type_changed_section()

        if not self.result.has_changes:
            html += '<div class="no-changes">✅ 两个配置文件完全相同，没有差异。</div>'

        html += '''
</div>
</body>
</html>
'''
        return html

    def _render_added_section(self) -> str:
        html = '<div class="section"><h2>新增项</h2>'
        html += '<table><thead><tr><th>路径</th><th>值</th><th>类型</th></tr></thead><tbody>'
        for item in self.result.added:
            val = self._format_value(item.new_value)
            html += f'''
<tr>
    <td class="path">{item.path}</td>
    <td><pre>{self._escape_html(val)}</pre></td>
    <td><span class="type-badge {item.new_type}">{item.new_type}</span></td>
</tr>'''
        html += '</tbody></table></div>'
        return html

    def _render_removed_section(self) -> str:
        html = '<div class="section"><h2>删除项</h2>'
        html += '<table><thead><tr><th>路径</th><th>值</th><th>类型</th></tr></thead><tbody>'
        for item in self.result.removed:
            val = self._format_value(item.old_value)
            html += f'''
<tr>
    <td class="path">{item.path}</td>
    <td><pre>{self._escape_html(val)}</pre></td>
    <td><span class="type-badge {item.old_type}">{item.old_type}</span></td>
</tr>'''
        html += '</tbody></table></div>'
        return html

    def _render_modified_section(self) -> str:
        html = '<div class="section"><h2>修改项</h2>'
        html += '<table><thead><tr><th>路径</th><th>旧值</th><th>新值</th></tr></thead><tbody>'
        for item in self.result.modified:
            old_val = self._format_value(item.old_value)
            new_val = self._format_value(item.new_value)
            html += f'''
<tr>
    <td class="path">{item.path}</td>
    <td><pre>{self._escape_html(old_val)}</pre></td>
    <td><pre>{self._escape_html(new_val)}</pre></td>
</tr>'''
        html += '</tbody></table></div>'
        return html

    def _render_type_changed_section(self) -> str:
        html = '<div class="section"><h2>类型变化</h2>'
        html += '<table><thead><tr><th>路径</th><th>旧类型</th><th>新类型</th><th>旧值</th><th>新值</th></tr></thead><tbody>'
        for item in self.result.type_changed:
            old_val = self._format_value(item.old_value)
            new_val = self._format_value(item.new_value)
            html += f'''
<tr>
    <td class="path">{item.path}</td>
    <td><span class="type-badge {item.old_type}">{item.old_type}</span></td>
    <td><span class="type-badge {item.new_type}">{item.new_type}</span></td>
    <td><pre>{self._escape_html(old_val)}</pre></td>
    <td><pre>{self._escape_html(new_val)}</pre></td>
</tr>'''
        html += '</tbody></table></div>'
        return html

    @staticmethod
    def _escape_html(text: str) -> str:
        return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;'))

    def save(self, filepath: str):
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.generate())
