import json
import re
import time
from datetime import datetime

def contains_forbidden_text(text, forbidden_words):
    if not text or not forbidden_words:
        return False

    lower_text = text.lower()

    for word in forbidden_words:
        pattern = r'(?<![a-z])' + re.escape(word.lower()) + r'(?![a-z])'
        match = re.search(pattern, lower_text)

        if match:
            start, end = match.span()
            context = text[max(0, start - 10):min(len(text), end + 10)]
            print(f"🔥 检测到违禁词匹配 | 词: '{word}' | 位置: {start}-{end} | 上下文: '...{context}...'")
            return True

    return False


def contains_filter_words(text, forbidden_words):
    """检查文本中是否包含任何违禁词，返回匹配的违禁词列表"""
    if not text or not forbidden_words:
        return False

    lower_text = text.lower()

    for word in forbidden_words:
        pattern = r'(?<![a-z])' + re.escape(word.lower()) + r'(?![a-z])'
        match = re.search(pattern, lower_text)

        if match:
            start, end = match.span()
            context = text[max(0, start - 10):min(len(text), end + 10)]
            print(f"🔥 检测到违禁词匹配 | 词: '{word}' | 位置: {start}-{end} | 上下文: '...{context}...'")
            return word

    return None


def filter_useStoryTopicQuery(response_body, filter_words):
    print("开始过滤Today‘s News")
    try:
        # 解析JSON数据
        data = json.loads(response_body)

        # 获取故事条目列表
        items = data.get("data", {}).get("story_topic", {}).get("stories", {}).get("items", [])

        # 创建新列表存储过滤后的条目
        filtered_items = []
        removed_count = 0

        # 遍历所有条目
        for item in items:
            # 获取核心内容（标题+摘要）
            result = item.get("trend_results", {}).get("result", {})
            core = result.get("core", {})
            name = core.get("name", "")
            hook = core.get("hook", "")

            # 检查是否包含任何过滤词
            contains_filter_word = (
                    contains_forbidden_text(name, filter_words) or
                    contains_forbidden_text(hook, filter_words)
            )

            # 保留未包含过滤词的条目
            if not contains_filter_word:
                filtered_items.append(item)
            else:
                removed_count += 1
                print(f"🗑 移除条目: {name}")

        # 更新数据结构
        if "stories" in data["data"]["story_topic"]:
            data["data"]["story_topic"]["stories"]["items"] = filtered_items

        print(f" 过滤完成 | 原始条目: {len(items)} | 保留: {len(filtered_items)} | 移除: {removed_count}")

        # 返回过滤后的JSON
        return json.dumps(data, separators=(",", ":"))


    except Exception as e:

        print(f"过滤Today's news出错: {e}")

        return response_body


def filter_suggestions(data, filter_words):
    """过滤搜索建议中的敏感内容"""
    # 创建数据副本（避免修改原始数据）
    filtered_data = data.copy()

    # 1. 过滤用户列表
    if "users" in filtered_data:
        filtered_users = []
        for user in filtered_data["users"]:
            # 检查用户字段是否包含违禁词
            user_text = " ".join([
                user.get("name", ""),
                user.get("screen_name", ""),
                user.get("location", "")
            ]).lower()

            # 如果未检测到违禁词则保留
            if not any(banned_word.lower() in user_text for banned_word in filter_words):
                filtered_users.append(user)

        filtered_data["users"] = filtered_users

    # 2. 过滤话题列表
    if "topics" in filtered_data:
        filtered_topics = []
        for topic in filtered_data["topics"]:
            # 检查话题字段是否包含违禁词
            topic_text = topic.get("topic", "").lower()

            # 如果未检测到违禁词则保留
            if not any(banned_word.lower() in topic_text for banned_word in filter_words):
                filtered_topics.append(topic)

        filtered_data["topics"] = filtered_topics

    # 3. 更新结果计数
    filtered_data["num_results"] = (
            len(filtered_data.get("users", [])) +
            len(filtered_data.get("topics", [])) +
            len(filtered_data.get("events", [])) +
            len(filtered_data.get("lists", [])))

    return filtered_data


def filter_search_timeline_response(response_body, filter_words):
    try:
        data = json.loads(response_body)
        instructions = data.get("data", {}).get("search_by_raw_query", {}).get("search_timeline", {}).get("timeline",
                                                                                                          {}).get(
            "instructions", [])

        # 初始化统计
        total_entries = 0
        filtered_count = 0
        filtered_details = []

        for instruction in instructions:
            if instruction.get("type") != "TimelineAddEntries":
                continue

            original_count = len(instruction.get("entries", []))
            filtered_entries = []

            for entry in instruction.get("entries", []):
                total_entries += 1
                entry_id = entry.get("entryId", "")
                filtered = False
                filter_reason = ""

                # 1. 用户模块过滤
                if "usermodule" in entry_id or entry_id.startswith("user-"):
                    # 统一处理用户模块和用户条目
                    user_data = None

                    if "usermodule" in entry_id:
                        # 用户模块结构
                        for item in entry.get("content", {}).get("items", []):
                            user_data = item.get("item", {}).get("itemContent", {}).get("user_results", {}).get(
                                "result", {})
                            if user_data:
                                break
                    else:
                        # 用户条目结构
                        content = entry.get("content", {})
                        item_content = content.get("itemContent", {})
                        user_results = item_content.get("user_results", {})
                        user_data = user_results.get("result", {})

                    if user_data:
                        # 正确获取用户信息
                        core = user_data.get("core", {})
                        legacy = user_data.get("legacy", {})
                        screen_name = core.get("screen_name", "")
                        description = legacy.get("description", "")
                        name = core.get("name", "") or legacy.get("name", "")  # 兼容两种位置

                        # 检查用户信息中的违禁词
                        if contains_forbidden_text(screen_name, filter_words):
                            filter_reason = f"用户名 '{screen_name}' 含违禁词"
                            filtered = True
                        elif contains_forbidden_text(description, filter_words):
                            filter_reason = f"用户描述含违禁词: '{truncate_text(description, 30)}'"
                            filtered = True
                        elif contains_forbidden_text(name, filter_words):
                            filter_reason = f"用户显示名 '{name}' 含违禁词"
                            filtered = True

                        if filtered:
                            filtered_details.append(f" 用户过滤 | @{screen_name} | 原因: {filter_reason}")
                            filtered_count += 1

                # 2. 推文过滤
                elif entry_id.startswith("tweet-"):
                    tweet = entry.get("content", {}).get("itemContent", {}).get("tweet_results", {}).get("result", {})
                    legacy = tweet.get("legacy", {})
                    core = tweet.get("core", {})

                    # 获取推文作者信息 - 修复路径问题
                    user_data = core.get("user_results", {}).get("result", {})
                    if not user_data:
                        # 尝试备用路径
                        user_data = tweet.get("core", {}).get("user_results", {}).get("result", {})

                    # 获取用户详细信息
                    user_core = user_data.get("core", {})
                    user_legacy = user_data.get("legacy", {})
                    screen_name = user_legacy.get("screen_name", "")
                    description = user_legacy.get("description", "")
                    name = user_core.get("name", "") or user_legacy.get("name", "")

                    # 获取推文内容
                    tweet_text = legacy.get("full_text", "")

                    # 获取所有提及的用户名
                    user_mentions = []
                    entities = legacy.get("entities", {})
                    if entities:
                        for mention in entities.get("user_mentions", []):
                            user_mentions.append(mention.get("screen_name", ""))

                    # 检查过滤条件
                    # 1. 检查用户信息（用户名、显示名、描述）
                    if contains_forbidden_text(screen_name, filter_words):
                        filter_reason = f"作者用户名 @{screen_name} 含违禁词"
                        filtered = True
                    elif contains_forbidden_text(name, filter_words):
                        filter_reason = f"作者显示名 '{name}' 含违禁词"
                        filtered = True
                    elif contains_forbidden_text(description, filter_words):
                        filter_reason = f"作者描述含违禁词: '{truncate_text(description, 30)}'"
                        filtered = True

                    # 2. 检查推文内容
                    elif contains_forbidden_text(tweet_text, filter_words):
                        filter_reason = f"推文内容含违禁词: '{truncate_text(tweet_text, 40)}'"
                        filtered = True

                    # 3. 检查所有提及的用户名
                    elif any(contains_forbidden_text(mention, filter_words) for mention in user_mentions):
                        # 找出具体是哪个提及触发了过滤
                        for mention in user_mentions:
                            if contains_forbidden_text(mention, filter_words):
                                filter_reason = f"提及用户 @{mention} 含违禁词"
                                filtered = True
                                break

                    # 4. 检查媒体描述
                    else:
                        extended_entities = legacy.get("extended_entities", {})
                        media_list = extended_entities.get("media", []) if extended_entities else entities.get("media",
                                                                                                               [])

                        for media in media_list:
                            # 检查媒体描述
                            if contains_forbidden_text(media.get("description", ""), filter_words):
                                filter_reason = f"媒体描述含违禁词: '{truncate_text(media.get('description', ''), 30)}'"
                                filtered = True
                                break

                            # 检查附加媒体信息
                            additional_info = media.get("additional_media_info", {})
                            if contains_forbidden_text(additional_info.get("title", ""), filter_words) or \
                                    contains_forbidden_text(additional_info.get("description", ""), filter_words):
                                filter_reason = f"媒体附加信息含违禁词"
                                filtered = True
                                break

                    if filtered:
                        tweet_id = tweet.get("rest_id", "")
                        filtered_details.append(f" 推文过滤 | ID:{tweet_id} | @{screen_name} | 原因: {filter_reason}")
                        filtered_count += 1

                # 3. 社区模块过滤
                elif "community" in entry_id:
                    for item in entry.get("content", {}).get("items", []):
                        comm_data = item.get("itemContent", {}).get("community_results", {}).get("result", {})
                        comm_name = comm_data.get("name", "")
                        comm_desc = comm_data.get("description", "")

                        if contains_forbidden_text(comm_name, filter_words):
                            filter_reason = f"社区名称 '{comm_name}' 含违禁词"
                            filtered = True
                        elif contains_forbidden_text(comm_desc, filter_words):
                            filter_reason = f"社区描述含违禁词: '{truncate_text(comm_desc, 30)}'"
                            filtered = True

                        if filtered:
                            filtered_details.append(f" 社区过滤 | {comm_name} | 原因: {filter_reason}")
                            filtered_count += 1
                            break

                # 保留未过滤的条目
                if not filtered:
                    filtered_entries.append(entry)

            # 更新指令中的条目
            instruction["entries"] = filtered_entries
            remaining_count = len(filtered_entries)
            print(
                f" 模块处理 | 类型: {entry_id.split('-')[0] if '-' in entry_id else entry_id} | 原始条目: {original_count} | 保留: {remaining_count} | 过滤: {original_count - remaining_count}")

        # 最终统计
        print(
            f"\n 过滤完成 | 总条目: {total_entries} | 过滤: {filtered_count} | 保留: {total_entries - filtered_count}")

        if filtered_details:
            print("\n 过滤详情:")
            for detail in filtered_details:
                print(f"  - {detail}")
        else:
            print(" 无内容被过滤")

        return json.dumps(data).encode('utf-8')

    except Exception as e:
        print(f"❌ 过滤响应时出错: {e}")
        import traceback
        traceback.print_exc()
        return response_body.encode('utf-8')



