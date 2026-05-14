#!/usr/bin/env python3
"""
任务日期三种模式 API 测试
验证单日/周/月三种任务周期模式的API功能
"""
import sys
import time
import requests
import logging
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_task_period_api():
    """测试任务周期API功能"""
    base_url = "http://20.20.30.81:8000"  # 后端API地址
    session = requests.Session()
    test_results = []
    
    # 1. 登录
    logger.info("1. 教师登录...")
    login_url = f"{base_url}/api/auth/login"
    login_data = {
        "phone": "13800138000",
        "password": "test123456"
    }
    
    try:
        response = session.post(login_url, json=login_data)
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            session.headers.update({"Authorization": f"Bearer {token}"})
            logger.info(f"✅ 登录成功，token: {token[:20]}...")
            test_results.append({"test": "教师登录", "status": "PASS"})
        else:
            logger.error(f"❌ 登录失败: {response.status_code} - {response.text}")
            test_results.append({"test": "教师登录", "status": "FAIL", "error": response.text})
            return False, test_results
    except Exception as e:
        logger.error(f"❌ 登录异常: {e}")
        test_results.append({"test": "教师登录", "status": "FAIL", "error": str(e)})
        return False, test_results
    
    # 2. 获取班级
    logger.info("2. 获取班级列表...")
    classes_url = f"{base_url}/api/schools/classes"
    
    try:
        response = session.get(classes_url)
        if response.status_code == 200:
            classes = response.json()
            if len(classes) > 0:
                class_data = classes[0]
                logger.info(f"✅ 获取到班级: {class_data['name']}")
                test_results.append({"test": "获取班级", "status": "PASS", "class": class_data['name']})
            else:
                logger.error("❌ 未获取到班级")
                test_results.append({"test": "获取班级", "status": "FAIL", "error": "班级列表为空"})
                return False, test_results
        else:
            logger.error(f"❌ 获取班级失败: {response.status_code} - {response.text}")
            test_results.append({"test": "获取班级", "status": "FAIL", "error": response.text})
            return False, test_results
    except Exception as e:
        logger.error(f"❌ 获取班级异常: {e}")
        test_results.append({"test": "获取班级", "status": "FAIL", "error": str(e)})
        return False, test_results
    
    # 3. 测试单日任务
    logger.info("3. 测试单日任务创建...")
    tasks_url = f"{base_url}/api/tasks"
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    day_task_data = {
        "class_id": class_data["id"],
        "subject": "语文",
        "title": f"单日任务API测试-{datetime.now().strftime('%H%M%S')}",
        "content": "这是单日任务API测试内容",
        "suggested_duration": 30,
        "task_date": tomorrow,
        "task_period": "day",
        "target_type": "all"
    }
    
    try:
        response = session.post(tasks_url, json=day_task_data)
        if response.status_code == 200:
            data = response.json()
            if data.get("task_period") == "day":
                logger.info(f"✅ 单日任务创建成功，ID: {data['id']}, task_period: {data['task_period']}")
                test_results.append({"test": "单日任务创建", "status": "PASS", "task_period": data['task_period']})
            else:
                logger.error(f"❌ 单日任务task_period不正确: {data.get('task_period')}")
                test_results.append({"test": "单日任务创建", "status": "FAIL", "error": f"task_period不正确: {data.get('task_period')}"})
        else:
            logger.error(f"❌ 单日任务创建失败: {response.status_code} - {response.text}")
            test_results.append({"test": "单日任务创建", "status": "FAIL", "error": response.text})
    except Exception as e:
        logger.error(f"❌ 单日任务创建异常: {e}")
        test_results.append({"test": "单日任务创建", "status": "FAIL", "error": str(e)})
    
    # 4. 测试周任务
    logger.info("4. 测试周任务创建...")
    
    # 获取下周一
    today = datetime.now()
    days_ahead = (7 - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    next_monday = today + timedelta(days=days_ahead)
    
    week_task_data = {
        "class_id": class_data["id"],
        "subject": "数学",
        "title": f"周任务API测试-{datetime.now().strftime('%H%M%S')}",
        "content": "这是周任务API测试内容",
        "suggested_duration": 45,
        "task_date": next_monday.strftime("%Y-%m-%d"),
        "task_period": "week",
        "target_type": "all"
    }
    
    try:
        response = session.post(tasks_url, json=week_task_data)
        if response.status_code == 200:
            data = response.json()
            if data.get("task_period") == "week":
                logger.info(f"✅ 周任务创建成功，ID: {data['id']}, task_period: {data['task_period']}")
                test_results.append({"test": "周任务创建", "status": "PASS", "task_period": data['task_period']})
            else:
                logger.error(f"❌ 周任务task_period不正确: {data.get('task_period')}")
                test_results.append({"test": "周任务创建", "status": "FAIL", "error": f"task_period不正确: {data.get('task_period')}"})
        else:
            logger.error(f"❌ 周任务创建失败: {response.status_code} - {response.text}")
            test_results.append({"test": "周任务创建", "status": "FAIL", "error": response.text})
    except Exception as e:
        logger.error(f"❌ 周任务创建异常: {e}")
        test_results.append({"test": "周任务创建", "status": "FAIL", "error": str(e)})
    
    # 5. 测试月任务
    logger.info("5. 测试月任务创建...")
    
    # 获取下个月1号
    if today.month == 12:
        next_month = datetime(today.year + 1, 1, 1)
    else:
        next_month = datetime(today.year, today.month + 1, 1)
    
    month_task_data = {
        "class_id": class_data["id"],
        "subject": "英语",
        "title": f"月任务API测试-{datetime.now().strftime('%H%M%S')}",
        "content": "这是月任务API测试内容",
        "suggested_duration": 50,
        "task_date": next_month.strftime("%Y-%m-%d"),
        "task_period": "month",
        "target_type": "all"
    }
    
    try:
        response = session.post(tasks_url, json=month_task_data)
        if response.status_code == 200:
            data = response.json()
            if data.get("task_period") == "month":
                logger.info(f"✅ 月任务创建成功，ID: {data['id']}, task_period: {data['task_period']}")
                test_results.append({"test": "月任务创建", "status": "PASS", "task_period": data['task_period']})
            else:
                logger.error(f"❌ 月任务task_period不正确: {data.get('task_period')}")
                test_results.append({"test": "月任务创建", "status": "FAIL", "error": f"task_period不正确: {data.get('task_period')}"})
        else:
            logger.error(f"❌ 月任务创建失败: {response.status_code} - {response.text}")
            test_results.append({"test": "月任务创建", "status": "FAIL", "error": response.text})
    except Exception as e:
        logger.error(f"❌ 月任务创建异常: {e}")
        test_results.append({"test": "月任务创建", "status": "FAIL", "error": str(e)})
    
    # 6. 验证任务列表包含task_period字段
    logger.info("6. 验证任务列表API返回task_period字段...")
    
    try:
        response = session.get(tasks_url, params={"class_id": class_data["id"], "page_size": 10})
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                has_task_period = all("task_period" in task for task in data[:3])  # 检查前3个任务
                if has_task_period:
                    logger.info(f"✅ 任务列表包含task_period字段，共{len(data)}个任务")
                    test_results.append({"test": "任务列表包含task_period", "status": "PASS", "count": len(data)})
                    
                    # 打印最近创建的任务
                    for i, task in enumerate(data[:3]):
                        logger.info(f"   任务{i+1}: {task['title'][:20]}... - task_period: {task.get('task_period', '未设置')}")
                else:
                    logger.error("❌ 任务列表缺少task_period字段")
                    test_results.append({"test": "任务列表包含task_period", "status": "FAIL", "error": "缺少task_period字段"})
            else:
                logger.error("❌ 任务列表为空或格式不正确")
                test_results.append({"test": "任务列表包含task_period", "status": "FAIL", "error": "列表为空"})
        else:
            logger.error(f"❌ 获取任务列表失败: {response.status_code} - {response.text}")
            test_results.append({"test": "任务列表包含task_period", "status": "FAIL", "error": response.text})
    except Exception as e:
        logger.error(f"❌ 获取任务列表异常: {e}")
        test_results.append({"test": "任务列表包含task_period", "status": "FAIL", "error": str(e)})
    
    return True, test_results

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("任务日期三种模式API测试")
    logger.info("=" * 60)
    
    success, results = test_task_period_api()
    
    # 输出测试结果
    logger.info("\n" + "=" * 60)
    logger.info("测试结果汇总")
    logger.info("=" * 60)
    
    passed = sum(1 for r in results if r["status"] == "PASS")
    total = len(results)
    
    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result["status"] == "PASS" else "❌ FAIL"
        test_name = result["test"]
        extra = ""
        
        if "task_period" in result:
            extra = f" (task_period={result['task_period']})"
        elif "class" in result:
            extra = f" (班级: {result['class']})"
        elif "count" in result:
            extra = f" (任务数: {result['count']})"
        elif "error" in result:
            extra = f" (错误: {result['error'][:50]})"
        
        logger.info(f"{i:2d}. {status}: {test_name}{extra}")
    
    logger.info(f"\n总计: {passed}/{total} 通过 ({passed/total*100:.1f}%)")
    
    if passed == total:
        logger.info("🎉 所有测试通过！")
        sys.exit(0)
    else:
        logger.warning("⚠️ 部分测试失败")
        sys.exit(1)

if __name__ == "__main__":
    main()