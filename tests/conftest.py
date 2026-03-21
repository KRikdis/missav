#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pytest 配置和共享 fixture
"""

import pytest
import json
import tempfile
from pathlib import Path


@pytest.fixture
def sample_video():
    """
    提供标准的测试视频对象
    """
    return {
        'code': 'ABC-001',
        'url': 'https://example.com/stream.m3u8',
        'genres': ['日本', '高清', '新作'],
        'thumbnail': 'https://example.com/thumb.jpg',
        'group_title': '日本'
    }


@pytest.fixture
def multiple_videos():
    """
    提供多个测试视频对象
    """
    return [
        {
            'code': 'ABC-001',
            'url': 'https://example.com/stream1.m3u8',
            'genres': ['日本', '高清'],
            'thumbnail': 'https://example.com/thumb1.jpg'
        },
        {
            'code': 'DEF-002',
            'url': 'https://example.com/stream2.m3u8',
            'genres': ['中文', '欧美'],
            'thumbnail': 'https://example.com/thumb2.jpg'
        },
        {
            'code': 'GHI-003',
            'url': 'https://example.com/stream3.m3u8',
            'genres': [],  # 无分类
            'thumbnail': 'https://example.com/thumb3.jpg'
        }
    ]


@pytest.fixture
def temp_state_file():
    """
    提供临时状态文件
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        state = {
            'videos': [
                {
                    'code': 'ABC-001',
                    'url': 'https://example.com/stream.m3u8',
                    'genres': ['日本', '高清'],
                    'thumbnail': 'https://example.com/thumb.jpg'
                }
            ],
            'last_update': '2026-03-21T10:00:00',
            'current_query_index': 0
        }
        json.dump(state, f, ensure_ascii=False, indent=2)
        temp_path = Path(f.name)
    
    yield temp_path
    
    # 清理
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def temp_m3u_file():
    """
    提供临时 M3U 输出文件
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.m3u', delete=False) as f:
        f.write('#EXTM3U\n')
        temp_path = Path(f.name)
    
    yield temp_path
    
    # 清理
    if temp_path.exists():
        temp_path.unlink()
