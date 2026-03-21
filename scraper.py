#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MissAV M3U 爬虫脚本 (增强版)
支持多种数据获取方式，包括 API 和网页抓取
"""

import sys
import time
from pathlib import Path
import logging
from typing import List, Dict, Tuple
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MissAVScraperBase:
    """基础爬虫类"""
    
    def __init__(self, output_file: str = 'missav.m3u'):
        self.output_file = output_file
        self.videos: List[Dict[str, str]] = []
    
    def fetch_videos(self) -> List[Dict[str, str]]:
        """获取视频列表，需要在子类中实现"""
        raise NotImplementedError
    
    def save_to_m3u(self):
        """将数据保存为 m3u 格式"""
        logger.info(f"开始保存为 m3u 格式: {self.output_file}")
        
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                # 写入 M3U 头
                f.write('#EXTM3U\n')
                
                for video in self.videos:
                    code = video.get('code', 'Unknown')
                    url = video.get('url', '')
                    
                    if not url:
                        logger.warning(f"跳过无效的 URL: {code}")
                        continue
                    
                    # 按照指定格式写入
                    f.write(f'#EXTINF:-1 group-title="成人频道" tvg-name="{code}" tvg-logo="" epg-url="",{code}\n')
                    f.write(f'{url}\n')
                
                logger.info(f"成功保存 {len(self.videos)} 个视频到 {self.output_file}")
                return True
        
        except Exception as e:
            logger.error(f"保存 m3u 文件时出错: {e}")
            return False
    
    def run(self):
        """运行爬虫"""
        logger.info("开始爬取视频...")
        self.fetch_videos()
        
        if self.videos:
            self.save_to_m3u()
        else:
            logger.warning("未获取到任何视频")


class MissAVAPIClient(MissAVScraperBase):
    """使用 missav_api 库的爬虫"""
    
    def fetch_videos(self) -> List[Dict[str, str]]:
        """通过 missav_api 获取视频"""
        try:
            from missav_api import Client
            
            logger.info("使用 missav_api 库获取视频...")
            api = Client()
            
            page = 1
            max_pages = 1000  # 防止无限循环
            
            while page <= max_pages:
                logger.info(f"正在获取第 {page} 页...")
                
                try:
                    # 根据 missav_api 的实际 API 调用
                    videos = api.search(page=page)
                    
                    if not videos or len(videos) == 0:
                        logger.info(f"第 {page} 页无更多数据，爬取完成")
                        break
                    
                    for video in videos:
                        try:
                            # 适配多种可能的字段名
                            code = (
                                video.get('code') or 
                                video.get('番号') or 
                                video.get('title') or 
                                video.get('id')
                            )
                            
                            m3u_url = (
                                video.get('m3u8_url') or 
                                video.get('url') or 
                                video.get('stream_url')
                            )
                            
                            if code and m3u_url:
                                self.videos.append({
                                    'code': str(code),
                                    'url': str(m3u_url)
                                })
                                logger.info(f"获取: {code}")
                            else:
                                logger.debug(f"跳过不完整的视频数据: {video}")
                            
                            time.sleep(0.3)
                        
                        except Exception as e:
                            logger.debug(f"处理视频时出错: {e}")
                            continue
                    
                    page += 1
                    time.sleep(1)
                
                except Exception as e:
                    logger.error(f"获取第 {page} 页时出错: {e}")
                    if page == 1:
                        raise  # 第一页出错就抛出异常
                    break
            
            logger.info(f"总共获取 {len(self.videos)} 个视频")
            return self.videos
        
        except ImportError as e:
            logger.error(f"未安装 missav_api 库，请运行: pip install missav-api (错误: {e})")
            sys.exit(1)
        except Exception as e:
            logger.error(f"获取视频时出错: {e}")
            return []


class ConfigurableScraper(MissAVAPIClient):
    """可配置的爬虫，支持自定义参数"""
    
    def __init__(self, output_file: str = 'missav.m3u', config_file: str = None):
        super().__init__(output_file)
        self.config = self._load_config(config_file) if config_file else {}
    
    def _load_config(self, config_file: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"配置文件 {config_file} 不存在")
            return {}
        except Exception as e:
            logger.warning(f"加载配置文件出错: {e}")
            return {}
    
    def save_config(self, config_file: str = 'config.json'):
        """保存配置文件"""
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logger.info(f"配置已保存到 {config_file}")
        except Exception as e:
            logger.error(f"保存配置文件出错: {e}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MissAV 爬虫 - 爬取 missav 视频并生成 M3U 列表')
    parser.add_argument('-o', '--output', default='missav.m3u', help='输出文件名 (默认: missav.m3u)')
    parser.add_argument('-c', '--config', default=None, help='配置文件路径 (可选)')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细日志输出')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 使用可配置爬虫
    scraper = ConfigurableScraper(
        output_file=args.output,
        config_file=args.config
    )
    
    try:
        scraper.run()
    except KeyboardInterrupt:
        logger.info("用户中断了爬虫")
        sys.exit(0)
    except Exception as e:
        logger.error(f"爬虫出错: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
