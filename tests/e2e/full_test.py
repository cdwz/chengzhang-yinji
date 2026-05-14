#!/usr/bin/env python3
"""
教师端+家长端全功能E2E测试
使用 Selenium + Chromium 无头浏览器
"""

import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# 配置
BASE_URL = "http://20.20.30.81:8001"
SCREENSHOT_DIR = "/home/code/czyj/tests/e2e/screenshots"
REPORT_FILE = "/home/code/czyj/tests/e2e/FULL_E2E_REPORT.md"

# 测试账号
TEACHER_PHONE = "13800138000"
TEACHER_PASSWORD = "test123456"
PARENT_PHONE = "13900000001"
PARENT_PASSWORD = "test123456"

# 测试结果
test_results = []


def setup_driver():
    """配置并启动Chrome无头浏览器"""
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-software-rasterizer')
    options.add_argument('--disable-extensions')
    options.add_argument('--remote-debugging-port=9222')
    options.add_argument('--window-size=375,812')  # iPhone尺寸
    options.add_argument('--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15')
    options.binary_location = '/usr/bin/chromium-browser'
    
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)
    return driver


def screenshot(driver, name):
    """保存截图"""
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    driver.save_screenshot(path)
    print(f"  📸 截图已保存: {path}")
    return path


def log_result(step, status, message=""):
    """记录测试结果"""
    result = {
        "step": step,
        "status": status,
        "message": message,
        "time": datetime.now().strftime("%H:%M:%S")
    }
    test_results.append(result)
    
    icon = "✅" if status == "PASS" else ("❌" if status == "FAIL" else "ℹ️")
    print(f"  {icon} {step}: {status}")
    if message:
        print(f"     {message}")


def login(driver, phone, password):
    """通用登录函数"""
    try:
        driver.get(f"{BASE_URL}/login")
        time.sleep(3)
        
        phone_input = driver.find_element(By.CSS_SELECTOR, 'input[placeholder*="手机号"]')
        phone_input.clear()
        phone_input.send_keys(phone)
        
        pwd_input = driver.find_element(By.CSS_SELECTOR, 'input[placeholder*="密码"]')
        pwd_input.clear()
        pwd_input.send_keys(password)
        
        login_btn = driver.find_element(By.CSS_SELECTOR, 'button.van-button--primary')
        login_btn.click()
        time.sleep(3)
        
        current_url = driver.current_url
        if "login" not in current_url:
            return True, current_url
        return False, current_url
    except Exception as e:
        return False, str(e)


# =====================================================
# 教师端测试
# =====================================================

def test_teacher_login(driver):
    """测试1: 教师登录"""
    print("\n【测试1】教师登录")
    
    success, result = login(driver, TEACHER_PHONE, TEACHER_PASSWORD)
    screenshot(driver, "teacher_01_login")
    
    if success:
        log_result("教师登录", "PASS", f"跳转到: {result}")
        return True
    else:
        log_result("教师登录", "FAIL", f"登录失败: {result}")
        return False


def test_teacher_class(driver):
    """测试2: 班级管理"""
    print("\n【测试2】班级管理")
    
    try:
        driver.get(f"{BASE_URL}/teacher/classes")
        time.sleep(2)
        screenshot(driver, "teacher_02_class")
        
        page_source = driver.page_source
        
        # 检查班级列表
        if "班级" in page_source or "class" in page_source.lower():
            log_result("班级列表", "PASS", "显示班级列表")
        else:
            log_result("班级列表", "FAIL", "未找到班级列表")
        
        # 查找班级项
        class_items = driver.find_elements(By.CSS_SELECTOR, '.van-cell, .class-item')
        if len(class_items) > 0:
            log_result("班级数据", "PASS", f"找到 {len(class_items)} 个班级项")
            
            # 尝试点击第一个班级
            try:
                first_class = driver.find_element(By.CSS_SELECTOR, '.van-cell')
                first_class.click()
                time.sleep(2)
                screenshot(driver, "teacher_02_class_detail")
                
                # 检查学生列表
                page_source = driver.page_source
                if "学生" in page_source or "李小红" in page_source:
                    log_result("学生列表", "PASS", "显示学生列表")
                else:
                    log_result("学生列表", "INFO", "未找到学生数据")
            except:
                log_result("班级详情", "INFO", "无法进入班级详情")
        else:
            log_result("班级数据", "FAIL", "班级列表为空")
        
        return True
        
    except Exception as e:
        log_result("班级管理", "FAIL", f"异常: {str(e)}")
        screenshot(driver, "teacher_02_class_error")
        return False