# 辅助函数：截断长文本
def truncate_text(text, max_length):
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text


def filter_explore_content(response_body, filter_words):
    """过滤探索侧边栏JSON（explore_content.json）"""
    try:
        data = json.loads(response_body)
        if "data" not in data or "explore_sidebar" not in data["data"]:
            return response_body

        instructions = data["data"]["explore_sidebar"]["timeline"]["instructions"]
        deleted_items = []

        # 查找包含entries的instruction
        target_instruction = None
        for instruction in instructions:
            if instruction.get("type") == "TimelineAddEntries":
                target_instruction = instruction
                break

        if not target_instruction or "entries" not in target_instruction:
            return response_body

        entries = target_instruction["entries"]
        new_entries = []

        for entry in entries:
            if entry.get("content", {}).get("__typename") == "TimelineTimelineModule":
                items = entry["content"].get("items", [])
                new_items = []

                for item in items:
                    # 确保item结构存在
                    if not all(key in item for key in ["item", "itemContent"]):
                        new_items.append(item)
                        continue

                    item_content = item["item"]["itemContent"]
                    trend_name = item_content.get("name", "").lower()
                    metadata = item_content.get("trend_metadata", {})
                    domain_context = metadata.get("domain_context", "").lower()

                    if any(word in trend_name or word in domain_context for word in filter_words):
                        deleted_items.append({
                            "id": item.get("entryId", "unknown"),
                            "name": item_content.get("name", "unknown"),
                            "reason": f"Contains filter words in trend ({trend_name}) or domain ({domain_context})"
                        })
                    else:
                        new_items.append(item)

                if new_items:
                    entry["content"]["items"] = new_items
                    new_entries.append(entry)
                else:
                    deleted_items.append({
                        "id": entry.get("entryId", "unknown"),
                        "name": "Entire trend module",
                        "reason": "All items filtered out"
                    })
            else:
                new_entries.append(entry)

        target_instruction["entries"] = new_entries

        # 打印删除的元素
        if deleted_items:
            print(f"Filtered {len(deleted_items)} items from explore_content:")
            for item in deleted_items:
                print(f"  - {item['id']}: {item['name']} ({item['reason']})")

        return json.dumps(data)

    except Exception as e:
        print(f"Error filtering explore_content: {str(e)}")
        return response_body


def filter_TrendRelevantUsers(response_body, filter_words):

    # 解析JSON数据
    data = json.loads(response_body)

    try:
        # 定位到用户条目列表
        items = \
        data['data']['ai_trend_by_rest_id']['result']['trend_relevant_users']['timeline']['instructions'][0]['entries'][
            0]['content']['items']

        # 创建新的条目列表（用于存储保留的条目）
        new_items = []
        removed_count = 0

        # 检查每个用户条目
        for item in items:
            user_result = item['item']['itemContent']['user_results']['result']
            user_info = {
                'screen_name': user_result['core']['screen_name'],
                'name': user_result['core']['name'],
                'description': user_result.get('legacy', {}).get('description', ''),
                'location': user_result.get('location', {}).get('location', '')
            }

            # 检查是否包含过滤词
            match_found = False
            for field, value in user_info.items():
                if any(filter_word.lower() in value.lower() for filter_word in filter_words):
                    print(f"删除用户 @{user_info['screen_name']} - 字段 [{field}] 包含过滤词: '{value}'")
                    match_found = True
                    removed_count += 1
                    break

            # 保留未匹配的用户条目
            if not match_found:
                new_items.append(item)

        # 更新条目列表
        data['data']['ai_trend_by_rest_id']['result']['trend_relevant_users']['timeline']['instructions'][0]['entries'][
            0]['content']['items'] = new_items

        print(f"已过滤 {removed_count} 个用户条目，保留 {len(new_items)} 个条目")
        return json.dumps(data, ensure_ascii=False)


    except Exception as e:

        print(f"Error filtering : {str(e)}")

        return response_body


def filter_sidebar_recommendations(response_body, filter_words):
    """过滤推荐关注JSON（sidebar_recommendations.json）"""
    try:
        data = json.loads(response_body)
        if "data" not in data or "sidebar_user_recommendations" not in data["data"]:
            return response_body

        recommendations = data["data"]["sidebar_user_recommendations"]
        new_recommendations = []
        deleted_users = []

        for rec in recommendations:
            user = rec["user_results"]["result"]
            screen_name = user["core"]["screen_name"].lower()
            description = user["legacy"]["description"].lower() if "legacy" in user else ""

            if any(word in screen_name or word in description for word in filter_words):
                deleted_users.append({
                    "id": user["rest_id"],
                    "name": user["core"]["name"],
                    "reason": f"Contains filter words in screen_name ({screen_name}) or description ({description})"
                })
            else:
                new_recommendations.append(rec)

        data["data"]["sidebar_user_recommendations"] = new_recommendations

        # 打印删除的用户
        if deleted_users:
            print(f"Filtered {len(deleted_users)} users from sidebar_recommendations:")
            for user in deleted_users:
                print(f"  - {user['id']}: {user['name']} ({user['reason']})")

        return json.dumps(data)

    except Exception as e:
        print(f"Error filtering sidebar_recommendations: {str(e)}")
        return response_body


def filter_following_timeline(response_body, filter_words):
    """过滤首页时间线JSON（home_timeline.json）"""
    try:
        data = json.loads(response_body)
        if "data" not in data or "home" not in data["data"]:
            return response_body

        instructions = data["data"]["home"]["home_timeline_urt"]["instructions"]
        deleted_tweets = []
        filter_words = [word.lower() for word in filter_words]

        for instruction in instructions:
            if instruction["type"] != "TimelineAddEntries":
                continue

            entries = instruction["entries"]
            new_entries = []

            for entry in entries:
                entry_content = entry["content"]
                entry_type = entry_content.get("entryType")
                should_delete = False

                # 处理单条推文
                if entry_type == "TimelineTimelineItem":
                    item_content = entry_content["itemContent"]

                    # 获取推文数据
                    tweet_data = item_content.get("tweet_results", {}).get("result", {})

                    # 提取推文文本（支持普通推文和长文本）
                    tweet_text = ""
                    if "legacy" in tweet_data:
                        tweet_text = tweet_data["legacy"].get("full_text", "").lower()
                    elif "note_tweet" in tweet_data:
                        note_tweet = tweet_data["note_tweet"].get("note_tweet_results", {}).get("result", {})
                        tweet_text = note_tweet.get("text", "").lower()

                    # 提取用户信息
                    user_text = ""
                    user_screen_name = ""
                    if "core" in tweet_data:
                        user_data = tweet_data["core"].get("user_results", {}).get("result", {})
                        if "legacy" in user_data:
                            legacy = user_data["legacy"]
                            user_screen_name = legacy.get("screen_name", "").lower()
                            user_name = legacy.get("name", "").lower()
                            description = legacy.get("description", "").lower()
                            user_text = f"{user_screen_name} {user_name} {description}"

                    # 检查转推的原始内容
                    if "legacy" in tweet_data:
                        legacy = tweet_data["legacy"]
                        if "retweeted_status_result" in legacy:
                            retweet_data = legacy["retweeted_status_result"].get("result", {})
                            if "legacy" in retweet_data:
                                retweet_text = retweet_data["legacy"].get("full_text", "").lower()
                                tweet_text += " " + retweet_text

                    # 检查是否包含过滤词
                    full_text = f"{tweet_text} {user_text}".lower()
                    if any(word in full_text for word in filter_words):
                        deleted_tweets.append({
                            "id": entry["entryId"],
                            "text": tweet_text[:50] + "..." if tweet_text else "No text",
                            "user": user_screen_name if user_screen_name else "Unknown"
                        })
                        should_delete = True

                # 处理对话线程
                elif entry_type == "TimelineTimelineModule":
                    items = entry_content["items"]
                    new_items = []

                    for item in items:
                        item_content = item["item"]["itemContent"]
                        item_tweet_data = item_content.get("tweet_results", {}).get("result", {})

                        # 提取推文文本
                        item_tweet_text = ""
                        if "legacy" in item_tweet_data:
                            item_tweet_text = item_tweet_data["legacy"].get("full_text", "").lower()
                        elif "note_tweet" in item_tweet_data:
                            note_tweet = item_tweet_data["note_tweet"].get("note_tweet_results", {}).get("result", {})
                            item_tweet_text = note_tweet.get("text", "").lower()

                        # 提取用户信息
                        item_user_text = ""
                        item_user_screen_name = ""
                        if "core" in item_tweet_data:
                            item_user_data = item_tweet_data["core"].get("user_results", {}).get("result", {})
                            if "legacy" in item_user_data:
                                legacy = item_user_data["legacy"]
                                item_user_screen_name = legacy.get("screen_name", "").lower()
                                user_name = legacy.get("name", "").lower()
                                description = legacy.get("description", "").lower()
                                item_user_text = f"{item_user_screen_name} {user_name} {description}"

                        # 检查是否包含过滤词
                        item_full_text = f"{item_tweet_text} {item_user_text}".lower()
                        if any(word in item_full_text for word in filter_words):
                            deleted_tweets.append({
                                "id": item["entryId"],
                                "text": item_tweet_text[:50] + "..." if item_tweet_text else "No text",
                                "user": item_user_screen_name if item_user_screen_name else "Unknown"
                            })
                        else:
                            new_items.append(item)

                    # 更新对话线程中的条目
                    entry_content["items"] = new_items
                    should_delete = len(new_items) == 0

                # 保留不需要删除的条目
                if not should_delete:
                    new_entries.append(entry)

            # 更新指令中的条目列表
            instruction["entries"] = new_entries

        # 打印删除的推文
        if deleted_tweets:
            print(f"Filtered {len(deleted_tweets)} tweets from home_timeline:")
            for tweet in deleted_tweets:
                print(f"  - {tweet['id']} by @{tweet['user']}: {tweet['text']}")

        return json.dumps(data, ensure_ascii=False)

    except Exception as e:
        print(f"Error filtering home_timeline: {str(e)}")
        return response_body


