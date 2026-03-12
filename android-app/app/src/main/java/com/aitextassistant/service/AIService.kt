package com.aitextassistant.service

import android.util.Log
import com.aitextassistant.model.AIRequest
import com.aitextassistant.model.AIResponse
import com.aitextassistant.model.Message
import com.aitextassistant.model.ModelsResponse
import com.aitextassistant.model.RequestConfig
import com.aitextassistant.model.RequestResult
import com.aitextassistant.model.StreamResponse
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOn
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.encodeToJsonElement
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.sse.EventSource
import okhttp3.sse.EventSourceListener
import okhttp3.sse.EventSources
import java.io.IOException
import java.net.InetSocketAddress
import java.net.Proxy
import java.util.concurrent.TimeUnit

/**
 * AI服务
 * 负责与AI API进行通信
 */
class AIService private constructor() {
    
    companion object {
        private const val TAG = "AIService"
        private const val CONNECT_TIMEOUT = 30L
        private const val READ_TIMEOUT = 60L
        private const val WRITE_TIMEOUT = 30L
        
        @Volatile
        private var instance: AIService? = null
        
        fun getInstance(): AIService {
            return instance ?: synchronized(this) {
                instance ?: AIService().also {
                    instance = it
                }
            }
        }
    }
    
    private val json = Json {
        ignoreUnknownKeys = true
        isLenient = true
    }
    
    private var httpClient: OkHttpClient? = null
    
    /**
     * 创建HTTP客户端
     */
    private fun createHttpClient(config: RequestConfig): OkHttpClient {
        val builder = OkHttpClient.Builder()
            .connectTimeout(CONNECT_TIMEOUT, TimeUnit.SECONDS)
            .readTimeout(READ_TIMEOUT, TimeUnit.SECONDS)
            .writeTimeout(WRITE_TIMEOUT, TimeUnit.SECONDS)
        
        // 配置代理
        config.proxyUrl?.let { proxyUrl ->
            if (proxyUrl.isNotBlank()) {
                try {
                    val url = java.net.URL(proxyUrl)
                    val proxy = Proxy(
                        Proxy.Type.HTTP,
                        InetSocketAddress(url.host, url.port)
                    )
                    builder.proxy(proxy)
                } catch (e: Exception) {
                    Log.e(TAG, "代理配置错误", e)
                }
            }
        }
        
        return builder.build()
    }
    
    /**
     * 获取HTTP客户端
     */
    private fun getHttpClient(config: RequestConfig): OkHttpClient {
        return httpClient ?: createHttpClient(config).also {
            httpClient = it
        }
    }
    
    /**
     * 执行文本补全
     */
    suspend fun completeText(
        text: String,
        config: RequestConfig
    ): Flow<RequestResult> = flow {
        val systemPrompt = config.completePrompt
        val userPrompt = buildString {
            append("请根据以下上下文进行智能补全，补全字数控制在${config.completeNumber}字以内：\n\n")
            append(text)
        }
        
        emitAll(callAIAPI(systemPrompt, userPrompt, config))
    }.flowOn(Dispatchers.IO)
    
    /**
     * 执行问答
     */
    suspend fun answerQuestion(
        question: String,
        config: RequestConfig
    ): Flow<RequestResult> = flow {
        val systemPrompt = config.qaPrompt
        val userPrompt = "问题：$question"
        
        emitAll(callAIAPI(systemPrompt, userPrompt, config))
    }.flowOn(Dispatchers.IO)
    
