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
    - 断点续爬：保存爬虫状态，支持中断后继续
    - 限制收集：每次运行最多收集指定数量的视频
    - 限流：自动添加延迟，避免 IP 被限制
    - 批量处理：支持多演员轮转，每个演员视频按不同 group_title 分类

    属性：
        output_file: M3U 输出文件路径
        enable_checkpoint: 是否启用断点续爬
        max_videos: 每次运行最多收集的视频数
        videos: 本次收集的视频列表
        existing_urls: 已存在的 URL 集合（用于统计）
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
        self.scraper_mode = constants.SCRAPER_MODE  # 爬虫模式: "video-codes", "batch-actresses", "single-query"

        # 初始化数据结构
        self.videos: List[Dict[str, str]] = []      # 所有已收集的视频条目（用于状态保存）
        self.new_entries: List[Dict[str, str]] = [] # 本次运行新增的条目（用于写入 M3U）
        self.processed_codes: Set[str] = set()      # 已处理（获取）的视频代码集合
        self.request_count = 0
        self.existing_entries: Set[tuple] = set()  # 已存在的 M3U 条目集合 (code, url)，用于去重（包含历史）

        # 根据模式选择搜索列表
        if self.scraper_mode == "batch-actresses":
            self.search_queries = constants.ACTRESS_SEARCH_LIST
        elif self.scraper_mode == "single-query":
            self.search_queries = constants.DEFAULT_QUERIES
        elif self.scraper_mode == "video-codes":
            self.search_queries = constants.VIDEO_CODE_LIST
        else:
            logger.warning(f"未知的爬虫模式: {self.scraper_mode}, 回退到 video-codes 模式")
            self.search_queries = constants.VIDEO_CODE_LIST

        self.current_query_index = 0
        self.query_group_mapping = {}  # 映射: 查询 -> 数量统计 (仅 batch-actresses 使用)

        # 加载已存在的 URL（用于统计）
        self.existing_urls: Set[str] = utils.load_existing_urls(self.output_file)

        # 加载保存的状态
        self.state = self._load_state() if enable_checkpoint else {}
        if self.state.get('videos'):
            self.videos = self.state['videos']
            self.processed_codes = set(v['code'] for v in self.videos)

        # 从状态恢复当前查询索引
        self.current_query_index = self.state.get('current_query_index', 0)
        self.query_group_mapping = self.state.get('query_group_mapping', {})

        # 构建 existing_entries 集合用于去重 (包含已保存的条目)
        for v in self.videos:
            self.existing_entries.add((v['group_title'], v['url']))
        
        # 输出启动信息
        self._print_startup_info()
    
    def _print_startup_info(self) -> None:
        """打印爬虫启动信息"""
        logger.info("=" * 70)
        logger.info("爬虫启动参数:")

        if self.scraper_mode == "batch-actresses":
            logger.info(f"  模式: 批量获取演员视频 (使用 search)")
            logger.info(f"  总演员数: {len(self.search_queries)}")
            logger.info(f"  当前进度: {self.current_query_index + 1}/{len(self.search_queries)}")
            logger.info(f"  当前演员: {self.search_queries[self.current_query_index]}")
        elif self.scraper_mode == "single-query":
            logger.info(f"  模式: 单查询模式 (使用 search)")
            logger.info(f"  查询列表: {len(self.search_queries)} 个查询")
        elif self.scraper_mode == "video-codes":
            logger.info(f"  模式: 视频代码模式 (使用 get_video)")
            logger.info(f"  总视频代码数: {len(self.search_queries)}")
            logger.info(f"  当前进度: {self.current_query_index + 1}/{len(self.search_queries)}")
            if self.current_query_index < len(self.search_queries):
                logger.info(f"  当前代码: {self.search_queries[self.current_query_index]}")
        else:
            logger.info(f"  模式: 未知 ({self.scraper_mode})")

        logger.info(f"  本次运行限制: 最多 {self.max_videos} 个 M3U 条目")
        logger.info(f"  已存在的 M3U 条目: {len(self.existing_urls)} 个 URL")
        logger.info(f"  已处理视频代码: {len(self.processed_codes)} 个")
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
    
    def _process_video_object(self, video_obj, source_query: str) -> int:
        """
        处理单个视频对象，创建M3U条目
        
        此方法提取了video-codes和搜索模式中重复的视频处理逻辑
        
        Args:
            video_obj: 视频对象（包含video_code、m3u8_base_url、genres等字段）
            source_query: 视频来源（查询词或演员名）
        
        Returns:
            本次处理新增的M3U条目数量
        """
        try:
            # 提取基本信息
            video_code = video_obj.video_code
            m3u8_url = video_obj.m3u8_base_url or ""
            
            if not m3u8_url:
                logger.warning(f"  跳过: 无法获取 m3u8 URL")
                return 0
            
            logger.info(f"  ✓ 视频代码: {video_code}")
            logger.info(f"  ✓ m3u8 URL: {m3u8_url[:50]}...")
            
            # 提取 genres 和 thumbnail
            genres_raw = getattr(video_obj, 'genres', [])
            if not isinstance(genres_raw, list):
                genres_raw = [genres_raw] if genres_raw else []
            thumbnail = getattr(video_obj, 'thumbnail', "") or ""
            
            # 规范化 genres（去除空、去重）
            genres = utils.normalize_genres(genres_raw)
            unique_genres = set(genres)
            logger.info(f"  ✓ 找到 {len(unique_genres)} 个分类: {list(unique_genres)}")
            
            # 为每个 genre 创建独立的 M3U 条目
            entries_added = 0
            for genre in unique_genres:
                # 检查运行限制
                if len(self.videos) >= self.max_videos:
                    logger.info(f"  达到条目限制，停止添加")
                    break
                
                # 去重检查: (group_title, url) 同时匹配则跳过
                if (genre, m3u8_url) in self.existing_entries:
                    logger.debug(f"    跳过重复条目: {video_code} / {genre}")
                    continue
                
                # 创建条目
                video_entry = {
                    'code': str(video_code),
                    'url': str(m3u8_url),
                    'genres': genres,
                    'thumbnail': str(thumbnail),
                    'group_title': genre
                }
                self.videos.append(video_entry)
                self.new_entries.append(video_entry)
                self.existing_entries.add((genre, m3u8_url))
                entries_added += 1
                
                logger.info(f"    + 新增条目: {video_code} / {genre}")
                utils.random_delay(0.3, 0.8)
            
            logger.info(f"  本次视频共新增 {entries_added} 个 M3U 条目")
            return entries_added
            
        except Exception as e:
            logger.error(f"处理视频对象时出错: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return 0
    
    def fetch_videos(self) -> List[Dict[str, str]]:
        """
        从 missav_api 获取视频 (支持多种模式)

        Modes:
          - "batch-actresses": 使用 search() 搜索演员名
          - "single-query": 使用 search() 搜索单个或多个查询词
          - "video-codes": 使用 get_video() 直接获取番号对应的视频，并按 genres 展开多个条目

        Returns:
            获取到的视频列表（已展开为多个条目）

        Raises:
            ImportError: 如果 missav_api 未安装
        """
        try:
            from missav_api import Client
        except ImportError:
            logger.error(constants.ERROR_NO_API)
            sys.exit(1)

        logger.info(f"使用 missav_api 库获取视频 (限制: {self.max_videos} 条)...")
        logger.info(f"限流配置: {constants.MIN_DELAY}-{constants.MAX_DELAY}秒/请求")

        client = Client()
        # Suppress debug logs from third-party libraries after client creation
        for _logger_name in ['BASE API', 'BaseCore', 'missav_api', 'httpx', 'httpcore']:
            logging.getLogger(_logger_name).setLevel(logging.WARNING)

        logger.info(f"开始获取视频列表...")

        try:
            # 确定剩余要处理的查询/代码
            if self.scraper_mode in ("batch-actresses", "single-query"):
                remaining_queries = self.search_queries[self.current_query_index:]
            else:  # video-codes
                remaining_queries = self.search_queries[self.current_query_index:]

            total_queries = len(self.search_queries)
            logger.info(f"模式: {self.scraper_mode}, 剩余 {len(remaining_queries)}/{total_queries} 项")

            for query_offset, query in enumerate(remaining_queries):
                real_query_idx = self.current_query_index + query_offset

                # 检查索引范围
                if real_query_idx >= total_queries:
                    logger.info(f"\n✅ 所有 {total_queries} 项已处理完毕！")
                    break

                # 检查是否已达到总限制
                if len(self.videos) >= self.max_videos:
                    logger.info(f"\n✅ 已达到总条目限制 ({self.max_videos})，停止处理")
                    break

                logger.info(f"\n{'='*70}")
                if self.scraper_mode == "video-codes":
                    logger.info(f"处理视频代码 {real_query_idx + 1}/{total_queries}: {query}")
                else:
                    logger.info(f"处理查询 {real_query_idx + 1}/{total_queries}: {query}")

                # ==================== video-codes 模式 ====================
                if self.scraper_mode == "video-codes":
                    video_code_input = query
                    # 如果该代码已经在 processed_codes 中，说明已获取过，跳过
                    if video_code_input in self.processed_codes:
                        logger.info(f"  跳过已处理的番号: {video_code_input}")
                        self.current_query_index = real_query_idx + 1
                        continue

                    # 构建视频页面 URL
                    video_url = f"https://missav.ws/cn/{video_code_input}"
                    logger.info(f"  获取视频: {video_url}")

                    try:
                        # 使用 get_video 获取视频对象（单次获取，非列表）
                        video_obj = client.get_video(video_url)
                        self.request_count += 1

                        # 使用公共方法处理视频对象
                        self._process_video_object(video_obj, video_code_input)
                        self.processed_codes.add(video_code_input)
                        
                    except Exception as e:
                        logger.error(f"  获取视频失败: {e}")
                        import traceback
                        logger.debug(traceback.format_exc())
                        utils.random_delay(5, 10)
                        self.current_query_index = real_query_idx + 1
                        continue

                # ==================== 搜索模式 (batch-actresses / single-query) ====================
                else:
                    try:
                        # 获取本次查询的视频列表
                        search_results = client.search(
                            query=query,
                            video_count=constants.VIDEOS_PER_QUERY
                        )

                        result_count = 0
                        new_videos_count = 0
                        # 记录搜索请求
                        self.request_count += 1
                        for video_summary in search_results:
                            # 检查是否已达到本次运行限制
                            if len(self.videos) >= self.max_videos:
                                logger.info(f"  已达到本次运行限制，停止处理此查询")
                                break

                            result_count += 1

                            try:
                                video_code = video_summary.video_code
                                video_url = f"https://missav.ws/cn/{video_code}"

                                if result_count == 1:
                                    logger.info(f"  ✓ 首个视频: {video_code}")

                                # 检查是否已处理该番号
                                if video_code in self.processed_codes:
                                    continue

                                # 使用 get_video 获取完整视频信息
                                logger.debug(f"    获取视频详情: {video_url}")
                                video_obj = client.get_video(video_url)
                                self.request_count += 1

                                # 使用公共方法处理视频对象
                                entries = self._process_video_object(video_obj, query)
                                new_videos_count += entries
                                self.processed_codes.add(video_code)

                            except Exception as e:
                                logger.debug(f"处理视频时出错: {e}")
                                continue

                        logger.info(f"  本次查询结果: {result_count} 个 (新增: {new_videos_count} 个)")

                    except Exception as e:
                        logger.warning(f"查询 '{query}' 失败: {e}")
                        utils.random_delay(5, 10)
                        # 移动索引并继续
                        self.current_query_index = real_query_idx + 1
                        continue

                # 更新进度（成功完成此项）
                self.current_query_index = real_query_idx + 1

                # 定期保存状态 (每处理 5 项或在 video-codes 模式下每项)
                self._save_state()

                # 批次间延迟 (搜索模式)
                if self.scraper_mode != "video-codes" and (real_query_idx + 1) % 5 == 0:
                    logger.info(f"⏸ 批量请求完成，暂停 {constants.BATCH_DELAY} 秒...")
                    import time
                    time.sleep(constants.BATCH_DELAY)
                else:
                    utils.random_delay()

            logger.info(f"\n{'='*70}")
            logger.info(f"爬虫完成! 共获取 {len(self.videos)} 个 M3U 条目")
            logger.info(f"总请求数: {self.request_count}")
            logger.info(f"已处理项目: {self.current_query_index}/{total_queries}")
            logger.info(f"{'='*70}")

        except KeyboardInterrupt:
            logger.info("用户中断")
        except Exception as e:
            logger.error(f"获取视频时出错: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            if len(self.videos) == 0:
                raise

        self._save_state()
        return self.videos
    
    def save_to_m3u(self) -> bool:
        """
        将数据保存为 M3U 格式

        特点：
        - 增量更新：以追加模式保存
        - 不去重：所有视频都会保存（包括重复 URL）
        - 多 genre 支持：为每个 genre 创建独立条目
        - 按演员/搜索参数分组：不同查询使用不同的 group_title

        Returns:
            保存成功返回 True，失败返回 False
        """
        logger.info(f"开始保存为 M3U 格式: {self.output_file}")
        
        # 如果没有新增条目，则跳过写入
        if not self.new_entries:
            logger.info("没有新增条目需要写入 M3U")
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
                
                # 处理本次新增的每个视频条目
                for video in self.new_entries:
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
