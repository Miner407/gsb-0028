# JSON 配置差异对比工具

## 工具用途

JSON 配置差异对比工具用于对两个 JSON 配置文件进行结构化对比，自动识别新增项、删除项、修改项和类型变化，输出格式化的控制台报告，并支持导出 HTML 可视化报告和 Markdown 报告。适用于配置版本变更审查、环境差异核对、CI/CD 流水线配置校验等场景。

## 运行环境

- **Python 版本**: Python 3.7 及以上
- **依赖库**: 无第三方依赖，仅使用 Python 标准库
- **操作系统**: Windows / macOS / Linux 全平台兼容

## 目录结构

```
gsb-0028/
├── json_diff/                  # 核心包
│   ├── __init__.py            # 包入口
│   ├── comparator.py          # 对比核心逻辑
│   └── report.py              # 报告生成模块
├── json_diff_cli.py           # CLI 入口脚本
├── test_json_diff.py          # 自动化测试脚本
├── examples/                  # 示例配置文件
│   ├── basic/                 # 基础对比示例
│   ├── arrays/                # 数组变化示例
│   ├── ignore_rules/          # 忽略规则示例
│   └── type_changes/          # 类型变化示例
├── README.md                  # 本文档
└── 题目.md                     # 原始需求说明
```

## 基础对比命令

### 最基础用法

```bash
python json_diff_cli.py 旧文件.json 新文件.json
```

### 示例

```bash
python json_diff_cli.py examples/basic/config_v1.json examples/basic/config_v2.json
```

控制台将输出：
- 对比的文件路径
- 统计摘要（新增、删除、修改、类型变化、总计）
- 各类型差异的详细路径和值

## 忽略路径用法

### 通过 -i / --ignore 指定忽略模式

支持通配符 `*`，可多次指定：

```bash
# 忽略 secrets 下的所有字段
python json_diff_cli.py old.json new.json -i "secrets.*"

# 忽略所有 password 字段
python json_diff_cli.py old.json new.json -i "*.password"

# 忽略特定路径
python json_diff_cli.py old.json new.json -i "database.username"

# 组合多个忽略规则
python json_diff_cli.py old.json new.json \
    -i "secrets.*" \
    -i "*.password" \
    -i "metadata.timestamp"
```

### 匹配规则说明

- 使用 `fnmatch` 通配符匹配
- `*` 匹配任意字符（不含路径分隔符 `.`）
- `secrets.*` 匹配 `secrets.api_key`、`secrets.token` 等
- `*.password` 匹配 `database.password`、`user.password` 等
- 完整路径也可直接指定

## 排序开关

### 默认行为（排序输出）

默认按路径字母序排序，便于定位：

```bash
python json_diff_cli.py old.json new.json
```

### 关闭排序（--no-sort）

按 JSON 中出现的原始顺序输出：

```bash
python json_diff_cli.py old.json new.json --no-sort
```

## HTML 报告导出

使用 `--html` 参数导出可视化 HTML 报告：

```bash
python json_diff_cli.py old.json new.json --html diff_report.html
```

报告包含：
- 彩色统计卡片
- 详细差异表格
- 类型徽章标识
- 响应式布局，支持浏览器查看

## Markdown 报告导出

使用 `--markdown`（或 `--md`）参数导出 Markdown 报告：

```bash
python json_diff_cli.py old.json new.json --markdown diff_report.md
```

适用于：
- 贴入 Issue / PR 评论
- 归档到文档库
- 邮件发送

## Summary JSON 导出

使用 `--summary-json` 参数将差异统计导出为 JSON 文件：

```bash
python json_diff_cli.py old.json new.json --summary-json summary.json
```

导出的 JSON 结构示例：

```json
{
  "added_count": 5,
  "removed_count": 3,
  "modified_count": 4,
  "type_changed_count": 2,
  "total_changes": 14,
  "has_changes": true,
  "old_file": "path/to/old.json",
  "new_file": "path/to/new.json",
  "ignore_rules": ["secrets.*", "*.password"]
}
```

字段说明：

| 字段 | 类型 | 说明 |
|------|------|------|
| `added_count` | number | 新增项数量 |
| `removed_count` | number | 删除项数量 |
| `modified_count` | number | 修改项数量 |
| `type_changed_count` | number | 类型变化数量 |
| `total_changes` | number | 总变化数 |
| `has_changes` | boolean | 是否存在差异 |
| `old_file` | string | 旧文件路径 |
| `new_file` | string | 新文件路径 |
| `ignore_rules` | array | 忽略规则列表 |

## 返回码控制（--fail-on）

使用 `--fail-on` 指定哪些变化类型会导致命令返回非零值。支持以逗号分隔的类型列表。

### 可用类型

| 类型 | 说明 |
|------|------|
| `added` | 新增项 |
| `removed` | 删除项 |
| `modified` | 修改项 |
| `type_changed` | 类型变化 |

### 用法示例

```bash
# 只有新增或删除时才返回非零（修改和类型变化不计）
python json_diff_cli.py old.json new.json --fail-on added,removed

# 只有类型变化时返回非零
python json_diff_cli.py old.json new.json --fail-on type_changed

# 新增、删除、类型变化都算失败，修改不算
python json_diff_cli.py old.json new.json --fail-on added,removed,type_changed
```

### 在 CI 中的典型用法

```bash
# 配置必须完全一致（任何差异都失败），等价于默认行为
python json_diff_cli.py prod.json staging.json

# 允许修改值，但不允许新增或删除字段
python json_diff_cli.py prod.json staging.json --fail-on added,removed

# 只关心类型不被破坏（比如 string 改成 number）
python json_diff_cli.py prod.json staging.json --fail-on type_changed
```

## 返回码含义

