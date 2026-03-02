from playwright.async_api import async_playwright
import asyncio

async def example() -> None:
    # 1. 创建 playwright 异步实例
    async with async_playwright() as playwright:
        # 2. 连接到 cdp 获取浏览器实例
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9222")
        default_context = browser.contexts[0]

        # 3. 获取当前上下文的第一个页面
        page = default_context.pages[0]
        print("页面标题:", await page.title())
        print("页面URL:", page.url)

        # 4. 新增页面并且跳转到 imooc.com
        page = await default_context.new_page()
        await page.goto("https://imooc.com")

        # 5. 在页面上执行 js 并获取结果
        href = await page.evaluate("""
        () => document.location.href
        """)
        print("JS执行结果:", href)

        # 6. 截图
        await page.screenshot(path="./screenshot.png")
        await page.screenshot(path="./screenshot-full.png", full_page=True)

        # 7. 关闭浏览器
        await browser.close()

if __name__ == "__main__":
    asyncio.run(example())
