#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本 - 检查爬虫是否能正确运行
"""

import sys
import os
from pathlib import Path

def check_installation():
    """检查依赖是否安装"""
    print("=" * 50)
    print("检查环境...")
    print("=" * 50)
    
    # 检查 Python 版本
    print(f"✓ Python 版本: {sys.version}")
    
    # 检查必要的库
    required_libs = ['requests']
    optional_libs = ['missav_api']
    
    print("\n必要库:")
    for lib in required_libs:
        try:
            __import__(lib)
            print(f"  ✓ {lib}")
        except ImportError:
            print(f"  ✗ {lib} - 未安装")
            return False
    
    print("\n可选库:")
    for lib in optional_libs:
        try:
            __import__(lib.replace('-', '_'))
            print(f"  ✓ {lib}")
        except ImportError:
            print(f"  ✗ {lib} - 未安装 (需要运行: pip install {lib})")
    
    return True


def check_script_files():
    """检查脚本文件"""
    print("\n" + "=" * 50)
    print("检查脚本文件...")
    print("=" * 50)
    
    files = ['main.py', 'scraper.py', 'requirements.txt', 'README.md']
    
    for file in files:
        path = Path(file)
        if path.exists():
            size = path.stat().st_size
            print(f"  ✓ {file} ({size} 字节)")
        else:
            print(f"  ✗ {file} - 不存在")
    
    return True


def test_m3u_format():
    """测试 M3U 格式生成"""
    print("\n" + "=" * 50)
    print("测试 M3U 格式...")
    print("=" * 50)
    
    test_data = [
        {'code': 'ABP-123', 'url': 'http://example.com/video1.m3u8'},
        {'code': 'CD-456', 'url': 'http://example.com/video2.m3u8'},
    ]
    
    test_file = 'test_output.m3u'
    
    try:
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write('#EXTM3U\n')
            for video in test_data:
                code = video['code']
                url = video['url']
                f.write(f'#EXTINF:-1 group-title="成人频道" tvg-name="{code}" tvg-logo="" epg-url="",{code}\n')
                f.write(f'{url}\n')
        
        # 验证文件内容
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if '#EXTM3U' in content and 'ABP-123' in content:
            print(f"  ✓ 成功生成测试文件: {test_file}")
            print(f"  ✓ 文件内容验证通过")
            
            # 显示生成的内容
            print("\n  生成的内容示例:")
            for line in content.split('\n')[:5]:
                if line:
                    print(f"    {line}")
            
            # 清理测试文件
            os.remove(test_file)
            return True
        else:
            print(f"  ✗ 生成的文件内容不正确")
            return False
    
    except Exception as e:
        print(f"  ✗ 测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("\nMissAV M3U 爬虫 - 环境检查\n")
    
    all_pass = True
    
    # 检查安装
    if not check_installation():
        all_pass = False
    
    # 检查文件
    if not check_script_files():
        all_pass = False
    
    # 测试 M3U 格式
    if not test_m3u_format():
        all_pass = False
    
    # 总结
    print("\n" + "=" * 50)
    if all_pass:
        print("✓ 所有检查通过！")
        print("\n快速开始:")
        print("  1. 安装依赖: pip install -r requirements.txt")
        print("  2. 运行爬虫: python main.py")
    else:
        print("✗ 某些检查失败，请查看上面的错误信息")
    print("=" * 50 + "\n")


if __name__ == '__main__':
    main()
