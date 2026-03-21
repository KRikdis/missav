#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MissAV M3U 爬虫脚本 (最终版本 - 带限流)
支持 missav_api 库，具有完善的错误处理、限流、进度保存
"""

import json
import time
import random
from pathlib import Path
from typing import List, Dict
from datetime import datetime
import logging
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MissAVScraper:
    """MissAV 爬虫类 - 带智能限流"""
    
    STATE_FILE = 'scraper_state.json'
    MAX_RETRIES = 3
    
    # 限流配置
    MIN_DELAY = 2      # 最小延迟 2 秒
    MAX_DELAY = 5      # 最大延迟 5 秒
    BATCH_SIZE = 10    # 每批最多 10 个请求
    BATCH_DELAY = 15   # 批次间延迟 15 秒
    
    def __init__(self, output_file: str = 'missav.m3u', enable_checkpoint: bool = True):
        self.output_file = output_file
        self.enable_checkpoint = enable_checkpoint
        self.videos: List[Dict[str, str]] = []
        self.state = self._load_state() if enable_checkpoint else {}
        self.processed_codes: set = set(v['code'] for v in self.state.get('videos', []))
        self.request_count = 0  # 请求计数，用于限流
    
    def _random_delay(self, min_delay=None, max_delay=None):
        """随机延迟，避免被限制"""
        min_delay = min_delay or self.MIN_DELAY
        max_delay = max_delay or self.MAX_DELAY
        delay = random.uniform(min_delay, max_delay)
        logger.debug(f"延迟 {delay:.2f} 秒...")
        time.sleep(delay)
    
    def _load_state(self) -> Dict:
        """加载保存的状态"""
        try:
            state_path = Path(self.STATE_FILE)
            if state_path.exists():
                with open(state_path, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                logger.info(f"已加载保存的状态 (已有 {len(state.get('videos', []))} 个视频)")
                return state
        except Exception as e:
            logger.warning(f"加载状态文件失败: {e}")
        
        return {'videos': []}
    
    def _save_state(self):
        """保存爬虫状态"""
        if not self.enable_checkpoint:
            return
        
        try:
            state = {
                'videos': self.videos,
                'last_update': datetime.now().isoformat()
            }
            
            with open(self.STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            logger.info(f"进度已保存 ({len(self.videos)} 个视频)")
        except Exception as e:
            logger.error(f"保存状态失败: {e}")
    
    def fetch_videos(self) -> List[Dict[str, str]]:
        """从 missav_api 获取视频"""
        
        # 加载之前保存的视频
        if self.state.get('videos'):
            self.videos = self.state['videos']
            logger.info(f"已加载 {len(self.videos)} 个旧视频")
        
        try:
            from missav_api import Client
            
            logger.info("使用 missav_api 库获取视频...")
            logger.info(f"限流配置: {self.MIN_DELAY}-{self.MAX_DELAY}秒/请求, 批次延迟{self.BATCH_DELAY}秒")
            
            client = Client()
            
            video_count = 0
            
            logger.info("开始获取视频列表...")
            
            try:
                # 测试版本只爬取前 2 页
                # 字母覆盖从 A-Z，这样可以获得多个领域的视频
                queries = [
                    "a", "b", "c", "d", "e",  # 第一批：a-e
                ]
                
                all_processed_codes = set()
                batch_count = 0
                
                for query_idx, query in enumerate(queries):
                    batch_count += 1
                    logger.info(f"\n查询 {query_idx + 1}/{len(queries)}: '{query}' (第 {batch_count} 批)")
                    
                    try:
                        # 每个查询只获取 50 个视频（用于测试）
                        search_results = client.search(query=query, video_count=50)
                        
                        result_count = 0
                        for video in search_results:
                            try:
                                # 从 Video 对象中提取信息
                                video_code = video.video_code
                                m3u8_url = video.m3u8_base_url
                                
                                result_count += 1
                                
                                if result_count == 1:
                                    logger.info(f"  ✓ 首个视频: {video_code}")
                                    logger.info(f"    M3U8 URL: {m3u8_url[:50]}..." if len(m3u8_url) > 50 else f"    M3U8 URL: {m3u8_url}")
                                
                                if video_code and video_code not in all_processed_codes and video_code not in self.processed_codes:
                                    if not m3u8_url:
                                        m3u8_url = ""
                                    
                                    self.videos.append({
                                        'code': str(video_code),
                                        'url': str(m3u8_url)
                                    })
                                    self.processed_codes.add(video_code)
                                    all_processed_codes.add(video_code)
                                    video_count += 1
                                    
                                    logger.info(f"    - 新增: {video_code}")
                                
                                # 每个视频请求之间添加随机延迟
                                self._random_delay(0.5, 1.5)
                                self.request_count += 1
                            
                            except Exception as e:
                                logger.debug(f"处理视频时出错: {e}")
                                continue
                        
                        logger.info(f"  本次查询: {result_count} 个结果，新增 {video_count} 个视频")
                        
                        # 批次间延迟，避免被限制
                        if (query_idx + 1) % 5 == 0:
                            logger.info(f"⏸ 批量请求完成，暂停 {self.BATCH_DELAY} 秒...")
                            time.sleep(self.BATCH_DELAY)
                        else:
                            # 查询间的延迟
                            self._random_delay()
                    
                    except Exception as e:
                        logger.warning(f"查询 '{query}' 失败: {e}")
                        # 失败后也要延迟
                        self._random_delay(5, 10)
                        continue
                
                logger.info(f"\n{'='*50}")
                logger.info(f"爬虫完成! 总共获取 {len(self.videos)} 个视频")
                logger.info(f"总请求数: {self.request_count}")
                logger.info(f"{'='*50}")
                
            except KeyboardInterrupt:
                logger.info("用户中断")
            except Exception as e:
                logger.error(f"获取视频时出错: {e}")
                if len(self.videos) == 0:
                    raise
            
            self._save_state()
            return self.videos
        
        except ImportError:
            logger.error("未安装 missav_api 库，请运行: pip install missav-api")
            sys.exit(1)
    
    def save_to_m3u(self):
        """将数据保存为 m3u 格式"""
        logger.info(f"开始保存为 m3u 格式: {self.output_file}")
        
        if not self.videos:
            logger.warning("没有视频数据可保存")
            return False
        
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                # 写入 M3U 头
                f.write('#EXTM3U\n')
                
                for i, video in enumerate(self.videos, 1):
                    code = video.get('code', 'Unknown')
                    url = video.get('url', '')
                    
                    if not url:
                        logger.warning(f"跳过无效的 URL: {code}")
                        continue
                    
                    # 按照指定格式写入
                    f.write(f'#EXTINF:-1 group-title="成人频道" tvg-name="{code}" tvg-logo="" epg-url="",{code}\n')
                    f.write(f'{url}\n')
                    
                    if i % 100 == 0:
                        logger.info(f"已保存 {i} 个视频...")
                
                logger.info(f"✓ 成功保存 {len(self.videos)} 个视频到 {self.output_file}")
                return True
        
        except Exception as e:
            logger.error(f"保存 m3u 文件时出错: {e}")
            return False
    
    def run(self):
        """运行爬虫"""
        logger.info("=" * 50)
        logger.info("MissAV 爬虫程序启动")
        logger.info("=" * 50)
        
        try:
            self.fetch_videos()
            if self.videos:
                self.save_to_m3u()
                logger.info("=" * 50)
                logger.info(f"✓ 爬虫完成! 已保存 {len(self.videos)} 个视频")
                logger.info("=" * 50)
            else:
                logger.warning("未获取到任何视频")
        
        except KeyboardInterrupt:
            logger.info("用户中断")
            self._save_state()
        except Exception as e:
            logger.error(f"爬虫运行失败: {e}")
            self._save_state()
            sys.exit(1)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='MissAV 爬虫 - 爬取 missav 视频并生成 M3U 列表',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python scraper_final.py                    # 基本使用
  python scraper_final.py -o custom.m3u      # 自定义输出文件
  python scraper_final.py --no-checkpoint    # 不保存进度
  python scraper_final.py --clean            # 清除进度和输出文件
        '''
    )
    
    parser.add_argument('-o', '--output', default='missav.m3u', help='输出文件名 (默认: missav.m3u)')
    parser.add_argument('-c', '--checkpoint', dest='checkpoint', action='store_true', default=True, help='启用断点续爬 (默认)')
    parser.add_argument('--no-checkpoint', dest='checkpoint', action='store_false', help='禁用断点续爬')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细日志输出')
    parser.add_argument('--clean', action='store_true', help='清除保存的进度')
    
    args = parser.parse_args()
    
    # 调整日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 处理 --clean 参数
    if args.clean:
        try:
            Path(MissAVScraper.STATE_FILE).unlink()
            print(f"✓ 已清除进度文件: {MissAVScraper.STATE_FILE}")
        except FileNotFoundError:
            print("进度文件不存在")
        
        try:
            Path(args.output).unlink()
            print(f"✓ 已清除输出文件: {args.output}")
        except FileNotFoundError:
            print("输出文件不存在")
        return
    
    # 创建爬虫并运行
    scraper = MissAVScraper(output_file=args.output, enable_checkpoint=args.checkpoint)
    scraper.run()


if __name__ == '__main__':
    main()
    
    def _load_state(self) -> Dict:
        """加载保存的状态"""
        try:
            state_path = Path(self.STATE_FILE)
            if state_path.exists():
                with open(state_path, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                logger.info(f"已加载保存的状态 (已有 {len(state.get('videos', []))} 个视频)")
                return state
        except Exception as e:
            logger.warning(f"加载状态文件失败: {e}")
        
        return {'videos': []}
    
    def _save_state(self):
        """保存爬虫状态"""
        if not self.enable_checkpoint:
            return
        
        try:
            state = {
                'videos': self.videos,
                'last_update': datetime.now().isoformat()
            }
            
            with open(self.STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            logger.info(f"进度已保存 ({len(self.videos)} 个视频)")
        except Exception as e:
            logger.error(f"保存状态失败: {e}")
    
    def fetch_videos(self) -> List[Dict[str, str]]:
        """从 missav_api 获取视频"""
        
        # 加载之前保存的视频
        if self.state.get('videos'):
            self.videos = self.state['videos']
            logger.info(f"已加载 {len(self.videos)} 个旧视频")
        
        try:
            from missav_api import Client
            
            logger.info("使用 missav_api 库获取视频...")
            client = Client()
            
            video_count = 0
            
            logger.info("开始获取视频列表...")
            
            try:
                # 只测试前 2 页的数据
                queries = ["", " "]  # 只测试 2 个查询
                
                all_processed_codes = set()
                
                for query_idx, query in enumerate(queries):
                    logger.info(f"尝试查询 {query_idx + 1}/{len(queries)}: '{query}'")
                    
                    try:
                        # 每个查询只获取 50 个视频（用于测试）
                        search_results = client.search(query=query, video_count=50)
                        
                        result_count = 0
                        for video in search_results:
                            try:
                                # 从 Video 对象中提取信息
                                video_code = video.video_code
                                m3u8_url = video.m3u8_base_url
                                
                                result_count += 1
                                
                                if result_count == 1:
                                    logger.info(f"  首个视频: {video_code}")
                                    logger.info(f"  M3U8 URL: {m3u8_url}")
                                
                                if video_code and video_code not in all_processed_codes and video_code not in self.processed_codes:
                                    if not m3u8_url:
                                        m3u8_url = ""
                                    
                                    self.videos.append({
                                        'code': str(video_code),
                                        'url': str(m3u8_url)
                                    })
                                    self.processed_codes.add(video_code)
                                    all_processed_codes.add(video_code)
                                    video_count += 1
                                    
                                    logger.info(f"✓ 获取: {video_code}")
                                
                                time.sleep(0.02)
                            
                            except Exception as e:
                                logger.debug(f"处理视频时出错: {e}")
                                continue
                        
                        logger.info(f"  本次查询获取 {result_count} 个结果，新增 {video_count} 个视频\n")
                        
                        time.sleep(1)
                    
                    except Exception as e:
                        logger.warning(f"查询 '{query}' 失败: {e}")
                        continue
                
                logger.info(f"\n爬虫完成! 总共获取 {len(self.videos)} 个视频")
                
            except KeyboardInterrupt:
                logger.info("用户中断")
            except Exception as e:
                logger.error(f"获取视频时出错: {e}")
                if len(self.videos) == 0:
                    raise
            
            self._save_state()
            return self.videos
        
        except ImportError:
            logger.error("未安装 missav_api 库，请运行: pip install missav-api")
            sys.exit(1)
    
    def save_to_m3u(self):
        """将数据保存为 m3u 格式"""
        logger.info(f"开始保存为 m3u 格式: {self.output_file}")
        
        if not self.videos:
            logger.warning("没有视频数据可保存")
            return False
        
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                # 写入 M3U 头
                f.write('#EXTM3U\n')
                
                for i, video in enumerate(self.videos, 1):
                    code = video.get('code', 'Unknown')
                    url = video.get('url', '')
                    
                    if not url:
                        logger.warning(f"跳过无效的 URL: {code}")
                        continue
                    
                    # 按照指定格式写入
                    f.write(f'#EXTINF:-1 group-title="成人频道" tvg-name="{code}" tvg-logo="" epg-url="",{code}\n')
                    f.write(f'{url}\n')
                    
                    if i % 100 == 0:
                        logger.info(f"已保存 {i} 个视频...")
                
                logger.info(f"成功保存 {len(self.videos)} 个视频到 {self.output_file}")
                return True
        
        except Exception as e:
            logger.error(f"保存 m3u 文件时出错: {e}")
            return False
    
    def run(self):
        """运行爬虫"""
        logger.info("=" * 50)
        logger.info("MissAV 爬虫程序启动")
        logger.info("=" * 50)
        
        try:
            self.fetch_videos()
            if self.videos:
                self.save_to_m3u()
                logger.info("=" * 50)
                logger.info(f"✓ 爬虫完成! 已保存 {len(self.videos)} 个视频")
                logger.info("=" * 50)
            else:
                logger.warning("未获取到任何视频")
        
        except KeyboardInterrupt:
            logger.info("用户中断")
            self._save_state()
        except Exception as e:
            logger.error(f"爬虫运行失败: {e}")
            self._save_state()
            sys.exit(1)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='MissAV 爬虫 - 爬取 missav 视频并生成 M3U 列表',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python scraper_final.py                    # 基本使用
  python scraper_final.py -o custom.m3u      # 自定义输出文件
  python scraper_final.py --no-checkpoint    # 不保存进度
        '''
    )
    
    parser.add_argument('-o', '--output', default='missav.m3u', help='输出文件名 (默认: missav.m3u)')
    parser.add_argument('-c', '--checkpoint', dest='checkpoint', action='store_true', default=True, help='启用断点续爬 (默认)')
    parser.add_argument('--no-checkpoint', dest='checkpoint', action='store_false', help='禁用断点续爬')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细日志输出')
    parser.add_argument('--clean', action='store_true', help='清除保存的进度')
    
    args = parser.parse_args()
    
    # 调整日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 处理 --clean 参数
    if args.clean:
        try:
            Path(MissAVScraper.STATE_FILE).unlink()
            print(f"✓ 已清除进度文件")
        except FileNotFoundError:
            print("进度文件不存在")
        return
    
    # 创建爬虫并运行
    scraper = MissAVScraper(output_file=args.output, enable_checkpoint=args.checkpoint)
    scraper.run()


if __name__ == '__main__':
    main()
