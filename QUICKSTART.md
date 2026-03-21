# MissAV 爬虫快速入门

## 📋 概览

这是一个完整的 MissAV 爬虫项目，用于爬取所有 AV 番号和对应的 m3u8 直播流地址，并生成标准的 M3U 播放列表文件。

**功能对比：**

| 功能 | main.py | scraper.py | advanced_scraper.py |
|------|---------|-----------|-------------------|
| 基础爬虫 | ✓ | ✓ | ✓ |
| 命令行参数 | ✗ | ✓ | ✓ |
| 配置文件 | ✗ | ✓ | ✓ |
| 断点续爬 | ✗ | ✗ | ✓ |
| 增量更新 | ✗ | ✗ | ✓ |
| 进度保存 | ✗ | ✗ | ✓ |

## 🚀 快速开始

### 第 1 步：安装依赖

```bash
pip install -r requirements.txt
```

### 第 2 步：检查环境（可选）

```bash
python check_env.py
```

### 第 3 步：运行爬虫

**最简单的方式：**
```bash
python main.py
```

**高级用法：**
```bash
python scraper.py -o missav.m3u -v
```

**支持断点续爬：**
```bash
python advanced_scraper.py
```

中断后再次运行，会自动从上次中断的地方继续。

## 📁 项目文件说明

```
missav/
├── main.py                 # 简单入口脚本（推荐新手使用）
├── scraper.py              # 主爬虫模块（支持更多选项）
├── advanced_scraper.py     # 高级爬虫（支持断点续爬）
├── check_env.py            # 环境检查脚本
├── requirements.txt        # 依赖列表
├── config.example.json     # 配置文件示例
├── .gitignore              # Git 忽略配置
├── README_CN.md            # 本文件
└── README.md               # 英文文档
```

## 💻 使用示例

### 示例 1：最简单的用法

```bash
python main.py
```

生成文件：`missav.m3u`

### 示例 2：自定义输出文件名

```bash
python scraper.py -o my_list.m3u
```

### 示例 3：启用详细日志

```bash
python scraper.py -v
```

### 示例 4：使用配置文件

创建 `config.json`：
```json
{
  "output_file": "custom.m3u",
  "group_title": "自定义频道",
  "max_pages": 100
}
```

运行：
```bash
python scraper.py -c config.json
```

### 示例 5：支持断点续爬

```bash
# 首次运行
python advanced_scraper.py

# 如果中断，再次运行会从上次中断的地方继续
python advanced_scraper.py

# 清除保存的进度，重新开始
python advanced_scraper.py --clean
```

## 📊 输出格式示例

```
#EXTM3U
#EXTINF:-1 group-title="成人频道" tvg-name="ABP-001" tvg-logo="" epg-url="",ABP-001
http://example.com/stream/abp001.m3u8
#EXTINF:-1 group-title="成人频道" tvg-name="ABP-002" tvg-logo="" epg-url="",ABP-002
http://example.com/stream/abp002.m3u8
...
```

该格式兼容所有主流播放器：
- IPTV 播放器
- VLC 媒体播放器
- Kodi
- 其他支持 M3U 的播放器

## ⚙️ 高级配置

### 命令行参数

```bash
python scraper.py --help

usage: scraper.py [-h] [-o OUTPUT] [-c CONFIG] [-v]

MissAV 爬虫 - 爬取 missav 视频并生成 M3U 列表

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        输出文件名 (默认: missav.m3u)
  -c CONFIG, --config CONFIG
                        配置文件路径 (可选)
  -v, --verbose         详细日志输出
```

### advanced_scraper.py 参数

```bash
python advanced_scraper.py --help

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        输出文件名
  -c CHECKPOINT, --checkpoint CHECKPOINT
                        启用/禁用断点续爬
  --clean               清除保存的进度状态
```

## 📝 在 Python 代码中使用

```python
from scraper import MissAVAPIClient

# 方式 1：基础爬虫
scraper = MissAVAPIClient(output_file='my_videos.m3u')
scraper.run()

# 方式 2：展开操作
scraper = MissAVAPIClient()
scraper.fetch_videos()
print(f"获取了 {len(scraper.videos)} 个视频")
scraper.save_to_m3u()

# 方式 3：访问视频列表
for video in scraper.videos:
    print(f"{video['code']}: {video['url']}")
```

高级用法（断点续爬）：

```python
from advanced_scraper import AdvancedMissAVScraper

# 启用断点续爬
scraper = AdvancedMissAVScraper(enable_checkpoint=True)
scraper.run()

# 清除进度
scraper.clean_state()
```

## 🔍 调试

### 启用详细日志

```bash
python scraper.py -v
```

### 检查爬虫状态

```bash
cat scraper_state.json
```

### 查看生成的 M3U 文件

```bash
head -20 missav.m3u
wc -l missav.m3u  # 查看总行数（每个视频占 2 行）
```

## ⚠️ 注意事项

1. **礼貌爬虫**
   - 爬虫会自动在请求之间添加延迟
   - 不要频繁运行爬虫
   - 不要增加并发请求数量

2. **法律和道德**
   - 请遵守当地法律
   - 尊重网站的 robots.txt
   - 爬取的数据仅供个人学习使用

3. **性能**
   - 首次爬虫可能需要较长时间（取决于视频数量和网络）
   - 使用 advanced_scraper.py 支持断点续爬
   - 可以定期运行来更新列表

## 🐛 常见问题

### Q: 找不到 missav_api 模块？

A: 运行 `pip install -r requirements.txt` 安装依赖

### Q: 爬虫没有获取到任何数据？

A: 
1. 检查网络连接
2. 确认 missav 网站可访问
3. 运行 `python scraper.py -v` 查看详细错误信息

### Q: 可以加快爬虫速度吗？

A: 不建议修改延迟时间，为了避免被网站限制访问，请保持默认设置

### Q: 爬虫中途中断了怎么办？

A: 如果使用了 `advanced_scraper.py`，只需再次运行同一命令即可继续

### Q: 如何修改 M3U 格式或其他配置？

A: 
1. 编辑代码中的格式字符串
2. 或使用配置文件 `config.json`
3. 参考 `config.example.json` 文件

## 📚 相关资源

- [M3U 格式说明](https://en.wikipedia.org/wiki/M3U)
- [IPTV 播放列表格式](https://github.com/iptv-org/iptv)
- [VLC 媒体播放器](https://www.videolan.org/)

## 📄 许可

本项目仅供学习参考使用。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**最后更新**：2024 年
**版本**：1.0
