# MissAV M3U 爬虫

这是一个使用 `missav_api` 库爬取 missav 网站所有 AV 番号和对应 m3u 地址的程序。支持将数据保存为标准 M3U 格式，兼容各种播放器。

## 功能

- ✓ 爬取 missav 网站所有视频的番号和 m3u 地址
- ✓ 将数据保存为标准 M3U 格式，兼容各种播放器
- ✓ 支持自动分页和完善的错误处理
- ✓ 完整的日志记录和调试支持
- ✓ 支持配置文件自定义
- ✓ 支持命令行参数

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行爬虫

```bash
python main.py
```

或者使用 `scraper.py` 获得更多功能选项：

```bash
python scraper.py -o missav.m3u -v
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `main.py` | 简单入口脚本 |
| `scraper.py` | 主要爬虫模块（支持命令行参数） |
| `requirements.txt` | 依赖列表 |
| `config.example.json` | 配置文件示例 |
| `README.md` | 本文件 |

## 使用方法

### 方式 1：最简单（main.py）

```bash
python main.py
```

**输出**: `missav.m3u`

### 方式 2：高级选项（scraper.py）

```bash
# 基本用法
python scraper.py

# 自定义输出文件
python scraper.py -o custom_output.m3u

# 加载配置文件
python scraper.py -c config.json

# 详细日志输出
python scraper.py -v

# 组合使用
python scraper.py -o output.m3u -c config.json -v
```

### 方式 3：在 Python 代码中使用

```python
from scraper import MissAVAPIClient

scraper = MissAVAPIClient(output_file='missav.m3u')
scraper.run()
```

## 输出格式

生成的 M3U 文件格式如下：

```
#EXTM3U
#EXTINF:-1 group-title="成人频道" tvg-name="番号1" tvg-logo="" epg-url="",番号1
m3u地址1
#EXTINF:-1 group-title="成人频道" tvg-name="番号2" tvg-logo="" epg-url="",番号2
m3u地址2
```

## 命令行参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--output` | `-o` | 输出文件名 | `missav.m3u` |
| `--config` | `-c` | 配置文件路径 | 无 |
| `--verbose` | `-v` | 详细日志输出 | 关闭 |

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
