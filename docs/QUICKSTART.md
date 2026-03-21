# 快速入门指南

## 三步启动

### 1️⃣ 安装依赖

```bash
pip install -r requirements.txt
```

### 2️⃣ 运行爬虫

```bash
python main.py
```

### 3️⃣ 查看结果

```bash
# Linux/Mac
cat output/missav.m3u

# Windows
type output\missav.m3u
```

---

## 常见用法

### 基础运行
```bash
python main.py
```
生成文件：`output/missav.m3u`（500 条视频，默认限制）

### 自定义输出文件
```bash
python main.py -o my_list.m3u
```

### 更改收集数量
```bash
# 保守模式（200 条）
python main.py --max-videos 200

# 快速模式（1000 条）
python main.py --max-videos 1000
```

### 启用详细日志
```bash
python main.py -v
```

---

## 启动参数解释

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-o`, `--output` | 输出文件路径 | `output/missav.m3u` |
| `--max-videos` | 每次收集的最多视频数 | 500 |
| `-v`, `--verbose` | 详细日志输出 | 关闭 |
| `--no-checkpoint` | 禁用断点续爬 | 启用 |
| `--clean` | 清除进度文件（保留 M3U） | - |
| `--clean-all` | 清除进度和 M3U 文件 | - |

---

## 爬虫参数详解

可在 `src/missav_scraper/constants.py` 中修改：

```python
DEFAULT_QUERIES = ["a", "b", "c", "d", "e"]  # 查询字符串
VIDEOS_PER_QUERY = 50                        # 每个查询的视频数
MAX_VIDEOS_PER_RUN = 500                     # 每次运行限制
MIN_DELAY = 2                                # 最小延迟 (秒)
MAX_DELAY = 5                                # 最大延迟 (秒)
BATCH_DELAY = 15                             # 批次间延迟 (秒)
```

---

## 输出文件示例

```
#EXTM3U
#EXTINF:-1 group-title="日本" tvg-name="ABC-123" tvg-logo="https://example.com/thumb.jpg" epg-url="",ABC-123
https://media.example.com/video.m3u8
#EXTINF:-1 group-title="中文" tvg-name="ABC-124" tvg-logo="https://example.com/thumb2.jpg" epg-url="",ABC-124
https://media.example.com/video2.m3u8
```

---

## 常见问题

### Q1：怎样才能保证 IP 不被限制？

**A**：使用默认参数即可：
```bash
python main.py                  # 默认 500 条，安全
```

如果要更保守：
```bash
python main.py --max-videos 200 # 200 条，极低风险
```

### Q2：如何快速积累视频？

**A**：多次运行爬虫（每次自动追加）：
```bash
# 第 1 天
python main.py

# 第 2 天
python main.py

# 第 3 天
python main.py

# 现在有 1500 条视频（3 × 500）
```

### Q3：怎样清除进度重新开始？

**A**：
```bash
# 仅清除进度，保留 M3U
python main.py --clean

# 完全清除（删除 M3U）
python main.py --clean-all
```

### Q4：如何在 Python 代码中使用？

**A**：
```python
from src.missav_scraper import MissAVScraper

scraper = MissAVScraper(
    output_file='output/my_playlist.m3u',
    max_videos=500,
    verbose=True
)
scraper.run()
```

---

## 下一步

- 📖 [详细使用指南](GUIDE.md)
- 🔧 [故障排除](TROUBLESHOOTING.md)
- 💻 [API 参考](API.md)
