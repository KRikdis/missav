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

        self.current_query_index = -1
        self.query_group_mapping = {}  # 映射: 查询 -> 数量统计 (仅 batch-actresses 使用)
        self.m3u_file_initialized = False  # 标记 M3U 文件头是否已写入

        # 加载已存在的 URL（用于统计）
        self.existing_urls: Set[str] = utils.load_existing_urls(self.output_file)

        # 加载保存的状态
        self.state = self._load_state() if enable_checkpoint else {}
        
        # 从状态恢复当前查询索引
        # 默认值应该是 -1（表示还没处理任何查询），不是 0
        self.current_query_index = self.state.get('current_query_index', -1)
        self.query_group_mapping = self.state.get('query_group_mapping', {})

        # 构建 existing_entries 集合用于去重 (从 M3U 文件中读取已保存的条目)
        self._load_existing_entries_from_m3u()
        
        # 输出启动信息
        self._print_startup_info()
    
    def _print_startup_info(self) -> None:
        """打印爬虫启动信息"""
        logger.info("=" * 70)
        logger.info("爬虫启动参数:")
        next_idx = self.current_query_index + 1
        is_resume = self.current_query_index >= 0

        if self.scraper_mode == "batch-actresses":
            logger.info(f"  模式: 批量获取演员视频 (使用 search)")
            logger.info(f"  总演员数: {len(self.search_queries)}")
            if is_resume:
                logger.info(f"  恢复进度: {next_idx}/{len(self.search_queries)}")
                logger.info(f"  下一个演员: {self.search_queries[next_idx] if next_idx < len(self.search_queries) else '（已完成）'}")
            else:
                logger.info(f"  准备开始: 从第 1/{len(self.search_queries)} 开始")
                logger.info(f"  第一个演员: {self.search_queries[0]}")
        elif self.scraper_mode == "single-query":
            logger.info(f"  模式: 单查询模式 (使用 search)")
            logger.info(f"  查询列表: {len(self.search_queries)} 个查询")
        elif self.scraper_mode == "video-codes":
            logger.info(f"  模式: 视频代码模式 (使用 get_video)")
            logger.info(f"  总视频代码数: {len(self.search_queries)}")
            if is_resume:
                logger.info(f"  恢复进度: {next_idx}/{len(self.search_queries)}")
                logger.info(f"  下一个代码: {self.search_queries[next_idx] if next_idx < len(self.search_queries) else '（已完成）'}")
            else:
                logger.info(f"  准备开始: 从第 1/{len(self.search_queries)} 开始")
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
        
        只加载进度信息，不加载视频数据
        
        Returns:
            包含保存状态的字典
        """
        try:
            state_path = Path(constants.STATE_FILE)
            if state_path.exists():
                with open(state_path, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                logger.info(f"已加载保存的状态")
                return state
        except Exception as e:
            logger.warning(f"加载状态文件失败: {e}")
        
        return {}
    
    def _load_existing_entries_from_m3u(self) -> None:
        """
        从 M3U 文件中读取已存在的条目用于去重
        
        M3U 格式: 每个条目占两行
        - 第一行: #EXTINF:... group-title="..." tvg-name="..." ...
        - 第二行: URL
        """
        try:
            m3u_path = Path(self.output_file)
            if m3u_path.exists():
                with open(m3u_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                i = 0
                while i < len(lines):
                    line = lines[i].strip()
                    
                    # 查找 EXTINF 行
                    if line.startswith('#EXTINF:'):
                        # 提取 group-title
                        group_title = ""
                        if 'group-title="' in line:
                            start = line.find('group-title="') + len('group-title="')
                            end = line.find('"', start)
                            group_title = line[start:end]
                        
                        # 下一行应该是 URL
                        if i + 1 < len(lines):
                            url = lines[i + 1].strip()
                            if url and not url.startswith('#'):
                                self.existing_entries.add((group_title, url))
                                logger.debug(f"加载已存在的条目: {group_title} / {url[:50]}...")
                        i += 2
                    else:
                        i += 1
                
                logger.info(f"从 M3U 文件加载了 {len(self.existing_entries)} 个已存在的条目用于去重")
        except Exception as e:
            logger.warning(f"加载 M3U 文件中的条目失败: {e}")
    
    def _save_state(self) -> None:
        """
        保存爬虫状态（用于断点续爬）
        
        只保存进度信息，不保存具体视频数据（视频数据已实时写入 M3U 文件）
        """
        if not self.enable_checkpoint:
            return
        
        try:
            next_query_idx = self.current_query_index + 1
            state = {
                'last_update': datetime.now().isoformat(),
                'current_query_index': self.current_query_index,
                'next_query_index': next_query_idx,
                'next_query': self.search_queries[next_query_idx] if next_query_idx < len(self.search_queries) else None,
                'scraper_mode': self.scraper_mode,
                'total_queries': len(self.search_queries)
            }
            
            with open(constants.STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            logger.debug(f"进度已保存 (查询 {self.current_query_index + 1}/{len(self.search_queries)})")
        except Exception as e:
            logger.error(f"保存状态失败: {e}")
    
    def _append_to_m3u(self, video_entry: Dict[str, str]) -> None:
        """
        实时追加单个视频条目到 M3U 文件（每获取到一个视频就立即保存）
        
        Args:
            video_entry: 视频条目字典，包含 code, url, series, thumbnail, group_title
        """
        try:
            output_path = utils.ensure_output_directory(self.output_file)
            
            # 首次写入时创建文件头
            if not self.m3u_file_initialized:
                # 检查文件是否存在且非空
                file_exists = output_path.exists() and output_path.stat().st_size > 0
                
                if not file_exists:
                    # 创建新文件，写入头部
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(f'{constants.M3U_HEADER}\n')
                    logger.debug("✓ 创建新的 M3U 文件并写入头部")
                
                self.m3u_file_initialized = True
            
            # 追加条目
            code = video_entry.get('code', 'Unknown')
            url = video_entry.get('url', '')
            thumbnail = video_entry.get('thumbnail', '')
            group_title = video_entry.get('group_title', constants.M3U_GROUP_TITLE)
            
            if not url:
                logger.warning(f"  跳过无效的 URL: {code}")
                return
            
            # 写入条目到文件
            with open(output_path, 'a', encoding='utf-8') as f:
                extinf = constants.M3U_EXTINF_FORMAT.format(
                    group=group_title,
                    code=code,
                    logo=thumbnail
                )
                f.write(f'{extinf}\n')
                f.write(f'{url}\n')
            
            self.existing_urls.add(url)
            logger.debug(f"  ✓ 已保存到 M3U 文件: {code} / {group_title}")
            
        except Exception as e:
            logger.error(f"追加到 M3U 文件时出错: {e}")
    
    def _process_video_object(self, video_obj, source_query: str) -> int:
        """
        处理单个视频对象，创建M3U条目
        
        此方法提取了video-codes和搜索模式中重复的视频处理逻辑
        
        Args:
            video_obj: 视频对象（包含video_code、m3u8_base_url、series等字段）
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
            
            # 提取 series 和 thumbnail
            series_raw = getattr(video_obj, 'series', [])
            if not isinstance(series_raw, list):
                series_raw = [series_raw] if series_raw else []
            thumbnail = getattr(video_obj, 'thumbnail', "") or ""
            
            # 规范化 series（去除空、去重）
            series = utils.normalize_series(series_raw)
            unique_series = set(series)
            logger.info(f"  ✓ 找到 {len(unique_series)} 个系列: {list(unique_series)}")
            
            # 为每个 series 创建独立的 M3U 条目
            entries_added = 0
            for s in unique_series:
                # 检查运行限制
                if len(self.videos) >= self.max_videos:
                    logger.info(f"  达到条目限制，停止添加")
                    break
                
                # 去重检查: (group_title, url) 同时匹配则跳过
                if (s, m3u8_url) in self.existing_entries:
                    logger.debug(f"    跳过重复条目: {video_code} / {s}")
                    continue
                
                # 创建条目
                video_entry = {
                    'code': str(video_code),
                    'url': str(m3u8_url),
                    'series': series,
                    'thumbnail': str(thumbnail),
                    'group_title': s
                }
                self.videos.append(video_entry)
                self.new_entries.append(video_entry)
                self.existing_entries.add((s, m3u8_url))
                entries_added += 1
                
                # 实时保存到 M3U 文件（每获取到一个就立即保存）
                self._append_to_m3u(video_entry)
                
                logger.info(f"    + 新增条目: {video_code} / {s}")
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
          - "video-codes": 使用 get_video() 直接获取番号对应的视频，并按 series 展开多个条目

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
            logging.getLogger(_logger_name).setLevel(logging.INFO)

        logger.info(f"开始获取视频列表...")

        try:
            # 确定剩余要处理的查询/代码
            # current_query_index 表示已处理的最后一个索引，所以从 current_query_index + 1 开始
            start_idx = self.current_query_index + 1
            remaining_queries = self.search_queries[start_idx:]

            total_queries = len(self.search_queries)
            logger.info(f"模式: {self.scraper_mode}, 已处理 {start_idx}/{total_queries}, 剩余 {len(remaining_queries)} 项")

            for query_offset, query in enumerate(remaining_queries):
                real_query_idx = start_idx + query_offset

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
                        self.current_query_index = real_query_idx
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
                        # 失败时也要更新索引，标记已处理过此项
                        self.current_query_index = real_query_idx
                        continue

                # ==================== 搜索模式 (batch-actresses / single-query) ====================
                else:
                    try:
                        # 获取本次查询的视频列表
                        # search() 返回的已是完整视频对象，可直接使用（无需再调用 get_video）
                        search_results = client.search(
                            query=query,
                            video_count=constants.VIDEOS_PER_QUERY,
                            max_workers=20
                        )

                        result_count = 0
                        new_videos_count = 0
                        # 记录搜索请求
                        self.request_count += 1
                        for video_obj in search_results:
                            # 检查是否已达到本次运行限制
                            if len(self.videos) >= self.max_videos:
                                logger.info(f"  已达到本次运行限制，停止处理此查询")
                                break

                            result_count += 1

                            try:
                                video_code = video_obj.video_code

                                if result_count == 1:
                                    logger.info(f"  ✓ 首个视频: {video_code}")

                                # 检查是否已处理该番号
                                if video_code in self.processed_codes:
                                    continue

                                # 使用公共方法处理视频对象（search 已返回完整对象，无需再调用 get_video）
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
                        # 失败时也要更新索引，标记已处理过此项
                        self.current_query_index = real_query_idx
                        continue

                # 更新进度（成功完成此项，标记为已处理）
                self.current_query_index = real_query_idx
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
            logger.info(f"已处理项目: {self.current_query_index + 1}/{total_queries}")
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
        完成 M3U 文件保存（条目已在实时保存中完成）

        返回保存统计信息
        
        Returns:
            如果有新条目被保存返回 True，否则返回 False
        """
        # 如果没有新增条目，则跳过处理
        if not self.new_entries:
            logger.info("没有新增条目需要处理")
            return False
        
        # 输出保存统计信息（条目已在 _append_to_m3u 中实时保存）
        logger.info(f"✓ M3U 文件已完成保存: {self.output_file}")
        logger.info(f"✓ 本次新增 {len(self.new_entries)} 个条目")
        logger.info(f"  文件: {self.output_file}")
        return True
    
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
