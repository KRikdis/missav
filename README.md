# MissAV M3U 爬虫 2.0

一个完整的、高质量的 Python 项目，用于爬取 MissAV 网站视频并生成 M3U 播放列表。

**版本**: 2.0.0 · **状态**: 生产级别 ✅ · **许可证**: MIT

## 🎯 功能特性

### 核心功能
- ✅ 爬取 MissAV 网站所有视频的番号和 M3U 地址
- ✅ 生成标准 M3U 格式文件（兼容所有播放器）
- ✅ 多类型分类（从 API 的 `genres` 字段提取）
- ✅ 自动添加缩略图（从 API 的 `thumbnail` 字段提取）

### 高级功能
- ✅ **增量更新**：每次运行自动追加新视频到 M3U 文件
- ✅ **自动去重**：智能检查和跳过重复 URL
- ✅ **断点续爬**：保存进度，中断后可继续爬取
- ✅ **限制收集**：每次最多 500 条（默认），保护 IP 安全
- ✅ **限流保护**：自动添加请求延迟，避免 IP 被频繁限制

### 工程化
- ✅ 模块化架构：清晰的代码结构和职责划分
- ✅ 标准化命名：严格遵循 PEP 8 代码规范
- ✅ 完善的日志：详细的执行日志和调试信息
- ✅ 错误处理：健壮的异常捕获和恢复机制

## 📦 项目结构

```
missav/
├── src/missav_scraper/              # 核心模块
│   ├── __init__.py                  # 包初始化
│   ├── core.py                      # MissAVScraper 主类
│   ├── constants.py                 # 常量定义
│   └── utils.py                     # 工具函数
│
├── tests/                           # 测试文件
│   ├── __init__.py
│   ├── test_api.py
│   └── test_upgrade.py
│
├── examples/                        # 示例和演示
│   ├── basic_usage.py
│   ├── demo_incremental.py
│   ├── demo_collection_limit.py
│   ├── check_env.py
│   └── diagnose.py
│
├── docs/                            # 文档
│   ├── README.md
│   ├── QUICKSTART.md
│   ├── GUIDE.md
│   └── TROUBLESHOOTING.md
│
├── config/                          # 配置文件
│   └── config.example.json
│
├── output/                          # 输出目录（自动生成）
│   └── missav.m3u                   # 生成的 M3U 文件
│
├── main.py                          # 主入口脚本
├── setup.py                         # 项目配置（setuptools）
├── pyproject.toml                   # 项目元信息（PEP 517）
├── requirements.txt                 # 依赖列表
└── README.md                        # 本文件
```

## 🚀 快速开始

### 安装

1. **克隆项目**
```bash
git clone https://github.com/KRikdis/missav.git
cd missav
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

### 基础使用

```bash
# 最简单的使用（推荐）
python main.py

# 自定义输出文件
python main.py -o my_playlist.m3u

# 限制收集数量（保守，IP 更安全）
python main.py --max-videos 200

# 详细日志输出
python main.py -v

# 查看所有选项
python main.py --help
```

### 在代码中使用

```python
from src.missav_scraper import MissAVScraper

# 创建爬虫实例
scraper = MissAVScraper(
    output_file='output/missav.m3u',
    max_videos=500,
    verbose=True
)

# 运行爬虫
scraper.run()
```

## 📋 启动参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `output_file` | str | `output/missav.m3u` | M3U 输出文件路径 |
| `enable_checkpoint` | bool | True | 是否启用断点续爬 |
| `max_videos` | int | 500 | 每次运行最多收集的视频数 |
| `verbose` | bool | False | 是否启用详细日志 |

### 查询参数（可配置）

在 `src/missav_scraper/constants.py` 中修改：

```python
DEFAULT_QUERIES = ["a", "b", "c", "d", "e"]  # 查询字符串
VIDEOS_PER_QUERY = 50                        # 每个查询的视频数
MAX_VIDEOS_PER_RUN = 500                     # 每次运行限制
```

## 📤 输出格式

生成的 M3U 文件示例：

```
#EXTM3U
#EXTINF:-1 group-title="日本" tvg-name="ABC-123" tvg-logo="https://example.com/thumb.jpg" epg-url="",ABC-123
https://media.example.com/video.m3u8
#EXTINF:-1 group-title="高清" tvg-name="ABC-124" tvg-logo="https://example.com/thumb2.jpg" epg-url="",ABC-124
https://media.example.com/video2.m3u8
```

**特点**：
- 每个视频的每个分类生成独立条目
- 自动提取缩略图作为 `tvg-logo`
- 使用分类作为 `group-title`

## ⚙️ 高级配置

### 修改收集限制

```bash
# 保守模式（极低风险）
python main.py --max-videos 100

