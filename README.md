# ExileWebUIEngine

### 参数描述

```python
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
        :param listening_api: 监听的`api`或页面`path`存储对应的出入参数据 例如: ["/api/login", "/order_list", ...]
        """
        self.is_debug = is_debug
        self.headless = headless
        self.debugger_address = debugger_address
        self.debugger_address_url = debugger_address_url
        self.playwright = None  # playwright实例
        self.browser: Union[Browser, None] = None  # 浏览器实例
        self.context = None  # 上下文实例
        self.page = None  # 页签实例, 通过`self.context`切换
        self.page_list = []  # 页签实例列表, 用于记录索引切换
        self.page_list_len = None  # 页签实例列表长度
        self.page_obj_list = []  # 页签实例对象列表: [{'index': 0, 'title': 'GitHub', 'url': 'https://github.com/'}...]
        self.browser_type = browser_type
        self.init_url = init_url
        self.width = width
        self.height = height
        self.listening_api = listening_api

        # 存储所有API请求与响应, 配合`listening_api`使用
        self.api_requests = []  # 被监听api请求参数
        self.api_responses = []  # 被监听api响应参数
        self.cookies = []

        # 启动浏览器命令, 结合 `self.debugger_address`
        # MACOS: /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
        # MACOS: /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug-profile
        # Windows: ...
```

### 简单例子

```python
import asyncio

from main import ExileWebUIEngine


async def test():
    engine = ExileWebUIEngine(
        is_debug=True,
        headless=False,
        init_url="https://github.com/yangyuexiong",
    )
    await engine.start()

    # 点击搜索
    await engine.action_click(
        t="xpath",
        element="""/html/body/div[1]/div[1]/header/div/div[2]/div/div/qbsearch-input/div[1]/button"""
    )

    # 输入内容
    await engine.action_input(
        t="xpath",
        element="""//*[@id="query-builder-test"]""",
        value="Flask_BestPractices"
    )

    # 键盘事件
    await engine.page.keyboard.press("Enter")

    # 点击Star
    await engine.action_click(
        t="xpath",
        element="""/html/body/div[1]/div[4]/main/react-app/div/div/div[1]/div/div/div[2]/div/div/div[1]/div[4]/div/div/div[1]/div/div[2]/div/a/span"""
    )

    await engine.stop()


asyncio.run(test())

```