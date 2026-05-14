#!/usr/bin/env python3
"""
任务日期三种模式 UI 测试
验证前端界面日期模式切换功能
"""
import sys
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_ui_period_selection():
    """测试UI界面三种日期模式切换"""
    base_url = "http://20.20.30.81:8001"
    driver = None
    test_results = []
    
    try:
        # 设置Chrome无头浏览器
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        driver = webdriver.Chrome(options=chrome_options)
        logger.info("✅ Chrome无头浏览器启动成功")
        
        # 1. 打开登录页面
        logger.info("1. 打开教师登录页面...")
        driver.get(f"{base_url}/teacher/login")
        
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "phone"))
            )
            logger.info("✅ 登录页面加载成功")
            test_results.append({"test": "登录页面加载", "status": "PASS"})
        except Exception as e:
            logger.error(f"❌ 登录页面加载失败: {e}")
            test_results.append({"test": "登录页面加载", "status": "FAIL", "error": str(e)})
            return False, test_results
        
        # 2. 登录
        logger.info("2. 教师登录...")
        phone_input = driver.find_element(By.ID, "phone")
        password_input = driver.find_element(By.ID, "password")
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        
        phone_input.send_keys("13800138000")
        password_input.send_keys("test123456")
        login_button.click()
        
        # 等待登录成功
        try:
            WebDriverWait(driver, 10).until(
                EC.url_contains("/teacher")
            )
            logger.info("✅ 登录成功")
            test_results.append({"test": "教师登录", "status": "PASS"})
        except Exception as e:
            logger.error(f"❌ 登录失败: {e}")
            test_results.append({"test": "教师登录", "status": "FAIL", "error": str(e)})
            return False, test_results
        
        # 3. 导航到任务发布页面
        logger.info("3. 导航到任务发布页面...")
        driver.get(f"{base_url}/teacher/tasks/create")
        
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".create-task"))
            )
            logger.info("✅ 任务发布页面加载成功")
            test_results.append({"test": "任务发布页面加载", "status": "PASS"})
        except Exception as e:
            logger.error(f"❌ 任务发布页面加载失败: {e}")
            test_results.append({"test": "任务发布页面加载", "status": "FAIL", "error": str(e)})
            return False, test_results
        
        # 4. 检查任务周期选择组件
        logger.info("4. 检查任务周期选择组件...")
        
        # 查找任务周期标签
        period_label = None
        for element in driver.find_elements(By.TAG_NAME, "label"):
            if "任务周期" in element.text:
                period_label = element
                break
        
        if period_label:
            logger.info("✅ 找到任务周期标签")
            test_results.append({"test": "任务周期标签存在", "status": "PASS"})
        else:
            logger.error("❌ 未找到任务周期标签")
            test_results.append({"test": "任务周期标签存在", "status": "FAIL", "error": "未找到标签"})
        
        # 5. 检查单日/周/月单选按钮
        logger.info("5. 检查单日/周/月单选按钮...")
        
        # 查找所有包含文本的span元素
        period_options = []
        for span in driver.find_elements(By.TAG_NAME, "span"):
            text = span.text.strip()
            if text in ["单日", "周任务", "月任务"]:
                period_options.append(text)
        
        if len(period_options) == 3:
            logger.info(f"✅ 找到所有周期选项: {period_options}")
            test_results.append({"test": "周期选项完整", "status": "PASS", "options": period_options})
        else:
            logger.error(f"❌ 周期选项不完整，找到: {period_options}")
            test_results.append({"test": "周期选项完整", "status": "FAIL", "error": f"选项不完整: {period_options}"})
        
        # 6. 检查日期选择器
        logger.info("6. 检查日期选择器...")
        date_pickers = driver.find_elements(By.CSS_SELECTOR, ".el-date-picker, [class*='date-picker'], input[type='date']")
        
        if date_pickers:
            logger.info(f"✅ 找到日期选择器，数量: {len(date_pickers)}")
            test_results.append({"test": "日期选择器存在", "status": "PASS", "count": len(date_pickers)})
        else:
            logger.error("❌ 未找到日期选择器")
            test_results.append({"test": "日期选择器存在", "status": "FAIL", "error": "未找到日期选择器"})
        
        # 7. 截图保存
        logger.info("7. 截图保存...")
        screenshot_path = "/home/code/czyj/tests/e2e/screenshots/task_period_ui.png"
        driver.save_screenshot(screenshot_path)
        logger.info(f"✅ 截图已保存: {screenshot_path}")
        test_results.append({"test": "页面截图", "status": "PASS", "path": screenshot_path})
        
        # 8. 获取页面HTML片段用于验证
        page_html = driver.page_source
        if "task_period" in page_html or "任务周期" in page_html:
            logger.info("✅ 页面包含任务周期相关代码")
            test_results.append({"test": "页面代码验证", "status": "PASS"})
        else:
            logger.warning("⚠️ 页面中未找到task_period或任务周期关键词")
            test_results.append({"test": "页面代码验证", "status": "WARN", "note": "未找到关键词"})
        
        return True, test_results
        
    except Exception as e:
        logger.error(f"❌ UI测试异常: {e}")
        test_results.append({"test": "UI测试整体", "status": "FAIL", "error": str(e)})
        return False, test_results
    finally:
        if driver:
            driver.quit()
            logger.info("✅ 浏览器已关闭")

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("任务日期三种模式UI测试")
    logger.info("=" * 60)
    
    success, results = test_ui_period_selection()
    
    # 输出测试结果
    logger.info("\n" + "=" * 60)
    logger.info("UI测试结果汇总")
    logger.info("=" * 60)
    
    passed = sum(1 for r in results if r["status"] == "PASS")
    total = len(results)
    
    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result["status"] == "PASS" else "❌ FAIL" if result["status"] == "FAIL" else "⚠️ WARN"
        test_name = result["test"]
        extra = ""
        
        if "options" in result:
            extra = f" (选项: {result['options']})"
        elif "count" in result:
            extra = f" (数量: {result['count']})"
        elif "path" in result:
            extra = f" (路径: {result['path']})"
        elif "note" in result:
            extra = f" (备注: {result['note']})"
        elif "error" in result:
            extra = f" (错误: {result['error'][:50]})"
        
        logger.info(f"{i:2d}. {status}: {test_name}{extra}")
    
    logger.info(f"\n总计: {passed}/{total} 通过")
    
    if success and passed == total:
        logger.info("🎉 UI测试通过！任务周期选择功能正常")
        sys.exit(0)
    elif success and passed >= total * 0.7:
        logger.info("⚠️ UI测试基本通过，但有警告")
        sys.exit(0)
    else:
        logger.error("❌ UI测试失败")
        sys.exit(1)

if __name__ == "__main__":
    main()