import logging
import asyncio
from typing import List, Optional

from markdownify import markdownify
from playwright.async_api import Browser, ElementHandle, Page, Playwright, async_playwright

from app.domain.external.llm import LLM
from app.domain.external.browser import Browser as BrowserProtocol
from app.domain.models.tool_result import ToolResult
from app.infrastructure.external.browser.playwright_browser_fun import GET_INTERACTIVE_ELEMENTS_FUNC, GET_VISIBLE_CONTENT_FUNC, INJECT_CONSOLE_LOGS_FUNC

logger = logging.getLogger(__name__)

class PlaywrightBrowser(BrowserProtocol):
    """基础 Playwright 管理的浏览器扩展"""

    def __init__(
        self,
        cdp_url: str, # CDP 的连接地址
        llm: Optional[LLM] = None, # 可选参数，传递 LLM，如果传递了则会使用 LLM 对页面内容进行整理变成 markdown 格式
    ) -> None:
        self.llm: Optional[LLM] = llm
        self.cdp_url: str = cdp_url
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    async def _ensure_browser(self) -> None:
        """确保浏览器存在，如果不存在，则初始化"""
        if not self.browser or not self.page:
            if not await self.initialize():
                raise Exception("初始化 PlayWright 浏览器失败")
    
    async def _ensure_page(self) -> None:
        """确保浏览器页面存在，如果不存在，则新建"""
        await self._ensure_browser()
        if not self.page:
            self.page = await self.browser.new_page()
        else:
            contexts = self.browser.contexts
            if contexts:
                default_context = contexts[0]
                pages = default_context.pages
                if pages:
                    latest_page = pages[-1]
                    if self.page != latest_page:
                        self.page = latest_page
    
    async def _extract_content(self) -> str:
        """提取当前页面内容"""
        try:
            visible_content = await self.page.evaluate(GET_VISIBLE_CONTENT_FUNC)
        except Exception as e:
            logger.warning(f"page.evaluate 提取页面内容失败，回退到 page.content(): {e}")
            try:
                visible_content = await self.page.content()
            except Exception:
                return ""
        markdown_content = markdownify(visible_content)
        max_content_length = min(len(markdown_content), 50000)

        if self.llm:
            response = await self.llm.invoke([
                {
                    "role": "system",
                    "content": "您是一名专业的网页信息提取助手。请从当前页面内容中提取所有信息并将其转换为markdown格式。",
                },
                {
                    "role": "user",
                    "content": markdown_content[:max_content_length],
                }
            ])
            return response.get("content", "")
        else:
            return markdown_content[:max_content_length]

    async def _extract_interactive_elements(self) -> List[str]:
        """提取当前页面上的可交互元素"""
        await self._ensure_page()

        # 清除当前页面上的可交互元素列表
        self.page.interactive_elements_cache = []

        # 执行 js 脚本获取可交互的元素列表
        try:
            interactive_elements = await self.page.evaluate(GET_INTERACTIVE_ELEMENTS_FUNC)
        except Exception as e:
            logger.warning(f"page.evaluate 提取可交互元素失败: {e}")
            return []

        # 更新缓存的可交互元素列表
        self.page.interactive_elements_cache = interactive_elements

        # 格式化可交互元素为字符串
        formatted_elements = []
        for element in interactive_elements:
            formatted_elements.append(f"{element['index']}:<{element['tag']}>{element['text']}</{element['tag']}>")
        
        return formatted_elements

    async def _get_element_by_id(self, index: int) -> Optional[ElementHandle]:
        """根据传递的索引获取对应的元素"""
        if (
            not hasattr(self.page, "interactive_elements_cache") or
            not self.page.interactive_elements_cache or
            index >= len(self.page.interactive_elements_cache)
        ):
            return None

        selector = f'[data-manus-id="manus-element-{index}"]'
        return await self.page.query_selector(selector)

    async def click(
        self,
        index: Optional[int] = None,
        coordinate_x: Optional[float] = None,
        coordinate_y: Optional[float] = None,
    ) -> ToolResult:
        await self._ensure_page()

        if coordinate_x is not None and coordinate_y is not None:
            await self.page.mouse.click(coordinate_x, coordinate_y)
        elif index is not None:
            try:
                # 根据 index 获取元素
                element = await self._get_element_by_id(index)
                if not element:
                    return ToolResult(success=False, message=f"使用索引[{index}]找不到该元素")
                
                # 检查元素是否是可见的
                is_visible = await self.page.evaluate("""(element) => {
                    if (!element) return false;
                    const rect = element.getBoundingClientRect();
                    const style = window.getComputedStyle(element);
                    return !(
                        rect.width === 0 ||
                        rect.height === 0 ||
                        style.display === 'none' ||
                        style.visibility === 'hidden' ||
                        style.opacity === '0'
                    );
                }""", element)

                if not is_visible:
                    # 如果元素不可见，尝试将页面滚动到该元素的位置
                    await self.page.evaluate("""(element) => {
                        if (element) {
                            element.scrollIntoView({behavior: 'smooth', block: 'center})
                        }
                    }""", element)
                    await asyncio.sleep(1)
                
                # 点击元素
                await element.click(timeout=5000)
            except Exception as e:
                return ToolResult(success=False, message=f"点击元素出错: {str(e)}")

        return ToolResult(success=True)

    async def initialize(self) -> bool:
        """初始化并确保资源是可用的"""
        max_retries = 5
        retry_interval = 1

        for attempt in range(max_retries):
            try:
                # 创建 playwright 上下文并连接到 cdp 浏览器
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.connect_over_cdp(self.cdp_url)

                # 获取浏览器的所有上下文
                contexts = self.browser.contexts

                # 如果上下文存在，并且第一个上下文只有一个页面则执行如下逻辑
                if contexts and len(contexts[0].pages) == 1:
                    # 获取当前上下文的第一个页面
                    page = contexts[0].pages[0]

                    # 判断当前页面是不是空页面，如果是则直接使用page，否则新建一个
                    if(
                        page.url == "about:blank" or
                        page.url == "chrome://newtab/" or
                        page.url == "chrome://new-tab-page/" or
                        not page.url
                    ):
                        self.page = page
                    else:
                        self.page = await contexts[0].new_page()
                else:
                    # 上下文不存在或者页面不唯一则表示数据被污染，新建一个页面
                    context = contexts[0] if contexts else await self.browser.new_context()
                    self.page = await context.new_page()
                
                return True
            except Exception as e:
                await self.cleanup()
                if attempt == max_retries - 1:
                    logger.error(f"初始化Playwright浏览器失败(已重试{max_retries}次): {str(e)}")
                    return False
                
                retry_interval = min(retry_interval * 2, 10)
                logger.warning(f"初始化Playwright浏览器失败, 即将进行第{attempt + 1}次重试: {str(e)}")
                await asyncio.sleep(retry_interval)

    async def cleanup(self) -> None:
        """清除Playwright资源，包含浏览器+页面+Playwright"""
        try:
            if self.browser:
                contexts = self.browser.contexts
                if contexts:
                    for context in contexts:
                        pages = context.pages
                        for page in pages:
                            if not page.is_closed():
                                await page.close()
            
            if self.page and not self.page.is_closed():
                await self.page.close()
            
            if self.browser:
                await self.browser.close()
            
            if self.playwright:
                assert self.playwright.stop()
        except Exception as e:
            logger.error(f"清理Playwright浏览器资源出错: {str(e)}")
        finally:
            self.page = None
            self.browser = None
            self.playwright = None

    async def wait_for_page_Load(self, timeout: int = 15) -> bool:
        """传递超时时间，等待当前页面是否加载完毕"""
        await self._ensure_page()

        start_time = asyncio.get_event_loop().time()
        check_interval = 0.5

        while asyncio.get_event_loop().time() - start_time < timeout:
            try:
                is_completed = await self.page.evaluate("() => document.readyState === 'complete'")
                if is_completed:
                    return True
            except Exception:
                pass
            await asyncio.sleep(check_interval)
        
        return False

    async def navigate(self, url: str) -> ToolResult:
        await self._ensure_page()

        try:
            self.page.interactive_elements_cache = []

            await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
            return ToolResult(
                success=True,
                data={"interactive_elements": await self._extract_interactive_elements()}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                message=f"浏览器导航到[{url}]失败: {str(e)}"
            )

    async def view_page(self) -> ToolResult:
        await self._ensure_page()

        await self.wait_for_page_Load()
        interactive_elements = await self._extract_interactive_elements()
        return ToolResult(
            success=True,
            data={
                "content": await self._extract_content(),
                "interactive_elements": interactive_elements,
            }
        )

    async def input(
        self,
        text: str,
        press_enter: bool,
        index: Optional[int] = None,
        coordinate_x: Optional[float] = None,
        coordinate_y: Optional[float] = None,
    ) -> ToolResult:
        await self._ensure_page()

        if coordinate_x is not None and coordinate_y is not None:
            # 点击
            await self.page.mouse.click(coordinate_x, coordinate_y)
            # 输入信息
            await self.page.keyboard.type(text)
        elif index is not None:
            try:
                element = await self._get_element_by_id(index)
                if not element:
                    return ToolResult(success=False, message=f"输入文本失败，该元素不存在: {index}")
                
                try:
                    # 先清空原始输入框的内容
                    await element.fill("")
                    await element.type(text)
                except Exception as e:
                    # 如果填充失败，则尝试点击后输入文本
                    await element.click()
                    await element.type(text)
            except Exception as e:
                return ToolResult(success=False, message=f"输入文本失败: {str(e)}")
        
        # 判断是否按 Enter 键
        if press_enter:
            await self.page.keyboard.press("Enter")

        return ToolResult(success=True)

    async def move_mouse(self, coordinate_x: float, coordinate_y: float) -> ToolResult:
        await self._ensure_page()
        await self.page.mouse.move(coordinate_x, coordinate_y)
        return ToolResult(success=True)
    
    async def press_key(self, key: str) -> ToolResult:
        await self._ensure_page()
        await self.page.keyboard.press(key)
        return ToolResult(success=True)

    async def select_option(self, index: int, option: int) -> ToolResult:
        await self._ensure_page()
        
        try:
            element = await self._get_element_by_id(index)
            if not element:
                return ToolResult(success=False, message=f"使用索引[{index}]查找该下拉菜单不存在")
            
            await element.select_option(index=option)
            return ToolResult(success=True)
        except Exception as e:
            return ToolResult(success=False, message=f"选择下拉菜单选项失败: {str(e)}")

    async def restart(self, url: str) -> ToolResult:
        await self.cleanup()
        return await self.navigate(url)

    async def scroll_up(self, to_top: Optional[bool] = None) -> ToolResult:
        await self._ensure_page()

        if to_top:
            await self.page.evaluate("""window.scrollTo(0, 0)""")
        else:
            await self.page.evaluate("""window.scrollBy(0, -window.innerHeight)""")
        
        return ToolResult(success=True)
    
    async def scroll_down(self, to_down: Optional[bool] = None) -> ToolResult:
        await self._ensure_page()

        if to_down:
            await self.page.evaluate("""window.scrollTo(0, document.body.scrollHeight)""")
        else:
            await self.page.evaluate("""window.scrollBy(0, window.innerHeight)""")
        
        return ToolResult(success=True)
    
    async def screenshot(self, full_page: Optional[bool] = None) -> bytes:
        await self._ensure_page()

        screentshot_options = {
            "full_page": full_page,
            "type": "png"
        }

        return await self.page.screenshot(**screentshot_options)
    
    async def console_exec(self, javascript: str) -> ToolResult:
        await self._ensure_page()

        try:
            await self.page.evaluate(INJECT_CONSOLE_LOGS_FUNC)
        except Exception as e:
            logger.warning(f"注入 window.console.logs 失败: {str(e)}")

        result = await self.page.evaluate(javascript)
        return ToolResult(success=True, data={"result": result})
    
    async def console_view(self, max_lines: Optional[int] = None) -> ToolResult:
        await self._ensure_page()

        logs = self.page.evaluate("""() => {
            return window.console.logs || [];
        }""")

        if max_lines is not None:
            logs = logs[-max_lines:]
        
        return ToolResult(success=True, data={"logs": logs})