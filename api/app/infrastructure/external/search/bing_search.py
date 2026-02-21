import logging
import re
import time
from typing import Optional
import httpx
from bs4 import BeautifulSoup

from app.domain.external.search import SearchEngine
from app.domain.models.search import SearchResult, SearchResultItem
from app.domain.models.tool_result import ToolResult

logger = logging.getLogger(__name__)

class BingSearchEngine(SearchEngine):
    """bing 搜索引擎"""

    def __init__(self) -> None:
        self.base_url = "https://www.bing.com/search"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        self.cookies = httpx.Cookies()

    async def invoke(self, query: str, date_range: Optional[str] = None) -> ToolResult[SearchResult]:
        # 1. 构建请求参数
        params = {"q": query}
        if date_range and date_range != "all":
            days_since_epoch = int(time.time() / (24 * 60 * 60))
            date_mapping = {
                "past_hour": "ex1%3a\"ez1\"",
                "past_day": "ex1%3a\"ez1\"",
                "past_week": "ex1%3a\"ez2\"",
                "past_month": "ex1%3a\"ez3\"",
                "past_year": f"ex1%3a\"ez5_{days_since_epoch-365}_{days_since_epoch}\""
            }
            if date_range in date_mapping:
                params["filters"] = date_mapping[date_range]

        # 2. 发送请求
        try:
            async with httpx.AsyncClient(
                headers=self.headers,
                cookies=self.cookies,
                timeout=60,
                follow_redirects=True,
            ) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()

                self.cookies.update(response.cookies)

                # 3. 解析响应内容
                soup = BeautifulSoup(response.text, "html.parser")

                # 4. 解析出 title, url, snippet
                # 从 b_algo 中解析出 title/url
                search_results = []
                result_items = soup.find_all("li", class_="b_algo")
                for item in result_items:
                    try:
                        title, url = ("", "")
                        title_tag = item.find("h2")
                        if title_tag:
                            a_tag = title_tag.find("a")
                            if a_tag:
                                title = a_tag.get_text(strip=True)
                                url = a_tag.get("href", "")
                        
                        # 如果标题不存在，则提取该 dom 下的 a 标签中的 href+text 作为标题和链接作为兜底
                        if not title:
                            a_tags = item.find_all("a")
                            for a_tag in a_tags:
                                text = a_tag.get_text(strip=True)
                                if len(text) > 10 and not text.startswith("http"):
                                    title = text
                                    url = a_tag.get("href")
                                    break
                        
                        if not title:
                            continue

                        # 提取摘要信息
                        snippet = ""
                        snippet_items = item.find_all(
                            ["p", "div"],
                            class_=re.compile(r"b_lineclamp|b_descript|b_caption"),
                        )
                        if snippet_items:
                            snippet = snippet_items[0].get_text(strip=True)
                        
                        if not snippet:
                            p_tags = item.find_all("p")
                            for p in p_tags:
                                text = p.get_text(strip=True)
                                if len(text) > 20:
                                    snippet = text
                                    break
                        
                        if not snippet:
                            all_text = item.get_text(strip=True)
                            sentences = re.split(r"[.!?\n。！]", all_text)
                            for sentence in sentences:
                                clean_sentence = sentence.strip()
                                if len(clean_sentence) > 20 and clean_sentence != title:
                                    snippet = clean_sentence
                                    break
                        
                        if url and not url.startswith("http"):
                            if url.startswith("//"):
                                url = "https:" + url
                            elif url.startswith("/"):
                                url = "https://www.bing.com" + url

                        search_results.append(SearchResultItem(
                            url=url,
                            title=title,
                            snippet=snippet,
                        ))
                    except Exception as e:
                        logger.warning(f"Bing 搜索结果解析失败: {str(e)}")
                        continue

                # 5. 解析总条数
                total_results = 0
                result_stats = soup.find_all(string=re.compile(r"\d+[,\d+]\s*results"))
                if result_stats:
                    for stat in result_stats:
                        match = re.search(r"([\d,]+)\s*results", stat)
                        if match:
                            try:
                                total_results = int(match.group(1).replace(",", ""))
                                break
                            except Exception as e:
                                continue

                if total_results == 0:
                    count_elements = soup.find_all(
                        ["span", "p", "div"],
                        class_=re.compile(r"sb_count|b_focusTextMedium"),
                    )
                    for element in count_elements:
                        text = element.get_text(strip=True)
                        match = re.match(r"[\d,]+\s*results", text)
                        if match:
                            try:
                                total_results = int(match.group(1).replace(",", ""))
                                break
                            except Exception as e:
                                continue
                
                # 6. 返回结果
                results = SearchResult(
                    query=query,
                    date_range=date_range,
                    total_results=total_results,
                    results=search_results,
                )
                return ToolResult(success=True, data=results)
        except Exception as e:
            logger.error(f"Bing 搜索出错: {str(e)}")
            error_result = SearchResult(
                query=query,
                date_range=date_range,
                total_results=0,
                results=[],
            )
            return ToolResult(
                success=False,
                message=f"Bing 搜索出错: {str(e)}",
                data=error_result,
            )
        

if __name__ == "__main__":
    import asyncio

    async def test():
        search_engine = BingSearchEngine()
        result = await search_engine.invoke("gemini")
        print(result)
        for item in result.data.results:
            print(item)

    asyncio.run(test())
