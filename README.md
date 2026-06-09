# AstrBot 主动接话插件

[![AstrBot](https://img.shields.io/badge/AstrBot-Plugin-blue)](https://github.com/AstrBotDevs/AstrBot)
[![License](https://img.shields.io/badge/License-AGPLv3-green)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.2.1-blueviolet)](CHANGELOG.md)

## 简介

一个智能的 AstrBot 群聊主动接话插件。Bot 发出消息后，自动监听后续群友的回复，使用 LLM 分析是否在跟 Bot 说话，如果是，则使用 LLM 生成自然回复并主动发言。

插件自带 **Token 用量统计面板**，可在 AstrBot WebUI 中查看各群的 LLM Token 消耗趋势。

## 功能特点

### 三模式工作

| 模式 | 说明 |
|------|------|
| **回复模式** | Bot 发言后，跟踪窗口内群友消息，由 LLM 分析是否回复 Bot |
| **主动模式** | Bot 没发言时，监控群聊话题，由 LLM 判断是否主动参与讨论 |
| **关键词模式** | 检测群消息中预定义的关键词，命中后 LLM 自动生成回复 |

### 核心特性

- ✅ **LLM 智能分析** — 判断群友消息是否在回复 Bot，以及 Bot 是否应主动参与话题
- ✅ **分离 Provider 支持** — 分析用便宜的模型（如本地部署/DeepSeek），生成用高质量模型（如 GPT-5.5）
- ✅ **冷却机制** — 防止 Bot 过于频繁发言（支持回复冷却和主动冷却独立配置）
- ✅ **自定义提示词** — 分析、生成、主动参与的 LLM 提示词均可自由定制
- ✅ **专属人设提示词** — 为不同人格设置专属的回复分析人设
- ✅ **Token 用量统计** — 内置 WebUI 面板，按群/按天展示 Token 消耗趋势及多群对比
- ✅ **关键词监听回复** — 检测群消息中预定义的关键词，命中后 LLM 自动生成回复参与对话
- ✅ **LLM 介入判断** — 关键词触发后可先由 LLM 判断上下文是否适合插话
- ✅ **图片转述缓存** — SQLite 哈希缓存图片转述结果，避免重复请求 API，节省 Token 额度
- ✅ **延迟转述** — 平时发图 0 API 消耗，仅在 Bot 回复构建上下文时对未转述图片强制转述
- ✅ **伪人模式** — Bot 根据人格自主决定状态（如睡觉/忙碌/空闲），活跃度控制回复快慢，支持睡觉被 @ 唤醒
- ✅ **延迟批次分析** — 自适应群聊节奏，等停顿后批量分析，避免抢话
- ✅ **`/bot在干嘛`** — 群内随时查询 Bot 当前状态
- ✅ **`/bot计划表`** — 群内查询 Bot 完整日程安排
- ✅ **多平台兼容** — 支持 aiocqhttp / telegram / discord / lark / qq_official / dingtalk / kook / slack / mattermost / satori

## 配置说明

### 基础设置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `trigger_mode` | string | `llm_response` | 触发模式：`llm_response`（仅 LLM 回复后监听）/ `any_message`（任何消息后监听） |

### LLM Provider

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `analyzer_provider_id` | string | 空 | 分析用 LLM Provider（建议便宜的模型如本地部署/DeepSeek） |
| `generator_provider_id` | string | 空 | 生成用 LLM Provider（建议高质量模型如 GPT-5.5） |

### 回复模式 (Route 1)

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `track_timeout_seconds` | int | `120` | 跟踪窗口(秒)，群聊沉默超时即停止，10~600 |
| `max_detection_count` | int | `10` | 最多分析条数后停止本轮，1~50 |
| `enable_llm_tools` | bool | `true` | 是否启用 LLM 工具/技能 |
| `analyzer_system_prompt` | text | 默认 | 回复分析 LLM 提示词 |
| `persona_replies` | template_list | `[]` | 专属回复分析人设提示词列表 |

### 主动模式 (Route 2)

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `max_proactive_rounds` | int | `3` | 最大连续主动回复轮数，0~10 |
| `proactive_cooldown_seconds` | int | `300` | 主动发言冷却(秒)，30~3600 |
| `proactive_analyzer_system_prompt` | text | 默认 | 主动分析 LLM 提示词 |

### 关键词模式 (Route 3)

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `enable_keyword_trigger` | bool | `false` | 启用关键词监听 |
| `enable_keyword_llm_judgment` | bool | `false` | 关键词命中后是否由 LLM 判断是否参与 |
| `keyword_rules` | template_list | `[]` | 关键词规则列表，支持多关键词（逗号分隔）和按群设置 |
| `keyword_default_probability` | int | `100` | 关键词默认触发概率(%)，0~100 |
| `enable_keyword_on_image` | bool | `false` | 关键词是否匹配图片内容 |

### 图片转述

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `enable_image_caption` | bool | `false` | 启用图片转述（非多模态模型建议开启） |
| `image_caption_probability` | int | `100` | 平时图片转述概率(%)，0~100 |
| `image_caption_provider_id` | string | 空 | 图片转述 LLM Provider |

### 批次分析

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `batch_analysis_enabled` | bool | `true` | 启用延迟批次分析 |
| `silence_multiplier` | float | `2.5` | 静默判定倍数，1.5~5.0 |
| `min_silence_seconds` | int | `3` | 最小静默秒数，2~10 |
| `max_silence_seconds` | int | `12` | 最大静默秒数，5~30 |
| `max_batch_wait_seconds` | int | `15` | 绝对超时秒数，5~60 |
| `max_batch_messages` | int | `6` | 最大消息数，2~20 |
| `instant_at_bot` | bool | `true` | @Bot 时立即触发分析 |
| `caption_timeout_seconds` | int | `10` | 图片转述等待超时(秒) |
| `caption_timeout_behavior` | string | `wait_then_fallback` | 图片转述超时策略：等待降级 / 直接传URL / 占位符 |

### 伪人模式

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `human_like_mode` | bool | `false` | 启用伪人模式 |
| `wake_at_threshold` | int | `3` | 唤醒所需@次数 |
| `wake_window_minutes` | int | `30` | @唤醒有效窗口(分钟) |
| `activity_max_delay` | int | `10` | 活跃度最大延迟(秒)。活跃度 1.0 时约 1 秒回复，活跃度越低回复越慢 |

## 安装

### 方法一：插件市场安装

1. 打开 AstrBot WebUI 管理面板
2. 进入「插件市场」
3. 搜索 `astrbot_plugin_chat_echo`
4. 点击安装

### 方法二：手动安装

```bash
cd AstrBot/data/plugins
git clone https://github.com/AMYdd00/astrbot_plugin_chat_echo.git
```

## 使用

1. 在 AstrBot 管理面板中启用插件
2. 根据需要调整其他配置项（建议至少配置 `analyzer_provider_id` 和 `generator_provider_id`）
3. 在群聊中正常与 Bot 对话即可

### Token 统计面板

启用插件后，在 AstrBot WebUI 中可通过以下路径访问 Token 用量统计：
- `插件页面 → Token 用量统计`
- 支持按日/周/月/年/全部维度的数据查看
- 展示各群的 Token 消耗排行和趋势图

## 工作原理

```
Bot 发言 → 开始跟踪窗口 → 群友回复 → LLM 分析是否回复 Bot
                                         ↓
                                    是 → LLM 生成自然回复 → Bot 主动发言
                                         ↓
                                    否 → 继续跟踪 / 超时停止

同时：群聊消息 → LLM 分析话题是否参与 → 是 → 生成发言
```

## 技术细节

- **路由互斥**：回复模式（Route 1）和主动模式（Route 2）使用 per-group 独立锁，避免同时触发冲突且群间不互相影响
- **Token 统计**：每次 LLM 调用自动记录 Prompt/Completion Token 用量，按群按天聚合，自动清理超过 365 天的旧数据
- **群名缓存**：群名自动捕获并持久化，Token 统计面板可直接显示群名
- **伪人调度**：通过 LLM 自主生成日间活动计划表，状态由活跃度（0.0-1.0）控制回复快慢而非是否发言，睡觉状态（0.0）可被群友 @ 唤醒

## 开源协议

本项目基于 [GNU Affero General Public License v3.0](LICENSE) 开源。

## 更新日志

详见 [CHANGELOG.md](CHANGELOG.md)

## 作者

- [AMYdd00](https://github.com/AMYdd00)
- [Yao-lin101](https://github.com/Yao-lin101)

> 本插件代码完全由 AI 生成。

## 相关链接

- [AstrBot](https://github.com/AstrBotDevs/AstrBot) - 一个易于上手的多平台 LLM 对话机器人框架
- [QQ 群](https://qm.qq.com/q/cOrzqdkW7m) - 欢迎提交 Issue 和加群反馈

<div align="center">
  <img src="https://count.getloli.com/@astrbot_plugin_chat_echo?name=astrbot_plugin_chat_echo&theme=green&padding=7&offset=0&align=top&scale=1&pixelated=1&darkmode=auto&prefix=0" alt="访问统计"/>
</div>