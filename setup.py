#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MissAV 爬虫项目配置文件

允许项目作为 Python 包安装
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="missav-scraper",
    version="2.0.0",
    author="MissAV Team",
    description="一个用于爬取 MissAV 网站视频并生成 M3U 播放列表的完整项目",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/KRikdis/missav",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "missav-scraper=src.missav_scraper.cli:main",
        ],
    },
)
