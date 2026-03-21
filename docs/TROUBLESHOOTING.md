# 故障排除指南

## 常见错误

### 1. ImportError: No module named 'missav_api'

**错误信息**：
```
ImportError: No module named 'missav_api'
```

**原因**：未安装 missav_api 库

**解决方案**：
```bash
# 安装单个库
pip install missav-api

# 或重新安装所有依赖
pip install -r requirements.txt

# 验证安装
python -c "import missav_api; print('OK')"
```

---

### 2. FileNotFoundError: output directory

**错误信息**：
```
FileNotFoundError: [Errno 2] No such file or directory: 'output/missav.m3u'
```

**原因**：输出目录不存在

**解决方案**：
```bash
# 自动创建（脚本会自动处理，但可以手动创建）
mkdir -p output

# 或使用绝对路径
python main.py -o /full/path/to/missav.m3u
```

---

### 3. PermissionError: access denied

**错误信息**：
```
PermissionError: [Errno 13] Permission denied
```

**原因**：
- 没有写入权限
- 文件被其他程序占用
- 磁盘空间不足

**解决方案**：
```bash
# 检查权限
ls -la output/

# 修改权限
chmod 755 output

# 使用其他目录
python main.py -o ~/missav.m3u

# 检查磁盘空间
df -h
```

---

### 4. ConnectionError 或 Timeout

**错误信息**：
```
ConnectionError: Connection to https://missav.ws failed
HTTPError: 429 Too Many Requests
```

**原因**：
- 网络连接问题
- MissAV 网站无法访问
- 请求被限流

**解决方案**：
```bash
# 检查网络连接
ping 8.8.8.8

# 测试网站可访问性
python examples/diagnose.py

# 等等后再试
sleep 300 && python main.py

# 减少收集数量
python main.py --max-videos 100

# 增加延迟
# 编辑 src/missav_scraper/constants.py
# MIN_DELAY = 5
# MAX_DELAY = 10
```

---

### 5. JSON 解析错误

**错误信息**：
```
json.JSONDecodeError: Expecting value
ValueError: No JSON object could be decoded
```

**原因**：
- 状态文件损坏
- API 返回非预期格式

**解决方案**：
```bash
# 清除进度文件
python main.py --clean

# 查看状态文件内容
cat scraper_state.json

# 如果损坏，删除它
rm scraper_state.json
python main.py

# 再次尝试
python main.py -v
```

---

## 性能问题

### 1. 慢速爬取

**症状**：爬虫运行速度很慢

**可能原因**：
- 网络延迟
- 延迟设置过大
- 服务器远离

**解决方案**：
```bash
# 检查网络
ping -c 5 missav.ws

# 减少延迟（编辑 constants.py）
MIN_DELAY = 1
MAX_DELAY = 3

# 增加每批查询数量
VIDEOS_PER_QUERY = 100

# 使用 verbose 日志查看详情
python main.py -v
```

---

### 2. 内存占用过高

**症状**：程序占用大量内存

**可能原因**：
- 收集了过多视频
- 内存泄漏

**解决方案**：
```bash
# 减少每次收集数量
python main.py --max-videos 100

# 检查进程内存
ps aux | grep python

# 定期重启爬虫
python main.py --max-videos 200 && sleep 3600 && python main.py --max-videos 200
```

---

## 数据问题

### 1. M3U 文件为空或不完整

**症状**：生成的 M3U 文件很小或没有内容

**可能原因**：
- 没有获得到数据
- 所有 URL 都是重复的
- 网络中断

**解决方案**：
```bash
# 查看文件内容
head -20 output/missav.m3u
tail -20 output/missav.m3u
wc -l output/missav.m3u

# 清除进度重新开始
python main.py --clean

# 使用详细日志
python main.py -v

# 检查 API 是否正常
python examples/test_api.py
```

---

### 2. 重复的视频条目

**症状**：M3U 文件中有大量重复条目

**可能原因**：
- 去重功能未正常工作
- 旧的 M3U 文件损坏

**解决方案**：
```bash
# 备份旧文件
cp output/missav.m3u output/missav.m3u.bak

# 完全重置
python main.py --clean-all

# 重新爬取
python main.py

# 或手动去重
sort -u output/missav.m3u > output/missav_unique.m3u
```

---

### 3. 缺失分类或缩略图

**症状**：M3U 中没有分类或缩略图