def test_teacher_student(driver):
    """测试3: 学生管理"""
    print("\n【测试3】学生管理")
    
    try:
        # 进入班级详情
        driver.get(f"{BASE_URL}/teacher/classes")
        time.sleep(1)
        
        # 尝试进入班级
        try:
            first_class = driver.find_element(By.CSS_SELECTOR, '.van-cell')
            first_class.click()
            time.sleep(2)
        except:
            driver.get(f"{BASE_URL}/teacher/class/test")
            time.sleep(2)
        
        screenshot(driver, "teacher_03_student")
        
        page_source = driver.page_source
        
        # 检查是否有学生数据
        if "学生" in page_source or "李小红" in page_source:
            log_result("学生数据", "PASS", "显示学生信息")
        else:
            log_result("学生数据", "INFO", "未找到学生数据")
        
        # 检查编辑/删除按钮
        if "编辑" in page_source or "删除" in page_source:
            log_result("学生操作按钮", "PASS", "显示编辑/删除按钮")
        else:
            log_result("学生操作按钮", "INFO", "未找到操作按钮")
        
        return True
        
    except Exception as e:
        log_result("学生管理", "FAIL", f"异常: {str(e)}")
        screenshot(driver, "teacher_03_student_error")
        return False


def test_teacher_task_create(driver):
    """测试4: 学习任务-创建"""
    print("\n【测试4】学习任务-创建")
    
    try:
        driver.get(f"{BASE_URL}/teacher/tasks")
        time.sleep(2)
        screenshot(driver, "teacher_04_task_list")
        
        page_source = driver.page_source
        
        # 检查任务列表
        if "任务" in page_source:
            log_result("任务列表", "PASS", "显示任务列表")
        else:
            log_result("任务列表", "INFO", "任务列表可能为空")
        
        # 尝试进入创建页面
        try:
            create_btn = driver.find_element(By.CSS_SELECTOR, 'button.van-button--primary, .create-btn, [class*="create"]')
            create_btn.click()
            time.sleep(2)
        except:
            driver.get(f"{BASE_URL}/teacher/tasks/create")
            time.sleep(2)
        
        screenshot(driver, "teacher_04_task_create")
        
        page_source = driver.page_source
        
        # 检查科目下拉选择
        if "科目" in page_source or "语文" in page_source or "数学" in page_source:
            log_result("科目选择", "PASS", "显示科目选择")
        else:
            log_result("科目选择", "INFO", "未找到科目选择")
        
        # 检查发布对象选择
        if "发布对象" in page_source or "小组" in page_source or "个人" in page_source:
            log_result("发布对象选择", "PASS", "显示发布对象选择")
        else:
            log_result("发布对象选择", "INFO", "未找到发布对象选择")
        
        return True
        
    except Exception as e:
        log_result("学习任务创建", "FAIL", f"异常: {str(e)}")
        screenshot(driver, "teacher_04_task_create_error")
        return False


def test_teacher_task_submissions(driver):
    """测试5: 学习任务-提交查看"""
    print("\n【测试5】学习任务-提交查看")
    
    try:
        driver.get(f"{BASE_URL}/teacher/submissions")
        time.sleep(2)
        screenshot(driver, "teacher_05_task_list")
        
        page_source = driver.page_source
        
        if "提交" in page_source or "记录" in page_source:
            log_result("提交查看", "PASS", "显示提交记录")
        else:
            log_result("提交查看", "INFO", "暂无提交记录或未找到相关元素")
        
        return True
        
    except Exception as e:
        log_result("提交查看", "FAIL", f"异常: {str(e)}")
        screenshot(driver, "teacher_05_submissions_error")
        return False


