# Changelog

## [1.0.0] - 2025-05-08

### 新增
- 🎉 首次发布
- 双模式主动接话：**回复模式**（Bot 发言后监听群友回复）和 **主动模式**（Bot 没发言时随机抽取消息参与讨论）
- LLM 智能分析：判断群友消息是否在回复 Bot，以及 Bot 是否应主动参与群聊话题
- 支持分离 Provider：分析用便宜的模型，生成用高质量模型
- 群白名单机制：支持按群自定义回复概率和主动概率
- 冷却机制：防止 Bot 过于频繁发言
- 自定义提示词：分析、生成、主动参与的 LLM 提示词均可自定义
- Token 用量统计面板：WebUI 实时查看各群 Token 消耗趋势
- 多平台支持：aiocqhttp / telegram / discord / lark / qq_official / dingtalk / kook / slack / mattermost / satori
