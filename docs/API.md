# API 参考

## MissAVScraper 类

核心爬虫类，位于 `src.missav_scraper.core.MissAVScraper`

### 初始化

```python
from src.missav_scraper import MissAVScraper

scraper = MissAVScraper(
    output_file: str = "output/missav.m3u",
    enable_checkpoint: bool = True,
    max_videos: int = None,
    verbose: bool = False
)
```

**参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `output_file` | str | `output/missav.m3u` | M3U 输出文件路径 |
| `enable_checkpoint` | bool | True | 是否启用断点续爬 |
| `max_videos` | int | 500 | 每次运行最多收集的视频数 |
| `verbose` | bool | False | 是否启用详细日志 |

### 主要方法

#### run()
```python
scraper.run() -> None
```

运行爬虫完整流程（获取 → 保存 → 报告）

**返回值**：无

**异常**：
- `ImportError`：如果 missav_api 未安装
- `KeyboardInterrupt`：用户中断
- 其他异常：爬虫运行错误

**示例**：
```python
scraper = MissAVScraper()
scraper.run()
```

---

#### fetch_videos()
```python
scraper.fetch_videos() -> List[Dict[str, str]]
```

从 MissAV API 获取视频列表

**返回值**：视频列表，每个元素包含：
- `code`: 视频代码
- `url`: M3U8 地址
- `genres`: 分类列表
- `thumbnail`: 缩略图 URL

**异常**：
- `ImportError`：如果 missav_api 未安装

**示例**：
```python
scraper = MissAVScraper()
videos = scraper.fetch_videos()
print(f"获取了 {len(videos)} 个视频")
```

---

#### save_to_m3u()
```python
scraper.save_to_m3u() -> bool
```

将视频数据保存为 M3U 格式

**返回值**：
- True：保存成功
- False：保存失败

**异常**：无（所有异常内部处理）

**特点**：
- 增量更新：追加模式
- 自动去重：检查重复 URL
- 多分类支持：每个分类生成独立条目

**示例**：
```python
scraper = MissAVScraper()
scraper.fetch_videos()
if scraper.save_to_m3u():
    print("保存成功")
```

---

#### clean_state()
```python
scraper.clean_state(clean_output: bool = False) -> None
```

清除保存的爬虫状态

**参数**：
- `clean_output` (bool)：是否同时删除输出文件

**返回值**：无

**示例**：
```python
# 仅清除进度
scraper.clean_state()

# 连同输出文件一起清除
scraper.clean_state(clean_output=True)
```

---

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `output_file` | str | M3U 输出文件路径 |
| `enable_checkpoint` | bool | 是否启用断点续爬 |
| `max_videos` | int | 每次运行最多收集的视频数 |
| `videos` | List[Dict] | 本次收集的视频列表 |
| `existing_urls` | Set[str] | 已存在的 URL（用于去重） |
| `processed_codes` | Set[str] | 已处理的视频代码 |
| `request_count` | int | 本次请求总数 |

---

## 常量模块

位于 `src.missav_scraper.constants`

### 文件配置

```python
STATE_FILE = "scraper_state.json"      # 进度保存文件
OUTPUT_DIR = "output"                   # 输出目录
OUTPUT_FILE = "missav.m3u"              # M3U 文件名
```

### 爬虫参数

```python
DEFAULT_QUERIES = ["a", "b", "c", "d", "e"]  # 查询字符串
VIDEOS_PER_QUERY = 50                        # 每个查询的视频数
MAX_VIDEOS_PER_RUN = 500                     # 每次运行限制
```

### 限流配置

```python
MIN_DELAY = 2      # 请求间最小延迟 (秒)
MAX_DELAY = 5      # 请求间最大延迟 (秒)
BATCH_DELAY = 15   # 批次间延迟 (秒)
```

---

## 工具函数模块

位于 `src.missav_scraper.utils`

### setup_logging()
```python
utils.setup_logging(verbose: bool = False) -> None
```

配置日志系统

**参数**：
- `verbose`：是否启用 DEBUG 级别

---

### random_delay()
```python
utils.random_delay(
    min_seconds: float = None,
    max_seconds: float = None
) -> None
```

添加随机延迟

**参数**：
- `min_seconds`：最小延迟（使用常量默认值）
- `max_seconds`：最大延迟（使用常量默认值）

---

### load_existing_urls()
```python
utils.load_existing_urls(output_file: str) -> Set[str]
```

从 M3U 文件读取已存在的 URL

**参数**：
- `output_file`：M3U 文件路径

**返回值**：URL 集合

---

### normalize_genres()
```python
utils.normalize_genres(genres) -> list
```

规范化分类数据

**参数**：
- `genres`：可以是 str、list 或任何其他类型

**返回值**：规范化后的分类列表

---

## 使用示例

### 示例 1：基础使用
```python
from src.missav_scraper import MissAVScraper

scraper = MissAVScraper()
scraper.run()
```

### 示例 2：自定义参数
```python
from src.missav_scraper import MissAVScraper

scraper = MissAVScraper(
    output_file='my_playlist.m3u',
    max_videos=1000,
    verbose=True
)
scraper.run()
```

### 示例 3：分步执行
```python
from src.missav_scraper import MissAVScraper

scraper = MissAVScraper()

# 获取视频
videos = scraper.fetch_videos()
print(f"获取了 {len(videos)} 个视频")

# 保存为 M3U
if scraper.save_to_m3u():
    print("保存成功！")

# 显示统计
print(f"总 M3U 条目: {len(scraper.existing_urls)}")
```

### 示例 4：错误处理
```python
from src.missav_scraper import MissAVScraper

try:
    scraper = MissAVScraper(max_videos=500, verbose=True)
    scraper.run()
    print("✓ 爬虫完成")
except ImportError as e:
    print(f"✗ 依赖缺失: {e}")
except KeyboardInterrupt:
    print("✗ 用户中断")
except Exception as e:
    print(f"✗ 错误: {e}")
```

---

## 状态文件格式

`scraper_state.json` 包含以下字段：

```json
{
  "videos": [
    {
      "code": "ABC-123",
      "url": "https://...",
      "genres": ["日本", "高清"],
      "thumbnail": "https://..."
    }
  ],
  "existing_urls_count": 1500,
  "last_update": "2026-03-21T10:30:00.000000",
  "total_videos_processed": 50
}
```

---

## M3U 文件格式

```
#EXTM3U
#EXTINF:-1 group-title="日本" tvg-name="ABC-123" tvg-logo="https://..." epg-url="",ABC-123
https://media.example.com/video.m3u8
```

**字段说明**：
- `group-title`：分类（来自 API 的 genres）
- `tvg-name`：视频代码
- `tvg-logo`：缩略图 URL
- 最后一行：视频 URL

---

## 环境变量

暂无特殊环境变量配置

---

## 版本信息

```python
import src.missav_scraper
print(src.missav_scraper.__version__)  # "2.0.0"
```