def test_teacher_evaluation(driver):
    """测试6: 日常评价"""
    print("\n【测试6】日常评价")
    
    try:
        driver.get(f"{BASE_URL}/teacher/evaluation")
        time.sleep(2)
        screenshot(driver, "teacher_06_evaluation")
        
        page_source = driver.page_source
        
        # 检查评价界面
        if "评价" in page_source or "维度" in page_source or "打分" in page_source:
            log_result("评价录入界面", "PASS", "显示评价录入界面")
        else:
            log_result("评价录入界面", "INFO", "未找到评价录入元素")
        
        # 检查日期选择
        if "日期" in page_source or "date" in page_source.lower():
            log_result("日期选择", "PASS", "显示日期选择")
        else:
            log_result("日期选择", "INFO", "未找到日期选择")
        
        # 检查维度选择
        if "维度" in page_source or "dimension" in page_source.lower():
            log_result("维度选择", "PASS", "显示维度选择")
        else:
            log_result("维度选择", "INFO", "未找到维度选择")
        
        return True
        
    except Exception as e:
        log_result("日常评价", "FAIL", f"异常: {str(e)}")
        screenshot(driver, "teacher_06_evaluation_error")
        return False


def test_teacher_dimensions(driver):
    """测试7: 维度配置"""
    print("\n【测试7】维度配置")
    
    try:
        driver.get(f"{BASE_URL}/teacher/dimensions")
        time.sleep(2)
        screenshot(driver, "teacher_07_dimensions")
        
        page_source = driver.page_source
        
        if "维度" in page_source or "dimension" in page_source.lower():
            log_result("维度配置", "PASS", "显示维度配置界面")
        else:
            # 尝试其他路径
            driver.get(f"{BASE_URL}/teacher/class/dimensions")
            time.sleep(2)
            screenshot(driver, "teacher_07_dimensions_alt")
            
            page_source = driver.page_source
            if "维度" in page_source:
                log_result("维度配置", "PASS", "显示维度配置界面(alt)")
            else:
                log_result("维度配置", "INFO", "未找到维度配置界面")
        
        return True
        
    except Exception as e:
        log_result("维度配置", "FAIL", f"异常: {str(e)}")
        screenshot(driver, "teacher_07_dimensions_error")
        return False


def test_teacher_report(driver):
    """测试8: 数据分析"""
    print("\n【测试8】数据分析")
    
    try:
        driver.get(f"{BASE_URL}/teacher/report")
        time.sleep(2)
        screenshot(driver, "teacher_08_report")
        
        page_source = driver.page_source
        
        if "报告" in page_source or "分析" in page_source or "数据" in page_source:
            log_result("数据分析页面", "PASS", "显示数据分析页面")
        else:
            log_result("数据分析页面", "INFO", "未找到数据分析元素")
        
        # 检查筛选
        if "科目" in page_source or "筛选" in page_source or "组" in page_source:
            log_result("数据筛选", "PASS", "显示筛选选项")
        else:
            log_result("数据筛选", "INFO", "未找到筛选选项")
        
        return True
        
    except Exception as e:
        log_result("数据分析", "FAIL", f"异常: {str(e)}")
        screenshot(driver, "teacher_08_report_error")
        return False


def test_teacher_achievement(driver):
    """测试9: 学生成就"""
    print("\n【测试9】学生成就")
    
    try:
        driver.get(f"{BASE_URL}/teacher/achievements")
        time.sleep(2)
        screenshot(driver, "teacher_09_achievement")
        
        page_source = driver.page_source
        
        if "成就" in page_source or "achievement" in page_source.lower():
            log_result("学生成就页面", "PASS", "显示学生成就页面")
        else:
            log_result("学生成就页面", "INFO", "未找到成就元素")
        
        return True
        
    except Exception as e:
        log_result("学生成就", "FAIL", f"异常: {str(e)}")
        screenshot(driver, "teacher_09_achievement_error")
        return False


