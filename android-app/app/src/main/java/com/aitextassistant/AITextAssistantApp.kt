package com.aitextassistant

import android.app.Application
import android.util.Log

/**
 * 应用类
 * 应用级别的初始化
 */
class AITextAssistantApp : Application() {
    
    companion object {
        private const val TAG = "AITextAssistantApp"
    }
    
    override fun onCreate() {
        super.onCreate()
        Log.d(TAG, "应用启动")
        
        // 初始化应用级别的配置
        initializeApp()
    }
    
    /**
     * 初始化应用
     */
    private fun initializeApp() {
        // 可以在这里进行全局初始化
        // 例如：崩溃报告、日志配置、第三方SDK初始化等
    }
}
