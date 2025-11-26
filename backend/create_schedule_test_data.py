#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Create test data for schedule view with different project colors and priorities"""

import sys
import requests
import json
from datetime import datetime, timedelta

def create_test_data():
    base_url = 'http://localhost:8000/api'

    # Create test projects with different colors
    projects = [
        {'name': 'Work Project', 'color': '#3498DB', 'description': 'Work related tasks'},
        {'name': 'Study Plan', 'color': '#E74C3C', 'description': 'Learning tasks'},
        {'name': 'Health Life', 'color': '#2ECC71', 'description': 'Health tasks'}
    ]

    created_projects = []

    print('Creating test projects...')
    for proj in projects:
        try:
            resp = requests.post(f'{base_url}/projects/', json=proj)
            if resp.status_code == 200:
                created_projects.append(resp.json())
                print(f"✓ Created: {proj['name']} (Color: {proj['color']})")
        except Exception as e:
            print(f"✗ Failed to create project: {e}")

    # Create schedule test tasks (this week, different priorities)
    now = datetime.now()
    monday = now - timedelta(days=now.weekday())

    tasks = []
    if len(created_projects) >= 3:
        # Monday - Work project (Blue) - Priority 5
        tasks.append({
            'title': 'Team Meeting',
            'project_id': created_projects[0]['id'],
            'priority': 5,  # opacity 1.0
            'start_time': monday.replace(hour=10, minute=0, second=0, microsecond=0).isoformat(),
            'end_time': monday.replace(hour=11, minute=30, second=0, microsecond=0).isoformat(),
            'status': 'pending'
        })

        # Tuesday - Study (Red) - Priority 3
        tasks.append({
            'title': 'Python Learning',
            'project_id': created_projects[1]['id'],
            'priority': 3,  # opacity 0.7
            'start_time': (monday + timedelta(days=1)).replace(hour=14, minute=0, second=0, microsecond=0).isoformat(),
            'end_time': (monday + timedelta(days=1)).replace(hour=16, minute=0, second=0, microsecond=0).isoformat(),
            'status': 'pending'
        })

        # Wednesday - Health (Green) - Priority 1
        tasks.append({
            'title': 'Gym Workout',
            'project_id': created_projects[2]['id'],
            'priority': 1,  # opacity 0.4
            'start_time': (monday + timedelta(days=2)).replace(hour=18, minute=0, second=0, microsecond=0).isoformat(),
            'end_time': (monday + timedelta(days=2)).replace(hour=19, minute=30, second=0, microsecond=0).isoformat(),
            'status': 'pending'
        })

        # Thursday - Work (Blue) - Priority 4
        tasks.append({
            'title': 'Project Demo Prep',
            'project_id': created_projects[0]['id'],
            'priority': 4,  # opacity 0.85
            'start_time': (monday + timedelta(days=3)).replace(hour=9, minute=0, second=0, microsecond=0).isoformat(),
            'end_time': (monday + timedelta(days=3)).replace(hour=12, minute=0, second=0, microsecond=0).isoformat(),
            'status': 'pending'
        })

        # Friday - Study (Red) - Priority 2
        tasks.append({
            'title': 'Read Documentation',
            'project_id': created_projects[1]['id'],
            'priority': 2,  # opacity 0.55
            'start_time': (monday + timedelta(days=4)).replace(hour=15, minute=0, second=0, microsecond=0).isoformat(),
            'end_time': (monday + timedelta(days=4)).replace(hour=17, minute=0, second=0, microsecond=0).isoformat(),
            'status': 'pending'
        })

    print('\nCreating schedule test tasks...')
    for task in tasks:
        try:
            resp = requests.post(f'{base_url}/tasks/', json=task)
            if resp.status_code == 200:
                opacity = 0.25 + task['priority'] * 0.15
                print(f"✓ {task['title']} | Priority {task['priority']} | Opacity {opacity:.2f}")
        except Exception as e:
            print(f"✗ Failed to create task: {e}")

    print('\n✅ Test data created successfully!')
    print('Please refresh the frontend to see the schedule view.')
    print('\nColor mapping:')
    print('  - Blue (#3498DB) = Work Project')
    print('  - Red (#E74C3C) = Study Plan')
    print('  - Green (#2ECC71) = Health Life')
    print('\nOpacity mapping (priority):')
    print('  - Priority 5 -> opacity 1.0 (darkest)')
    print('  - Priority 4 -> opacity 0.85')
    print('  - Priority 3 -> opacity 0.70')
    print('  - Priority 2 -> opacity 0.55')
    print('  - Priority 1 -> opacity 0.40 (lightest)')

if __name__ == '__main__':
    create_test_data()