def filter_explore_page(json_str, filter_words):
    try:
        data = json.loads(json_str)
        removed_count = 0
        removed_details = []

        # 增强版日志记录函数
        def log_removal(entry_id, entry_type, filter_reason, content_sample):
            nonlocal removed_count
            removed_count += 1
            # 构建详细的日志对象
            detail = {
                "id": entry_id,
                "type": entry_type,
                "reason": filter_reason,
                "content": content_sample
            }
            removed_details.append(detail)

        # 检查文本是否包含过滤词
        def contains_filter_words(text):
            if not text: return None
            for word in filter_words:
                if re.search(rf'\b{re.escape(word)}\b', text, re.IGNORECASE):
                    return word
            return None

        # 主过滤函数
        def filter_entries(entries):
            filtered = []
            for entry in entries:
                content = entry.get("content")
                entry_id = entry.get("entryId", "unknown")

                # 跳过无内容条目
                if not content:
                    filtered.append(entry)
                    continue

                # 1. 处理推文类型
                if (content.get("entryType") == "TimelineTimelineItem" and
                        content.get("itemContent", {}).get("itemType") == "TimelineTweet"):

                    tweet = content["itemContent"].get("tweet_results", {}).get("result", {})
                    text = tweet.get("legacy", {}).get("full_text", "")

                    if filter_reason := contains_filter_words(text):
                        # 记录详细日志
                        preview = text[:100] + "..." if len(text) > 100 else text
                        log_removal(entry_id, "推文", f"匹配关键词: {filter_reason}", preview)
                        continue

                # 2. 处理趋势/新闻条目
                elif (content.get("entryType") == "TimelineTimelineItem" and
                      content.get("itemContent", {}).get("itemType") == "TimelineTrend"):

                    trend = content["itemContent"]
                    text = trend.get("name", "")
                    meta_desc = trend.get("trend_metadata", {}).get("meta_description", "")
                    full_text = f"{text} {meta_desc}"

                    if filter_reason := contains_filter_words(full_text):
                        # 记录详细日志
                        preview = f"{text} ({meta_desc})"
                        log_removal(entry_id, "趋势话题", f"匹配关键词: {filter_reason}", preview)
                        continue

                # 3. 处理用户推荐模块
                elif (content.get("entryType") == "TimelineTimelineModule" and
                      entry_id.startswith("who-to-follow-")):

                    # 过滤模块内的每个用户
                    filtered_items = []
                    for item in content.get("items", []):
                        item_id = item.get("entryId", "unknown")
                        user = item.get("item", {}).get("itemContent", {}).get("user_results", {}).get("result", {})
                        name = user.get("legacy", {}).get("name", "")
                        desc = user.get("legacy", {}).get("description", "")
                        text = f"{name} {desc}"

                        if filter_reason := contains_filter_words(text):
                            # 记录详细日志
                            preview = f"{name}: {desc[:50]}..." if desc else name
                            log_removal(item_id, "推荐用户", f"匹配关键词: {filter_reason}", preview)
                            continue

                        filtered_items.append(item)

                    # 处理空模块
                    if not filtered_items:
                        header = content.get("header", {}).get("text", "用户推荐")
                        log_removal(entry_id, "推荐模块", "所有用户被过滤", f"模块标题: {header}")
                        continue

                    # 更新模块内容
                    content["items"] = filtered_items
                    entry["content"] = content

                # 4. 处理新闻故事模块
                elif (content.get("entryType") == "TimelineTimelineModule" and
                      entry_id.startswith("stories-")):

                    # 过滤模块内的新闻
                    filtered_items = []
                    for item in content.get("items", []):
                        item_id = item.get("entryId", "unknown")
                        trend = item.get("item", {}).get("itemContent", {})
                        name = trend.get("name", "")
                        context = trend.get("social_context", {}).get("text", "") if isinstance(
                            trend.get("social_context"), dict) else ""
                        text = f"{name} {context}"

                        if filter_reason := contains_filter_words(text):
                            # 记录详细日志
                            preview = f"{name} | {context}"
                            log_removal(item_id, "新闻故事", f"匹配关键词: {filter_reason}", preview)
                            continue

                        filtered_items.append(item)

                    # 处理空模块
                    if not filtered_items:
                        header = content.get("header", {}).get("text", "今日新闻")
                        log_removal(entry_id, "新闻模块", "所有故事被过滤", f"模块标题: {header}")
                        continue

                    # 更新模块内容
                    content["items"] = filtered_items
                    entry["content"] = content

                # 保留其他类型条目
                filtered.append(entry)

            return filtered

        # 1. 处理初始时间线
        explore_body = data.get("data", {}).get("explore_page", {}).get("body", {})
        if initial_timeline := explore_body.get("initialTimeline"):
            if timeline_obj := initial_timeline.get("timeline", {}).get("timeline"):
                for instruction in timeline_obj.get("instructions", []):
                    if instruction.get("type") == "TimelineAddEntries":
                        instruction["entries"] = filter_entries(instruction.get("entries", []))

        # 2. 处理所有分类时间线
        for timeline in explore_body.get("timelines", []):
            if timeline_data := timeline.get("timeline"):
                for instruction in timeline_data.get("instructions", []):
                    if instruction.get("type") == "TimelineAddEntries":
                        instruction["entries"] = filter_entries(instruction.get("entries", []))

        # 打印删除的条目信息
        if removed_details:
            print(f" 已删除 {removed_count} 个违规条目:")
            for detail in removed_details:
                print(f"   - ID: {detail['id']}")
                print(f"     类型: {detail['type']}, 原因: {detail['reason']}")
                print(f"     内容: {detail['content']}")

        return json.dumps(data, ensure_ascii=False)

    except Exception as e:
        print(f"JSON处理错误: {e}")
        return json_str


def filter_generic_timeline(response_body, filter_words):
    """
    过滤Twitter趋势数据，移除包含关键词的趋势条目
    """
    try:
        # 解析JSON数据
        data = json.loads(response_body)

        # 获取趋势条目列表路径
        instructions = data["data"]["timeline"]["timeline"]["instructions"]
        print(f" 找到 {len(instructions)} 条指令")

        # 寻找包含趋势的TimelineAddEntries指令
        trend_count = 0
        filtered_count = 0
        preserved_count = 0

        for instruction in instructions:
            if instruction["type"] == "TimelineAddEntries":
                entries = instruction["entries"]
                new_entries = []
                print(f" 开始处理 {len(entries)} 个条目...")

                # 过滤每个趋势条目
                for entry in entries:
                    # 处理非趋势条目（如游标）
                    if not entry["entryId"].startswith("trend-"):
                        new_entries.append(entry)
                        continue

                    trend_count += 1
                    # 获取趋势内容
                    content = entry["content"]
                    item_content = content.get("itemContent", {})

                    # 检查是否为趋势条目
                    if item_content.get("itemType") == "TimelineTrend":
                        name = item_content.get("name", "")
                        metadata = item_content.get("trend_metadata", {})
                        description = metadata.get("meta_description", "")

                        # 检查是否包含过滤关键词
                        should_filter = any(
                            keyword.lower() in name.lower() or
                            keyword.lower() in description.lower()
                            for keyword in filter_words
                        )

                        # 输出趋势信息
                        rank = item_content.get("rank", "?")
                        domain = metadata.get("domain_context", "")
                        trend_info = f"#{rank} {name} | {domain} | {description}"

                        # 保留不包含关键词的条目
                        if not should_filter:
                            preserved_count += 1
                            new_entries.append(entry)
                            print(f" 保留趋势: {trend_info}")
                        else:
                            filtered_count += 1
                            print(f" 过滤趋势: {trend_info}")
                    else:
                        new_entries.append(entry)

                # 更新条目列表
                instruction["entries"] = new_entries
                print(f" 条目更新完成: 原始 {len(entries)} → 当前 {len(new_entries)}")

        # 打印过滤摘要
        print(f"\n 过滤摘要:")
        print(f"• 总趋势条目: {trend_count}")
        print(f"• 过滤条目数: {filtered_count} (关键词: {', '.join(filter_words)})")
        print(f"• 保留条目数: {preserved_count}")

        # 返回过滤后的JSON
        return json.dumps(data, ensure_ascii=False)

    except Exception as e:
        print(f" 过滤趋势数据时出错: {e}")
        # 出错时返回原始数据
        return response_body


