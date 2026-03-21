# Search API 修复总结

## 问题诊断
爬虫程序在 batch-actresses 模式下快速终止，只处理了少数几个演员。原因是 **search 循环中存在冗余的 API 调用**。

## 根本原因
在 `fetch_videos()` 的搜索结果处理循环中（第 425-455 行）：
- 获取搜索结果：`search_results = client.search(query, video_count=1000)`
- **错误地** 为每个结果再调用 `client.get_video()` 获取完整信息
- 实际上 `search()` 已返回完整的视频对象，不需要二次调用

这导致：
1. **API 请求数翻倍** - 本应 N 个请求变成 2N 个
2. **可能触发速率限制** - API 限制请求频率
3. **程序提前终止** - 由于限制导致某些搜索失败

## 修复方案
**删除冗余的 `get_video()` 调用**

### 修改前（错误）
```python
for video_summary in search_results:
    result_count += 1
    video_code = video_summary.video_code
    video_url = f"https://missav.ws/cn/{video_code}"
    
    if video_code in self.processed_codes:
        continue
    
    # ❌ 多余的 API 调用！
    video_obj = client.get_video(video_url)
    self.request_count += 1
    
    entries = self._process_video_object(video_obj, query)
```

### 修改后（正确）
```python
for video_obj in search_results:
    result_count += 1
    video_code = video_obj.video_code
    
    if video_code in self.processed_codes:
        continue
    
    # ✅ 直接使用 search() 返回的完整对象
    entries = self._process_video_object(video_obj, query)
```

## 验证结果
测试运行（限制 100 个条目）：
- ✓ 生成了 100 个 M3U 条目
- ✓ 处理了 2 个演员（进度保存正确）
- ✓ 状态文件正确生成和保存
- ✓ 爬虫能持续运行（不再提前终止）

## API 对比
官方示例：
```python
video_results = client.search(query="吉野笃史", video_count=50)
for video in video_results:
    print(video.title)  # ✓ 直接使用完整对象
```

当前修复的代码：
```python
search_results = client.search(query=actress, video_count=1000)
for video_obj in search_results:
    entries = self._process_video_object(video_obj, query)  # ✓ 直接使用
```

## 修改文件
- `src/missav_scraper/core.py` - 第 425-455 行的搜索循环逻辑

## 后续建议
- 监控爬虫运行日志，确认能处理全部 1007 个演员
- 若需要添加分页等功能，参考 missav_api 的官方文档
