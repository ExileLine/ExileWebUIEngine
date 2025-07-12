# -*- coding: utf-8 -*-
# @Time    : 2025/7/4 16:57
# @Author  : yangyuexiong
# @Email   : yang6333yyx@126.com
# @File    : main.py
# @Software: PyCharm

import os
import json
import asyncio
from typing import Union, Optional, List
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
            browser_type: str = "chrome",
            init_url: str = "https://github.com/ExileLine",
            width: int = None,
            height: int = None,
            listening_api: List[str] = None
    ) -> None:
        """

        :param is_debug: 调试模式,浏览器不会直接执行`self.end()`关闭,需要手动键入`回车`后才会触发 self.end()
        :param headless: 是否使用无界面
        :param debugger_address: 是否操作已启动的浏览器
        :param debugger_address_url: 结合 `debugger_address` 使用
        :param browser_type: 浏览器类型 chrome,firefox
        :param init_url: 浏览器初始页面地址
        :param width: 浏览器初始宽
        :param height: 浏览器初始高
        :param listening_api: 监听的`api`或页面`path`
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
        self.browser_type = browser_type
        self.init_url = init_url
        self.width = width
        self.height = height

        self.listening_api = listening_api

        # 存储所有API请求与响应
        self.api_requests = []
        self.api_responses = []
        self.cookies = []

        # MACOS: /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
        # MACOS: /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug-profile
        # Windows: ...

    async def get_cookies(self):
        """获取操作接口的`cookies`"""

        try:
            cookies = self.page.context.cookies()
            return cookies
        except BaseException as e:
            return {
                "func": "get_cookies",
                "message": f"`get_cookies` 错误 {e}"
            }

    async def log_request(self, request):
        """监听请求"""

        for api in self.listening_api:
            if api in request.url:
                self.api_requests.append(request)

    async def log_response(self, response):
        """监听响应"""

        for api in self.listening_api:
            if api in response.url:
                self.api_responses.append(response)

    async def start(self):
        """启动"""

        self.playwright = await async_playwright().start()

        if self.browser_type not in ["chrome", "firefox"]:
            raise ValueError("browser_type not in ['chrome', 'firefox']")

        if self.debugger_address:
            if self.browser_type == "chrome":
                self.browser = await self.playwright.chromium.connect_over_cdp(self.debugger_address_url)
            elif self.browser_type == "firefox":
                self.browser = await self.playwright.firefox.connect_over_cdp(self.debugger_address_url)
            else:
                pass

            await self.handle_context_page()
            await self.reload_pages()
        else:
            rule_list = [
                "--disable-http-cache",  # 禁用缓存
                "--disable-features=SameSiteByDefaultCookies"  # 临时解决Cookie策略问题
            ]
            if self.browser_type == "chrome":
                self.browser = await self.playwright.chromium.launch(headless=self.headless, args=rule_list)
            elif self.browser_type == "firefox":
                self.browser = await self.playwright.firefox.launch(headless=self.headless, args=rule_list)
            else:
                pass

            self.context = await self.browser.new_context(
                ignore_https_errors=True,  # 忽略HTTPS错误
                storage_state=None,  # 关键：每次启动使用全新存储状态
                bypass_csp=True,  # 强制覆盖所有内容安全策略
            )

            await self.out_logs(f"listening_api: {self.listening_api}")
            if self.listening_api:
                self.context.on("request", self.log_request)
                self.context.on("response", self.log_response)

            self.page = await self.context.new_page()

            if self.width and self.height:
                await self.page.set_viewport_size({"width": self.width, "height": self.height})  # type: ignore

            await self.page.goto(self.init_url)
            await self.show_title()

    async def stop(self):
        """停止"""

        if self.is_debug:
            input("输入回车后关闭浏览器...")

        await self.context.close()
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

    async def page_wait(self, timeout: int | float):
        """
        等待所有请求完成
        :param timeout:
        :return:
        """

        await self.page.wait_for_timeout(timeout)

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

    async def action_input(self, t: str, element: str, value: str):
        """
        输入
        :param t: 元素类型 XPATH, CSS, ...
        :param element: 元素值
        :param value:   输入值
        :return:
        """

        await self.check_element(element)

        if t in ["xpath", "XPATH"]:
            await self.page.locator(f"xpath={element}").fill(value)
        else:
            await self.page.fill(element, value)

    async def action_click(self, t: str, element: str):
        """点击"""

        await self.check_element(element)

        if t in ["xpath", "XPATH"]:
            await self.page.click(f"xpath={element}")
        else:
            await self.page.click(element)

    async def test(self):
        """test"""

        await self.start()
        await self.stop()

    async def test2(self):
        """test2"""

        await self.start()

        await self.action_input(
            t="xpath",
            element="""/html/body/div[1]/div/div[2]/form/div[1]/div[2]/div/div/div/input""",
            value="super"
        )
        await self.action_input(
            t="xpath",
            element="""/html/body/div[1]/div/div[2]/form/div[2]/div[2]/div/div/div/input""",
            value="123456"
        )
        await self.action_click(
            t="xpath",
            element="""/html/body/div[1]/div/div[2]/form/div[3]/div[2]/div/div/div/button[1]"""
        )

        await self.page_wait(1000)

        # 输出结果
        print("\n=== 捕获的API请求 ===")
        for request in self.api_requests:
            # print(request.__dir__())
            request_dict = {
                "method": request.method,
                "url": request.url,
                "headers": request.headers,
                "data": request.post_data,
                "json_data": request.post_data_json,
            }

            # print(request.method)
            # print(request.url)
            # print(request.headers)
            # print(request.post_data)
            # print(request.post_data_json)

            print(json.dumps(request_dict, ensure_ascii=False))

        print("\n=== API响应数据 ===")
        for response in self.api_responses:
            # print(response.__dir__())
            response_dict = {
                "url": response.url,
                "http_code": response.status,
                "http_message": response.status_text,
                "headers": response.headers,
                "all_headers": await response.all_headers(),
                # "response_json": await response.json(),
                # "response_text": await response.text(),
                # "response_body": await response.body()
            }
            try:
                response_dict["response_json"] = await response.json()
            except Exception as e:
                print(f"无法解析JSON响应: {str(e)}")

            try:
                response_dict["response_text"] = await response.text()
            except Exception as e:
                print(f"无法解析TEXT响应: {str(e)}")

            # print(response.url)
            # print(response.status)
            # print(response.status_text)
            # print(response.headers)
            # print(await response.all_headers())
            # print(await response.json())
            # print(await response.text())
            # print(await response.body())

            print(json.dumps(response_dict, ensure_ascii=False))

            print("\n=== API响应Cookies ===")

            cookies = response_dict.get("all_headers", {}).get("set-cookie", "")
            print(cookies.split(";"))

        await self.stop()


if __name__ == '__main__':
    # engine = ExileWebUIEngine(
    #     is_debug=True,
    #     headless=False,
    #     init_url="https://www.metatuple.com/"
    # )
    # asyncio.run(engine.test())

    engine = ExileWebUIEngine(
        is_debug=True,
        headless=False,
        init_url="http://localhost:3200/",
        listening_api=["/api/account/login"]
    )
    asyncio.run(engine.test2())