# 标准模式（推荐）
python main.py --max-videos 500

# 快速模式（中等风险）
python main.py --max-videos 1000
```

### 扩展查询范围

编辑 `src/missav_scraper/constants.py`：

```python
DEFAULT_QUERIES = [
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j",  # 10 个查询
    "k", "l", "m", "n", "o"
]
VIDEOS_PER_QUERY = 100  # 每个查询 100 个视频
```

### 清除进度和数据

```bash
# 仅清除进度文件（保留已下载的 M3U）
python main.py --clean

# 完全重置（删除进度和 M3U 文件）
python main.py --clean-all
```

## 📖 使用场景

### 场景 1：初次使用（推荐）

```bash
# Day 1
python main.py --max-videos 500
# 收集 500 条，生成 output/missav.m3u

# Day 2
python main.py --max-videos 500
# 继续收集 500 条，追加到 output/missav.m3u (共 1000 条)

# Day 3
python main.py --max-videos 500
# 再收集 500 条，追加到 output/missav.m3u (共 1500 条)
```

### 场景 2：保守构建（IP 安全第一）

```bash
# 每次只收集 200 条，间隔 24 小时
# 5 天后累积 1000 条
python main.py --max-videos 200
```

### 场景 3：快速积累（网络稳定时）

```bash
# 快速收集 1000 条
python main.py --max-videos 1000
```

## 🔧 故障排除

### 导入错误：`No module named 'missav_api'`

```bash
pip install missav-api
# 或重新安装所有依赖
pip install -r requirements.txt
```

### 获取不到数据

1. 检查网络连接
2. 验证 MissAV 网站是否可访问
3. 运行诊断脚本：

```bash
python examples/diagnose.py
```

### 文件保存出错

- 确保 `/workspaces/missav/output` 目录有写入权限
- 检查磁盘空间是否充足
- 尝试指定不同的输出路径：

```bash
python main.py -o /tmp/missav.m3u
```

### 更多帮助

查看完整文档：
- [快速入门指南](docs/QUICKSTART.md)
- [详细使用指南](docs/GUIDE.md)
- [故障排除](docs/TROUBLESHOOTING.md)

## 📝 更新日志

### v2.0.0 (2026-03-21)
- ✅ 完整重构：模块化架构
- ✅ 新增 `src/` 目录结构
- ✅ 统一代码风格和命名规范
- ✅ 创建 setup.py 和 pyproject.toml
- ✅ 整理测试文件到 tests/
- ✅ 整理示例到 examples/
- ✅ 重新组织文档到 docs/
- ✅ 支持 M3U 增量更新和自动去重
- ✅ 实现断点续爬功能
- ✅ 添加收集限制保护 IP

### v1.0.0
- 初始版本

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**⚠️ 免责声明**

本项目仅供学习和研究使用，用户对使用本项目所造成的任何后果负责。

**📧 联系方式**

- Issue: https://github.com/KRikdis/missav/issues
- 讨论: https://github.com/KRikdis/missav/discussions

## 配置文件示例

创建 `config.json`：

```json
{
  "output_file": "missav.m3u",
  "request_timeout": 30,
  "retry_count": 3,
  "request_delay": 1,
  "max_pages": 1000,
  "group_title": "成人频道",
  "tvg_logo": "",
  "epg_url": ""
}
```

## 注意事项

- ⚠️ 爬虫会在请求之间添加延迟以避免被网站限制
- ⚠️ 请尊重网站的 robots.txt 和服务条款
- ⚠️ 爬取的数据**仅供个人学习使用**
- ⚠️ 不要频繁运行爬虫，避免给网站造成压力

## 故障排除

### 导入错误：`No module named 'missav_api'`

确保已安装依赖：

```bash
pip install -r requirements.txt
# 或者
pip install missav-api requests
```

### 获取不到数据

1. 检查网络连接
2. 验证 missav 网站是否可访问
3. 运行时加入详细日志：`python scraper.py -v`
4. 检查 `missav_api` 库的版本是否过旧

### 文件保存出错

- 确保当前目录有写入权限
- 检查磁盘空间是否充足
- 尝试指定完整的输出路径

## 许可

本项目仅供学习和参考使用。

## 更新日志

### v1.0
- ✓ 基础爬虫功能
- ✓ M3U 格式输出
- ✓ 错误处理和日志记录
- ✓ 命令行参数支持
