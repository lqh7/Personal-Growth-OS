#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sqlite3
from datetime import datetime
import sys
import io

# Set UTF-8 encoding for output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

conn = sqlite3.connect('personal_growth_os.db')
cursor = conn.cursor()

# Query all snoozed tasks
cursor.execute('''
    SELECT id, title, start_time, snooze_until, status, created_at
    FROM tasks
    WHERE snooze_until IS NOT NULL
    ORDER BY snooze_until DESC
''')

tasks = cursor.fetchall()
now = datetime.now()

print('=== All Snoozed Tasks ===')
print(f'Current time: {now}')
print(f'Total {len(tasks)} snoozed tasks\n')

for task in tasks:
    task_id, title, start_time, snooze_until, status, created_at = task

    # Parse snooze_until
    try:
        snooze_dt = datetime.fromisoformat(snooze_until.replace('Z', '+00:00')) if snooze_until else None
    except:
        snooze_dt = datetime.fromisoformat(snooze_until) if snooze_until else None

    is_active = snooze_dt > now if snooze_dt else False
    should_display = is_active and status != 'completed'

    print(f'ID: {task_id}')
    print(f'Title: {title}')
    print(f'Start Time: {start_time or "None"}')
    print(f'Snooze Until: {snooze_until}')
    print(f'Status: {status}')
    print(f'Should Display: {"YES" if should_display else "NO (" + ("Expired" if not is_active else "Completed") + ")"}')
    print('-' * 50)

# Also check tasks without start_time (unscheduled tasks)
print('\n=== Unscheduled Tasks (no start_time) ===')
cursor.execute('''
    SELECT id, title, snooze_until, status
    FROM tasks
    WHERE start_time IS NULL AND status != 'completed'
    ORDER BY id DESC
    LIMIT 10
''')

unscheduled = cursor.fetchall()
print(f'Total {len(unscheduled)} unscheduled tasks (showing last 10)\n')

for task in unscheduled:
    task_id, title, snooze_until, status = task
    print(f'ID: {task_id} | Title: {title[:30]} | Snoozed: {snooze_until or "No"}')

conn.close()
