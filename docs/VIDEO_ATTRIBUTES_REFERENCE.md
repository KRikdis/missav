# 视频对象属性参考文档

## 视频对象完整属性列表

获取时间: 2026-03-21
测试视频: SNOS-147-UNCENSORED-LEAK （女演员：鷲尾めい）

### 📌 核心播放属性

| 属性名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| `video_code` | str | 视频代码/番号 | `SNOS-147-UNCENSORED-LEAK` |
| `m3u8_base_url` | str | M3U8 播放地址（流媒体URL） | `https://surrit.com/.../playlist.m3u8` |
| `url` | str | 视频页面 URL | `https://missav.ws/cn/SNOS-147-UNCENSORED-LEAK` |
| `thumbnail` | str | 缩略图 URL | `https://fourhoi.com/snos-147.../cover-n.jpg` |

### 📌 分类/标签属性

| 属性名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| `series` | **str** | **系列名称（单个字符串！）** | `吉野笃史` |
| `genres` | list | 流派/标签列表 | `['鹫尾芽衣 (鷲尾めい)']` |
| `manufacturer` | str | 工作室/厂家 | `无码流出` |
| `etiquette` | str | 标签代码 | `S1` |

### 📌 内容属性

| 属性名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| `title` | str | 中文标题 | `SNOS-147 一位身材异常丰满的女子...` |
| `title_original_japanese` | str | 日文原标题 | `異常に巨乳で異様なエロウェア...` |
| `publish_date` | str | 发布日期 | `2026-03-20` |

### 📌 其他属性

| 属性名 | 类型 | 说明 |
|--------|------|------|
| `content` | str | HTML 页面内容 |
| `core` | BaseCore | 爬虫核心对象 |
| `logger` | Logger | 日志对象 |
| `meta_divs` | ResultSet | 元数据 div 元素 |

## 🔍 不存在的属性

以下属性在对象中不存在：
- `actresses` - 女演员信息
- `studio` - 工作室（改用 `manufacturer`）
- `release_date` - 发布日期（改用 `publish_date`）
- `rating` - 评分
- `description` - 描述

## ⚠️ 注意事项

1. **`series` 是字符串**
   - 不是列表！例如：`"吉野笃史"` 而不是 `["吉野笃史"]`
   - 代码需要检查类型并转换为列表
   - 当前代码处理正确：
     ```python
     series_raw = getattr(video_obj, 'series', [])
     if not isinstance(series_raw, list):
         series_raw = [series_raw] if series_raw else []
     ```

2. **`genres` 是列表**
   - 包含女演员信息，例如：`['鹫尾芽衣 (鷲尾めい)']`
   - 可能包含多个元素

3. **`manufacturer` 字段名易混淆**
   - 虽然名叫 `manufacturer`，但实际是"工作室/厂家"

4. **发布日期格式**
   - `publish_date` 是字符串格式：`"YYYY-MM-DD"`

## 💾 在我们代码中的使用

核心字段映射：
```python
video_entry = {
    'code': video_obj.video_code,          # 视频代码
    'url': video_obj.m3u8_base_url,        # M3U8 播放地址
    'series': normalize_series(video_obj.series),  # 系列/分类
    'thumbnail': video_obj.thumbnail,      # 缩略图
    'group_title': s  # 按系列展开后的分类标题
}
```
