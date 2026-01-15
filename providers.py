#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
参数提供器模块
包含查询提供器和 API Key 提供器
"""

import threading
from typing import Optional
from collections import deque


class QueryProvider:
    """参数化查询提供器（线程安全）"""
    
    def __init__(self, param_file: Optional[str] = None, default_query: str = "你是谁"):
        """
        初始化查询提供器
        
        Args:
            param_file: 参数化文件路径，每行一个查询
            default_query: 默认查询文本
        """
        self.lock = threading.Lock()
        self.queries = deque()
        self.current_index = 0
        
        if param_file:
            try:
                with open(param_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        query = line.strip()
                        if query:  # 跳过空行
                            self.queries.append(query)
            except FileNotFoundError:
                print(f"警告: 参数化文件 '{param_file}' 不存在，使用默认查询")
                self.queries.append(default_query)
            except Exception as e:
                print(f"警告: 读取参数化文件失败: {e}，使用默认查询")
                self.queries.append(default_query)
        else:
            self.queries.append(default_query)
        
        if not self.queries:
            self.queries.append(default_query)
    
    def get_next_query(self) -> str:
        """
        获取下一个查询（线程安全，循环轮询）
        
        Returns:
            查询文本
        """
        with self.lock:
            if not self.queries:
                return "你是谁"
            
            query = self.queries[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.queries)
            return query


class ApiKeyProvider:
    """API Key 提供器（线程安全，循环使用）"""

    def __init__(self, key_file: Optional[str] = None, default_key: str = ""):
        self.lock = threading.Lock()
        self.keys = deque()
        self.current_index = 0

        if key_file:
            try:
                with open(key_file, "r", encoding="utf-8") as f:
                    for line in f:
                        k = line.strip()
                        if k:
                            self.keys.append(k)
            except Exception as e:
                print(f"警告: 读取 API Key 文件失败 ({e})，回退到默认 key")
                if default_key:
                    self.keys.append(default_key)
        if not self.keys and default_key:
            self.keys.append(default_key)

    def get_next_key(self) -> str:
        with self.lock:
            if not self.keys:
                return ""
            key = self.keys[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.keys)
            return key

