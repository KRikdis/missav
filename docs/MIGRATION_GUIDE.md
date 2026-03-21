# 迁移指南 - v1.0 → v2.0

从旧版本升级到新版本 2.0 的完整指南。

---

## 🔄 变更概览

**关键改动**：
- 项目结构重组
- M3U 输出位置改变
- 代码模块化
- 文档重新组织

**影响**：
- ⚠️ 输出文件位置改变
- ⚠️ 导入路径改变（如果使用 Python 代码）
- ✅ 功能完全相同
- ✅ 用法基本相同

---

## 📦 安装升级

### 方法 1：直接替换（推荐新用户）

```bash
# 1. 备份旧文件
cp -r missav missav_backup

# 2. 克隆新版本
git clone https://github.com/KRikdis/missav.git
cd missav

# 3. 安装依赖
pip install -r requirements.txt

# 4. 测试运行
python main.py --help
```

### 方法 2：原地升级（保留现有数据）

```bash
# 1. 在项目目录运行
cd /path/to/missav

# 2. 备份 M3U 文件
cp *.m3u backup/

# 3. 更新项目（假设使用 git）
git pull origin main

# 4. 迁移 M3U 文件
mkdir -p output
mv *.m3u output/

# 5. 测试新版本
python main.py --help
```

---

## 🔗 命令迁移

### 旧命令

```bash
# scraper.py（v1.0）
python scraper.py
python scraper.py -o custom.m3u
python scraper.py -v

# advanced_scraper.py（v1.0）
python advanced_scraper.py

# main.py（v1.0）
python main.py
```

### 新命令

```bash
# main.py（v2.0）
python main.py                      # 完全相同功能
python main.py -o custom.m3u        # 新增支持
python main.py -v                   # 完全相同
python main.py --max-videos 500     # 新功能：限制收集
python main.py --help               # 新增：完整帮助
```

**对应关系**：

| v1.0 命令 | v2.0 等效命令 |
|----------|-------------|
| `python main.py` | `python main.py` |
| `python scraper.py -o out.m3u` | `python main.py -o out.m3u` |
| `python scraper.py -v` | `python main.py -v` |
| `python advanced_scraper.py` | `python main.py` (功能已内置) |

---

## 📁 文件位置变化

### M3U 输出文件

**v1.0**：
```
missav.m3u             ← 项目根目录
```

**v2.0**：
```
output/missav.m3u      ← 输出目录
```

**迁移步骤**：
```bash
# 自动化迁移（推荐）
mkdir -p output
mv *.m3u output/

# 或使用新版本自动生成
python main.py

# 找到生成的文件
cat output/missav.m3u
```

---

## 💻 Python 代码迁移

### 旧方式（v1.0）

```python
# ❌ v1.0 风格
from scraper_final import MissAVScraper

scraper = MissAVScraper(output_file='missav.m3u')
scraper.run()
```

### 新方式（v2.0）

```python
# ✅ v2.0 推荐方式
from src.missav_scraper import MissAVScraper

scraper = MissAVScraper(
    output_file='output/missav.m3u',
    max_videos=500,
    verbose=True
)
scraper.run()
```

### 迁移指南

1. **更新导入**：
```python
# 旧
from scraper_final import MissAVScraper

# 新
from src.missav_scraper import MissAVScraper
```

2. **更新输出文件路径**：
```python
# 旧
scraper = MissAVScraper(output_file='missav.m3u')

# 新
from pathlib import Path
from src.missav_scraper import constants
default_path = str(Path(constants.OUTPUT_DIR) / constants.OUTPUT_FILE)
scraper = MissAVScraper(output_file=default_path)

# 或简洁方式
scraper = MissAVScraper()  # 自动使用 output/missav.m3u
```

3. **使用新的参数**：
```python
# v2.0 新增参数
scraper = MissAVScraper(
    output_file='output/missav.m3u',
    enable_checkpoint=True,      # 断点续爬
    max_videos=500,              # 限制收集数量
    verbose=True                 # 详细日志
)
```

