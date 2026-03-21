#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MissAV M3U 爬虫脚本 (最终版本 - 带限流、增量更新、去重)
支持增量更新、URL 去重、断点续爬
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
    """MissAV 爬虫类 - 支持增量更新、去重、限制收集数量"""
    
    STATE_FILE = 'scraper_state.json'
    MAX_RETRIES = 3
    
    # 限流配置
    MIN_DELAY = 2      # 最小延迟 2 秒
    MAX_DELAY = 5      # 最大延迟 5 秒
    BATCH_SIZE = 10    # 每批最多 10 个请求
    BATCH_DELAY = 15   # 批次间延迟 15 秒
    
    # 爬虫起始参数（便于查看和修改）
    DEFAULT_QUERIES = ["a", "b", "c", "d", "e"]  # 查询字符串
    VIDEOS_PER_QUERY = 50                         # 每个查询获取的视频数
    MAX_VIDEOS_PER_RUN = 500                      # 每次运行最多收集的视频数
    
    def __init__(self, output_file: str = 'missav.m3u', enable_checkpoint: bool = True, max_videos: int = None):
        self.output_file = output_file
        self.enable_checkpoint = enable_checkpoint
        self.max_videos = max_videos or self.MAX_VIDEOS_PER_RUN  # 每次运行最多收集的视频数
        self.videos: List[Dict[str, str]] = []
        self.state = self._load_state() if enable_checkpoint else {}
        self.processed_codes: set = set(v['code'] for v in self.state.get('videos', []))
        self.request_count = 0
        self.total_collected = 0  # 本次运行已收集的数量
        
        # 读取已存在的 M3U 文件，提取 URL 用于去重
        self.existing_urls: set = self._load_existing_urls()
        
        # 清楚显示爬虫起始参数
        logger.info("=" * 70)
        logger.info("爬虫起始参数:")
        logger.info(f"  查询字符串: {self.DEFAULT_QUERIES}")
        logger.info(f"  每个查询获取: {self.VIDEOS_PER_QUERY} 个视频")
        logger.info(f"  本次运行限制: 最多 {self.max_videos} 个视频")
        logger.info(f"  已存在的 M3U 条目: {len(self.existing_urls)} 个 URL")
        logger.info("=" * 70)
    
    def _random_delay(self, min_delay=None, max_delay=None):
        """随机延迟，避免被限制"""
        min_delay = min_delay or self.MIN_DELAY
        max_delay = max_delay or self.MAX_DELAY
        delay = random.uniform(min_delay, max_delay)
        logger.debug(f"延迟 {delay:.2f} 秒...")
        time.sleep(delay)
    
    def _load_existing_urls(self) -> set:
        """从现有的 M3U 文件中读取所有 URL，用于去重
        
        Returns:
            包含所有已存在 URL 的集合
        """
        existing_urls = set()
        try:
            m3u_path = Path(self.output_file)
            if m3u_path.exists():
                with open(m3u_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        # 提取 URL（不以 # 开头的行）
                        if line and not line.startswith('#'):
                            existing_urls.add(line)
                
                if existing_urls:
                    logger.info(f"从 {self.output_file} 读取到 {len(existing_urls)} 个已存在的 URL")
        except Exception as e:
            logger.warning(f"读取现有 M3U 文件失败: {e}")
        
        return existing_urls
    
    def _load_state(self) -> Dict:
        """加载保存的状态（用于断点续爬）"""
        try:
            state_path = Path(self.STATE_FILE)
            if state_path.exists():
                with open(state_path, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                logger.info(f"已加载保存的状态 (已有 {len(state.get('videos', []))} 个视频, {state.get('existing_urls_count', 0)} 个 URL)")
                return state
        except Exception as e:
            logger.warning(f"加载状态文件失败: {e}")
        
        return {'videos': []}
    
    def _save_state(self):
        """保存爬虫状态（用于断点续爬）"""
        if not self.enable_checkpoint:
            return
        
        try:
            state = {
                'videos': self.videos,
                'existing_urls_count': len(self.existing_urls),
                'last_update': datetime.now().isoformat(),
                'total_videos_processed': len(self.processed_codes)
            }
            
            with open(self.STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            logger.debug(f"进度已保存 ({len(self.videos)} 个新视频, 已有 {len(self.existing_urls)} 个 URL)")
        except Exception as e:
            logger.error(f"保存状态失败: {e}")
    
    def fetch_videos(self) -> List[Dict[str, str]]:
        """从 missav_api 获取视频（受限制，最多 max_videos 条）"""
        
        # 加载之前保存的视频
        if self.state.get('videos'):
            self.videos = self.state['videos']
            logger.info(f"已加载 {len(self.videos)} 个旧视频")
        
        try:
            from missav_api import Client
            
            logger.info(f"使用 missav_api 库获取视频 (限制: {self.max_videos} 条)...")
            logger.info(f"限流配置: {self.MIN_DELAY}-{self.MAX_DELAY}秒/请求, 批次延迟{self.BATCH_DELAY}秒")
            
            client = Client()
            
            logger.info(f"开始获取视频列表...")
            
            try:
                # 使用起始参数中的查询字符串
                queries = self.DEFAULT_QUERIES
                
                all_processed_codes = set()
                batch_count = 0
                
                for query_idx, query in enumerate(queries):
                    # 检查是否已达到限制
                    if len(self.videos) >= self.max_videos:
                        logger.info(f"\n⏹ 已达到本次运行限制 ({self.max_videos} 条)，停止爬虫")
                        break
                    
                    batch_count += 1
                    remaining = self.max_videos - len(self.videos)
                    logger.info(f"\n查询 {query_idx + 1}/{len(queries)}: '{query}' (第 {batch_count} 批, 剩余配额: {remaining} 条)")
                    
                    try:
                        # 每个查询获取 VIDEOS_PER_QUERY 个视频
                        search_results = client.search(query=query, video_count=self.VIDEOS_PER_QUERY)
                        
                        result_count = 0
                        for video in search_results:
                            # 检查是否已达到限制
                            if len(self.videos) >= self.max_videos:
                                logger.info(f"  已达到配额，停止处理此查询")
                                break
                            
                            try:
                                # 从 Video 对象中提取信息
                                video_code = video.video_code
                                m3u8_url = video.m3u8_base_url
                                
                                result_count += 1
                                
                                if result_count == 1:
                                    logger.info(f"  ✓ 首个视频: {video_code}")
                                
                                if video_code and video_code not in all_processed_codes and video_code not in self.processed_codes:
                                    if not m3u8_url:
                                        m3u8_url = ""
                                    
                                    # 提取 genres 和 thumbnail
                                    genres = []
                                    thumbnail = ""
                                    
                                    try:
                                        if hasattr(video, 'genres'):
                                            genres = video.genres if isinstance(video.genres, list) else [video.genres] if video.genres else []
                                        if hasattr(video, 'thumbnail'):
                                            thumbnail = video.thumbnail or ""
                                    except Exception as e:
                                        logger.debug(f"提取 genres/thumbnail 时出错: {e}")
                                    
                                    self.videos.append({
                                        'code': str(video_code),
                                        'url': str(m3u8_url),
                                        'genres': genres,
                                        'thumbnail': thumbnail
                                    })
                                    self.processed_codes.add(video_code)
                                    all_processed_codes.add(video_code)
                                    
                                    genres_str = ', '.join(genres) if genres else 'N/A'
                                    logger.info(f"    - 新增: {video_code} | 分类: {genres_str}")
                                
                                # 每个视频请求之间添加随机延迟
                                self._random_delay(0.5, 1.5)
                                self.request_count += 1
                            
                            except Exception as e:
                                logger.debug(f"处理视频时出错: {e}")
                                continue
                        
                        logger.info(f"  本次查询: {result_count} 个结果，新增 {len(self.videos)} 个视频")
                        
                        # 批次间延迟
                        if (query_idx + 1) % 5 == 0:
                            logger.info(f"⏸ 批量请求完成，暂停 {self.BATCH_DELAY} 秒...")
                            time.sleep(self.BATCH_DELAY)
                        else:
                            self._random_delay()
                    
                    except Exception as e:
                        logger.warning(f"查询 '{query}' 失败: {e}")
                        self._random_delay(5, 10)
                        continue
                
                logger.info(f"\n{'='*70}")
                logger.info(f"爬虫完成! 本次获取 {len(self.videos)} 个视频")
                logger.info(f"总请求数: {self.request_count}")
                logger.info(f"{'='*70}")
                
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
        """将数据保存为 m3u 格式（增量更新 + 去重）
        
        对于每个视频的每个 genre，创建独立的 M3U 条目
        使用 genres 作为 group-title，thumbnail 作为 tvg-logo
        检查重复 URL，只保存新的条目
        """
        logger.info(f"开始保存为 m3u 格式: {self.output_file} (增量更新模式)")
        
        if not self.videos:
            logger.warning("没有视频数据可保存")
            return False
        
        try:
            total_new_entries = 0
            skipped_duplicates = 0
            skipped_invalid = 0
            
            # 检查是否需要写入 M3U 头
            m3u_path = Path(self.output_file)
            file_exists = m3u_path.exists() and m3u_path.stat().st_size > 0
            
            # 以追加模式打开文件
            with open(self.output_file, 'a', encoding='utf-8') as f:
                # 如果文件不存在或为空，写入 M3U 头
                if not file_exists:
                    f.write('#EXTM3U\n')
                    logger.info("✓ 创建新的 M3U 文件")
                else:
                    logger.info("✓ 追加到现有的 M3U 文件")
                
                for video in self.videos:
                    code = video.get('code', 'Unknown')
                    url = video.get('url', '')
                    genres = video.get('genres', [])
                    thumbnail = video.get('thumbnail', '')
                    
                    if not url:
                        logger.warning(f"跳过无效的 URL: {code}")
                        skipped_invalid += 1
                        continue
                    
                    # 检查 URL 是否已存在（去重）
                    if url in self.existing_urls:
                        logger.debug(f"跳过重复的 URL: {code}")
                        skipped_duplicates += 1
                        continue
                    
                    # 如果 genres 为空，创建一个默认条目
                    if not genres or (isinstance(genres, list) and len(genres) == 0):
                        genres = ['未分类']
                    
                    # 为每个 genre 创建独立的 M3U 条目
                    for genre in genres:
                        genre_str = str(genre).strip() if genre else '未分类'
                        
                        # 按照指定格式写入
                        f.write(f'#EXTINF:-1 group-title="{genre_str}" tvg-name="{code}" tvg-logo="{thumbnail}" epg-url="",{code}\n')
                        f.write(f'{url}\n')
                        
                        total_new_entries += 1
                        self.existing_urls.add(url)  # 添加到已存在集合
                
                logger.info(f"✓ 本次新增 {total_new_entries} 个条目")
                if skipped_duplicates > 0:
                    logger.info(f"  跳过重复 {skipped_duplicates} 个")
                if skipped_invalid > 0:
                    logger.info(f"  跳过无效 {skipped_invalid} 个")
                logger.info(f"  文件: {self.output_file}")
                return True
        
        except Exception as e:
            logger.error(f"保存 m3u 文件时出错: {e}")
            return False
    
    def run(self):
        """运行爬虫"""
        logger.info("=" * 60)
        logger.info("MissAV 爬虫程序启动 (支持增量更新、去重、断点续爬)")
        logger.info("=" * 60)
        
        try:
            self.fetch_videos()
            if self.videos:
                self.save_to_m3u()
                logger.info("=" * 60)
                logger.info(f"✓ 爬虫完成!")
                logger.info(f"  总 M3U 条目数: {len(self.existing_urls)}")
                logger.info(f"  本次处理: {len(self.videos)} 个视频")
                logger.info("=" * 60)
            else:
                logger.warning("未获取到任何新视频")
        
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
        description='MissAV 爬虫 - 支持增量更新、去重、断点续爬、限制收集数量',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python scraper_final.py                    # 基本使用（默认 500 条）
  python scraper_final.py -o custom.m3u      # 自定义输出文件
  python scraper_final.py --max-videos 1000  # 每次收集 1000 条
  python scraper_final.py -v                 # 详细日志输出
  python scraper_final.py --clean            # 清除进度文件（但保留 M3U）
  python scraper_final.py --clean-all        # 清除进度和 M3U 文件

起始参数:
  查询字符串: a, b, c, d, e (5个字母)
  每个查询获取: 50 个视频
  本次运行限制: 默认 500 条 (可通过 --max-videos 修改)
        '''
    )
    
    parser.add_argument('-o', '--output', default='missav.m3u', help='输出文件名 (默认: missav.m3u)')
    parser.add_argument('--max-videos', type=int, default=500, help='每次运行最多收集的视频数 (默认: 500)')
    parser.add_argument('-c', '--checkpoint', dest='checkpoint', action='store_true', default=True, help='启用断点续爬 (默认)')
    parser.add_argument('--no-checkpoint', dest='checkpoint', action='store_false', help='禁用断点续爬')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细日志输出')
    parser.add_argument('--clean', action='store_true', help='清除保存的进度文件（保留 M3U）')
    parser.add_argument('--clean-all', action='store_true', help='清除进度文件和 M3U 文件')
    
    args = parser.parse_args()
    
    # 调整日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 处理 --clean 参数
    if args.clean:
        try:
            Path(MissAVScraper.STATE_FILE).unlink()
            print(f"✓ 已清除进度文件: {MissAVScraper.STATE_FILE}")
            print(f"  注意: M3U 文件 {args.output} 已保留")
        except FileNotFoundError:
            print("进度文件不存在")
        return
    
    # 处理 --clean-all 参数
    if args.clean_all:
        try:
            Path(MissAVScraper.STATE_FILE).unlink()
            print(f"✓ 已清除进度文件: {MissAVScraper.STATE_FILE}")
        except FileNotFoundError:
            pass
        
        try:
            Path(args.output).unlink()
            print(f"✓ 已清除输出文件: {args.output}")
        except FileNotFoundError:
            print("输出文件不存在")
        return
    
    # 创建爬虫并运行
    scraper = MissAVScraper(
        output_file=args.output,
        enable_checkpoint=args.checkpoint,
        max_videos=args.max_videos
    )
    scraper.run()


if __name__ == '__main__':
    main()
