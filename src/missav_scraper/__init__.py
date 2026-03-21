#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MissAV 爬虫包

一个用于爬取 MissAV 网站视频并生成 M3U 播放列表的完整项目。

支持功能：
    - 增量更新：每次运行追加新视频到 M3U 文件
    - 去重：自动检查和跳过重复 URL
    - 断点续爬：保存进度，中断后可继续
    - 限制收集：每次运行最多收集指定数量视频，保护 IP
    - 限流保护：自动添加请求延迟，避免 IP 被限制

快速开始：
    >>> from missav_scraper import MissAVScraper
    >>> scraper = MissAVScraper(output_file='output/missav.m3u')
    >>> scraper.run()

命令行使用：
    $ python main.py                           # 基础使用
    $ python -m missav_scraper                 # 直接运行模块
    $ python main.py --help                    # 查看帮助

版本: 2.0.0
作者: MissAV Team
"""

__version__ = "2.0.0"
__author__ = "MissAV Team"

from .core import MissAVScraper
from . import constants
from . import utils

__all__ = [
    'MissAVScraper',
    'constants',
    'utils',
]
