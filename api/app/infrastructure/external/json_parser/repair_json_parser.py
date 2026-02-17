from typing import Any, Dict, List, Optional, Union
import logging
import json_repair

from app.domain.external.json_parser import JsonParser

logger = logging.getLogger(__name__)

class RepairJsonParser(JsonParser):
    """基于修复逻辑的 JSON 解析器"""

    async def invoke(self, text: str, default_value: Optional[Any] = None) -> Union[Dict, List, Any]:
        """传递文本，并使用 json-repair 库进行修复"""
        logger.info(f"解析 json 文本: {text}")
        if not text or text.strip():
            if default_value is not None:
                return default_value
            raise ValueError("json 文本为空，且无默认值")

        return json_repair.repair_json(text, ensure_ascii=False)