#!/usr/bin/env python3
"""
任务日期三种模式 E2E 测试
验证单日/周/月三种任务周期模式的功能
"""
import os
import sys
import time
import requests
import logging
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TaskPeriodTest:
    """任务周期功能测试"""
    
    def __init__(self, base_url="http://20.20.30.81:8001"):
        self.base_url = base_url
        self.driver = None
        self.session = requests.Session()
        self.test_results = []
        
        # 测试账号
        self.teacher_phone = "13800138000"
        self.teacher_password = "test123456"
        
        # API端点
        self.login_url = f"{base_url}/api/auth/login"
        self.tasks_url = f"{base_url}/api/tasks"
        
    def setup_driver(self):
        """设置Chrome无头浏览器"""
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        logger.info("Chrome无头浏览器启动成功")
        
    def teardown_driver(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            logger.info("浏览器已关闭")
            
    def api_login(self):
        """API登录获取token"""
        try:
            payload = {
                "phone": self.teacher_phone,
                "password": self.teacher_password
            }
            response = self.session.post(self.login_url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {token}"})
                logger.info("API登录成功")
                return True
            else:
                logger.error(f"API登录失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"API登录异常: {e}")
            return False
    
    def get_classes(self):
        """获取班级列表"""
        try:
            response = self.session.get(f"{self.base_url}/api/schools/classes")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"获取到 {len(data)} 个班级")
                return data
            else:
                logger.error(f"获取班级失败: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"获取班级异常: {e}")
            return []
    
    def create_task_via_api(self, task_data):
        """通过API创建任务"""
        try:
            response = self.session.post(self.tasks_url, json=task_data)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"API创建任务成功: ID={data['id']}")
                return data
            else:
                logger.error(f"API创建任务失败: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"API创建任务异常: {e}")
            return None
    
    def test_day_task(self):
        """测试单日任务"""
        logger.info("开始测试单日任务...")
        
        classes = self.get_classes()
        if not classes:
            logger.error("无法获取班级列表，跳过单日任务测试")
            return False
        
        class_data = classes[0]
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        task_data = {
            "class_id": class_data["id"],
            "subject": "语文",
            "title": f"单日任务测试-{datetime.now().strftime('%H%M%S')}",
            "content": "这是单日任务测试内容",
            "suggested_duration": 30,
            "task_date": tomorrow,
            "task_period": "day",
            "target_type": "all"
        }
        
        result = self.create_task_via_api(task_data)
        if result and "task_period" in result:
            logger.info(f"单日任务创建成功，task_period={result['task_period']}")
            self.test_results.append({"test": "单日任务API创建", "status": "PASS", "task_period": result["task_period"]})
            return True
        else:
            logger.error("单日任务创建失败")
            self.test_results.append({"test": "单日任务API创建", "status": "FAIL", "error": "API返回失败"})
            return False
    
    def test_week_task(self):
        """测试周任务"""
        logger.info("开始测试周任务...")
        
        classes = self.get_classes()
        if not classes:
            logger.error("无法获取班级列表，跳过周任务测试")
            return False
        
        class_data = classes[0]
        # 获取下周一
        today = datetime.now()
        days_ahead = (7 - today.weekday()) % 7  # 0=周一, 6=周日
        if days_ahead == 0:
            days_ahead = 7  # 如果今天是周一，就选下周一
        next_monday = today + timedelta(days=days_ahead)
        
        task_data = {
            "class_id": class_data["id"],
            "subject": "数学",
            "title": f"周任务测试-{datetime.now().strftime('%H%M%S')}",
            "content": "这是周任务测试内容",
            "suggested_duration": 60,
            "task_date": next_monday.strftime("%Y-%m-%d"),
            "task_period": "week",
            "target_type": "all"
        }
        
        result = self.create_task_via_api(task_data)
        if result and result.get("task_period") == "week":
            logger.info(f"周任务创建成功，task_period={result['task_period']}")
            self.test_results.append({"test": "周任务API创建", "status": "PASS", "task_period": result["task_period"]})
            return True
        else:
            logger.error("周任务创建失败")
            self.test_results.append({"test": "周任务API创建", "status": "FAIL", "error": "API返回失败或task_period不正确"})
            return False
    
    def test_month_task(self):
        """测试月任务"""
        logger.info("开始测试月任务...")
        
        classes = self.get_classes()
        if not classes:
            logger.error("无法获取班级列表，跳过月任务测试")
            return False
        
        class_data = classes[0]
        # 获取下个月1号
        today = datetime.now()
        if today.month == 12:
            next_month = datetime(today.year + 1, 1, 1)
        else:
            next_month = datetime(today.year, today.month + 1, 1)
        
        task_data = {
            "class_id": class_data["id"],
            "subject": "英语",
            "title": f"月任务测试-{datetime.now().strftime('%H%M%S')}",
            "content": "这是月任务测试内容",
            "suggested_duration": 45,
            "task_date": next_month.strftime("%Y-%m-%d"),
            "task_period": "month",
            "target_type": "all"
        }
        
        result = self.create_task_via_api(task_data)
        if result and result.get("task_period") == "month":
            logger.info(f"月任务创建成功，task_period={result['task_period']}")
            self.test_results.append({"test": "月任务API创建", "status": "PASS", "task_period": result["task_period"]})
            return True
        else:
            logger.error("月任务创建失败")
            self.test_results.append({"test": "月任务API创建", "status": "FAIL", "error": "API返回失败或task_period不正确"})
            return False
    
    def test_ui_period_selection(self):
        """测试UI界面三种日期模式切换"""
        logger.info("开始测试UI界面日期模式切换...")
        
        try:
            # 打开登录页面
            self.driver.get(f"{self.base_url}/teacher/login")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "phone"))
            )
            
            # 登录
            phone_input = self.driver.find_element(By.ID, "phone")
            password_input = self.driver.find_element(By.ID, "password")
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            
            phone_input.send_keys(self.teacher_phone)
            password_input.send_keys(self.teacher_password)
            login_button.click()
            
            # 等待跳转到教师首页
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".teacher-dashboard"))
            )
            
            # 导航到任务发布页面
            self.driver.get(f"{self.base_url}/teacher/tasks/create")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".create-task"))
            )
            
            # 检查单日模式默认选中
            day_radio = self.driver.find_element(By.XPATH, "//span[contains(text(), '单日')]/preceding-sibling::span[contains(@class, 'el-radio__input')]")
            if "is-checked" in day_radio.get_attribute("class"):
                logger.info("单日模式默认选中 ✔")
                self.test_results.append({"test": "UI单日模式默认选中", "status": "PASS"})
            else:
                logger.error("单日模式未默认选中 ✗")
                self.test_results.append({"test": "UI单日模式默认选中", "status": "FAIL"})
            
            # 检查日期选择器类型
            date_picker = self.driver.find_element(By.CSS_SELECTOR, ".el-date-picker")
            if date_picker:
                logger.info("日期选择器存在 ✔")
                self.test_results.append({"test": "日期选择器存在", "status": "PASS"})
            else:
                logger.error("日期选择器不存在 ✗")
                self.test_results.append({"test": "日期选择器存在", "status": "FAIL"})
            
            # 切换到周模式
            week_radio = self.driver.find_element(By.XPATH, "//span[contains(text(), '周任务')]/preceding-sibling::span[contains(@class, 'el-radio__input')]")
            week_radio.click()
            time.sleep(1)
            
            # 检查周选择器
            week_hint = self.driver.find_elements(By.CLASS_NAME, "period-hint")
            if week_hint:
                logger.info("周模式切换成功，周期提示存在 ✔")
                self.test_results.append({"test": "UI周模式切换", "status": "PASS"})
            else:
                logger.error("周模式切换失败 ✗")
                self.test_results.append({"test": "UI周模式切换", "status": "FAIL"})
            
            # 切换到月模式
            month_radio = self.driver.find_element(By.XPATH, "//span[contains(text(), '月任务')]/preceding-sibling::span[contains(@class, 'el-radio__input')]")
            month_radio.click()
            time.sleep(1)
            
            # 检查月选择器
            month_hint = self.driver.find_elements(By.CLASS_NAME, "period-hint")
            if month_hint:
                logger.info("月模式切换成功，周期提示存在 ✔")
                self.test_results.append({"test": "UI月模式切换", "status": "PASS"})
            else:
                logger.error("月模式切换失败 ✗")
                self.test_results.append({"test": "UI月模式切换", "status": "FAIL"})
            
            return True
            
        except Exception as e:
            logger.error(f"UI测试异常: {e}")
            self.test_results.append({"test": "UI界面测试", "status": "FAIL", "error": str(e)})
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        logger.info("=" * 60)
        logger.info("开始任务日期三种模式E2E测试")
        logger.info("=" * 60)
        
        # API测试
        if not self.api_login():
            logger.error("API登录失败，无法继续测试")
            return False
        
        # API创建任务测试
        api_tests = [
            self.test_day_task,
            self.test_week_task,
            self.test_month_task
        ]
        
        for test_func in api_tests:
            try:
                test_func()
            except Exception as e:
                logger.error(f"测试函数执行异常: {e}")
        
        # UI测试
        try:
            self.setup_driver()
            self.test_ui_period_selection()
        except Exception as e:
            logger.error(f"UI测试设置异常: {e}")
        finally:
            self.teardown_driver()
        
        # 输出测试结果
        self.print_results()
        
        # 统计成功率
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed = total - passed
        
        logger.info(f"\n测试完成: {passed}/{total} 通过 ({passed/total*100:.1f}%)")
        
        return failed == 0
    
    def print_results(self):
        """打印测试结果"""
        logger.info("\n" + "=" * 60)
        logger.info("测试结果汇总")
        logger.info("=" * 60)
        
        for i, result in enumerate(self.test_results, 1):
            status = "✅ PASS" if result["status"] == "PASS" else "❌ FAIL"
            test_name = result["test"]
            extra = ""
            
            if "task_period" in result:
                extra = f" (task_period={result['task_period']})"
            elif "error" in result:
                extra = f" (错误: {result['error']})"
            
            logger.info(f"{i:2d}. {status}: {test_name}{extra}")


def main():
    """主函数"""
    tester = TaskPeriodTest()
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"测试执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()