---

## 📖 文档位置变化

### 文档路径

**v1.0**：
```
README.md                    ← 主文档
QUICKSTART.md               ← 快速入门
MODIFICATIONS.md            ← 修改说明（现已删除）
INCREMENTAL_UPDATE.md       ← 增量更新（现已删除）
...（混乱的结构）
```

**v2.0**：
```
README.md                    ← 主文档（更新）
docs/
  ├── QUICKSTART.md         ← 快速入门
  ├── API.md                ← 新：API 参考
  ├── TROUBLESHOOTING.md    ← 新：故障排除
  └── REFACTOR_SUMMARY.md   ← 新：重构说明
```

**查看文档**：

| 需求 | v1.0 | v2.0 |
|------|------|------|
| 了解项目 | README.md | README.md |
| 快速开始 | QUICKSTART.md | docs/QUICKSTART.md |
| 查看 API | 无 | docs/API.md |
| 问题排除 | TROUBLESHOOTING.py | docs/TROUBLESHOOTING.md |

---

## 🗂️ 项目结构变化

### 文件保留

**v1.0 的旧文件保留备份**（供参考）：

```bash
# 这些文件仍在项目中作为备份（可选删除）
scraper.py              # v1.0 基础爬虫
scraper_final.py        # v1.0 最终版本
advanced_scraper.py     # v1.0 高级版本

# 这些文档已整合到 docs/ 目录
QUICKSTART.md           # 已复制到 docs/
QUICK_REFERENCE.md      （现已删除）
MODIFICATIONS.md        （现已删除）
INCREMENTAL_UPDATE.md   （现已删除）
COLLECTION_LIMIT.md     （现已删除）
SOLUTION_SUMMARY.md     （现已删除）
```

**清理旧文件**（可选）：
```bash
# 如果确认不需要，可以删除
rm scraper.py scraper_final.py advanced_scraper.py
rm QUICK_REFERENCE.md MODIFICATIONS.md ...
```

### 新的目录结构

```
src/missav_scraper/        ← 新：核心包
tests/                    ← 新：测试目录
examples/                 ← 新：示例目录
docs/                     ← 新：文档目录
config/                   ← 新：配置目录
output/                   ← 新：输出目录
```

---

## ⚙️ 配置迁移

### 旧配置（v1.0）

在 `scraper.py` 或 `main.py` 中编辑：
```python
# 硬编码在源代码中
DEFAULT_QUERIES = ["a", "b", "c"]
VIDEOS_PER_QUERY = 50
```

### 新配置（v2.0）

**位置**：`src/missav_scraper/constants.py`

```python
# 集中式配置
DEFAULT_QUERIES = ["a", "b", "c", "d", "e"]
VIDEOS_PER_QUERY = 50
MAX_VIDEOS_PER_RUN = 500
MIN_DELAY = 2
MAX_DELAY = 5
```

**优势**：
- ✅ 配置集中式管理
- ✅ 更易发现和修改
- ✅ 类型安全和格式统一

**迁移步骤**：
```bash
# 1. 编辑新配置文件
nano src/missav_scraper/constants.py

# 2. 修改需要的参数
# 例如增加查询范围
DEFAULT_QUERIES = ["a", "b", "c", "d", "e", "f", "g", "h"]

# 3. 保存并运行
python main.py
```

---

## 🧪 功能对比

### 功能保留

| 功能 | v1.0 | v2.0 |
|------|------|------|
| 基础爬虫 | ✅ | ✅ |
| M3U 输出 | ✅ | ✅ |
| 命令行参数 | ✅ | ✅ |
| 详细日志 | ✅ | ✅ |
| 断点续爬 | ❌ (advanced) | ✅ |
| URL 去重 | ❌ (final) | ✅ |
| 增量更新 | ❌ (final) | ✅ |
| **收集限制** | ❌ | ✅ 新！ |
| **API 文档** | ❌ | ✅ 新！ |

