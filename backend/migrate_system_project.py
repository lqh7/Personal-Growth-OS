#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：添加is_system字段并更新默认项目

执行步骤：
1. 为projects表添加is_system字段
2. 将ID=1的项目名称改为"默认"并标记为系统项目
"""
import sqlite3
import sys

def migrate():
    """执行数据库迁移"""
    db_path = 'personal_growth_os.db'

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 步骤1：检查is_system字段是否已存在
        cursor.execute("PRAGMA table_info(projects)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'is_system' not in columns:
            print("添加is_system字段...")
            cursor.execute('''
                ALTER TABLE projects
                ADD COLUMN is_system BOOLEAN DEFAULT 0
            ''')
            print("✓ is_system字段添加成功")
        else:
            print("⚠ is_system字段已存在，跳过添加")

        # 步骤2：更新ID=1的项目
        cursor.execute("SELECT id, name FROM projects WHERE id = 1")
        project = cursor.fetchone()

        if project:
            print(f"\n当前ID=1的项目: {project[1]}")
            cursor.execute('''
                UPDATE projects
                SET name = '默认', is_system = 1
                WHERE id = 1
            ''')
            print("✓ 已将ID=1的项目更新为'默认'并标记为系统项目")
        else:
            # 如果不存在ID=1的项目，创建一个
            print("\n⚠ 未找到ID=1的项目，创建默认项目...")
            cursor.execute('''
                INSERT INTO projects (id, name, description, color, is_system, created_at, updated_at)
                VALUES (1, '默认', '系统默认项目', '#667eea', 1, datetime('now'), datetime('now'))
            ''')
            print("✓ 默认项目创建成功")

        # 提交更改
        conn.commit()

        # 验证结果
        cursor.execute("SELECT id, name, is_system FROM projects WHERE id = 1")
        result = cursor.fetchone()
        print(f"\n验证结果:")
        print(f"  ID: {result[0]}")
        print(f"  名称: {result[1]}")
        print(f"  系统项目: {'是' if result[2] else '否'}")

        print("\n✅ 迁移成功完成！")

    except sqlite3.Error as e:
        print(f"❌ 数据库错误: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ 错误: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("数据库迁移：系统项目支持")
    print("=" * 60)
    migrate()
