#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import json

# Test creating a task with Chinese characters
url = "http://localhost:8000/api/tasks/"
headers = {"Content-Type": "application/json; charset=utf-8"}
data = {
    "title": "测试中文任务",
    "description": "这是一个中文描述",
    "priority": 3
}

response = requests.post(url, json=data, headers=headers)
print(f"Status Code: {response.status_code}")
if response.status_code == 201:
    result = response.json()
    print("Success! Task created:")
    print(f"  ID: {result['id']}")
    print(f"  Status: {result['status']}")
else:
    print(f"Error: {response.text}")