**可能原因**：
- API 未返回这些数据
- 数据提取出错

**解决方案**：
```bash
# 查看原始数据
python examples/debug_search.py

# 检查提取逻辑（constants.py）
# M3U_EXTINF_FORMAT

# 验证 API 返回
python -c "
from missav_api import Client
c = Client()
for v in c.search('a', 1):
    print('genres:', v.genres)
    print('thumbnail:', v.thumbnail)
"
```

---

## 网络和 IP 相关

### 1. IP 被频繁限制

**症状**：频繁收到 429 或 403 错误

**原因**：
- 请求过于频繁
- 夜间流量大
- 多个客户端共享 IP

**解决方案**：
```bash
# 减少收集数量
python main.py --max-videos 50

# 增加延迟
# 编辑 constants.py
MIN_DELAY = 10
MAX_DELAY = 20
BATCH_DELAY = 30

# 每天固定时间运行（避免高峰）
0 2 * * * /usr/bin/python3 /path/to/main.py

# 使用代理（高级用户）
# 编辑 core.py，在 Client() 初始化时添加 proxy
```

---

### 2. DNS 解析失败

**错误信息**：
```
socket.gaierror: [Errno -2] Name or service not known
```

**原因**：
- 无网络连接
- DNS 服务异常

**解决方案**：
```bash
# 检查网络
ping 8.8.8.8

# 检查 DNS
nslookup missav.ws

# 更换 DNS
# Linux: 编辑 /etc/resolv.conf
nameserver 8.8.8.8
nameserver 1.1.1.1

# 重试
python main.py -v
```

---

## 调试技巧

### 启用详细日志
```bash
python main.py -v
```

日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL

---

### 运行诊断脚本
```bash
python examples/diagnose.py
```

检查：
- ✓ API 连接
- ✓ 网络可达性
- ✓ 返回数据格式
- ✓ 文件系统权限

---

### 测试 API
```bash
python examples/test_api.py
```

验证：
- ✓ missav_api 安装
- ✓ API 返回格式
- ✓ 数据有效性

---

### 调试搜索
```bash
python examples/debug_search.py
```

分析：
- ✓ 查询结果
- ✓ 返回的属性
- ✓ 数据结构

---

## 获取帮助

### 1. 查看日志

```bash
# 详细日志输出
python main.py -v 2>&1 | tee scraper.log

# 查看日志
cat scraper.log
tail -100 scraper.log
```

---

### 2. 查看状态文件

```bash
cat scraper_state.json | python -m json.tool
```

---

### 3. 检查文件权限

```bash
ls -la output/
ls -la scraper_state.json
```

---

### 4. 提交 Issue

访问 [GitHub Issues](https://github.com/KRikdis/missav/issues)

提供以下信息：
- 错误信息（完整输出）
- 运行的命令
- 系统信息（OS, Python 版本）
- 故障排除步骤

---

## 高级调试

### 修改日志级别
```python
import logging
logging.basicConfig(level=logging.DEBUG)

from src.missav_scraper import MissAVScraper
scraper = MissAVScraper(verbose=True)
scraper.run()
```

### 单步调试
```python
from src.missav_scraper import MissAVScraper

scraper = MissAVScraper()

# 只获取，不保存
videos = scraper.fetch_videos()
print(f"获取 {len(videos)} 个视频")

# 检查数据
for v in videos[:3]:
    print(v)

# 手动保存
scraper.save_to_m3u()
```

### 检查 API 响应
```python
from missav_api import Client

client = Client()
results = client.search('a', 5)
for video in results:
    print(f"Code: {video.video_code}")
    print(f"URL: {video.m3u8_base_url}")
    print(f"Genres: {video.genres}")
    print(f"Thumbnail: {video.thumbnail}")
    print("---")
```

---

## 最后的手段

### 完全重置
```bash
# 删除所有状态和结果
rm -rf output/ scraper_state.json

# 创建空目录
mkdir -p output

# 重新开始
python main.py
```

### 虚拟环境重建
```bash
# 删除虚拟环境
rm -rf venv/

# 创建新环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate.bat # Windows

# 重新安装依赖
pip install -r requirements.txt

# 运行
python main.py
```

---

**还有问题？** 

提交 [Issue](https://github.com/KRikdis/missav/issues) 或查看 [讨论板](https://github.com/KRikdis/missav/discussions)
