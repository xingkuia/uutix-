# taskkill /F /IM msedge.exe
# & "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9222
# .\.venv\Scripts\python.exe uutix_booking.py


import os
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# 目标网址
TARGET_URL = "https://www.uutix.com/detail?pId=3702"
# Windows Edge 用户数据路径
# 为了避免 "TargetClosedError" 
# 创建一个专用的副本或独立目录。
EDGE_USER_DATA_DIR = os.path.join(os.getenv('LOCALAPPDATA'), r"Microsoft\Edge\User Data")
AUTOMATION_USER_DATA_DIR = os.path.join(os.getcwd(), "edge_automation_profile")

async def run():
    async with async_playwright() as p:
        print("正在尝试连接到本地已开启的 Edge 浏览器...")
        try:
            # 连接到在 9222 端口开启了远程调试的本地 Edge
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()
        except Exception as e:
            print("\n" + "="*60)
            print("❌ 连接本地 Edge 失败！")
            print("要直接接管本地的 Edge，您需要先【完全关闭】所有现有的 Edge 窗口，")
            print("然后打开 PowerShell 或 CMD，运行以下命令来以调试模式启动 Edge：")
            print(r'& "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9222')
            print("\n（注意：如果是使用 PowerShell 运行上面带 & 的整句，CMD 只需运行双引号部分加参数）")
            print("启动成功后，此时就是您的日常 Edge 浏览器，请再次运行本脚本！")
            print("="*60 + "\n")
            return
        await Stealth().apply_stealth_async(page)
        
        print(f"正在导航至 {TARGET_URL}...")
        try:
            await page.goto(TARGET_URL, timeout=60000)
        except Exception as e:
            print(f"初始导航失败: {e}。正在循环重试...")

        # "購買門票" 按钮的选择器
        # 结合类名和文本内容来提高准确性
        button_selector = "div.button.detail-normal-button:has-text('購買門票')"

        while True:
            try:
                # 等待按钮出现 (2秒超时，以便快速重试)
                print("正在搜索 '購買門票' 按钮...")
                button = await page.wait_for_selector(button_selector, timeout=500, state="visible")
                
                if button:
                    print("找到按钮！正在点击...")
                    await button.click()
                    print("成功点击 '購買門票'！")
                    # 进入下一步：选座确认页面
                    break
            except Exception:
                # 如果找不到按钮，检查是否显示 "人数过多"，或者直接刷新
                content = await page.content()
                if "人數過多" in content:
                    print("服务器繁忙 (人數過多)，正在刷新...")
                else:
                    print("按钮尚未准备好，正在刷新...")
                
                # 刷新页面以重试
                await page.reload()
                # 短暂暂停以避免请求过快被服务器封锁
                await asyncio.sleep(0.05)
        print("进入第二阶段：等待选座确认页面...")
        
        # 第二个 "購買" 按钮的选择器 (基于用户提供的 HTML 片段)
        second_button_selector = "button.right.roboto-bold-wrap:has-text('購買')"

        while True:
            try:
                # 使用较短的超时时间，以便在页面仍在加载或繁忙时快速重试
                print("正在搜索第二个 '購買' 按钮...")
                second_button = await page.wait_for_selector(second_button_selector, timeout=500, state="visible")
                
                if second_button:
                    # 检查按钮是否被禁用 (有时按钮可见但被禁用)
                    is_disabled = await second_button.is_disabled()
                    if not is_disabled:
                        print("找到第二个 '購買' 按钮且处于激活状态！正在点击...")
                        await second_button.click()
                        print("成功点击第二个 '購買' 按钮！")
                        break
                    else:
                        print("按钮可见但被禁用，正在等待...")
                        await asyncio.sleep(0.05)
            except Exception:
                content = await page.content()
                if "人數過多" in content:
                    print("第二阶段: 服务器繁忙 (人數過多)，正在刷新...")
                else:
                    print("第二阶段: 找不到按钮或未准备好，正在刷新...")
                
                # 刷新页面以重试
                await page.reload()
                await asyncio.sleep(0.1)    

        # 等待用户完成手动步骤 (支付)
        print("脚本已完成自动点击。如果需要，请继续进行支付。")
        await asyncio.sleep(3600) # 保持浏览器打开一小时，以便用户有时间支付

if __name__ == "__main__":
    asyncio.run(run())