def filter_aitrendbrestid_detail(json_str, filter_words):
    """
    过滤包含关键词的AI趋势页面内容
    """
    print(f"开始过滤AiTrendByRestId内容，关键词: {filter_words}")

    try:
        data = json.loads(json_str)
        print("JSON解析成功，开始检查文章内容...")

        # 定位到文章内容
        article_text = data.get("data", {}).get("ai_trend_by_rest_id", {}).get("result", {}).get("page", {}).get(
            "article", {}).get("article_text", {}).get("text", "")

        # 检查是否包含过滤词
        found_keywords = []
        for word in filter_words:
            if word and word.lower() in article_text.lower():
                found_keywords.append(word)

        if found_keywords:
            print(f" 检测到过滤关键词: {found_keywords}，开始清空页面内容...")

            # 清空整个页面内容
            page = data["data"]["ai_trend_by_rest_id"]["result"].get("page", {})
            if page:
                # 记录原始内容长度用于对比
                orig_title_len = len(page["article"]["title"]) if "article" in page else 0
                orig_text_len = len(page["article"]["article_text"]["text"]) if "article" in page else 0

                # 清空文章内容
                if "article" in page:
                    page["article"]["title"] = ""
                    page["article"]["article_text"]["text"] = ""
                    page["article"]["article_text"]["entities"] = []

                # 清空时间线
                orig_timelines = len(page.get("post_timelines", []))
                page["post_timelines"] = []

                # 清空其他字段
                page["disclaimer"] = ""
                page["available_actions"] = []

                disable_cache = True
                print(
                    f" 页面内容已清空 | 标题: {orig_title_len}→0 字符 | 正文: {orig_text_len}→0 字符 | 时间线: {orig_timelines}→0 条")
        else:
            print("未检测到过滤关键词，保留原始内容")

        return json.dumps(data, ensure_ascii=False)

    except Exception as e:
        print(f" JSON解析错误: {e}，返回原始内容")
        return json_str


def filter_UserTweets(json_str, filter_words):
    start_time = time.time()
    original_size = len(json_str)
    filtered_count = 0
    recommended_filtered = 0
    total_tweets = 0
    total_recommended = 0

    try:
        # 解析JSON为Python对象
        data = json.loads(json_str)

        # 获取instructions列表
        instructions = data["data"]["user"]["result"]["timeline"]["timeline"]["instructions"]

        # 遍历所有指令
        for instruction in instructions:
            if instruction.get("type") == "TimelineAddEntries":
                entries = instruction["entries"]
                filtered_entries = []

                for entry in entries:
                    entry_id = entry["entryId"]

                    # 处理推文条目
                    if entry_id.startswith("tweet-"):
                        total_tweets += 1
                        try:
                            # 获取推文文本
                            tweet_content = entry["content"]["itemContent"]["tweet_results"]["result"]
                            legacy = tweet_content.get("legacy", {})
                            full_text = legacy.get("full_text", "").lower()

                            # 检查是否包含过滤词
                            contains_filter_word = any(
                                word.lower() in full_text
                                for word in filter_words
                            )

                            if contains_filter_word:
                                filtered_count += 1
                                continue  # 跳过包含过滤词的推文

                            filtered_entries.append(entry)

                        except KeyError:
                            # 结构异常时保留条目
                            filtered_entries.append(entry)

                    # 处理推荐关注模块
                    elif entry_id.startswith("who-to-follow-"):
                        total_recommended += 1
                        try:
                            items = entry["content"]["items"]
                            filtered_items = []

                            for item in items:
                                try:
                                    user_result = item["itemContent"]["user_results"]["result"]
                                    legacy = user_result.get("legacy", {})
                                    description = legacy.get("description", "").lower()

                                    # 检查简介是否包含过滤词
                                    contains_filter_word = any(
                                        word.lower() in description
                                        for word in filter_words
                                    )

                                    if contains_filter_word:
                                        recommended_filtered += 1
                                        continue  # 跳过包含过滤词的用户

                                    filtered_items.append(item)

                                except KeyError:
                                    # 结构异常时保留条目
                                    filtered_items.append(item)

                            # 更新过滤后的项目
                            if filtered_items:
                                entry["content"]["items"] = filtered_items
                                filtered_entries.append(entry)
                            else:
                                # 如果所有推荐用户都被过滤，则移除整个模块
                                recommended_filtered += 1

                        except KeyError:
                            # 结构异常时保留条目
                            filtered_entries.append(entry)

                    # 保留其他类型条目
                    else:
                        filtered_entries.append(entry)

                # 更新过滤后的条目
                instruction["entries"] = filtered_entries

        # 序列化回JSON
        filtered_json = json.dumps(data, ensure_ascii=False)
        filtered_size = len(filtered_json)

        # 打印过滤统计信息
        duration = time.time() - start_time
        print(f"[UserTweets过滤] 耗时: {duration:.4f}s | "
              f"原始: {original_size}字节 | 过滤后: {filtered_size}字节 | "
              f"过滤推文: {filtered_count}/{total_tweets} | "
              f"过滤推荐用户: {recommended_filtered}/{total_recommended}")

        return filtered_json

    except (json.JSONDecodeError, KeyError) as e:
        print(f"[UserTweets过滤] 错误: {e} | 返回原始数据")
        return json_str  # 解析失败时返回原始数据


def filter_ConnectTabTimeline(json_str, filter_words):
    start_time = time.time()
    original_length = len(json_str)
    print(f"开始过滤ConnectTabTimeline数据 | 原始长度: {original_length} 字符 | 过滤词: {filter_words}")

    if not json_str or not filter_words:
        print("警告: 输入为空或无过滤词配置")
        return json_str

    try:
        data = json.loads(json_str)
        total_users = 0
        removed_users = 0

        # 获取指令集
        instructions = data.get("data", {}).get("connect_tab_timeline", {}).get("timeline", {}).get("instructions", [])

        for instruction in instructions:
            if instruction.get("type") == "TimelineAddEntries":
                entries = instruction.get("entries", [])

                for entry in entries:
                    entry_id = entry.get("entryId", "")

                    # 扩展支持的条目类型
                    if any(entry_id.startswith(prefix) for prefix in [
                        "creators-only-connect-tab-",
                        "mergeallcandidatesmodule-"
                    ]):
                        items = []

                        # 处理不同结构的数据容器
                        content = entry.get("content", {})
                        if "items" in content:  # 直接包含items
                            items = content["items"]
                        elif "items" in content.get("content", {}):  # 嵌套在content内
                            items = content["content"]["items"]

                        total_users += len(items)

                        # 倒序过滤
                        new_items = []
                        for item in items:
                            user_data = item.get("item", {}).get("itemContent", {}).get("user_results", {}).get(
                                "result", {})

                            if not user_data:
                                # 尝试替代路径
                                user_data = item.get("content", {}).get("itemContent", {}).get("user_results", {}).get(
                                    "result", {})

                            if not user_data:
                                new_items.append(item)  # 保留无法解析的条目
                                continue

                            # 获取用户信息
                            core = user_data.get("core", {})
                            legacy = user_data.get("legacy", {})
                            screen_name = core.get("screen_name", "未知用户")
                            user_id = user_data.get("rest_id", "未知ID")

                            # 检查字段
                            text_fields = [
                                core.get("name", ""),
                                screen_name,
                                legacy.get("description", ""),
                                user_data.get("location", {}).get("location", "")
                            ]

                            # 检查过滤词
                            should_remove = False
                            matched_word = ""
                            matched_field = ""

                            for field in text_fields:
                                if not field:
                                    continue

                                for word in filter_words:
                                    if re.search(rf'\b{re.escape(word)}\b', field, flags=re.IGNORECASE):
                                        should_remove = True
                                        matched_word = word
                                        matched_field = field[:50] + "..." if len(field) > 50 else field
                                        break

                                if should_remove:
                                    break

                            if should_remove:
                                removed_users += 1
                                print(f"⚠️ 移除用户: @{screen_name} (ID:{user_id})")
                                print(f"   匹配词: '{matched_word}' | 字段内容: '{matched_field}'")
                            else:
                                new_items.append(item)

                        # 更新条目内容
                        if "content" in content and "items" in content["content"]:
                            content["content"]["items"] = new_items
                        else:
                            content["items"] = new_items

        # 转换回JSON
        result_json = json.dumps(data, ensure_ascii=False)
        new_length = len(result_json)

        # 打印统计
        process_time = time.time() - start_time
        preserved_users = total_users - removed_users
        print(f"过滤完成 | 耗时: {process_time:.3f}s")
        print(f"用户统计: 总数={total_users} | 保留={preserved_users} | 移除={removed_users}")
        print(f"数据长度: 原始={original_length} | 处理后={new_length} | 缩减={original_length - new_length}字符")

        return result_json
    except Exception as e:
        print(f" 处理过程中发生严重错误: {e}")
        print("返回原始数据")
        return json_str


def filter_ListLatestTweetsTimeline(json_str, filter_words):
    """
    过滤Twitter时间线JSON数据，删除包含指定关键词的条目（包括非推文条目）
    """
    if not json_str or not filter_words:
        print("无需过滤: 空数据或空关键词列表")
        return json_str

    try:
        # 解析JSON数据
        data = json.loads(json_str)
        original_count = 0
        filtered_count = 0

        # 编译关键词正则表达式，忽略大小写
        pattern = re.compile('|'.join(map(re.escape, filter_words)), re.IGNORECASE)
        print(f"开始过滤，关键词: {', '.join(filter_words)}")

        # 遍历所有指令
        for instruction in data.get('data', {}).get('list', {}).get('tweets_timeline', {}).get('timeline', {}).get(
                'instructions', []):
            if instruction.get('type') == 'TimelineAddEntries':
                # 创建新的条目列表（只保留不含关键词的条目）
                new_entries = []
                entries = instruction.get('entries', [])
                original_count = len(entries)

                for entry in entries:
                    entry_id = entry.get('entryId', '')
                    should_keep = True

                    # 提取所有可能的文本内容
                    texts = extract_text_from_entry(entry)

                    # 检查是否包含关键词
                    for text in texts:
                        if text and pattern.search(text):
                            print(f"过滤条目 {entry_id}: 包含关键词 - {text[:50]}...")
                            should_keep = False
                            filtered_count += 1
                            break

                    if should_keep:
                        new_entries.append(entry)

                # 更新条目列表
                instruction['entries'] = new_entries

        # 打印过滤统计信息
        print(f"过滤完成: 原始条目数={original_count}, 保留条目数={len(new_entries)}, 过滤条目数={filtered_count}")

        # 返回过滤后的JSON
        return json.dumps(data, ensure_ascii=False)

    except json.JSONDecodeError as e:
        print(f"JSON解析失败: {e}，返回原始数据")
        return json_str
    except Exception as e:
        print(f"过滤过程中出错: {e}，返回原始数据")
        return json_str


