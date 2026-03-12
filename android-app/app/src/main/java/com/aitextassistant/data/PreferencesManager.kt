package com.aitextassistant.data

import android.content.Context
import android.content.SharedPreferences
import androidx.core.content.edit
import com.aitextassistant.model.RequestConfig

/**
 * 偏好设置管理器
 * 管理应用的所有配置项
 */
class PreferencesManager private constructor(context: Context) {
    
    private val prefs: SharedPreferences = context.getSharedPreferences(
        PREFS_NAME, 
        Context.MODE_PRIVATE
    )
    
    companion object {
        private const val PREFS_NAME = "ai_text_assistant_prefs"
        
        // API设置键
        private const val KEY_API_KEY = "api_key"
        private const val KEY_BASE_URL = "base_url"
        private const val KEY_MODEL = "model"
        private const val KEY_PROXY_URL = "proxy_url"
        
        // 参数设置键
        private const val KEY_TEMPERATURE = "temperature"
        private const val KEY_MAX_TOKENS = "max_tokens"
        private const val KEY_COMPLETE_NUMBER = "complete_number"
        
        // 提示词设置键
        private const val KEY_COMPLETE_PROMPT = "complete_prompt"
        private const val KEY_QA_PROMPT = "qa_prompt"
        
        // 功能设置键
        private const val KEY_SHOW_FLOATING_BUTTON = "show_floating_button"
        private const val KEY_AUTO_COPY_RESULT = "auto_copy_result"
        private const val KEY_VIBRATE_ON_TRIGGER = "vibrate_on_trigger"
        
        // 默认值
        private const val DEFAULT_BASE_URL = "https://api.openai.com/v1/chat/completions"
        private const val DEFAULT_MODEL = "gpt-3.5-turbo"
        private const val DEFAULT_TEMPERATURE = 0.9
        private const val DEFAULT_MAX_TOKENS = 2000
        private const val DEFAULT_COMPLETE_NUMBER = 150
        
        @Volatile
        private var instance: PreferencesManager? = null
        
        fun getInstance(context: Context): PreferencesManager {
            return instance ?: synchronized(this) {
                instance ?: PreferencesManager(context.applicationContext).also {
                    instance = it
                }
            }
        }
    }
    
    // ==================== API设置 ====================
    
    fun setApiKey(apiKey: String) {
        prefs.edit { putString(KEY_API_KEY, apiKey) }
    }
    
    fun getApiKey(): String {
        return prefs.getString(KEY_API_KEY, "") ?: ""
    }
    
    fun setBaseUrl(baseUrl: String) {
        prefs.edit { putString(KEY_BASE_URL, baseUrl) }
    }
    
    fun getBaseUrl(): String {
        return prefs.getString(KEY_BASE_URL, DEFAULT_BASE_URL) ?: DEFAULT_BASE_URL
    }
    
    fun setModel(model: String) {
        prefs.edit { putString(KEY_MODEL, model) }
    }
    
    fun getModel(): String {
        return prefs.getString(KEY_MODEL, DEFAULT_MODEL) ?: DEFAULT_MODEL
    }
    
    fun setProxyUrl(proxyUrl: String) {
        prefs.edit { putString(KEY_PROXY_URL, proxyUrl) }
    }
    
    fun getProxyUrl(): String {
        return prefs.getString(KEY_PROXY_URL, "") ?: ""
    }
    
    // ==================== 参数设置 ====================
    
    fun setTemperature(temperature: Float) {
        prefs.edit { putFloat(KEY_TEMPERATURE, temperature) }
    }
    
    fun getTemperature(): Float {
        return prefs.getFloat(KEY_TEMPERATURE, DEFAULT_TEMPERATURE.toFloat())
    }
    
    fun setMaxTokens(maxTokens: Int) {
        prefs.edit { putInt(KEY_MAX_TOKENS, maxTokens) }
    }
    
    fun getMaxTokens(): Int {
        return prefs.getInt(KEY_MAX_TOKENS, DEFAULT_MAX_TOKENS)
    }
    
    fun setCompleteNumber(completeNumber: Int) {
        prefs.edit { putInt(KEY_COMPLETE_NUMBER, completeNumber) }
    }
    
    fun getCompleteNumber(): Int {
        return prefs.getInt(KEY_COMPLETE_NUMBER, DEFAULT_COMPLETE_NUMBER)
    }
    
    // ==================== 提示词设置 ====================
    
    fun setCompletePrompt(prompt: String) {
        prefs.edit { putString(KEY_COMPLETE_PROMPT, prompt) }
    }
    
    fun getCompletePrompt(): String {
        return prefs.getString(KEY_COMPLETE_PROMPT, RequestConfig.DEFAULT_COMPLETE_PROMPT) 
            ?: RequestConfig.DEFAULT_COMPLETE_PROMPT
    }
    
    fun setQaPrompt(prompt: String) {
        prefs.edit { putString(KEY_QA_PROMPT, prompt) }
    }
    
    fun getQaPrompt(): String {
        return prefs.getString(KEY_QA_PROMPT, RequestConfig.DEFAULT_QA_PROMPT) 
            ?: RequestConfig.DEFAULT_QA_PROMPT
    }
    
    // ==================== 功能设置 ====================
    
    fun setShowFloatingButton(show: Boolean) {
        prefs.edit { putBoolean(KEY_SHOW_FLOATING_BUTTON, show) }
    }
    
    fun getShowFloatingButton(): Boolean {
        return prefs.getBoolean(KEY_SHOW_FLOATING_BUTTON, true)
    }
    
    fun setAutoCopyResult(autoCopy: Boolean) {
        prefs.edit { putBoolean(KEY_AUTO_COPY_RESULT, autoCopy) }
    }
    
    fun getAutoCopyResult(): Boolean {
        return prefs.getBoolean(KEY_AUTO_COPY_RESULT, false)
    }
    
    fun setVibrateOnTrigger(vibrate: Boolean) {
        prefs.edit { putBoolean(KEY_VIBRATE_ON_TRIGGER, vibrate) }
    }
    
    fun getVibrateOnTrigger(): Boolean {
        return prefs.getBoolean(KEY_VIBRATE_ON_TRIGGER, true)
    }
    
    // ==================== 配置对象 ====================
    
    /**
     * 获取完整的请求配置
     */
    fun getRequestConfig(): RequestConfig {
        return RequestConfig(
            apiKey = getApiKey(),
            baseUrl = getBaseUrl(),
            model = getModel(),
            temperature = getTemperature().toDouble(),
            maxTokens = getMaxTokens(),
            proxyUrl = getProxyUrl().takeIf { it.isNotBlank() },
            completePrompt = getCompletePrompt(),
            qaPrompt = getQaPrompt(),
            completeNumber = getCompleteNumber()
        )
    }
    
    /**
     * 检查配置是否有效
     */
    fun isConfigValid(): Boolean {
        return getApiKey().isNotBlank() && getBaseUrl().isNotBlank()
    }
    
    /**
     * 清除所有设置
     */
    fun clearAll() {
        prefs.edit { clear() }
    }
}
