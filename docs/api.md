
# API 文档

本项目提供了一组用于 Google 搜索结果过滤、图片 OCR 检测等功能的 HTTP API。所有接口均为 POST 请求，数据格式为 JSON，返回 JSON 格式。

## 通用说明
- 所有接口均以 `http://localhost:5000` 为基础地址。
- 推荐 Content-Type: `application/json`
- 返回值中如无特殊说明，`filtered_response` 字段为过滤后的response.body。

## 1. /google_search_filter
- **描述**：过滤 Google 搜索建议（complete/search）。
- **请求方式**：POST
- **请求参数**：
  - `response` (string): response.body 内容（非原始 HTML/请求头）。
  - `filter_words` (list[string], 可选): 过滤关键词列表。
- **返回示例**：
```json
{
  "filtered_response": "...过滤后的内容..."
}
```

---

## 2. /google_search_page_filter
- **描述**：过滤 Google 搜索主页面结果。
- **请求方式**：POST
- **请求参数**：
  - `response` (string): response.body 内容（非原始 HTML/请求头）。
  - `filter_words` (list[string], 可选): 过滤关键词列表。
- **返回示例**：
```json
{
  "filtered_response": "...过滤后的内容..."
}
```

---

## 3. /image_detection_paddle_ocr
- **描述**：对图片内容（通常为 response.body，非原始 HTML）进行 OCR 检测并过滤。
- **请求方式**：POST
- **请求参数**：
  - `image` (string): base64 编码的图片数据，通常为 response.body。
  - `filter_words` (list[string], 可选): 过滤关键词列表。
- **返回示例**：
```json
{
  "filter_result": true,
  "ocr_result": [
    {
      "text": "识别出的文本",
      "confidence": 0.99,
      "position": [[1.0, 2.0], [3.0, 4.0], ...]
    },
    ...
  ]
}
```


## 错误返回
- 所有接口出错时返回：
```json
{
  "error": "错误信息"
}
```

---

## 备注
- 建议合理设置 `filter_words`，以实现自定义过滤需求。
- 详细参数和返回内容可参考源码实现。