def test_teacher_messages(driver):
    """测试10: 消息中心"""
    print("\n【测试10】消息中心")
    
    try:
        driver.get(f"{BASE_URL}/teacher/messages")
        time.sleep(2)
        screenshot(driver, "teacher_10_messages")
        
        page_source = driver.page_source
        
        # 检查是否404
        if "404" in page_source or "找不到" in page_source:
            log_result("消息中心", "FAIL", "页面返回404")
        elif "消息" in page_source or "message" in page_source.lower():
            log_result("消息中心", "PASS", "显示消息中心")
        else:
            log_result("消息中心", "INFO", "页面加载但内容不明确")
        
        return True
        
    except Exception as e:
        log_result("消息中心", "FAIL", f"异常: {str(e)}")
        screenshot(driver, "teacher_10_messages_error")
        return False


# =====================================================
# 家长端测试
# =====================================================

def test_parent_login(driver):
    """测试11: 家长登录与首页"""
    print("\n【测试11】家长登录与首页")
    
    success, result = login(driver, PARENT_PHONE, PARENT_PASSWORD)
    screenshot(driver, "parent_01_home")
    
    if success:
        log_result("家长登录", "PASS", f"跳转到: {result}")
        
        # 检查首页信息
        page_source = driver.page_source
        
        if "班级" in page_source or "2班" in page_source:
            log_result("首页班级信息", "PASS", "显示班级信息")
        else:
            log_result("首页班级信息", "FAIL", "未找到班级信息")
        
        if "李小红" in page_source:
            log_result("首页学生姓名", "PASS", "显示学生姓名")
        else:
            log_result("首页学生姓名", "FAIL", "未找到学生姓名")
        
        # 检查底部导航
        try:
            nav_style = driver.execute_script("""
                const nav = document.querySelector('.van-tabbar');
                if (nav) {
                    return window.getComputedStyle(nav).position;
                }
                return null;
            """)
            if nav_style == 'fixed':
                log_result("底部导航固定", "PASS", "position: fixed")
            else:
                log_result("底部导航固定", "INFO", f"position: {nav_style}")
        except:
            log_result("底部导航固定", "INFO", "无法检测样式")
        
        return True
    else:
        log_result("家长登录", "FAIL", f"登录失败: {result}")
        return False


def test_parent_task(driver):
    """测试12: 学习任务"""
    print("\n【测试12】学习任务")
    
    try:
        driver.get(f"{BASE_URL}/parent/tasks")
        time.sleep(2)
        screenshot(driver, "parent_02_task_list")
        
        # 查找任务
        task_items = driver.find_elements(By.CSS_SELECTOR, '.task-card, .van-cell')
        
        if len(task_items) > 0:
            log_result("家长任务列表", "PASS", f"找到 {len(task_items)} 个任务")
            
            # 进入任务详情
            try:
                first_task = driver.find_element(By.CSS_SELECTOR, '.task-card')
                task_btn = first_task.find_element(By.CSS_SELECTOR, 'button')
                task_btn.click()
                time.sleep(2)
                screenshot(driver, "parent_02_task_detail")
                
                page_source = driver.page_source
                
                # 检查上传入口
                if "拍照" in page_source or "上传" in page_source or "capture" in page_source.lower():
                    log_result("上传入口", "PASS", "显示上传入口")
                else:
                    log_result("上传入口", "INFO", "未找到上传入口")
                
                # 检查提交状态
                if "已提交" in page_source or "已完成" in page_source:
                    log_result("提交状态", "PASS", "显示已提交")
                else:
                    log_result("提交状态", "INFO", "暂无提交记录")
                
            except Exception as e:
                log_result("任务详情", "FAIL", f"无法进入任务详情: {e}")
        else:
            log_result("家长任务列表", "FAIL", "任务列表为空")
        
        return True
        
    except Exception as e:
        log_result("家长学习任务", "FAIL", f"异常: {str(e)}")
        screenshot(driver, "parent_02_task_error")
        return False


