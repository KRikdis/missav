#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MissAV M3U 爬虫 - 主入口脚本

使用新的模块化结构，支持所有高级功能：
- 多模式支持：单查询模式 或 批量演员轮转模式
- 增量更新：追加模式保存 M3U 文件
- 断点续爬：保存爬虫状态，支持中断后继续（支持多参数续接）
- 限制收集：每次运行最多收集指定数量的视频，保护 IP
- 限流保护：自动添加延迟，避免 IP 被限制
- 分类保存：不同搜索词的视频按不同 group_title 保存
- 不去重：所有视频都会保存，允许重复 URL

说明：
  当前爬虫模式: batch-actresses

  如果 SCRAPER_MODE = "batch-actresses":
    - 会自动轮转处理所有演员
    - 每次执行处理一个演员的全部视频
    - 支持断点续爬：中断后下次自动继续下一个演员
    - 每个演员的视频按名字分类 (group_title)

  如果 SCRAPER_MODE = "single-query":
    - 使用单个查询字符串模式
    - 每次运行处理该查询

示例：
    基础使用（推荐）：
        python main.py

    限制该次运行最多收集视频数：
        python main.py --max-videos 15000

    详细日志输出：
        python main.py -v

    清除进度（继续下一个演员）：
        python main.py --skip-current

    清除所有进度：
        python main.py --clean
"""


import sys
import argparse
from pathlib import Path
from src.missav_scraper import MissAVScraper, constants


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='MissAV 爬虫 - 爬取 missav 视频并生成 M3U 列表',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f'''
示例:
  python main.py                         # 基本使用
  python main.py --max-videos 15000      # 每次收集 15000 条（或针对当前演员）
  python main.py -v                      # 详细日志输出
  
多演员模式 (当前: {constants.SCRAPER_MODE}):
  python main.py                         # 处理下一个未完成的演员
  python main.py --skip-current          # 跳过当前演员，继续下一个
  python main.py --list-progress         # 显示进度

清除:
  python main.py --clean                 # 清除进度文件（保留 M3U）
  python main.py --clean-all             # 清除进度和 M3U 文件
        '''
    )
    
    parser.add_argument(
        '-o', '--output',
        default=str(Path(constants.OUTPUT_DIR) / constants.OUTPUT_FILE),
        help=f'输出文件路径 (默认: {constants.OUTPUT_DIR}/missav.m3u)'
    )
    parser.add_argument(
        '--max-videos',
        type=int,
        default=constants.MAX_VIDEOS_PER_RUN,
        help=f'每次运行最多收集的视频数 (默认: {constants.MAX_VIDEOS_PER_RUN})'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='详细日志输出 (DEBUG 级别)'
    )
    parser.add_argument(
        '--no-checkpoint',
        action='store_true',
        help='禁用断点续爬'
    )
    parser.add_argument(
        '--skip-current',
        action='store_true',
        help='跳过当前演员，继续下一个 (仅在 batch-actresses 模式有效)'
    )
    parser.add_argument(
        '--list-progress',
        action='store_true',
        help='显示爬虫进度 (已完成/总数)'
    )
    parser.add_argument(
        '--clean',
        action='store_true',
        help='清除保存的进度文件 (保留 M3U 文件)'
    )
    parser.add_argument(
        '--clean-all',
        action='store_true',
        help='清除进度文件和 M3U 文件'
    )
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_arguments()
    
    # 处理 --list-progress 参数
    if args.list_progress:
        try:
            state_path = Path(constants.STATE_FILE)
            if state_path.exists():
                import json
                with open(state_path, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                
                current_idx = state.get('current_query_index', 0)
                total = state.get('total_queries', len(constants.ACTRESS_SEARCH_LIST))
                current_query = state.get('current_query', '未知')
                total_videos = len(state.get('videos', []))
                
                print(f"\n{'='*70}")
                print(f"爬虫进度:")
                print(f"  模式: {state.get('scraper_mode', constants.SCRAPER_MODE)}")
                print(f"  已完成演员: {current_idx}/{total}")
                if current_idx < total:
                    print(f"  当前演员: {current_query}")
                    print(f"  下个演员: {constants.ACTRESS_SEARCH_LIST[current_idx] if current_idx < len(constants.ACTRESS_SEARCH_LIST) else '无'}")
                else:
                    print(f"  ✅ 所有演员已完成!")
                print(f"  累计视频数: {total_videos}")
                print(f"{'='*70}\n")
            else:
                print("没有找到进度文件，尚未开始爬虫")
        except Exception as e:
            print(f"✗ 显示进度失败: {e}")
            sys.exit(1)
        return
    
    # 处理 --skip-current 参数
    if args.skip_current:
        try:
            state_path = Path(constants.STATE_FILE)
            if state_path.exists():
                import json
                with open(state_path, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                
                current_idx = state.get('current_query_index', 0)
                current_query = state.get('current_query', '未知')
                
                # 跳过当前演员，自动递增索引
                state['current_query_index'] = current_idx + 1
                
                with open(state_path, 'w', encoding='utf-8') as f:
                    json.dump(state, f, ensure_ascii=False, indent=2)
                
                print(f"✓ 已跳过演员: {current_query}")
                print(f"  下次运行将处理第 {current_idx + 2} 个演员")
            else:
                print("没有找到进度文件，无法跳过")
        except Exception as e:
            print(f"✗ 操作失败: {e}")
            sys.exit(1)
        return
    
    # 处理 --clean 参数
    if args.clean:
        try:
            state_path = Path(constants.STATE_FILE)
            if state_path.exists():
                state_path.unlink()
                print(f"✓ 已清除进度文件: {constants.STATE_FILE}")
                print(f"  注意: M3U 文件 {args.output} 已保留")
            else:
                print("进度文件不存在")
        except Exception as e:
            print(f"✗ 清除失败: {e}")
            sys.exit(1)
        return
    
    # 处理 --clean-all 参数
    if args.clean_all:
        errors = []
        try:
            state_path = Path(constants.STATE_FILE)
            if state_path.exists():
                state_path.unlink()
                print(f"✓ 已清除进度文件: {constants.STATE_FILE}")
        except Exception as e:
            errors.append(f"进度文件: {e}")
        
        try:
            output_path = Path(args.output)
            if output_path.exists():
                output_path.unlink()
                print(f"✓ 已清除输出文件: {args.output}")
        except Exception as e:
            errors.append(f"输出文件: {e}")
        
        if errors:
            print("✗ 某些文件清除失败:")
            for error in errors:
                print(f"  {error}")
            sys.exit(1)
        return
    
    # 创建爬虫并运行
    try:
        scraper = MissAVScraper(
            output_file=args.output,
            enable_checkpoint=not args.no_checkpoint,
            max_videos=args.max_videos,
            verbose=args.verbose
        )
        scraper.run()
        
        print(f"\n✓ 爬虫完成!")
        print(f"  M3U 文件: {args.output}")
        print(f"  本次收集: {len(scraper.videos)} 个视频")
        
        if constants.SCRAPER_MODE == "batch-actresses":
            total = len(constants.ACTRESS_SEARCH_LIST)
            completed = scraper.current_query_index
            print(f"  进度: {completed}/{total} 演员")
            if completed < total:
                print(f"  下个演员: {constants.ACTRESS_SEARCH_LIST[completed]}")
                print(f"  继续运行: python main.py")
            else:
                print(f"  ✅ 所有演员已完成！")
    
    except KeyboardInterrupt:
        print("\n✗ 用户中断了爬虫")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 爬虫出错: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
