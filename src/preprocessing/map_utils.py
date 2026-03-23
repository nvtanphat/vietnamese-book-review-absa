from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Mapping

# Xác định đường dẫn gốc của dự án (thường là thư mục cha của 'src')
PROJECT_ROOT = Path(__file__).resolve().parents[2]
# Đường dẫn đến thư mục chứa các file bản đồ (data/maps)
MAP_DIR = PROJECT_ROOT / "data" / "maps"


@lru_cache(maxsize=None)
def _read_map(path_str: str) -> dict[str, str]:
    """Đọc file JSON bản đồ và lưu vào bộ nhớ đệm (cache) để tăng tốc cho các lần gọi sau."""
    path = Path(path_str)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    # Đảm bảo nội dung file JSON là một đối tượng (dictionary)
    if not isinstance(data, dict):
        raise ValueError(f"File bản đồ phải chứa một đối tượng JSON: {path}")
    # Đảm bảo tất cả các khóa (key) và giá trị (value) đều là kiểu chuỗi
    return {str(key): str(value) for key, value in data.items()}


def load_json_map(filename: str, defaults: Mapping[str, str] | None = None) -> dict[str, str]:
    """Tải bản đồ từ file JSON và hợp nhất với các giá trị mặc định (nếu có)."""
    mapping = dict(defaults or {})
    # Tìm file trong thư mục MAP_DIR và cập nhật vào mapping
    mapping.update(_read_map(str(MAP_DIR / filename)))
    return mapping
