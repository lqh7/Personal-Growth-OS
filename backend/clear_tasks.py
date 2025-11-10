#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Clear all tasks from database"""
import sqlite3
import sys

try:
    conn = sqlite3.connect('personal_growth_os.db')
    cur = conn.cursor()

    # Delete all tasks
    cur.execute('DELETE FROM tasks')
    deleted_count = cur.rowcount

    conn.commit()
    print(f"[OK] Successfully deleted {deleted_count} tasks")
    print("[OK] Database is now clean and ready for new tasks with correct UTF-8 encoding")

except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)
finally:
    if conn:
        conn.close()
