#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check database encoding and actual stored data"""
import sqlite3

conn = sqlite3.connect('personal_growth_os.db')
cur = conn.cursor()

# Check encoding
encoding_result = conn.execute('PRAGMA encoding').fetchone()
print(f"Database encoding: {encoding_result[0]}")
print()

# Check last 5 tasks
cur.execute('SELECT id, title, description FROM tasks ORDER BY id DESC LIMIT 5')
print("Last 5 tasks:")
print("-" * 80)
for row in cur:
    task_id, title, description = row
    print(f"ID: {task_id}")
    print(f"  Title (repr): {repr(title)}")
    print(f"  Title (str):  {title}")
    print(f"  Desc (repr):  {repr(description)}")
    print()

conn.close()