    /**
     * 调用AI API
     */
    private suspend fun callAIAPI(
        systemPrompt: String,
        userPrompt: String,
        config: RequestConfig
    ): Flow<RequestResult> = flow {
        val client = getHttpClient(config)
        
        val request = AIRequest(
            model = config.model,
            messages = listOf(
                Message(role = "system", content = systemPrompt),
                Message(role = "user", content = userPrompt)
            ),
            temperature = config.temperature,
            max_tokens = config.maxTokens,
            stream = true
        )
        
        val requestBody = json.encodeToJsonElement(request).toString()
            .toRequestBody("application/json".toMediaType())
        
        val httpRequest = Request.Builder()
            .url(config.baseUrl)
            .post(requestBody)
            .header("Authorization", "Bearer ${config.apiKey}")
            .header("Content-Type", "application/json")
            .build()
        
        try {
            client.newCall(httpRequest).execute().use { response ->
                if (!response.isSuccessful) {
                    val errorBody = response.body?.string()
                    Log.e(TAG, "API请求失败: $errorBody")
                    
                    val errorMsg = try {
                        val errorResponse = json.decodeFromString<AIResponse>(errorBody ?: "")
                        errorResponse.error?.message ?: "请求失败: ${response.code}"
                    } catch (e: Exception) {
                        "请求失败: ${response.code}"
                    }
                    
                    emit(RequestResult.Error(errorMsg, response.code.toString()))
                    return@flow
                }
                
                // 处理流式响应
                response.body?.source()?.use { source ->
                    while (!source.exhausted()) {
                        val line = source.readUtf8Line() ?: continue
                        
                        if (line.startsWith("data: ")) {
                            val data = line.substring(6)
                            
                            if (data == "[DONE]") {
                                break
                            }
                            
                            try {
                                val streamResponse = json.decodeFromString<StreamResponse>(data)
                                val content = streamResponse.choices?.firstOrNull()?.delta?.content
                                
                                if (!content.isNullOrBlank()) {
                                    emit(RequestResult.Streaming(content))
                                }
                            } catch (e: Exception) {
                                Log.e(TAG, "解析流式响应失败", e)
                            }
                        }
                    }
                }
                
                emit(RequestResult.Success(""))
            }
        } catch (e: IOException) {
            Log.e(TAG, "网络请求失败", e)
            emit(RequestResult.Error("网络连接失败: ${e.message}"))
        } catch (e: Exception) {
            Log.e(TAG, "API调用失败", e)
            emit(RequestResult.Error("请求失败: ${e.message}"))
        }
    }
    
    /**
     * 获取可用模型列表
     */
    suspend fun getModels(config: RequestConfig): Result<List<String>> {
        return try {
            val client = getHttpClient(config)
            
            // 从baseUrl提取基础URL
            val baseUrl = config.baseUrl.substringBefore("/v1") + "/v1"
            
            val request = Request.Builder()
                .url("$baseUrl/models")
                .header("Authorization", "Bearer ${config.apiKey}")
                .build()
            
            client.newCall(request).execute().use { response ->
                if (!response.isSuccessful) {
                    return Result.failure(IOException("获取模型列表失败: ${response.code}"))
                }
                
                val body = response.body?.string()
                val modelsResponse = json.decodeFromString<ModelsResponse>(body ?: "")
                
                if (modelsResponse.error != null) {
                    return Result.failure(IOException(modelsResponse.error.message ?: "未知错误"))
                }
                
                val models = modelsResponse.data
                    ?.map { it.id }
                    ?.filter { it.contains("gpt") || it.contains("claude") || it.contains("llama") }
                    ?: emptyList()
                
                Result.success(models)
            }
        } catch (e: Exception) {
            Log.e(TAG, "获取模型列表失败", e)
            Result.failure(e)
        }
    }
    
    /**
     * 非流式调用API（用于简单请求）
     */
    suspend fun callAPINonStream(
        systemPrompt: String,
        userPrompt: String,
        config: RequestConfig
    ): RequestResult {
        val client = getHttpClient(config)
        
        val request = AIRequest(
            model = config.model,
            messages = listOf(
                Message(role = "system", content = systemPrompt),
                Message(role = "user", content = userPrompt)
            ),
            temperature = config.temperature,
            max_tokens = config.maxTokens,
            stream = false
        )
        
        val requestBody = json.encodeToJsonElement(request).toString()
            .toRequestBody("application/json".toMediaType())
        
        val httpRequest = Request.Builder()
            .url(config.baseUrl)
            .post(requestBody)
            .header("Authorization", "Bearer ${config.apiKey}")
            .header("Content-Type", "application/json")
            .build()
        
        return try {
            client.newCall(httpRequest).execute().use { response ->
                if (!response.isSuccessful) {
                    val errorBody = response.body?.string()
                    val errorMsg = try {
                        val errorResponse = json.decodeFromString<AIResponse>(errorBody ?: "")
                        errorResponse.error?.message ?: "请求失败: ${response.code}"
                    } catch (e: Exception) {
                        "请求失败: ${response.code}"
                    }
                    return RequestResult.Error(errorMsg, response.code.toString())
                }
                
                val body = response.body?.string()
                val aiResponse = json.decodeFromString<AIResponse>(body ?: "")
                
                val content = aiResponse.choices?.firstOrNull()?.message?.content ?: ""
                RequestResult.Success(content, aiResponse.usage)
            }
        } catch (e: IOException) {
            RequestResult.Error("网络连接失败: ${e.message}")
        } catch (e: Exception) {
            RequestResult.Error("请求失败: ${e.message}")
        }
    }
    
    /**
     * 清除HTTP客户端（用于配置变更后）
     */
    fun clearHttpClient() {
        httpClient = null
    }
}
