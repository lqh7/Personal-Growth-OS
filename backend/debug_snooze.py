"""Debug script to test snooze logic"""
from datetime import datetime, timedelta

# Simulate the task data
task_start = datetime.fromisoformat("2025-01-15T14:00:00")
task_end = datetime.fromisoformat("2025-01-15T16:00:00")
snooze_until = datetime.fromisoformat("2025-01-16T10:00:00")

print("Original task:")
print(f"  Start: {task_start}")
print(f"  End: {task_end}")
print(f"  Duration: {task_end - task_start}")

# Test mode="start" logic (from tasks.py lines 235-239)
if task_start and task_end:
    duration = task_end - task_start
    new_start = snooze_until
    new_end = snooze_until + duration

    print(f"\nAfter snooze (mode='start'):")
    print(f"  New Start: {new_start}")
    print(f"  New End: {new_end}")
    print(f"  New Duration: {new_end - new_start}")
    print(f"  Duration preserved? {duration == (new_end - new_start)}")