def extract_text_from_entry(entry):
    """
    从条目中提取所有可能的文本内容
    """
    texts = []

    try:
        # 通用文本提取路径（适用于所有条目类型）
        content = entry.get('content', {})

        # 1. 直接文本字段
        for field in ['value', 'text', 'title', 'description', 'header', 'footer', 'displayText']:
            if field in content:
                texts.append(str(content[field]))

        # 2. 嵌套文本字段
        for field in ['primaryText', 'secondaryText']:
            if field in content.get('header', {}):
                texts.append(str(content['header'][field].get('text', '')))

        # 3. 项目列表中的文本
        for item in content.get('items', []):
            item_content = item.get('item', {}).get('itemContent', {})
            for field in ['displayText', 'text', 'title', 'description']:
                if field in item_content:
                    texts.append(str(item_content[field]))

        # 推文特定文本提取
        item_content = content.get('itemContent', {})
        tweet_results = item_content.get('tweet_results', {})
        result = tweet_results.get('result', {})
        legacy = result.get('legacy', {})

        # 4. 主推文文本
        if 'full_text' in legacy:
            texts.append(legacy['full_text'])

        # 5. 转发推文文本
        retweeted = legacy.get('retweeted_status_result', {}).get('result', {})
        if retweeted and 'legacy' in retweeted:
            texts.append(retweeted['legacy'].get('full_text', ''))

        # 6. 引用推文文本
        quoted = legacy.get('quoted_status_result', {}).get('result', {})
        if quoted and 'legacy' in quoted:
            texts.append(quoted['legacy'].get('full_text', ''))

        # 7. 笔记推文文本（长文本）
        note_tweet = result.get('note_tweet', {}).get('note_tweet_results', {}).get('result', {})
        if note_tweet and 'text' in note_tweet:
            texts.append(note_tweet['text'])

    except (KeyError, TypeError) as e:
        # 忽略路径错误
        print(f"提取文本时路径错误: {e}")

    return [t for t in texts if t]  # 过滤掉空文本


def filter_CommunitiesExploreTimeline(json_str, filter_words):
    """
    过滤 CommunitiesExploreTimeline 的JSON响应
    """
    # 初始化统计变量
    original_entry_count = 0
    filtered_entry_count = 0
    banned_matches = []

    try:
        print(f" 开始过滤 CommunitiesExploreTimeline 数据，使用 {len(filter_words)} 个违禁词")
        data = json.loads(json_str)

        # 确保数据结构存在
        instructions = data.get('data', {}).get('viewer', {}).get('explore_communities_timeline', {}).get('timeline',
                                                                                                          {}).get(
            'instructions', [])

        # 预处理违禁词为小写（不区分大小写匹配）
        banned_pattern = re.compile(
            '|'.join(re.escape(word.lower()) for word in filter_words),
            re.IGNORECASE
        )

        # 遍历所有指令
        for instruction in instructions:
            if instruction.get('type') == 'TimelineAddEntries':
                entries = instruction.get('entries', [])
                original_entry_count = len(entries)

                if original_entry_count == 0:
                    print(" 警告: 未找到任何条目数据")
                    return json_str

                print(f" 发现 {original_entry_count} 个待处理条目")
                new_entries = []

                # 遍历每个条目
                for idx, entry in enumerate(entries):
                    entry_id = entry.get('entryId', f"unknown_{idx}")
                    try:
                        # 获取推文全文（可能位于不同层级）
                        text_sources = []
                        content = entry.get('content', {})

                        # 层级1：直接获取legacy.full_text
                        legacy = content.get('itemContent', {}).get('tweet_results', {}).get('result', {}).get('legacy',
                                                                                                               {})
                        if legacy:
                            text = legacy.get('full_text', "")
                            if text: text_sources.append(("推文正文", text))

                        # 层级2：尝试获取用户描述
                        user_desc = content.get('itemContent', {}).get('tweet_results', {}).get('result', {}).get(
                            'core', {}).get('user_results', {}).get('result', {}).get('legacy', {}).get('description',
                                                                                                        "")
                        if user_desc: text_sources.append(("用户描述", user_desc))

                        # 层级3：尝试获取社区描述
                        community_desc = content.get('itemContent', {}).get('tweet_results', {}).get('result', {}).get(
                            'community_results', {}).get('result', {}).get('description', "")
                        if community_desc: text_sources.append(("社区描述", community_desc))

                        # 检查所有文本来源
                        found_banned = False
                        matched_words = set()

                        for source_type, text in text_sources:
                            # 检查违禁词
                            matches = banned_pattern.findall(text.lower())
                            if matches:
                                found_banned = True
                                matched_words.update(matches)

                                # 打印匹配详情
                                log_text = text[:50] + "..." if len(text) > 50 else text
                                print(f" 检测到违禁内容 | 条目ID: {entry_id}")
                                print(f"  来源: {source_type}")
                                print(f"  匹配词汇: {', '.join(matches)}")
                                print(f"  内容片段: '{log_text}'")

                        if found_banned:
                            filtered_entry_count += 1
                            banned_matches.append({
                                "entry_id": entry_id,
                                "matched_words": list(matched_words),
                                "sample_text": text_sources[0][1][:100] if text_sources else "无文本"
                            })
                            continue  # 跳过违禁条目

                        new_entries.append(entry)

                    except Exception as e:
                        print(f" 处理条目 {entry_id} 时出错: {str(e)}")
                        new_entries.append(entry)  # 出错时保留原条目

                # 更新过滤后的条目
                instruction['entries'] = new_entries

        # 打印最终报告
        if filtered_entry_count == 0:
            print(f" 过滤完成: 检查了 {original_entry_count} 个条目，未发现违禁内容")
        else:
            print(f" 过滤完成: 移除了 {filtered_entry_count}/{original_entry_count} 个违禁条目")
            print(" 违禁条目详情:")
            for match in banned_matches:
                print(f"  - 条目ID: {match['entry_id']}")
                print(f"    匹配词汇: {', '.join(match['matched_words'])}")
                print(f"    内容示例: '{match['sample_text']}'")

        return json.dumps(data, ensure_ascii=False)

    except Exception as e:
        print(f"❌ 过滤时发生未知错误: {str(e)}")
        return json_str


def filter_CommunitiesFetchOneQuery(response_body, filter_words):
    """
    过滤CommunitiesFetchOneQuery类型的社区数据，使用print输出详细操作信息
    """
    # 生成唯一操作ID
    operation_id = f"OP-{int(time.time() * 1000)}"

    try:
        print(f"[{operation_id}]  开始处理社区数据 | 违禁词数量: {len(filter_words)}")
        data = json.loads(response_body)
        community = data.get("data", {}).get("communityResults", {}).get("result")

        if not community:
            print(f"[{operation_id}] ⚠ 未找到社区数据，跳过处理")
            return response_body

        # 提取基础信息
        comm_id = community.get('id_str', '未知ID')
        comm_name = community.get('name', '未命名社区')
        print(f"[{operation_id}]  正在检查社区: ID={comm_id} | 名称='{comm_name}'")

        # 准备检查的文本字段
        text_fields = []
        field_sources = []

        # 添加名称和描述字段
        if name := community.get("name"):
            text_fields.append(name)
            field_sources.append(f"社区名称: '{name}'")

        if desc := community.get("description"):
            text_fields.append(desc)
            field_sources.append(f"社区描述: '{desc[:50]}{'...' if len(desc) > 50 else ''}'")

        # 添加规则字段
        for i, rule in enumerate(community.get("rules", [])):
            if rule_name := rule.get("name"):
                text_fields.append(rule_name)
                field_sources.append(f"规则#{i + 1}名称: '{rule_name}'")

            if rule_desc := rule.get("description"):
                text_fields.append(rule_desc)
                field_sources.append(f"规则#{i + 1}描述: '{rule_desc[:50]}{'...' if len(rule_desc) > 50 else ''}'")

        print(f"[{operation_id}]  检查字段数: {len(text_fields)}")
        for i, source in enumerate(field_sources):
            print(f"    - [{i + 1}] {source}")

        # 构建违禁词正则
        pattern = re.compile("|".join(filter_words), re.IGNORECASE)
        violations = []

        # 检查每个文本字段
        for i, text in enumerate(text_fields):
            if match := pattern.search(text):
                field_name = field_sources[i].split(':')[0]
                matched_word = match.group(0)
                context_start = max(0, match.start() - 10)
                context_end = min(len(text), match.end() + 10)
                context = text[context_start:context_end].replace('\n', ' ')

                violations.append({
                    "field": field_name,
                    "word": matched_word,
                    "context": context,
                    "index": i + 1
                })

        # 处理违规情况
        if violations:
            print(f"[{operation_id}]  发现 {len(violations)} 处违规内容!")
            for v in violations:
                print(f"        违规 #{v['index']}:")
                print(f"        字段: {v['field']}")
                print(f"        违禁词: '{v['word']}'")
                print(f"        上下文: ...{v['context']}...")

            print(f"[{operation_id}]  删除社区: ID={comm_id} | 名称='{comm_name}'")

            # 清空社区数据但保留结构
            data["data"]["communityResults"]["result"] = None
            return json.dumps(data, ensure_ascii=False)

        # 无违规情况
        print(f"[{operation_id}]  社区检查通过 | ID={comm_id} | 名称='{comm_name}'")
        print(f"    检查字段: {len(text_fields)} 个 | 无违禁词")
        return response_body

    except json.JSONDecodeError as e:
        print(f"[{operation_id}]  JSON解析失败: {str(e)}")
        return response_body
    except Exception as e:
        print(f"[{operation_id}]  处理异常: {str(e)}")
        return response_body


