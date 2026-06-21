"""JSON 差异对比核心模块"""

import json
import fnmatch
from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class DiffItem:
    """差异项"""
    path: str
    change_type: str
    old_value: Any = None
    new_value: Any = None
    old_type: str = ''
    new_type: str = ''


@dataclass
class DiffResult:
    """对比结果"""
    added: List[DiffItem] = field(default_factory=list)
    removed: List[DiffItem] = field(default_factory=list)
    modified: List[DiffItem] = field(default_factory=list)
    type_changed: List[DiffItem] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.modified or self.type_changed)

    @property
    def total_changes(self) -> int:
        return len(self.added) + len(self.removed) + len(self.modified) + len(self.type_changed)

    def all_items(self) -> List[DiffItem]:
        return self.added + self.removed + self.modified + self.type_changed


class JsonComparator:
    """JSON 配置对比器"""

    def __init__(self, ignore_paths: Optional[List[str]] = None, sort_paths: bool = True):
        self.ignore_patterns = ignore_paths or []
        self.sort_paths = sort_paths

    def _should_ignore(self, path: str) -> bool:
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(path, pattern):
                return True
        return False

    @staticmethod
    def _get_type_name(value: Any) -> str:
        if value is None:
            return 'null'
        if isinstance(value, bool):
            return 'boolean'
        if isinstance(value, int):
            return 'integer'
        if isinstance(value, float):
            return 'number'
        if isinstance(value, str):
            return 'string'
        if isinstance(value, list):
            return 'array'
        if isinstance(value, dict):
            return 'object'
        return type(value).__name__

    @staticmethod
    def _join_path(parent: str, key: str) -> str:
        if parent:
            return f"{parent}.{key}"
        return key

    def compare_files(self, file1: str, file2: str) -> DiffResult:
        with open(file1, 'r', encoding='utf-8') as f:
            data1 = json.load(f)
        with open(file2, 'r', encoding='utf-8') as f:
            data2 = json.load(f)
        return self.compare(data1, data2)

    def compare(self, data1: Any, data2: Any) -> DiffResult:
        result = DiffResult()
        self._compare_value(data1, data2, '', result)
        if self.sort_paths:
            result.added.sort(key=lambda x: x.path)
            result.removed.sort(key=lambda x: x.path)
            result.modified.sort(key=lambda x: x.path)
            result.type_changed.sort(key=lambda x: x.path)
        return result

    def _compare_value(self, old_val: Any, new_val: Any, path: str, result: DiffResult):
        if path and self._should_ignore(path):
            return

        old_type = self._get_type_name(old_val)
        new_type = self._get_type_name(new_val)

        if old_type != new_type:
            result.type_changed.append(DiffItem(
                path=path if path else '<root>',
                change_type='type_changed',
                old_value=old_val,
                new_value=new_val,
                old_type=old_type,
                new_type=new_type
            ))
            return

        if old_type == 'object':
            self._compare_objects(old_val, new_val, path, result)
        elif old_type == 'array':
            self._compare_arrays(old_val, new_val, path, result)
        else:
            if old_val != new_val:
                result.modified.append(DiffItem(
                    path=path if path else '<root>',
                    change_type='modified',
                    old_value=old_val,
                    new_value=new_val,
                    old_type=old_type,
                    new_type=new_type
                ))

    def _compare_objects(self, old_obj: dict, new_obj: dict, path: str, result: DiffResult):
        old_keys = set(old_obj.keys())
        new_keys = set(new_obj.keys())

        added_keys = new_keys - old_keys
        removed_keys = old_keys - new_keys
        common_keys = old_keys & new_keys

        for key in added_keys:
            full_path = self._join_path(path, key)
            if self._should_ignore(full_path):
                continue
            val = new_obj[key]
            result.added.append(DiffItem(
                path=full_path,
                change_type='added',
                new_value=val,
                new_type=self._get_type_name(val)
            ))
            self._add_nested_new(val, full_path, result)

        for key in removed_keys:
            full_path = self._join_path(path, key)
            if self._should_ignore(full_path):
                continue
            val = old_obj[key]
            result.removed.append(DiffItem(
                path=full_path,
                change_type='removed',
                old_value=val,
                old_type=self._get_type_name(val)
            ))
            self._add_nested_old(val, full_path, result)

        for key in common_keys:
            full_path = self._join_path(path, key)
            if self._should_ignore(full_path):
                continue
            self._compare_value(old_obj[key], new_obj[key], full_path, result)

    def _compare_arrays(self, old_arr: list, new_arr: list, path: str, result: DiffResult):
        min_len = min(len(old_arr), len(new_arr))
        max_len = max(len(old_arr), len(new_arr))

        for i in range(min_len):
            full_path = f"{path}[{i}]" if path else f"[{i}]"
            if self._should_ignore(full_path):
                continue
            self._compare_value(old_arr[i], new_arr[i], full_path, result)

        if len(new_arr) > len(old_arr):
            for i in range(min_len, max_len):
                full_path = f"{path}[{i}]" if path else f"[{i}]"
                if self._should_ignore(full_path):
                    continue
                val = new_arr[i]
                result.added.append(DiffItem(
                    path=full_path,
                    change_type='added',
                    new_value=val,
                    new_type=self._get_type_name(val)
                ))
                self._add_nested_new(val, full_path, result)
        elif len(old_arr) > len(new_arr):
            for i in range(min_len, max_len):
                full_path = f"{path}[{i}]" if path else f"[{i}]"
                if self._should_ignore(full_path):
                    continue
                val = old_arr[i]
                result.removed.append(DiffItem(
                    path=full_path,
                    change_type='removed',
                    old_value=val,
                    old_type=self._get_type_name(val)
                ))
                self._add_nested_old(val, full_path, result)

    def _add_nested_new(self, value: Any, path: str, result: DiffResult):
        if isinstance(value, dict):
            for k, v in value.items():
                full_path = self._join_path(path, k)
                if self._should_ignore(full_path):
                    continue
                result.added.append(DiffItem(
                    path=full_path,
                    change_type='added',
                    new_value=v,
                    new_type=self._get_type_name(v)
                ))
                self._add_nested_new(v, full_path, result)
        elif isinstance(value, list):
            for i, v in enumerate(value):
                full_path = f"{path}[{i}]"
                if self._should_ignore(full_path):
                    continue
                result.added.append(DiffItem(
                    path=full_path,
                    change_type='added',
                    new_value=v,
                    new_type=self._get_type_name(v)
                ))
                self._add_nested_new(v, full_path, result)

    def _add_nested_old(self, value: Any, path: str, result: DiffResult):
        if isinstance(value, dict):
            for k, v in value.items():
                full_path = self._join_path(path, k)
                if self._should_ignore(full_path):
                    continue
                result.removed.append(DiffItem(
                    path=full_path,
                    change_type='removed',
                    old_value=v,
                    old_type=self._get_type_name(v)
                ))
                self._add_nested_old(v, full_path, result)
        elif isinstance(value, list):
            for i, v in enumerate(value):
                full_path = f"{path}[{i}]"
                if self._should_ignore(full_path):
                    continue
                result.removed.append(DiffItem(
                    path=full_path,
                    change_type='removed',
                    old_value=v,
                    old_type=self._get_type_name(v)
                ))
                self._add_nested_old(v, full_path, result)