| 返回码 | 含义 |
|--------|------|
| `0` | 两个文件无差异（或指定的 `--fail-on` 类型均未触发） |
| `1` | 存在差异（默认：任意差异；指定 `--fail-on` 时：仅命中类型） |
| `2` | JSON 解析失败（文件格式错误） |
| `3` | 其他运行时错误（文件不存在、权限不足等） |

## 静默模式（--quiet / -q）

不在控制台打印报告，仅导出文件或通过返回码判断：

```bash
python json_diff_cli.py old.json new.json \
    --html report.html \
    --markdown report.md \
    --summary-json summary.json \
    --quiet
```

## 数组对比说明

### 路径格式

数组路径采用**索引格式**，下标从 0 开始：

| 路径示例 | 说明 |
|----------|------|
| `tags[0]` | tags 数组第 1 个元素 |
| `servers[2].host` | servers 数组第 3 个元素的 host 字段 |
| `config.ports[1]` | config.ports 数组第 2 个元素 |

### 对比策略

- **按索引对比**：`old[0]` vs `new[0]`、`old[1]` vs `new[1]`，以此类推
- **不做对象智能匹配**：不根据对象的 id/name 等字段重排匹配
- **长度差异**：多出的元素标记为新增，少出的元素标记为删除
- **嵌套数组**：索引格式逐层嵌套，如 `matrix[0][2]`

### 报告中的展示

HTML 和 Markdown 报告顶部均包含数组对比策略说明，提示阅读者注意索引语义。

## 示例配置说明

项目 `examples/` 目录下提供四组示例配置：

### 1. basic - 基础对比

```
examples/basic/config_v1.json  →  旧版本
examples/basic/config_v2.json  →  新版本
```

包含：字段新增、字段删除、值修改、嵌套对象变化。

### 2. arrays - 数组变化

```
examples/arrays/config_v1.json
examples/arrays/config_v2.json
```

包含：数组元素新增、数组元素删除、数组内对象字段修改。

### 3. ignore_rules - 忽略规则

```
examples/ignore_rules/config_old.json
examples/ignore_rules/config_new.json
```

包含：secrets 字段、password 字段、数据库用户名等适合忽略的场景。

### 4. type_changes - 类型变化

```
examples/type_changes/config_v1.json
examples/type_changes/config_v2.json
```

包含：string ↔ number、null ↔ object、array ↔ object 等各种类型转换场景，以及深层嵌套对象。

## 测试命令

### 运行完整测试套件

```bash
python test_json_diff.py
```

测试覆盖内容：

| 编号 | 测试项 | 覆盖内容 |
|------|--------|----------|
| 1 | 基本对比 | 新增、删除、修改检测 |
| 2 | 忽略规则 | -i 参数匹配逻辑 |
| 3 | 数组变化 | 索引格式、增删改检测 |
| 4 | 类型变化 | 各类型转换识别 |
| 5 | 深层嵌套 | 多层对象、数组类型变化 |
| 6 | 路径排序 | sort_paths 开关 |
| 7 | HTML 报告 | 生成、内容校验 |
| 8 | Markdown 报告 | 生成、内容校验 |
| 9 | CLI 基本功能 | 返回码、输出内容 |
| 10 | CLI 报告导出 | --html / --markdown 参数 |
| 11 | CLI 忽略参数 | -i 参数组合 |
| 12 | 无差异场景 | 相同文件对比、返回码 0 |
| 13 | .gitignore 检查 | 忽略规则完整性 |
| 14 | README 关键内容 | 文档完整性 |
| 15 | --summary-json 导出 | 统计 JSON 结构 |
| 16 | --fail-on 返回码 | 返回码控制逻辑 |
| 17 | 数组路径展示 | 报告中索引格式说明 |

### 仅编译检查

```bash
python -m py_compile json_diff_cli.py json_diff/__init__.py json_diff/comparator.py json_diff/report.py test_json_diff.py
```

## 作为库使用

除了 CLI，也可以作为 Python 库导入：

```python
from json_diff import JsonComparator, HtmlReport, MarkdownReport

comparator = JsonComparator(
    ignore_paths=["secrets.*"],
    sort_paths=True
)
result = comparator.compare_files("old.json", "new.json")

print(f"新增: {len(result.added)}")
print(f"删除: {len(result.removed)}")
print(f"修改: {len(result.modified)}")
print(f"类型变化: {len(result.type_changed)}")
print(f"总计: {result.total_changes}")

# 导出报告
HtmlReport(result, "old.json", "new.json").save("report.html")
MarkdownReport(result, "old.json", "new.json").save("report.md")
```

## 已知限制

1. **数组按索引对比**：不支持基于对象关键字段（如 id、name）的智能匹配，数组中间插入元素会导致后续所有元素被标记为修改。如需要 LCS 或键匹配，请自行扩展 `_compare_arrays` 方法。

2. **浮点精度**：直接使用 Python `!=` 比较，`1.0` 与 `1.0000001` 会被视为修改。若需要精度阈值，可在 `_compare_value` 中为 float 类型增加容差判断。

3. **顺序敏感**：对象键顺序不影响对比结果（集合比较），但数组元素顺序影响（索引比较）。

4. **通配符限制**：`*` 不跨路径层级匹配，即 `a.*.c` 无法匹配 `a.b.c`，只能匹配一级子键。若需要多级通配请改用 `**` 或正则匹配。

5. **不支持 JSON5 / JSONC**：仅支持标准 JSON，带注释或尾随逗号的文件会解析失败（返回码 2）。

6. **大文件性能**：深度递归遍历，极深层嵌套或极大数组可能触发递归深度限制。可考虑将 `_compare_value` 改为迭代式实现。

## License

内部工具，供项目交付使用。
