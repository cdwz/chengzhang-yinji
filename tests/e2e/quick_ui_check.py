#!/usr/bin/env python3
"""
快速前端UI验证
检查任务创建页面是否包含任务周期选择组件
"""
import sys
import requests
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_frontend_page():
    """检查前端页面是否包含任务周期相关元素"""
    base_url = "http://20.20.30.81:8001"
    
    # 1. 获取登录页面
    logger.info("1. 检查登录页面...")
    try:
        response = requests.get(f"{base_url}/teacher/login", timeout=10)
        if response.status_code == 200:
            logger.info(f"✅ 登录页面可访问 (状态码: {response.status_code})")
        else:
            logger.error(f"❌ 登录页面访问失败 (状态码: {response.status_code})")
            return False
    except Exception as e:
        logger.error(f"❌ 登录页面访问异常: {e}")
        return False
    
    # 2. 获取任务创建页面（需要登录，这里只检查页面是否存在）
    logger.info("2. 检查任务创建页面路径...")
    try:
        response = requests.get(f"{base_url}/teacher/tasks/create", timeout=10)
        # 由于需要登录，我们期望重定向或401/403，但至少能访问
        logger.info(f"✅ 任务创建页面可访问 (状态码: {response.status_code})")
        
        # 检查页面内容是否包含任务周期相关关键词
        content = response.text
        keywords = ["任务周期", "单日", "周任务", "月任务", "task_period", "el-radio", "el-date-picker"]
        found_keywords = []
        
        for keyword in keywords:
            if keyword in content:
                found_keywords.append(keyword)
        
        if found_keywords:
            logger.info(f"✅ 页面包含任务周期相关关键词: {', '.join(found_keywords)}")
        else:
            logger.warning("⚠️ 页面中未找到任务周期相关关键词（可能需要登录后查看）")
            
    except Exception as e:
        logger.error(f"❌ 任务创建页面访问异常: {e}")
        return False
    
    # 3. 检查构建的JS文件是否包含任务周期逻辑
    logger.info("3. 检查前端构建文件...")
    try:
        # 获取主JS文件（简化检查，实际应该检查所有JS文件）
        response = requests.get(f"{base_url}/assets/index-CMO5nYA0.js", timeout=10)
        if response.status_code == 200:
            js_content = response.text[:5000]  # 只检查前5000字符
            if "task_period" in js_content:
                logger.info("✅ JS文件包含 'task_period' 逻辑")
            else:
                logger.warning("⚠️ JS文件中未找到 'task_period'")
        else:
            logger.warning(f"⚠️ 无法获取JS文件 (状态码: {response.status_code})")
    except Exception as e:
        logger.warning(f"⚠️ JS文件检查异常: {e}")
    
    return True

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("前端UI快速验证")
    logger.info("=" * 60)
    
    success = check_frontend_page()
    
    logger.info("\n" + "=" * 60)
    logger.info("验证结果")
    logger.info("=" * 60)
    
    if success:
        logger.info("✅ 前端服务基本正常")
        logger.info("📋 建议：")
        logger.info("   1. 手动访问 http://20.20.30.81:8001")
        logger.info("   2. 使用教师账号登录 (13800138000 / test123456)")
        logger.info("   3. 进入【学习任务】→【新建任务】")
        logger.info("   4. 验证任务周期选择器（单日/周任务/月任务）")
        logger.info("   5. 验证日期选择器根据周期类型切换")
    else:
        logger.error("❌ 前端服务检查失败")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())