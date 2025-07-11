# -*- coding: utf-8 -*-
# @Time    : 2025/7/4 16:57
# @Author  : yangyuexiong
# @Email   : yang6333yyx@126.com
# @File    : main.py
# @Software: PyCharm

import os
import asyncio
from typing import Union, Optional
from platform import system

from playwright.async_api import Browser, FrameLocator, ElementHandle
from playwright.async_api import async_playwright, Playwright


class ExileWebUIEngine:
    """ExileWebUIEngine"""

    def __init__(
            self,
            is_debug: bool = False,
            headless: bool = False,
            debugger_address: bool = False,
            debugger_address_url: str = "http://127.0.0.1:9222",
            init_url: str = "https://github.com/ExileLine",
            width: int = None,
            height: int = None,
    ) -> None:
        """

        :param is_debug: 调试模式,浏览器不会直接执行`self.end()`关闭,需要手动键入`回车`后才会触发 self.end()
        :param headless: 是否使用无界面
        :param debugger_address: 是否操作已启动的浏览器
        :param debugger_address_url: 结合 `debugger_address` 使用
        :param init_url: 浏览器初始页面地址
        :param width: 浏览器初始宽
        :param height: 浏览器初始高
        """
        self.is_debug = is_debug
        self.headless = headless
        self.debugger_address = debugger_address
        self.debugger_address_url = debugger_address_url
        self.playwright = None
        self.browser: Union[Browser, None] = None
        self.context = None
        self.page = None
        self.page_list = []
        self.page_list_len = None
        self.page_obj_list = []  # [{'index': 0, 'title': 'GitHub', 'url': 'https://github.com/'}...]
        self.init_url = init_url
        self.width = width
        self.height = height

        # MACOS: /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
        # MACOS: /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug-profile
        # Windows: ...

    async def start(self):
        """启动"""

        self.playwright = await async_playwright().start()

        if self.debugger_address:
            self.browser = await self.playwright.chromium.connect_over_cdp(self.debugger_address_url)
            await self.handle_context_page()
            await self.reload_pages()
        else:
            self.browser = await self.playwright.chromium.launch(headless=self.headless)
            self.context = await self.browser.new_context(ignore_https_errors=True)
            self.page = await self.context.new_page()
            if self.width and self.height:
                await self.page.set_viewport_size({"width": self.width, "height": self.height})
            await self.page.goto(self.init_url)
            await self.show_title()

    async def stop(self):
        """停止"""

        if self.is_debug:
            input("输入回车后关闭浏览器...")

        await self.browser.close()
        await self.playwright.stop()

    async def out_logs(self, message: str):
        """out_logs"""

        print(message)
        ...

    async def show_title(self):
        """输出当前页签"""

        await self.out_logs(f"当前页签: {await self.page.title()}")

    async def show_context(self):
        """输出当前浏览器实例"""

        await self.out_logs(f"当前浏览器: {self.context}")

    async def reload_pages(self):
        """加载所有页签"""

        self.page_list = self.context.pages
        self.page_list_len = len(self.page_list)
        await self.out_logs(f"当前页签数量: {self.page_list_len}")
        for index, page in enumerate(self.page_list):
            page_obj = {
                "index": index,
                "title": await page.title(),
                "url": page.url,
            }
            await self.out_logs(f"页签对象: {page_obj}")
            self.page_obj_list.append(page_obj)

    async def browser_connet(self) -> bool:
        """获取浏览器连接状态"""

        result = self.browser.is_connected()
        await self.out_logs(f"获取浏览器连接状态: {result}")
        return result

    async def handle_context_page(self, ctx_index: int = 0, page_index: int = 0):
        """
        上下文切换
        :param ctx_index: 浏览器索引,默认情况下开启一个浏览器,默认是`0`
        :param page_index: 网页页签,通过索引切换进行操作,默认是`0`
        :return:
        """

        self.context = self.browser.contexts[ctx_index]
        await self.show_context()
        await self.browser_connet()
        self.page = self.context.pages[page_index]
        await self.show_title()

    async def get_iframe(self, iframe_selector: str) -> FrameLocator:
        """
        获取`iframe`实例, 对`iframe`内元素进行操作, 例如: iframe.query_selector(selector).click()
        :param iframe_selector:
        :return:
        """

        # 等待 iframe 加载完成
        iframe = await self.page.wait_for_selector(iframe_selector).content_frame()
        await iframe.wait_for_load_state()
        await self.out_logs(f"iframe实例: {iframe}")
        return iframe

    @staticmethod
    async def get_iframe_element(iframe_example, selector: str) -> Optional[ElementHandle]:
        """
        获取`iframe`内的元素, 结合 `self.get_iframe()` 使用
        :param iframe_example: `self.get_iframe()` 返回
        :param selector:
        :return:

        iframe_element.fill()
        iframe_element.click()
        ...
        """

        iframe_element = iframe_example.query_selector(selector)
        return iframe_element

    async def check_element(self, element: str):
        """检查元素"""

    async def action_input(self, element: str, value: str):
        """输入"""

        await self.check_element(element)
        await self.page.fill(element, value)

    async def action_click(self, element: str):
        """点击"""

        await self.check_element(element)
        await self.page.click(element)

    async def test(self):
        """test"""

        await self.start()
        await self.stop()


if __name__ == '__main__':
    engine = ExileWebUIEngine(
        is_debug=True,
        headless=True,
        init_url="https://www.metatuple.com/"
    )
    asyncio.run(engine.test())