### 新增功能

- ✅ 统一的入口点（main.py 支持所有功能）
- ✅ 模块化架构（便于扩展）
- ✅ 完整 API 文档
- ✅ 详细的故障排除指南
- ✅ 项目作为包可安装

---

## 🔍 兼容性检查

### 旧脚本是否仍然可用？

**直接使用 v1.0 脚本**：

```bash
# ✅ 仍然可用（文件保留）
python scraper_final.py
python scraper.py
python advanced_scraper.py

# ⚠️ 但不推荐，应使用新版本
python main.py  # ← 推荐
```

### 旧 cron 任务是否需要更新？

**旧 cron 任务**：
```bash
# v1.0 cron
0 2 * * * python /path/to/missav/scraper_final.py
```

**更新方式**：
```bash
# v2.0 cron（推荐）
0 2 * * * python /path/to/missav/main.py

# 或使用新的参数
0 2 * * * python /path/to/missav/main.py --max-videos 500
```

---

## 📱 从 Docker 运行（可选）

### 创建 Dockerfile（如需要）

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

### 构建和运行

```bash
docker build -t missav-scraper .
docker run -v $(pwd)/output:/app/output missav-scraper
```

---

## 📋 升级检查清单

- [ ] 备份现有数据
- [ ] 安装新版本依赖
- [ ] 测试 `python main.py --help`
- [ ] 运行 `python main.py -v`
- [ ] 验证 `output/missav.m3u` 生成
- [ ] 更新任何自定义脚本
- [ ] 更新任何 cron 任务
- [ ] 删除旧的临时文件（可选）

---

## ❓ 常见问题

### Q1：升级后速度是否变化？

**A**：基本相同。新版本在大多数情况下会稍快（更好的模块组织），但差异不明显。

### Q2：旧的 M3U 文件是否兼容？

**A**：是的，完全兼容。可以：
```bash
# 复制旧文件
cp old_missav.m3u output/missav.m3u

# 继续追加
python main.py

# 或导入到播放器
```

### Q3：是否可以在升级后回退到 v1.0？

**A**：可以，保留了 v1.0 的文件：
```bash
# 如果需要回退
git checkout <v1.0-commit>
python scraper_final.py
```

### Q4：Python 版本要求是否改变？

**A**：否，要求相同（Python 3.8+）

### Q5：依赖包是否改变？

**A**：否，requirements.txt 基本相同

---

## 🆘 升级遇到问题

### 问题 1：找不到 src 模块

```python
# ❌ 错误
from missav_scraper import MissAVScraper

# ✅ 正确
from src.missav_scraper import MissAVScraper

# ✅ 或在项目根目录运行
python main.py
```

### 问题 2：output 目录找不到

```bash
# 自动创建
mkdir -p output
python main.py

# 或明确指定路径
python main.py -o ./output/missav.m3u
```

### 问题 3：旧的导入仍然有效吗？

```python
# ❌ 不推荐（v1.0 方式，但保留兼容）
from scraper_final import MissAVScraper

# ✅ 推荐（v2.0 方式）
from src.missav_scraper import MissAVScraper
```

---

## 📞 获取帮助

如有升级问题：

1. 查看 [QUICKSTART.md](./docs/QUICKSTART.md)
2. 查看 [TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md)
3. 运行诊断脚本：`python examples/diagnose.py`
4. 提交 [Issue](https://github.com/KRikdis/missav/issues)

---

**升级完成！** 🎉

现在可以享受新版本的各种改进和新功能了。

---

**快速链接**：
- [项目 README](../README.md)
- [快速入门](./docs/QUICKSTART.md)
- [API 文档](./docs/API.md)
- [故障排除](./docs/TROUBLESHOOTING.md)