def filter_CommunitiesRankedTimeline(json_str, filter_words):
    total_communities = 0
    filtered_count = 0
    filtered_details = []

    try:
        # 将JSON字符串解析为Python字典
        data = json.loads(json_str)

        # 获取社区条目路径
        instructions = data["data"]["viewer"]["ranked_communities_timeline"]["timeline"]["instructions"]

        # 遍历所有指令
        for instruction in instructions:
            if instruction.get("type") == "TimelineAddEntries":
                entries = instruction.get("entries", [])
                new_entries = []

                # 遍历所有条目
                for entry in entries:
                    # 只处理社区模块条目
                    if entry.get("entryId", "").startswith("community-to-join-"):
                        content = entry.get("content", {})
                        items = content.get("items", [])
                        new_items = []

                        # 检查每个社区条目
                        for item in items:
                            total_communities += 1
                            item_content = item.get("item", {}).get("itemContent", {})
                            community_results = item_content.get("community_results", {})
                            result = community_results.get("result", {})

                            community_id = result.get("id_str", "unknown")
                            community_name = result.get("name", "unknown")

                            # 检查关键字段是否包含违禁词
                            should_keep = True
                            trigger_word = None
                            trigger_field = None
                            trigger_text = None

                            # 检查名称、描述和问题字段
                            for field in ["name", "description", "question"]:
                                text = result.get(field, "")
                                for word in filter_words:
                                    if re.search(rf'\b{re.escape(word)}\b', text, re.IGNORECASE):
                                        should_keep = False
                                        trigger_word = word
                                        trigger_field = field
                                        trigger_text = text
                                        break
                                if not should_keep:
                                    break

                            # 检查规则字段
                            if should_keep:
                                for rule in result.get("rules", []):
                                    rule_text = rule.get("name", "") + " " + rule.get("description", "")
                                    for word in filter_words:
                                        if re.search(rf'\b{re.escape(word)}\b', rule_text, re.IGNORECASE):
                                            should_keep = False
                                            trigger_word = word
                                            trigger_field = "rule"
                                            trigger_text = rule_text
                                            break
                                    if not should_keep:
                                        break

                            # 处理过滤结果
                            if should_keep:
                                new_items.append(item)
                            else:
                                filtered_count += 1
                                filtered_details.append({
                                    "id": community_id,
                                    "name": community_name,
                                    "trigger_word": trigger_word,
                                    "trigger_field": trigger_field,
                                    "trigger_text": trigger_text
                                })

                        # 更新items列表
                        if new_items:
                            content["items"] = new_items
                            entry["content"] = content
                            new_entries.append(entry)
                        else:
                            # 如果模块中所有社区都被过滤，记录整个模块被移除
                            print(f"[社区过滤] 整个社区模块被移除，原包含 {len(items)} 个社区")
                    else:
                        # 保留非社区条目
                        new_entries.append(entry)

                # 更新entries列表
                instruction["entries"] = new_entries

        # 打印过滤结果摘要
        print("\n===== 社区过滤结果 =====")
        print(f"共检查 {total_communities} 个社区")

        if filtered_count > 0:
            print(f" 过滤了 {filtered_count} 个包含违禁词的社区:")
            for i, detail in enumerate(filtered_details, 1):
                print(f"\n【违规社区 #{i}】")
                print(f"  社区ID: {detail['id']}")
                print(f"  社区名称: '{detail['name']}'")
                print(f"  触发违禁词: '{detail['trigger_word']}'")
                print(f"  触发字段: {detail['trigger_field']}")
                print(f"  违规内容: '{detail['trigger_text']}'")
        else:
            print("🟢 未发现包含违禁词的社区")

        print("=======================\n")

        # 返回过滤后的JSON字符串
        return json.dumps(data, ensure_ascii=False)

    except Exception as e:
        print(f" 过滤JSON时出错: {e}")
        # 出错时返回原始JSON
        return json_str


def filter_community_entry(entry, filter_words):
    """过滤单个社区条目，返回过滤后的条目和违规信息"""
    try:
        # 获取社区内容的核心字段
        content = entry.get("content", {})
        item_content = content.get("itemContent", {})
        community_results = item_content.get("community_results", {})
        result = community_results.get("result", {})

        community_id = result.get("id_str", "unknown")
        community_name = result.get("name", "unnamed community")

        # 收集所有要检查的文本字段
        fields_to_check = {
            "名称": result.get("name", ""),
            "描述": result.get("description", ""),
            "问题": result.get("question", "")
        }

        # 添加搜索标签
        tags = result.get("search_tags", [])
        if tags:
            fields_to_check["搜索标签"] = ", ".join(tags)

        # 添加社区规则
        rules = result.get("rules", [])
        for i, rule in enumerate(rules):
            fields_to_check[f"规则{i + 1}名称"] = rule.get("name", "")
            fields_to_check[f"规则{i + 1}描述"] = rule.get("description", "")

        # 检查所有字段是否包含违禁词
        violations = []
        for field_name, field_value in fields_to_check.items():
            found_words = contains_filter_words(field_value, filter_words)
            if found_words:
                violations.append({
                    "field": field_name,
                    "value": field_value,
                    "words": found_words
                })

        # 如果有违规内容
        if violations:
            # 打印违规详情
            print(f" 发现违规社区: [ID: {community_id}, 名称: '{community_name}']")
            for violation in violations:
                print(f"   • 字段 '{violation['field']}': 值 '{violation['value']}'")
                print(f"     触发违禁词: {', '.join(violation['words'])}")
            return None  # 删除该条目

        # 没有违规内容
        return entry

    except Exception as e:
        print(f" 处理社区条目时出错: {e}")
        return entry


def filter_CommunityDiscoveryTimeline(json_str, filter_words):
    """过滤整个CommunityDiscoveryTimeline响应"""
    try:
        data = json.loads(json_str)
        instructions = data.get("data", {}).get("viewer", {}).get("community_discovery_timeline", {}).get("timeline",
                                                                                                          {}).get(
            "instructions", [])

        total_entries = 0
        community_entries = 0
        filtered_count = 0

        print("=" * 50)
        print("开始过滤社区发现时间线数据...")

        # 找到包含社区条目的TimelineAddEntries指令
        for instruction in instructions:
            if instruction.get("type") == "TimelineAddEntries":
                entries = instruction.get("entries", [])
                total_entries = len(entries)
                filtered_entries = []

                print(f"发现 {total_entries} 个条目")

                # 过滤每个社区条目
                for entry in entries:
                    entry_id = entry.get("entryId", "unknown-entry")

                    # 只处理社区类型的条目
                    if entry_id.startswith("community-"):
                        community_entries += 1
                        filtered_entry = filter_community_entry(entry, filter_words)

                        if filtered_entry is None:
                            filtered_count += 1
                        else:
                            filtered_entries.append(filtered_entry)
                    else:
                        # 保留非社区条目
                        filtered_entries.append(entry)

                # 更新条目列表
                instruction["entries"] = filtered_entries

        # 打印过滤结果
        print("\n过滤结果统计:")
        print(f"• 总条目数: {total_entries}")
        print(f"• 社区条目数: {community_entries}")
        print(f"• 过滤社区数: {filtered_count}")

        if filtered_count == 0:
            print("• 状态: 没有发现需要过滤的内容 ")
        else:
            print(f"• 状态: 已过滤 {filtered_count} 个社区 ")

        print("=" * 50)
        return json.dumps(data, ensure_ascii=False)

    except Exception as e:
        print(f" 解析JSON时出错: {e}")
        return json_str


def filter_TopicTimelineQuery(json_str, filter_words):
    # 获取当前时间戳
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 初始化统计变量
    total_communities = 0
    filtered_count = 0
    filtered_details = []

    try:
        # 解析JSON数据
        data = json.loads(json_str)

        # 获取社区列表
        communities = data.get("data", {}).get("fetch_popular_communities", {}).get("items_results", [])
        total_communities = len(communities)

        # 创建过滤后的社区列表
        filtered_communities = []

        # 将过滤词转换为小写以提高匹配效率
        lower_filter_words = [word.lower() for word in filter_words]

        # 打印处理开始信息
        print(f"[{timestamp}] 开始过滤社区数据 | 初始社区数: {total_communities} | 过滤词: {filter_words}")

        # 遍历所有社区条目
        for community in communities:
            # 获取社区结果对象
            result = community.get("result", {})
            community_name = result.get("name", "")
            community_id = result.get("rest_id", "")

            # 检查关键字段是否包含违禁词
            violation_reason = None
            violation_word = None

            # 检查社区名称
            name_lower = community_name.lower()
            for word in lower_filter_words:
                if word in name_lower:
                    violation_reason = "社区名称包含违禁词"
                    violation_word = word
                    break

            # 检查主话题名称
            if not violation_reason:
                topic = result.get("primary_community_topic", {})
                topic_name = topic.get("topic_name", "").lower()
                for word in lower_filter_words:
                    if word in topic_name:
                        violation_reason = "主题名称包含违禁词"
                        violation_word = word
                        break

            # 如果不包含违禁词，则保留该社区
            if not violation_reason:
                filtered_communities.append(community)
            else:
                # 记录过滤详情
                filtered_count += 1
                detail = {
                    "id": community_id,
                    "name": community_name,
                    "reason": violation_reason,
                    "word": violation_word
                }
                filtered_details.append(detail)
                # 打印过滤警告
                print(f"[{timestamp}] !!! 过滤社区: ID={community_id} | 名称='{community_name}' | "
                      f"原因: {violation_reason} '{violation_word}'")

        # 更新过滤后的社区列表
        if "data" in data and "fetch_popular_communities" in data["data"]:
            data["data"]["fetch_popular_communities"]["items_results"] = filtered_communities

        # 生成最终处理结果
        remaining_count = len(filtered_communities)

        if filtered_count > 0:
            # 打印过滤摘要
            print(f"[{timestamp}] === 过滤完成 ===")
            print(f"[{timestamp}] 原始社区数: {total_communities} | 过滤: {filtered_count} | 保留: {remaining_count}")

            # 打印过滤详情
            print(f"[{timestamp}] 过滤详情:")
            for detail in filtered_details:
                print(f"    - ID: {detail['id']} | 名称: '{detail['name']}' | "
                      f"原因: {detail['reason']} | 违禁词: '{detail['word']}'")
        else:
            # 打印无过滤通知
            print(f"[{timestamp}] === 未发现需过滤内容 ===")
            print(f"[{timestamp}] 原始社区数: {total_communities} | 过滤: 0 | 保留: {total_communities}")
            print(f"[{timestamp}] 所有社区均符合要求")

        # 返回过滤后的JSON字符串
        return json.dumps(data, ensure_ascii=False)

    except Exception as e:
        # 打印错误信息
        print(f"[{timestamp}] !!! 过滤JSON时出错: {str(e)}")
        print(f"[{timestamp}] 由于处理出错，返回原始未过滤数据")
        # 出错时返回原始数据
        return json_str