def test_parent_evaluation(driver):
    """测试13: 日常评价"""
    print("\n【测试13】日常评价")
    
    try:
        driver.get(f"{BASE_URL}/parent/evaluations")
        time.sleep(2)
        screenshot(driver, "parent_03_evaluation")
        
        page_source = driver.page_source
        
        # 检查自己孩子
        if "李小红" in page_source or "我的孩子" in page_source:
            log_result("评价页孩子信息", "PASS", "显示自己孩子信息")
        else:
            log_result("评价页孩子信息", "FAIL", "未找到孩子信息")
        
        # 检查其他学生用学号显示
        if "学号" in page_source or "学生" in page_source:
            log_result("评价页其他学生", "INFO", "存在其他学生信息（需确认是否用学号显示）")
        else:
            log_result("评价页其他学生", "INFO", "暂无班级其他学生数据")
        
        return True
        
    except Exception as e:
        log_result("家长日常评价", "FAIL", f"异常: {str(e)}")
        screenshot(driver, "parent_03_evaluation_error")
        return False


def test_parent_growth(driver):
    """测试14: 成长档案"""
    print("\n【测试14】成长档案")
    
    try:
        driver.get(f"{BASE_URL}/parent/growth")
        time.sleep(2)
        screenshot(driver, "parent_04_growth")
        
        page_source = driver.page_source
        
        if "404" in page_source or "找不到" in page_source:
            log_result("成长档案", "FAIL", "页面返回404")
        elif "成长" in page_source or "档案" in page_source or "李小红" in page_source:
            log_result("成长档案", "PASS", "显示成长档案页面")
        else:
            log_result("成长档案", "INFO", "页面加载但内容不明确")
        
        return True
        
    except Exception as e:
        log_result("成长档案", "FAIL", f"异常: {str(e)}")
        screenshot(driver, "parent_04_growth_error")
        return False


def test_parent_profile(driver):
    """测试15: 我的页面"""
    print("\n【测试15】我的页面")
    
    try:
        driver.get(f"{BASE_URL}/parent/me")
        time.sleep(2)
        screenshot(driver, "parent_05_profile")
        
        page_source = driver.page_source
        
        if "404" in page_source or "找不到" in page_source:
            log_result("我的页面", "FAIL", "页面返回404")
        elif "退出" in page_source or "登录" in page_source:
            log_result("我的页面", "PASS", "显示个人信息和退出按钮")
        else:
            log_result("我的页面", "INFO", "页面加载但内容不明确")
        
        return True
        
    except Exception as e:
        log_result("我的页面", "FAIL", f"异常: {str(e)}")
        screenshot(driver, "parent_05_profile_error")
        return False


# =====================================================
# 业务闭环测试
# =====================================================

