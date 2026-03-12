package com.aitextassistant.model

/**
 * 操作模式枚举
 * 定义两种功能模式：补全模式和问答模式
 */
enum class OperationMode {
    /**
     * 补全模式：根据上下文智能补全文本
     */
    COMPLETION,
    
    /**
     * 问答模式：针对选中文本进行问答
     */
    QUESTION_ANSWERING;
    
    companion object {
        /**
         * 根据字符串获取对应的操作模式
         */
        fun fromString(value: String): OperationMode {
            return when (value.uppercase()) {
                "COMPLETION", "COMPLETE", "补全" -> COMPLETION
                "QUESTION_ANSWERING", "QA", "问答" -> QUESTION_ANSWERING
                else -> COMPLETION
            }
        }
    }
    
    /**
     * 获取模式的显示名称
     */
    fun getDisplayName(): String {
        return when (this) {
            COMPLETION -> "文本补全"
            QUESTION_ANSWERING -> "智能问答"
        }
    }
    
    /**
     * 获取模式的描述
     */
    fun getDescription(): String {
        return when (this) {
            COMPLETION -> "根据上下文智能补全文本内容"
            QUESTION_ANSWERING -> "针对选中文本进行智能问答"
        }
    }
}