def filter_CommunitiesSearchQuery(json_str, filter_words):
    try:
        # 解析JSON数据
        data = json.loads(json_str)
        original_count = len(data.get("data", {}).get("communities_search_slice", {}).get("items_results", []))

        print(f" 开始过滤社区搜索结果，原始条目数: {original_count}")
        print(f" 使用违禁词列表: {filter_words}")

        # 获取社区列表
        communities = data.get("data", {}).get("communities_search_slice", {}).get("items_results", [])

        # 过滤包含违禁词的社区
        filtered_communities = []
        removed_count = 0
        removed_names = []

        for community in communities:
            result = community.get("result", {})
            community_name = result.get("name", "")
            lower_name = community_name.lower()

            # 检查社区名称是否包含违禁词
            found_bad_words = [word for word in filter_words if word in lower_name]

            if found_bad_words:
                removed_count += 1
                removed_names.append(community_name)
                print(f" 删除社区: '{community_name}' | 包含违禁词: {found_bad_words}")
            else:
                filtered_communities.append(community)

        # 重建过滤后的数据结构
        if "data" in data and "communities_search_slice" in data["data"]:
            data["data"]["communities_search_slice"]["items_results"] = filtered_communities

        # 打印过滤结果摘要
        print(f" 过滤完成: 删除 {removed_count} 个社区，保留 {len(filtered_communities)} 个社区")
        if removed_count > 0:
            print(f"🗑 被删除的社区列表: {removed_names}")
        else:
            print(" 未发现包含违禁词的社区")

        return json.dumps(data, ensure_ascii=False)

    except json.JSONDecodeError:
        print("️ JSON解析失败，返回原始数据")
        return json_str
    except Exception as e:
        print(f" 过滤社区数据时出错: {e}")
        return json_str


def filter_community_tweets(json_str, forbidden_words):
    """
    过滤社区推文时间线中包含违禁词的条目
    """
    # 初始化统计信息
    stats = {
        'total_entries': 0,
        'pinned_entries': 0,
        'removed_entries': 0,
        'removed_contents': []
    }

    def process_entry(entry):
        """处理单个条目，返回是否保留"""
        try:
            # 只处理推文类型的条目
            entry_id = entry.get("entryId", "")
            stats['total_entries'] += 1

            if not entry_id.startswith("tweet-"):
                return True  # 非推文条目保留

            content = entry["content"]
            # 验证条目结构
            if (content.get("entryType") == "TimelineTimelineItem" and
                    content.get("itemContent", {}).get("itemType") == "TimelineTweet"):

                tweet = content["itemContent"]["tweet_results"]["result"]
                tweet_text = tweet["legacy"]["full_text"]

                # 检查是否是置顶条目
                is_pinned = "socialContext" in content.get("itemContent", {})
                if is_pinned:
                    stats['pinned_entries'] += 1


                if contains_forbidden_text(tweet_text, forbidden_words):
                    # 记录被删除的内容
                    truncated_text = tweet_text[:100] + ('...' if len(tweet_text) > 100 else '')
                    author = tweet["core"]["user_results"]["result"]["legacy"]["screen_name"]
                    removed_info = {
                        'entry_id': entry_id,
                        'author': author,
                        'text': truncated_text,
                        'is_pinned': is_pinned
                    }
                    stats['removed_contents'].append(removed_info)
                    stats['removed_entries'] += 1
                    return False
        except KeyError:
            # 结构异常时保留条目
            pass
        return True

    try:
        # 打印开始处理信息
        print(f" 开始过滤社区推文，违禁词列表: {forbidden_words}")

        data = json.loads(json_str)
        timeline = data["data"]["communityResults"]["result"]["ranked_community_timeline"]["timeline"]
        new_instructions = []

        for instruction in timeline["instructions"]:
            # 处理置顶推文
            if instruction["type"] == "TimelinePinEntry":
                if process_entry(instruction["entry"]):
                    new_instructions.append(instruction)

            # 处理常规推文列表
            elif instruction["type"] == "TimelineAddEntries":
                original_count = len(instruction["entries"])
                instruction["entries"] = [
                    entry for entry in instruction["entries"]
                    if process_entry(entry)
                ]
                new_instructions.append(instruction)

            # 保留其他类型指令
            else:
                new_instructions.append(instruction)

        timeline["instructions"] = new_instructions
        result_json = json.dumps(data, ensure_ascii=False)

        # 打印处理结果统计
        print(f"  过滤完成! 共处理 {stats['total_entries']} 个条目")
        print(f"   - 置顶条目: {stats['pinned_entries']}")
        print(f"   - 删除条目: {stats['removed_entries']}")

        # 打印被删除的条目详情
        if stats['removed_entries'] > 0:
            print("\n 被删除的条目:")
            for i, content in enumerate(stats['removed_contents'], 1):
                pinned_tag = " [置顶]" if content['is_pinned'] else ""
                print(f"  {i}. 作者: @{content['author']}{pinned_tag}")
                print(f"     条目ID: {content['entry_id']}")
                print(f"     内容: '{content['text']}'")
                print("-" * 50)
        else:
            print("🎉 未发现包含违禁词的条目")

        return result_json

    except Exception as e:
        print(f" 过滤社区推文时出错: {e}")
        return json_str  # 出错时返回原始数据


