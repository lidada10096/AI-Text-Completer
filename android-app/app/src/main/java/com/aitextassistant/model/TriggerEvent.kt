package com.aitextassistant.model

import android.view.accessibility.AccessibilityEvent

/**
 * 触发事件类型
 * 定义用户操作的触发方式
 */
sealed class TriggerEvent {
    
    /**
     * 获取事件类型描述
     */
    abstract fun getTypeDescription(): String
    
    /**
     * 获取触发时间戳
     */
    abstract fun getTimestamp(): Long
    
    /**
     * 文本选择事件
     * 当用户在其他应用中选中文本时触发
     */
    data class TextSelectionEvent(
        val selectedText: String,
        val packageName: String,
        val className: String,
        val timestamp: Long = System.currentTimeMillis()
    ) : TriggerEvent() {
        override fun getTypeDescription(): String = "文本选择"
        override fun getTimestamp(): Long = timestamp
        
        /**
         * 检查文本是否有效
         */
        fun isValid(): Boolean {
            return selectedText.isNotBlank() && selectedText.length >= 2
        }
    }
    
    /**
     * 复制操作事件
     * 当用户执行复制操作时触发
     */
    data class CopyEvent(
        val copiedText: String,
        val packageName: String,
        val timestamp: Long = System.currentTimeMillis()
    ) : TriggerEvent() {
        override fun getTypeDescription(): String = "复制操作"
        override fun getTimestamp(): Long = timestamp
        
        /**
         * 检查文本是否有效
         */
        fun isValid(): Boolean {
            return copiedText.isNotBlank() && copiedText.length >= 2
        }
    }
    
    /**
     * 长按事件
     * 当用户长按文本时触发
     */
    data class LongPressEvent(
        val targetText: String,
        val packageName: String,
        val timestamp: Long = System.currentTimeMillis()
    ) : TriggerEvent() {
        override fun getTypeDescription(): String = "长按操作"
        override fun getTimestamp(): Long = timestamp
    }
    
    /**
     * 辅助功能按钮事件
     * 当用户点击辅助功能软键盘按钮时触发
     */
    data class AccessibilityButtonEvent(
        val currentText: String?,
        val timestamp: Long = System.currentTimeMillis()
    ) : TriggerEvent() {
        override fun getTypeDescription(): String = "辅助按钮"
        override fun getTimestamp(): Long = timestamp
    }
    
    companion object {
        /**
         * 从AccessibilityEvent创建触发事件
         */
        fun fromAccessibilityEvent(
            event: AccessibilityEvent,
            extractedText: String? = null
        ): TriggerEvent? {
            return when (event.eventType) {
                AccessibilityEvent.TYPE_VIEW_TEXT_SELECTION_CHANGED -> {
                    val text = extractedText ?: event.text?.joinToString("") ?: ""
                    if (text.isNotBlank()) {
                        TextSelectionEvent(
                            selectedText = text,
                            packageName = event.packageName?.toString() ?: "",
                            className = event.className?.toString() ?: ""
                        )
                    } else null
                }
                else -> null
            }
        }
        
        /**
         * 事件去重时间窗口（毫秒）
         * 同一位置的事件在此时间窗口内只处理一次
         */
        const val DEBOUNCE_WINDOW_MS = 500L
        
        /**
         * 最大文本长度限制
         */
        const val MAX_TEXT_LENGTH = 5000
    }
}

/**
 * 触发事件处理器接口
 */
interface TriggerEventHandler {
    /**
     * 处理触发事件
     * @param event 触发事件
     * @param mode 操作模式
     * @return 是否成功处理
     */
    suspend fun handleTriggerEvent(event: TriggerEvent, mode: OperationMode): Boolean
    
    /**
     * 检查是否可以处理该事件
     */
    fun canHandle(event: TriggerEvent): Boolean
}
