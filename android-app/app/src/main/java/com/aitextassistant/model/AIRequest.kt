package com.aitextassistant.model

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonObject

/**
 * AI请求数据类
 */
@Serializable
data class AIRequest(
    val model: String,
    val messages: List<Message>,
    val temperature: Double = 0.9,
    val max_tokens: Int = 2000,
    val stream: Boolean = true,
    val presence_penalty: Double = 0.0,
    val frequency_penalty: Double = 0.0
)

/**
 * 消息数据类
 */
@Serializable
data class Message(
    val role: String,
    val content: String
)

/**
 * AI响应数据类
 */
@Serializable
data class AIResponse(
    val id: String? = null,
    val object_type: String? = null,
    val created: Long? = null,
    val model: String? = null,
    val choices: List<Choice>? = null,
    val usage: Usage? = null,
    val error: ErrorDetail? = null
)

/**
 * 流式响应数据类
 */
@Serializable
data class StreamResponse(
    val id: String? = null,
    val `object`: String? = null,
    val created: Long? = null,
    val model: String? = null,
    val choices: List<StreamChoice>? = null
)

/**
 * 选项数据类
 */
@Serializable
data class Choice(
    val index: Int? = null,
    val message: Message? = null,
    val finish_reason: String? = null
)

/**
 * 流式选项数据类
 */
@Serializable
data class StreamChoice(
    val index: Int? = null,
    val delta: Delta? = null,
    val finish_reason: String? = null
)

/**
 * Delta数据类（用于流式响应）
 */
@Serializable
data class Delta(
    val role: String? = null,
    val content: String? = null
)

/**
 * 使用量数据类
 */
@Serializable
data class Usage(
    val prompt_tokens: Int? = null,
    val completion_tokens: Int? = null,
    val total_tokens: Int? = null
)

/**
 * 错误详情数据类
 */
@Serializable
data class ErrorDetail(
    val message: String? = null,
    val type: String? = null,
    val param: String? = null,
    val code: String? = null
)

/**
 * 模型信息数据类
 */
@Serializable
data class ModelInfo(
    val id: String,
    val `object`: String? = null,
    val created: Long? = null,
    val owned_by: String? = null
)

/**
 * 模型列表响应
 */
@Serializable
data class ModelsResponse(
    val `object`: String? = null,
    val data: List<ModelInfo>? = null,
    val error: ErrorDetail? = null
)

/**
 * 请求配置数据类
 */
data class RequestConfig(
    val apiKey: String,
    val baseUrl: String,
    val model: String,
    val temperature: Double = 0.9,
    val maxTokens: Int = 2000,
    val proxyUrl: String? = null,
    val completePrompt: String = DEFAULT_COMPLETE_PROMPT,
    val qaPrompt: String = DEFAULT_QA_PROMPT,
    val completeNumber: Int = 150
) {
    companion object {
        const val DEFAULT_COMPLETE_PROMPT = """你是一个AI文本补全助手，请根据用户输入的上下文进行智能补全。

要求：
1. 保持与原文一致的语气和风格
2. 补全内容要自然流畅
3. 根据语境自动添加合适的标点符号
4. 不要重复原文内容
5. 直接输出补全内容，不要添加解释"""

        const val DEFAULT_QA_PROMPT = """你是一个AI问答助手，请针对用户的问题给出详细、准确的回答。

回答要求：
1. 直接回答问题，不要添加无关内容
2. 条理清晰，层次分明
3. 如果问题不清晰，可以要求用户补充信息
4. 提供准确、有用的信息"""
    }
}

/**
 * 请求结果密封类
 */
sealed class RequestResult {
    data class Success(val text: String, val usage: Usage? = null) : RequestResult()
    data class Error(val message: String, val code: String? = null) : RequestResult()
    data class Streaming(val chunk: String) : RequestResult()
}
