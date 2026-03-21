#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MissAV M3U 爬虫脚本 (简单版)
这是一个简单的入口脚本，实际功能在 scraper_final.py 中实现
"""

from scraper_final import MissAVScraper
import sys


def main():
    """主函数"""
    scraper = MissAVScraper(output_file='missav.m3u')
    
    try:
        scraper.run()
        print(f"\n✓ 爬虫完成！已保存 {len(scraper.videos)} 个视频到 missav.m3u")
    except KeyboardInterrupt:
        print("\n用户中断了爬虫")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ 爬虫出错: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
