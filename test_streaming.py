#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流式接口测试脚本
用于测试AI小说生成系统的流式和非流式接口
"""

import requests
import json
import time
from typing import Dict, Any

# 配置
BASE_URL = "http://localhost:8001"
STREAM_ENDPOINT = f"{BASE_URL}/api/v1/generate-novel-stream"
NORMAL_ENDPOINT = f"{BASE_URL}/api/v1/generate-novel"

def test_streaming_interface():
    """测试流式接口"""
    print("=== 测试流式接口 ===")
    
    # 请求数据
    payload = {
        "novel_style": "修仙"  # 可选值: fantasy, romance, mystery, sci_fi, horror
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    
    try:
        print(f"发送请求到: {STREAM_ENDPOINT}")
        print(f"请求数据: {json.dumps(payload, ensure_ascii=False)}")
        print("\n开始接收流式数据...\n")
        
        # 发送流式请求
        response = requests.post(
            STREAM_ENDPOINT,
            json=payload,
            headers=headers,
            stream=True,
            timeout=300
        )
        
        if response.status_code == 200:
            print("✅ 连接成功，开始接收数据流...\n")
            
            # 处理流式响应
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    # 处理Server-Sent Events格式
                    if line.startswith('data: '):
                        data_str = line[6:]  # 移除'data: '前缀
                        try:
                            data = json.loads(data_str)
                            
                            if data.get('type') == 'title':
                                print(f"📖 章节标题: {data.get('content')}")
                                print("-" * 50)
                            elif data.get('type') == 'content':
                                print(data.get('content'))
                            elif data.get('type') == 'complete':
                                print("\n" + "=" * 50)
                                print("✅ 章节生成完成!")
                                break
                            elif data.get('type') == 'error':
                                print(f"❌ 错误: {data.get('content')}")
                                break
                                
                        except json.JSONDecodeError as e:
                            print(f"⚠️  JSON解析错误: {e}")
                            print(f"原始数据: {data_str}")
        else:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求错误: {e}")
    except Exception as e:
        print(f"❌ 未知错误: {e}")

def test_normal_interface():
    """测试非流式接口"""
    print("\n\n=== 测试非流式接口 ===")
    
    # 请求数据
    payload = {
        "novel_style": "romance"  # 可选值: fantasy, romance, mystery, sci_fi, horror
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print(f"发送请求到: {NORMAL_ENDPOINT}")
        print(f"请求数据: {json.dumps(payload, ensure_ascii=False)}")
        print("\n等待响应...")
        
        start_time = time.time()
        
        # 发送普通请求
        response = requests.post(
            NORMAL_ENDPOINT,
            json=payload,
            headers=headers,
            timeout=120
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        if response.status_code == 200:
            print(f"✅ 请求成功 (耗时: {duration:.2f}秒)")
            
            result = response.json()
            
            print("\n📋 生成结果:")
            print("=" * 60)
            
            # 世界设定
            if result.get('world_setting'):
                print("🌍 世界设定:")
                world = result['world_setting']
                for key, value in world.items():
                    print(f"  {key}: {value}")
                print()
            
            # 主角信息
            if result.get('protagonist_info'):
                print("👤 主角信息:")
                protagonist = result['protagonist_info']
                for key, value in protagonist.items():
                    print(f"  {key}: {value}")
                print()
            
            # 起始章节
            if result.get('start_chapter'):
                print("📖 起始章节:")
                chapter = result['start_chapter']
                print(f"  标题: {chapter.get('chapter_title', 'N/A')}")
                print(f"  内容: {chapter.get('chapter_content', 'N/A')}")
                print()
            
            print(f"📊 状态: {result.get('status', 'unknown')}")
            
        else:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求错误: {e}")
    except Exception as e:
        print(f"❌ 未知错误: {e}")

def test_server_health():
    """测试服务器健康状态"""
    print("=== 检查服务器状态 ===")
    
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ 服务器运行正常")
            return True
        else:
            print(f"⚠️  服务器响应异常，状态码: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 无法连接到服务器: {e}")
        print("请确保服务器已启动并运行在 http://localhost:8000")
        return False

def main():
    """主函数"""
    print("🚀 AI小说生成系统 - 流式接口测试")
    print("=" * 60)
    
    # 检查服务器状态
    if not test_server_health():
        print("\n❌ 测试终止：服务器不可用")
        return
    
    print("\n" + "=" * 60)
    
    # 测试流式接口
    test_streaming_interface()
    
    # 等待一段时间
    # print("\n" + "=" * 60)
    # print("等待3秒后测试非流式接口...")
    # time.sleep(3)
    
    # 测试非流式接口
    # test_normal_interface()
    
    # print("\n" + "=" * 60)
    # print("🎉 测试完成!")

if __name__ == "__main__":
    main()