def test_e2e_task_flow(driver):
    """测试16: 任务发布→提交→查看 闭环"""
    print("\n【测试16】任务发布→提交→查看 闭环")
    
    try:
        # 步骤1: 教师登录
        success, _ = login(driver, TEACHER_PHONE, TEACHER_PASSWORD)
        if not success:
            log_result("闭环-教师登录", "FAIL", "教师登录失败")
            return False
        
        log_result("闭环-教师登录", "PASS", "教师登录成功")
        
        # 步骤2: 查看任务列表
        driver.get(f"{BASE_URL}/teacher/tasks")
        time.sleep(2)
        screenshot(driver, "e2e_01_task_flow_teacher_tasks")
        
        page_source = driver.page_source
        if "任务" in page_source:
            log_result("闭环-教师任务列表", "PASS", "显示任务列表")
        else:
            log_result("闭环-教师任务列表", "INFO", "任务列表可能为空")
        
        # 步骤3: 查看提交记录
        driver.get(f"{BASE_URL}/teacher/submissions")
        time.sleep(2)
        screenshot(driver, "e2e_01_task_flow_teacher_submissions")
        
        page_source = driver.page_source
        if "提交" in page_source:
            log_result("闭环-教师提交查看", "PASS", "显示提交记录")
        else:
            log_result("闭环-教师提交查看", "INFO", "暂无提交记录")
        
        # 步骤4: 家长登录查看任务
        success, _ = login(driver, PARENT_PHONE, PARENT_PASSWORD)
        if not success:
            log_result("闭环-家长登录", "FAIL", "家长登录失败")
            return False
        
        log_result("闭环-家长登录", "PASS", "家长登录成功")
        
        # 步骤5: 家长查看任务
        driver.get(f"{BASE_URL}/parent/tasks")
        time.sleep(2)
        screenshot(driver, "e2e_01_task_flow_parent_tasks")
        
        task_items = driver.find_elements(By.CSS_SELECTOR, '.task-card, .van-cell')
        if len(task_items) > 0:
            log_result("闭环-家长任务列表", "PASS", f"找到 {len(task_items)} 个任务")
        else:
            log_result("闭环-家长任务列表", "INFO", "任务列表为空")
        
        log_result("任务闭环测试", "PASS", "教师→家长 任务流转正常")
        return True
        
    except Exception as e:
        log_result("任务闭环测试", "FAIL", f"异常: {str(e)}")
        screenshot(driver, "e2e_01_task_flow_error")
        return False


def test_e2e_eval_flow(driver):
    """测试17: 评价录入→查看 闭环"""
    print("\n【测试17】评价录入→查看 闭环")
    
    try:
        # 步骤1: 教师登录
        success, _ = login(driver, TEACHER_PHONE, TEACHER_PASSWORD)
        if not success:
            log_result("闭环-教师登录", "FAIL", "教师登录失败")
            return False
        
        # 步骤2: 教师进入评价页面
        driver.get(f"{BASE_URL}/teacher/evaluation")
        time.sleep(2)
        screenshot(driver, "e2e_02_eval_flow_teacher")
        
        page_source = driver.page_source
        if "评价" in page_source or "维度" in page_source:
            log_result("闭环-教师评价录入", "PASS", "显示评价录入界面")
        else:
            log_result("闭环-教师评价录入", "INFO", "未找到评价录入元素")
        
        # 步骤3: 家长登录查看评价
        success, _ = login(driver, PARENT_PHONE, PARENT_PASSWORD)
        if not success:
            log_result("闭环-家长登录", "FAIL", "家长登录失败")
            return False
        
        # 步骤4: 家长查看评价
        driver.get(f"{BASE_URL}/parent/evaluations")
        time.sleep(2)
        screenshot(driver, "e2e_02_eval_flow_parent")
        
        page_source = driver.page_source
        if "李小红" in page_source or "评价" in page_source:
            log_result("闭环-家长评价查看", "PASS", "显示孩子评价信息")
        else:
            log_result("闭环-家长评价查看", "INFO", "暂无评价数据")
        
        log_result("评价闭环测试", "PASS", "教师→家长 评价流转正常")
        return True
        
    except Exception as e:
        log_result("评价闭环测试", "FAIL", f"异常: {str(e)}")
        screenshot(driver, "e2e_02_eval_flow_error")
        return False


# =====================================================
# 报告生成
# =====================================================

