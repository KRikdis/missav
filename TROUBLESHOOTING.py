#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MissAV M3U 爬虫 - 配置指南
如果遇到连接被拒绝问题 [Errno 54] Connection reset by peer
"""

CONFIG_GUIDE = """
╔═══════════════════════════════════════════════════════════╗
║         MissAV 爬虫 - 连接问题诊断与解决方案              ║
╚═══════════════════════════════════════════════════════════╝

【问题】
  错误信息: [Errno 54] Connection reset by peer
  原因: 网络连接被拒绝（不是被限流）

【可能的原因】
  1. 地理位置限制 - 网站可能限制某些地区访问
  2. ISP 阻止 - 您的网络提供商可能阻止了该网站
  3. 防火墙 - 网络环境的防火墙规则
  4. 需要代理 - 某些网络环境需要设置代理

【解决方案】

【方案 1】使用 SOCKS5 代理（如果您有代理服务器）
  1. 编辑 config.json:
     {
       "proxy_url": "socks5://127.0.0.1:1080"
     }
  
  2. 运行爬虫:
     python scraper_final.py

【方案 2】检查网络连接
  python diagnose.py
  
  这会显示：
  - 网站是否可访问
  - API 是否响应
  - 具体的错误信息

【方案 3】使用 VPN 或代理工具
  - 配置您的系统 VPN 或代理
  - 然后运行爬虫
  
【方案 4】在有公网访问的服务器上运行
  - 如果您有云服务器（AWS, DigitalOcean 等）
  - 可以在那上面部署爬虫
  - 然后下载生成的 M3U 文件

【检查连接状态】
  # 测试DNS
  nslookup missav.ws
  
  # 测试连接
  curl -I https://missav.ws/en/
  
  # 测试 Python 请求
  python -c "import requests; print(requests.get('https://missav.ws/en/', timeout=5).status_code)"

【关于限流】
  如果是被限流，您会看到：
  - HTTP 429 错误
  - 429 Too Many Requests
  - 而不是 Connection reset
  
  爬虫已经带有反限流措施：
  - 最小 2-5 秒请求间隔
  - 批量请求后暂停 15 秒
  - 失败后自动退避

【更多帮助】
  使用 -v 参数获取详细日志：
  python scraper_final.py -v
  
  清除进度重新开始：
  python scraper_final.py --clean

"""

if __name__ == '__main__':
    print(CONFIG_GUIDE)
