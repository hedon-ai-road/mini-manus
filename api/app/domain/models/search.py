from typing import List, Optional
from pydantic import BaseModel, Field

class SearchResultItem(BaseModel):
    """搜索结果条目数据类型"""
    url: str # URL 链接
    title: str # 标题
    snippet: str = "" # 摘要

class SearchResult(BaseModel):
    """搜索结果数据模型"""
    query: str # 查询 query
    date_range: Optional[str] = None # 日期筛选范围
    total_results: int = 0 # 搜索结果条数
    results: List[SearchResultItem] = Field(default_factory=list) # 结果列表