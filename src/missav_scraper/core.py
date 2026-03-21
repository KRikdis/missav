#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心爬虫模块

包含 MissAVScraper 主爬虫类，支持增量更新、去重、断点续爬、限制收集数量
"""

import json
import sys
import logging
from pathlib import Path
from typing import List, Dict, Set
from datetime import datetime

from . import constants
from . import utils

logger = logging.getLogger(__name__)


class MissAVScraper:
    """
    MissAV 爬虫类
    
    支持功能：
    - 增量更新：追加模式保存 M3U 文件
    - 去重：自动检查和跳过重复 URL
    - 断点续爬：保存爬虫状态，支持中断后继续
    - 限制收集：每次运行最多收集指定数量的视频
    - 限流：自动添加延迟，避免 IP 被限制
    
    属性：
        output_file: M3U 输出文件路径
        enable_checkpoint: 是否启用断点续爬
        max_videos: 每次运行最多收集的视频数
        videos: 本次收集的视频列表
        existing_urls: 已存在的 URL 集合（用于去重）
    """
    
    def __init__(self, 
                 output_file: str = None,
                 enable_checkpoint: bool = True,
                 max_videos: int = None,
                 verbose: bool = False):
        """
        初始化爬虫
        
        Args:
            output_file: M3U 输出文件路径 (可选，默认 output/missav.m3u)
            enable_checkpoint: 是否启用断点续爬 (默认 True)
            max_videos: 每次运行最多收集的视频数 (默认 500)
            verbose: 是否启用详细日志 (默认 False)
        """
        # 设置日志
        utils.setup_logging(verbose)
        
        # 初始化输出文件路径
        if output_file is None:
            output_file = str(Path(constants.OUTPUT_DIR) / constants.OUTPUT_FILE)
        self.output_file = str(output_file)
        
        # 初始化爬虫参数
        self.enable_checkpoint = enable_checkpoint
        self.max_videos = max_videos or constants.MAX_VIDEOS_PER_RUN
        self.scraper_mode = constants.SCRAPER_MODE  # 爬虫模式: single-query 或 batch-actresses
        
        # 初始化数据结构
        self.videos: List[Dict[str, str]] = []
        self.processed_codes: Set[str] = set()
        self.request_count = 0
        
        # 多参数相关
        self.search_queries = constants.ACTRESS_SEARCH_LIST if self.scraper_mode == "batch-actresses" else constants.DEFAULT_QUERIES
        self.current_query_index = 0
        self.query_group_mapping = {}  # 映射: 查询 -> group_title
        
        # 加载已存在的 URL（用于去重）
        self.existing_urls: Set[str] = utils.load_existing_urls(self.output_file)
        
        # 加载保存的状态
        self.state = self._load_state() if enable_checkpoint else {}
        if self.state.get('videos'):
            self.videos = self.state['videos']
            self.processed_codes = set(v['code'] for v in self.videos)
        
        # 从状态恢复当前查询索引
        self.current_query_index = self.state.get('current_query_index', 0)
        self.query_group_mapping = self.state.get('query_group_mapping', {})
        
        # 输出启动信息
        self._print_startup_info()
    
    def _print_startup_info(self) -> None:
        """打印爬虫启动信息"""
        logger.info("=" * 70)
        logger.info("爬虫启动参数:")
        
        if self.scraper_mode == "batch-actresses":
            logger.info(f"  模式: 批量获取演员视频")
            logger.info(f"  总演员数: {len(self.search_queries)}")
            logger.info(f"  当前进度: {self.current_query_index + 1}/{len(self.search_queries)}")
            logger.info(f"  当前演员: {self.search_queries[self.current_query_index]}")
        else:
            logger.info(f"  模式: 单查询模式")
            logger.info(f"  查询字符串: {self.search_queries}")
        
        logger.info(f"  每个查询获取: {constants.VIDEOS_PER_QUERY} 个视频")
        logger.info(f"  本次运行限制: 最多 {self.max_videos} 个视频")
        logger.info(f"  已存在的 M3U 条目: {len(self.existing_urls)} 个 URL")
        logger.info(f"  已处理视频: {len(self.videos)} 个")
        logger.info(f"  断点续爬: {'启用' if self.enable_checkpoint else '禁用'}")
        logger.info("=" * 70)
    
    def _load_state(self) -> Dict:
        """
        加载保存的爬虫状态（用于断点续爬）
        
        Returns:
            包含保存状态的字典
        """
        try:
            state_path = Path(constants.STATE_FILE)
            if state_path.exists():
                with open(state_path, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                logger.info(f"已加载保存的状态 (已有 {len(state.get('videos', []))} 个视频)")
                return state
        except Exception as e:
            logger.warning(f"加载状态文件失败: {e}")
        
        return {'videos': []}
    
    def _save_state(self) -> None:
        """保存爬虫状态（用于断点续爬）"""
        if not self.enable_checkpoint:
            return
        
        try:
            state = {
                'videos': self.videos,
                'existing_urls_count': len(self.existing_urls),
                'last_update': datetime.now().isoformat(),
                'total_videos_processed': len(self.processed_codes),
                'current_query_index': self.current_query_index,
                'current_query': self.search_queries[self.current_query_index] if self.current_query_index < len(self.search_queries) else None,
                'query_group_mapping': self.query_group_mapping,
                'scraper_mode': self.scraper_mode,
                'total_queries': len(self.search_queries)
            }
            
            with open(constants.STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            logger.debug(f"进度已保存 (查询 {self.current_query_index + 1}/{len(self.search_queries)}, {len(self.videos)} 个视频)")
        except Exception as e:
            logger.error(f"保存状态失败: {e}")
    
    def fetch_videos(self) -> List[Dict[str, str]]:
        """
        从 missav_api 获取视频 (支持单查询和多参数轮转)
        
        Returns:
            获取到的视频列表
            
        Raises:
            ImportError: 如果 missav_api 未安装
        """
        try:
            from missav_api import Client
        except ImportError:
            logger.error(constants.ERROR_NO_API)
            sys.exit(1)
        
        logger.info(f"使用 missav_api 库获取视频 (限制: {self.max_videos} 条)...")
        logger.info(f"限流配置: {constants.MIN_DELAY}-{constants.MAX_DELAY}秒/请求, 批次延迟{constants.BATCH_DELAY}秒")
        
        client = Client()
        
        logger.info(f"开始获取视频列表...")
        
        try:
            # 多参数批量模式：从current_query_index开始，处理剩余的所有查询
            if self.scraper_mode == "batch-actresses":
                remaining_queries = self.search_queries[self.current_query_index:]
                logger.info(f"批量模式: 处理 {len(remaining_queries)} 个演员 (从第 {self.current_query_index + 1} 个开始)")
            else:
                remaining_queries = self.search_queries
                logger.info(f"单查询模式: 处理 {len(remaining_queries)} 个查询")
            
            for query_offset, query in enumerate(remaining_queries):
                # 计算真实的查询索引
                real_query_idx = self.current_query_index + query_offset
                
                # 批量模式中，当所有演员都处理完毕时，停止
                if self.scraper_mode == "batch-actresses" and real_query_idx >= len(self.search_queries):
                    logger.info(f"\n✅ 所有 {len(self.search_queries)} 个演员已处理完毕！爬虫任务完成")
                    break
                
                remaining = self.max_videos - len(self.videos)
                logger.info(f"\n{'='*70}")
                logger.info(f"查询 {real_query_idx + 1}/{len(self.search_queries)}: '{query}' (本次配额: {remaining} 条)")
                
                try:
                    # 获取本次查询的视频列表
                    search_results = client.search(
                        query=query,
                        video_count=constants.VIDEOS_PER_QUERY
                    )
                    
                    result_count = 0
                    new_videos_count = 0
                    for video in search_results:
                        # 检查是否已达到本次运行限制
                        if len(self.videos) >= self.max_videos:
                            logger.info(f"  已达到本次运行限制，停止处理此查询")
                            break
                        
                        result_count += 1
                        
                        try:
                            # 提取视频信息
                            video_code = video.video_code
                            m3u8_url = video.m3u8_base_url or ""
                            
                            if result_count == 1:
                                logger.info(f"  ✓ 首个视频: {video_code}")
                            
                            # 即使是重复视频，在多参数模式下也保存（用户要求不去重）
                            # 但仍然记录group_title用于M3U生成
                            if video_code not in self.processed_codes:
                                new_videos_count += 1
                            
                            # 提取 genres 和 thumbnail
                            genres = []
                            thumbnail = ""
                            
                            try:
                                if hasattr(video, 'genres'):
                                    genres_raw = video.genres
                                    if isinstance(genres_raw, list):
                                        genres = genres_raw
                                    elif genres_raw:
                                        genres = [genres_raw]
                                
                                if hasattr(video, 'thumbnail'):
                                    thumbnail = video.thumbnail or ""
                            except Exception as e:
                                logger.debug(f"提取 genres/thumbnail 时出错: {e}")
                            
                            # 规范化 genres
                            genres = utils.normalize_genres(genres)
                            
                            # 保存视频信息（包含group_title用于后续M3U生成）
                            video_entry = {
                                'code': str(video_code),
                                'url': str(m3u8_url),
                                'genres': genres,
                                'thumbnail': thumbnail,
                                'group_title': query  # 添加group_title字段
                            }
                            self.videos.append(video_entry)
                            
                            if video_code not in self.processed_codes:
                                self.processed_codes.add(str(video_code))
                                # 输出日志
                                info_str = utils.format_video_info(video_code, genres)
                                logger.info(f"    - 新增: {info_str}")
                            
                            # 请求间延迟
                            utils.random_delay(0.5, 1.5)
                            self.request_count += 1
                        
                        except Exception as e:
                            logger.debug(f"处理视频时出错: {e}")
                            continue
                    
                    logger.info(f"  本次查询结果: {result_count} 个 (新增: {new_videos_count} 个)")
                    
                    # 更新进度
                    self.current_query_index = real_query_idx + 1
                    if self.scraper_mode == "batch-actresses":
                        self.query_group_mapping[query] = len([v for v in self.videos if v.get('group_title') == query])
                    
                    # 定期保存状态
                    self._save_state()
                    
                    # 批次间延迟
                    if (real_query_idx + 1) % 5 == 0:
                        logger.info(f"⏸ 批量请求完成，暂停 {constants.BATCH_DELAY} 秒...")
                        import time
                        time.sleep(constants.BATCH_DELAY)
                    else:
                        utils.random_delay()
                
                except Exception as e:
                    logger.warning(f"查询 '{query}' 失败: {e}")
                    utils.random_delay(5, 10)
                    continue
            
            logger.info(f"\n{'='*70}")
            logger.info(f"爬虫完成! 本次获取 {len(self.videos)} 个视频")
            logger.info(f"总请求数: {self.request_count}")
            if self.scraper_mode == "batch-actresses":
                logger.info(f"已处理演员: {self.current_query_index}/{len(self.search_queries)}")
            logger.info(f"{'='*70}")
            
        except KeyboardInterrupt:
            logger.info("用户中断")
        except Exception as e:
            logger.error(f"获取视频时出错: {e}")
            if len(self.videos) == 0:
                raise
        
        self._save_state()
        return self.videos
    
    def save_to_m3u(self) -> bool:
        """
        将数据保存为 M3U 格式
        
        特点：
        - 增量更新：以追加模式保存
        - 去重：检查并跳过重复 URL
        - 多 genre 支持：为每个 genre 创建独立条目
        
        Returns:
            保存成功返回 True，失败返回 False
        """
        logger.info(f"开始保存为 M3U 格式: {self.output_file}")
        
        if not self.videos:
            logger.warning(constants.WARNING_NO_DATA)
            return False
        
        try:
            # 确保输出目录存在
            output_path = utils.ensure_output_directory(self.output_file)
            
            total_new_entries = 0
            skipped_duplicates = 0
            skipped_invalid = 0
            
            # 检查文件是否已存在
            file_exists = output_path.exists() and output_path.stat().st_size > 0
            
            # 以追加模式打开文件
            with open(output_path, 'a', encoding='utf-8') as f:
                # 如果文件不存在或为空，写入 M3U 头
                if not file_exists:
                    f.write(f'{constants.M3U_HEADER}\n')
                    logger.info("✓ 创建新的 M3U 文件")
                else:
                    logger.info("✓ 追加到现有的 M3U 文件")
                
                # 处理每个视频
                for video in self.videos:
                    code = video.get('code', 'Unknown')
                    url = video.get('url', '')
                    genres = video.get('genres', [])
                    thumbnail = video.get('thumbnail', '')
                    
                    # 使用video中的group_title，如果没有则使用默认值
                    group_title = video.get('group_title', constants.M3U_GROUP_TITLE)
                    
                    # 检查 URL 有效性
                    if not url:
                        logger.warning(f"跳过无效的 URL: {code}")
                        skipped_invalid += 1
                        continue
                    
                    # 检查重复 URL
                    if url in self.existing_urls:
                        logger.debug(f"跳过重复的 URL: {code}")
                        skipped_duplicates += 1
                        continue
                    
                    # 使用video指定的group_title（按演员分类）或默认值
                    extinf = constants.M3U_EXTINF_FORMAT.format(
                        group=group_title,
                        code=code,
                        logo=thumbnail
                    )
                    f.write(f'{extinf}\n')
                    f.write(f'{url}\n')
                    
                    total_new_entries += 1
                    self.existing_urls.add(url)
            
            # 输出保存统计信息
            logger.info(f"✓ 本次新增 {total_new_entries} 个条目")
            if skipped_duplicates > 0:
                logger.info(f"  跳过重复 {skipped_duplicates} 个")
            if skipped_invalid > 0:
                logger.info(f"  跳过无效 {skipped_invalid} 个")
            logger.info(f"  文件: {self.output_file}")
            return True
        
        except Exception as e:
            logger.error(f"保存 M3U 文件时出错: {e}")
            return False
    
    def run(self) -> None:
        """
        运行爬虫完整流程
        
        流程：
        1. 获取视频列表
        2. 保存为 M3U 格式
        3. 输出统计信息
        """
        logger.info("=" * 60)
        logger.info("MissAV 爬虫程序启动")
        logger.info("=" * 60)
        
        try:
            self.fetch_videos()
            if self.videos:
                self.save_to_m3u()
                logger.info("=" * 60)
                logger.info(f"✓ 爬虫完成!")
                logger.info(f"  所有 M3U 条目数: {len(self.existing_urls)}")
                logger.info(f"  本次处理: {len(self.videos)} 个视频")
                logger.info("=" * 60)
            else:
                logger.warning(constants.WARNING_NO_DATA)
        
        except KeyboardInterrupt:
            logger.info("用户中断，保存进度中...")
            self._save_state()
        except Exception as e:
            logger.error(f"爬虫运行失败: {e}")
            self._save_state()
            sys.exit(1)
    
    def clean_state(self, clean_output: bool = False) -> None:
        """
        清除保存的进度状态
        
        Args:
            clean_output: 是否同时删除输出文件
        """
        try:
            state_path = Path(constants.STATE_FILE)
            if state_path.exists():
                state_path.unlink()
                logger.info(f"✓ 已清除进度文件: {constants.STATE_FILE}")
        except Exception as e:
            logger.error(f"清除进度文件失败: {e}")
        
        if clean_output:
            try:
                output_path = Path(self.output_file)
                if output_path.exists():
                    output_path.unlink()
                    logger.info(f"✓ 已清除输出文件: {self.output_file}")
            except Exception as e:
                logger.error(f"清除输出文件失败: {e}")