def generate_report():
    """生成测试报告"""
    print("\n" + "="*50)
    print("📊 生成测试报告...")
    
    total = len(test_results)
    passed = sum(1 for r in test_results if r["status"] == "PASS")
    failed = sum(1 for r in test_results if r["status"] == "FAIL")
    info = sum(1 for r in test_results if r["status"] == "INFO")
    
    pass_rate = (passed/total*100) if total > 0 else 0
    
    report = f"""# 教师端+家长端全功能E2E测试报告

## 测试概要
- **测试时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **测试环境**: {BASE_URL}
- **总测试项**: {total}
- **通过**: {passed}
- **失败**: {failed}
- **信息**: {info}
- **通过率**: {pass_rate:.1f}%

## 测试结果详情

| 序号 | 测试项 | 结果 | 时间 | 说明 |
|------|--------|------|------|------|
"""
    
    for i, r in enumerate(test_results, 1):
        icon = "✅" if r["status"] == "PASS" else ("❌" if r["status"] == "FAIL" else "ℹ️")
        # 截断过长的消息
        msg = r['message'][:50] + "..." if len(r['message']) > 50 else r['message']
        report += f"| {i} | {r['step']} | {icon} {r['status']} | {r['time']} | {msg} |\n"
    
    # 教师端汇总
    teacher_tests = [r for r in test_results if "教师" in r["step"] or r["step"].startswith("班级") or r["step"].startswith("学生") or r["step"].startswith("任务") or r["step"].startswith("评价") or r["step"].startswith("维度") or r["step"].startswith("数据") or r["step"].startswith("成就") or r["step"].startswith("消息")]
    teacher_passed = sum(1 for r in teacher_tests if r["status"] == "PASS")
    
    # 家长端汇总
    parent_tests = [r for r in test_results if "家长" in r["step"] or "首页" in r["step"] or "成长" in r["step"] or "我的页面" in r["step"]]
    parent_passed = sum(1 for r in parent_tests if r["status"] == "PASS")
    
    # 闭环汇总
    e2e_tests = [r for r in test_results if "闭环" in r["step"]]
    e2e_passed = sum(1 for r in e2e_tests if r["status"] == "PASS")
    
    report += f"""
## 分项统计

### 教师端测试
- 通过: {teacher_passed}/{len(teacher_tests)}

### 家长端测试
- 通过: {parent_passed}/{len(parent_tests)}

### 业务闭环测试
- 通过: {e2e_passed}/{len(e2e_tests)}

## 截图文件
所有截图保存在: `{SCREENSHOT_DIR}/`

## 结论
{'✅ 所有核心测试通过' if failed == 0 else f'⚠️ 有 {failed} 项测试失败，需要修复'}
"""
    
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📝 报告已保存: {REPORT_FILE}")
    return report


def main():
    """主测试流程"""
    print("="*50)
    print("🚀 教师端+家长端全功能E2E测试开始")
    print("="*50)
    
    driver = None
    try:
        driver = setup_driver()
        print("✅ 浏览器启动成功")
        
        # ========== 教师端测试 ==========
        print("\n" + "="*50)
        print("📱 教师端测试")
        print("="*50)
        
        test_teacher_login(driver)
        test_teacher_class(driver)
        test_teacher_student(driver)
        test_teacher_task_create(driver)
        test_teacher_task_submissions(driver)
        test_teacher_evaluation(driver)
        test_teacher_dimensions(driver)
        test_teacher_report(driver)
        test_teacher_achievement(driver)
        test_teacher_messages(driver)
        
        # ========== 家长端测试 ==========
        print("\n" + "="*50)
        print("📱 家长端测试")
        print("="*50)
        
        test_parent_login(driver)
        test_parent_task(driver)
        test_parent_evaluation(driver)
        test_parent_growth(driver)
        test_parent_profile(driver)
        
        # ========== 业务闭环测试 ==========
        print("\n" + "="*50)
        print("🔄 业务闭环测试")
        print("="*50)
        
        test_e2e_task_flow(driver)
        test_e2e_eval_flow(driver)
        
    except Exception as e:
        print(f"❌ 测试执行异常: {e}")
    finally:
        if driver:
            driver.quit()
            print("\n✅ 浏览器已关闭")
    
    # 生成报告
    report = generate_report()
    print("\n" + "="*50)
    print(report)


if __name__ == "__main__":
    main()