def filter_ListsManagementPageTimeline(json_str, filter_words):
    if not filter_words:
        print("无过滤词，跳过列表过滤")
        return json_str

    print(f"开始过滤列表管理页面时间线，过滤词: {filter_words}")
    start_time = time.time()
    original_size = len(json_str)
    removed_count = 0
    kept_count = 0

    try:
        data = json.loads(json_str)
        instructions = data["data"]["viewer"]["list_management_timeline"]["timeline"]["instructions"]

        for instruction in instructions:
            if instruction["type"] == "TimelineAddEntries":
                entries = instruction["entries"]
                new_entries = []

                for entry in entries:
                    entry_id = entry["entryId"]

                    # 处理推荐列表模块
                    if entry_id.startswith("list-to-follow-module-"):
                        print(f"处理推荐列表模块: {entry_id}")
                        items = entry["content"]["items"]
                        original_item_count = len(items)
                        new_items = []

                        for item in items:
                            list_data = item["item"]["itemContent"].get("list")
                            if list_data:
                                list_name = list_data["name"]
                                # 检查是否包含过滤词
                                matched = False
                                for word in filter_words:
                                    if re.search(rf'\b{re.escape(word)}\b', list_name, re.IGNORECASE):
                                        print(f"  × 移除推荐列表: {list_name} (匹配过滤词: {word})")
                                        removed_count += 1
                                        matched = True
                                        break

                                if not matched:
                                    new_items.append(item)
                                    kept_count += 1

                        # 更新模块内容
                        entry["content"]["items"] = new_items
                        final_item_count = len(new_items)

                        if final_item_count > 0:
                            new_entries.append(entry)
                            print(f"  保留推荐列表: {final_item_count}/{original_item_count} 个")
                        else:
                            print(f"  ! 推荐列表模块已空，完全移除")

                    # 处理用户列表模块
                    elif entry_id.startswith("owned-subscribed-list-module-"):
                        print(f"处理用户列表模块: {entry_id}")
                        items = entry["content"]["items"]
                        original_item_count = len(items)
                        new_items = []

                        for item in items:
                            item_content = item["item"]["itemContent"]
                            # 保留空列表提示信息
                            if item_content.get("itemType") == "TimelineMessagePrompt":
                                print("  保留空列表提示信息")
                                new_items.append(item)
                                kept_count += 1
                            # 过滤实际列表项
                            elif item_content.get("list"):
                                list_name = item_content["list"]["name"]
                                matched = False
                                for word in filter_words:
                                    if re.search(rf'\b{re.escape(word)}\b', list_name, re.IGNORECASE):
                                        print(f"  × 移除用户列表: {list_name} (匹配过滤词: {word})")
                                        removed_count += 1
                                        matched = True
                                        break

                                if not matched:
                                    new_items.append(item)
                                    kept_count += 1

                        # 更新模块内容
                        entry["content"]["items"] = new_items
                        new_entries.append(entry)
                        final_item_count = len(new_items)

                        if original_item_count > 0:
                            print(f"  用户列表保留: {final_item_count}/{original_item_count} 个")


                # 更新指令条目
                instruction["entries"] = new_entries
                print(f"时间线条目更新: {len(new_entries)}/{len(entries)} 个条目保留")

        filtered_json = json.dumps(data, ensure_ascii=False)
        filtered_size = len(filtered_json)

        # 结果统计
        duration = time.time() - start_time
        print(f"过滤完成! 耗时: {duration:.4f}秒")
        print(f"原始大小: {original_size} 字节 | 过滤后: {filtered_size} 字节")
        print(f"处理条目: 保留 {kept_count} 个 | 移除 {removed_count} 个")

        if removed_count == 0:
            print("★ 未移除任何列表，所有内容均符合过滤规则")

        return filtered_json

    except Exception as e:
        print(f"!! 过滤过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return json_str



def filter_tweet_detail(response_body, filter_words):
    """过滤推文详情页JSON（unknown_TweetDetail.json）"""
    try:
        data = json.loads(response_body)

        # 检查响应结构是否有效
        if "data" not in data or "threaded_conversation_with_injections_v2" not in data["data"]:
            return response_body, False

        instructions = data["data"]["threaded_conversation_with_injections_v2"]["instructions"]
        deleted_items = []
        main_tweet_id = None

        # 将过滤词转为小写
        filter_words = [word.lower() for word in filter_words]

        # 1. 增强的主推文ID查找逻辑（三层查找）
        for instruction in instructions:
            if instruction["type"] == "TimelineAddEntries":
                for entry in instruction["entries"]:
                    entry_id = entry["entryId"]

                    # 情况1: 直接以tweet-开头的条目
                    if entry_id.startswith("tweet-"):
                        parts = entry_id.split("-")
                        if len(parts) > 1:
                            main_tweet_id = parts[1]
                            break

                    # 情况2: conversationthread-条目中的第一个item
                    elif entry_id.startswith("conversationthread-"):
                        items = entry["content"].get("items", [])
                        if items:
                            first_item_id = items[0].get("entryId", "")
                            if "-tweet-" in first_item_id:
                                main_tweet_id = first_item_id.split("-tweet-")[-1]
                                break
                if main_tweet_id:
                    break

        # 情况3: 如果仍未找到，尝试深度搜索推文数据
        if not main_tweet_id:
            for instruction in instructions:
                if instruction["type"] == "TimelineAddEntries":
                    for entry in instruction["entries"]:
                        tweet_data = extract_tweet_data(entry)
                        if tweet_data and tweet_data.get("rest_id"):
                            main_tweet_id = tweet_data["rest_id"]
                            break
                    if main_tweet_id:
                        break

        # 如果没有找到主推文ID，返回原始响应
        if not main_tweet_id:
            print("Warning: Main tweet ID not found")
            return response_body, False

        # 2. 优先检查主推文是否存在违禁词
        main_tweet_deleted = False
        for instruction in instructions:
            if instruction["type"] == "TimelineAddEntries":
                for entry in instruction["entries"]:
                    tweet_data = extract_tweet_data(entry)
                    if tweet_data and tweet_data.get("rest_id") == main_tweet_id:
                        # 提取推文内容
                        tweet_text = get_tweet_text(tweet_data).lower()
                        user_info = get_user_info(tweet_data).lower()

                        # 打印调试信息
                        print(f"Checking main tweet: ID={main_tweet_id}")
                        print(f"  Tweet text: {tweet_text[:100]}...")
                        print(f"  User info: {user_info[:100]}...")

                        # 检查是否包含过滤词
                        for word in filter_words:
                            if word in tweet_text or word in user_info:
                                print(f"  Banned word found: '{word}'")
                                main_tweet_deleted = True
                                break

                        if main_tweet_deleted:
                            deleted_items.append({
                                "type": "Main Tweet",
                                "id": entry["entryId"],
                                "text": tweet_text[:50] + "...",
                                "user": get_user_screen_name(tweet_data)
                            })
                            break
                if main_tweet_deleted:
                    break

        # 3. 如果主推文包含违禁词，返回"推文不存在"的响应
        if main_tweet_deleted:
            print(f"Main tweet contains banned words, returning 'Tweet unavailable' response")
            # 返回"推文不可用"响应并强制禁用缓存
            return create_tweet_unavailable_response(main_tweet_id), True

        # 4. 主推文安全，继续过滤其他区域
        print("Main tweet is safe, filtering replies and recommendations...")
        for instruction in instructions:
            if instruction["type"] == "TimelineAddEntries":
                entries = instruction["entries"]
                new_entries = []

                for entry in entries:
                    entry_id = entry["entryId"]
                    tweet_data = extract_tweet_data(entry)

                    # 保留主推文（已检查过安全）
                    if tweet_data and tweet_data.get("rest_id") == main_tweet_id:
                        new_entries.append(entry)
                        continue

                    # 过滤回复区域（评论）
                    if entry_id.startswith("conversationthread-"):
                        items = entry["content"].get("items", [])
                        new_items = []

                        for item in items:
                            item_content = item.get("item", {}).get("itemContent", {})
                            tweet_data = item_content.get("tweet_results", {}).get("result", {})

                            # 跳过主推文（已处理）
                            if tweet_data and tweet_data.get("rest_id") == main_tweet_id:
                                new_items.append(item)
                                continue

                            if should_delete_tweet(tweet_data, filter_words):
                                deleted_items.append({
                                    "type": "Reply",
                                    "id": item.get("entryId", ""),
                                    "text": get_tweet_text(tweet_data)[:50] + "...",
                                    "user": get_user_screen_name(tweet_data)
                                })
                            else:
                                new_items.append(item)

                        # 如果对话中所有回复都被删除，但包含主推文则保留
                        if not new_items:
                            # 检查是否包含主推文
                            has_main_tweet = any(
                                item.get("item", {}).get("itemContent", {}).get("tweet_results", {}).get("result",
                                                                                                         {}).get(
                                    "rest_id") == main_tweet_id
                                for item in items
                            )
                            if has_main_tweet:
                                new_items = [item for item in items if
                                             item.get("item", {}).get("itemContent", {}).get("tweet_results", {}).get(
                                                 "result", {}).get("rest_id") == main_tweet_id]

                        # 更新条目中的items
                        if new_items:
                            entry["content"]["items"] = new_items
                            new_entries.append(entry)

                    # 过滤Relevant People区域
                    elif entry_id.startswith("user-recommendations-"):
                        items = entry["content"].get("items", [])
                        new_items = []

                        for item in items:
                            user_data = item.get("item", {}).get("itemContent", {}).get("user_results", {}).get(
                                "result", {})
                            user_info = get_user_info(user_data).lower()

                            if any(word in user_info for word in filter_words):
                                deleted_items.append({
                                    "type": "Relevant People",
                                    "id": item.get("entryId", ""),
                                    "user": get_user_screen_name(user_data),
                                    "description": user_info[:50] + "..."
                                })
                            else:
                                new_items.append(item)

                        # 如果所有推荐用户都被删除，跳过整个条目
                        if new_items:
                            entry["content"]["items"] = new_items
                            new_entries.append(entry)
                    else:
                        # 保留其他类型的条目
                        new_entries.append(entry)

                # 更新指令中的条目
                instruction["entries"] = new_entries

        # 打印删除的项目信息
        if deleted_items:
            print(f"Filtered {len(deleted_items)} items from tweet_detail:")
            for item in deleted_items:
                if item["type"] == "Main Tweet":
                    print(f"  - MAIN TWEET by @{item['user']}: {item['text']}")
                elif item["type"] == "Reply":
                    print(f"  - REPLY by @{item['user']}: {item['text']}")
                elif item["type"] == "Relevant People":
                    print(f"  - USER RECOMMENDATION: @{item['user']} - {item['description']}")

        return json.dumps(data), False

    except Exception as e:
        print(f"Error filtering tweet_detail: {str(e)}")
        import traceback
        traceback.print_exc()
        return response_body, False


def extract_tweet_data(entry):
    """从不同条目结构中提取推文数据"""
    content = entry.get("content", {})

    # 类型1: 直接包含itemContent的条目
    if "itemContent" in content:
        return content["itemContent"].get("tweet_results", {}).get("result", {})

    # 类型2: conversationthread条目中的items
    if "items" in content:
        for item in content["items"]:
            item_content = item.get("item", {}).get("itemContent", {})
            if item_content:
                tweet_data = item_content.get("tweet_results", {}).get("result", {})
                if tweet_data:
                    return tweet_data

    # 类型3: TimelineTimelineItem结构
    if content.get("__typename") == "TimelineTimelineItem" and "itemContent" in content:
        return content["itemContent"].get("tweet_results", {}).get("result", {})

    return None


def create_tweet_unavailable_response(tweet_id):
    """创建'推文不可用'的标准响应"""
    return json.dumps({
        "data": {
            "threaded_conversation_with_injections_v2": {
                "instructions": [
                    {
                        "type": "TimelineAddEntries",
                        "entries": [
                            {
                                "entryId": f"tweet-{tweet_id}",
                                "content": {
                                    "entryType": "TimelineTimelineItem",
                                    "itemContent": {
                                        "itemType": "TimelineTombstone",
                                        "__typename": "TimelineTombstone",
                                        "tombstoneInfo": {
                                            "richText": {
                                                "text": "This Tweet is unavailable.",
                                                "entities": []
                                            }
                                        }
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        }
    })


def get_tweet_text(tweet_data):
    """从推文数据中提取文本"""
    if not tweet_data:
        return ""

    # 尝试从legacy字段获取
    if "legacy" in tweet_data:
        return tweet_data["legacy"].get("full_text", "")

    # 尝试从note_tweet字段获取
    if "note_tweet" in tweet_data:
        return tweet_data["note_tweet"].get("text", "")

    # 尝试从核心字段获取
    return tweet_data.get("text", "")


def get_user_info(user_data):
    """从用户数据中提取信息（用户名+描述）"""
    if not user_data:
        return ""

    screen_name = ""
    description = ""

    # 从不同位置提取用户名
    if "core" in user_data and "screen_name" in user_data["core"]:
        screen_name = user_data["core"]["screen_name"]
    elif "legacy" in user_data and "screen_name" in user_data["legacy"]:
        screen_name = user_data["legacy"]["screen_name"]
    elif "screen_name" in user_data:
        screen_name = user_data["screen_name"]

    # 提取用户描述
    if "legacy" in user_data and "description" in user_data["legacy"]:
        description = user_data["legacy"]["description"]
    elif "description" in user_data:
        description = user_data["description"]

    return f"{screen_name} {description}"


def get_user_screen_name(tweet_data):
    """获取推文发布者的用户名"""
    if not tweet_data:
        return "unknown"

    # 从核心用户数据获取
    if "core" in tweet_data and "user_results" in tweet_data["core"]:
        user_data = tweet_data["core"]["user_results"].get("result", {})
        if "core" in user_data and "screen_name" in user_data["core"]:
            return user_data["core"]["screen_name"]
        elif "legacy" in user_data and "screen_name" in user_data["legacy"]:
            return user_data["legacy"]["screen_name"]
        elif "screen_name" in user_data:
            return user_data["screen_name"]

    # 尝试直接从推文数据获取
    return tweet_data.get("screen_name", "unknown")


def should_delete_tweet(tweet_data, filter_words):
    """检查推文是否应被删除"""
    if not tweet_data:
        return False

    # 获取推文文本
    tweet_text = get_tweet_text(tweet_data).lower()

    # 获取用户信息
    user_info = get_user_info(tweet_data).lower()

    # 检查是否包含过滤词
    return any(word in tweet_text or word in user_info for word in filter_words)
