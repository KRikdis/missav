#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MissAV M3U 爬虫脚本 (专业版)
支持断点续爬、进度保存、增量更新等高级功能
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Set
from datetime import datetime
import logging
from scraper import MissAVAPIClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AdvancedMissAVScraper(MissAVAPIClient):
    """高级爬虫，支持进度保存和断点续爬"""
    
    STATE_FILE = 'scraper_state.json'
    
    def __init__(self, output_file: str = 'missav.m3u', enable_checkpoint: bool = True):
        super().__init__(output_file)
        self.enable_checkpoint = enable_checkpoint
        self.state = self._load_state()
    
    def _load_state(self) -> Dict:
        """加载保存的状态"""
        if not self.enable_checkpoint:
            return {'videos': {}, 'last_page': 0, 'last_update': None}
        
        try:
            state_path = Path(self.STATE_FILE)
            if state_path.exists():
                with open(state_path, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                logger.info(f"已加载保存的状态 (最后一页: {state.get('last_page', 0)})")
                return state
        except Exception as e:
            logger.warning(f"加载状态文件失败: {e}")
        
        return {'videos': {}, 'last_page': 0, 'last_update': None}
    
    def _save_state(self):
        """保存爬虫状态"""
        if not self.enable_checkpoint:
            return
        
        try:
            state = {
                'videos': {v['code']: v for v in self.videos},
                'last_page': getattr(self, 'current_page', 0),
                'last_update': datetime.now().isoformat()
            }
            
            with open(self.STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存状态失败: {e}")
    
    def fetch_videos(self) -> List[Dict[str, str]]:
        """从状态中加载已爬取的视频"""
        # 加载之前保存的视频
        if self.state.get('videos'):
            self.videos = list(self.state['videos'].values())
            logger.info(f"已加载 {len(self.videos)} 个旧视频")
        
        # 继续爬取新视频
        try:
            from missav_api import MissAV
            
            logger.info("继续获取新视频...")
            api = MissAV()
            
            page = self.state.get('last_page', 0) + 1
            max_pages = 1000
            duplicates = 0
            
            while page <= max_pages:
                logger.info(f"正在获取第 {page} 页...")
                self.current_page = page
                
                try:
                    videos = api.search(page=page)
                    
                    if not videos or len(videos) == 0:
                        logger.info(f"第 {page} 页无更多数据，爬取完成")
                        break
                    
                    for video in videos:
                        try:
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
                                # 检查是否已存在
                                if any(v['code'] == code for v in self.videos):
                                    duplicates += 1
                                    continue
                                
                                self.videos.append({
                                    'code': str(code),
                                    'url': str(m3u_url)
                                })
                                logger.info(f"获取新: {code}")
                            
                            time.sleep(0.3)
                        
                        except Exception as e:
                            logger.debug(f"处理视频时出错: {e}")
                            continue
                    
                    page += 1
                    time.sleep(1)
                    
                    # 定期保存进度
                    if page % 5 == 0:
                        self._save_state()
                
                except Exception as e:
                    logger.error(f"获取第 {page} 页时出错: {e}")
                    if page == self.state.get('last_page', 0) + 1:
                        raise
                    break
            
            logger.info(f"总共获取 {len(self.videos)} 个视频 (新增: {len(self.videos) - len(self.state.get('videos', {}))}, 重复: {duplicates})")
            
            # 保存最终状态
            self._save_state()
            return self.videos
        
        except ImportError as e:
            logger.error(f"未安装 missav_api 库 (错误: {e})")
            return self.videos
        except Exception as e:
            logger.error(f"获取视频时出错: {e}")
            self._save_state()  # 保存当前进度
            return self.videos
    
    def clean_state(self):
        """清除保存的状态"""
        try:
            state_path = Path(self.STATE_FILE)
            if state_path.exists():
                state_path.unlink()
                logger.info(f"已删除状态文件")
        except Exception as e:
            logger.error(f"删除状态文件失败: {e}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MissAV 爬虫 (专业版) - 支持断点续爬')
    parser.add_argument('-o', '--output', default='missav.m3u', help='输出文件名')
    parser.add_argument('-c', '--checkpoint', action='store_true', help='启用断点续爬 (默认: 启用)')
    parser.add_argument('--no-checkpoint', dest='checkpoint', action='store_false', help='禁用断点续爬')
    parser.add_argument('--clean', action='store_true', help='清除保存的进度状态')
    parser.set_defaults(checkpoint=True)
    
    args = parser.parse_args()
    
    scraper = AdvancedMissAVScraper(
        output_file=args.output,
        enable_checkpoint=args.checkpoint
    )
    
    if args.clean:
        scraper.clean_state()
        return
    
    try:
        scraper.run()
        if args.checkpoint:
            logger.info("进度已保存，下次可以继续爬取")
    except KeyboardInterrupt:
        logger.info("用户中断，已保存进度")
        scraper._save_state()
    except Exception as e:
        logger.error(f"爬虫出错: {e}")
        scraper._save_state()


if __name__ == '__main__':
    main()
