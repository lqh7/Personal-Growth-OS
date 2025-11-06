"""
生成测试任务数据用于测试分页功能

运行方式:
    cd backend
    python generate_test_tasks.py
"""
import requests
from datetime import datetime, timedelta
import random

# API配置
BASE_URL = "http://localhost:8000"
PROJECT_ID = 1

# 任务标题模板
TASK_TITLES = [
    "完成项目文档",
    "代码审查",
    "修复Bug",
    "编写单元测试",
    "优化性能",
    "更新依赖",
    "重构代码",
    "数据库迁移",
    "API设计",
    "UI优化",
    "安全审计",
    "部署上线",
    "监控告警",
    "日志分析",
    "用户调研",
    "需求评审",
    "技术方案设计",
    "代码规范检查",
    "集成测试",
    "压力测试",
]

# 任务描述模板
TASK_DESCRIPTIONS = [
    "这是一个重要任务,需要认真完成",
    "按照计划推进,注意时间节点",
    "与团队协作,确保质量",
    "优先级较高,尽快处理",
    "参考之前的实现经验",
    "注意边界条件和异常处理",
    "完成后需要进行充分测试",
    "做好文档记录",
]

# 状态选项
STATUSES = ["pending", "in_progress", "completed"]


def generate_task_data(index: int):
    """生成单个任务数据"""
    now = datetime.now()

    # 随机选择标题和描述
    title = f"{random.choice(TASK_TITLES)} #{index}"
    description = random.choice(TASK_DESCRIPTIONS)

    # 随机生成时间
    # start_time: 过去7天到未来7天
    start_offset = random.randint(-7, 7)
    start_time = now + timedelta(days=start_offset, hours=random.randint(0, 23))

    # end_time: start_time + 1-4小时
    duration = random.randint(1, 4)
    end_time = start_time + timedelta(hours=duration)

    # 随机优先级 (1-5)
    priority = random.randint(1, 5)

    # 随机状态(70%待办,20%进行中,10%已完成)
    status_random = random.random()
    if status_random < 0.7:
        status = "pending"
    elif status_random < 0.9:
        status = "in_progress"
    else:
        status = "completed"

    return {
        "title": title,
        "description": description,
        "project_id": PROJECT_ID,
        "priority": priority,
        "status": status,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "estimated_hours": float(duration)
    }


def create_task(task_data: dict):
    """创建单个任务"""
    url = f"{BASE_URL}/api/tasks/"
    try:
        response = requests.post(url, json=task_data, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"创建任务失败: {e}")
        return None


def main():
    """主函数:生成50个测试任务"""
    print(f"开始生成测试任务...")
    print(f"目标: 50个任务")
    print("-" * 50)

    success_count = 0
    fail_count = 0

    for i in range(1, 51):
        task_data = generate_task_data(i)
        print(f"[{i}/50] 创建任务: {task_data['title']} (优先级: {task_data['priority']}, 状态: {task_data['status']})")

        result = create_task(task_data)
        if result:
            success_count += 1
            print(f"  [OK] 成功创建 (ID: {result['id']})")
        else:
            fail_count += 1
            print(f"  [FAIL] 创建失败")

    print("-" * 50)
    print(f"完成! 成功: {success_count}, 失败: {fail_count}")

    # 验证数据
    verify_url = f"{BASE_URL}/api/tasks/?page=1&page_size=15"
    try:
        response = requests.get(verify_url, timeout=5)
        response.raise_for_status()
        data = response.json()
        total = data["pagination"]["total"]
        print(f"\n数据库中共有 {total} 个任务")
        print(f"分页测试: 第1页显示 {len(data['items'])} 个任务")
    except requests.exceptions.RequestException as e:
        print(f"验证失败: {e}")


if __name__ == "__main__":
    main()
