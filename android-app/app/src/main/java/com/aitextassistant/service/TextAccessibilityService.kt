package com.aitextassistant.service

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import com.aitextassistant.data.PreferencesManager
import com.aitextassistant.model.OperationMode
import com.aitextassistant.model.TriggerEvent
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import java.util.concurrent.ConcurrentHashMap

/**
 * 文本无障碍服务
 * 核心服务，用于检测用户操作并触发AI功能
 */
class TextAccessibilityService : AccessibilityService() {
    
    companion object {
        private const val TAG = "TextAccessibilityService"
        
        // 服务状态
        @Volatile
        var isRunning = false
            private set
        
        // 最后处理的事件时间戳（用于去重）
        private val lastProcessedEvents = ConcurrentHashMap<String, Long>()
        
        // 事件去重时间窗口
        private const val DEBOUNCE_MS = 500L
        
        // 剪贴板监听时间窗口
        private const val CLIPBOARD_DEBOUNCE_MS = 1000L
        
        // 获取服务实例
        @Volatile
        var instance: TextAccessibilityService? = null
    }
    
    private lateinit var prefsManager: PreferencesManager
    private lateinit var clipboardManager: ClipboardManager
    private var lastClipboardText: String = ""
    private var lastClipboardTime: Long = 0
    
    // 协程作用域
    private val serviceScope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
    
    // 浮动按钮服务
    private var floatingButtonService: FloatingButtonService? = null
    
    // 当前选中的文本
    private var currentSelectedText: String = ""
    private var lastSelectedText: String = ""
    private var lastSelectionTime: Long = 0
    
    // 处理程序
    private val handler = Handler(Looper.getMainLooper())
    
    override fun onCreate() {
        super.onCreate()
        Log.d(TAG, "服务创建")
        
        prefsManager = PreferencesManager.getInstance(this)
        clipboardManager = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        instance = this
        
        // 启动剪贴板监听
        startClipboardMonitoring()
    }
    
    override fun onServiceConnected() {
        super.onServiceConnected()
        Log.d(TAG, "服务已连接")
        
        isRunning = true
        
        // 配置服务信息
        serviceInfo = serviceInfo.apply {
            // 监听所有事件类型
            eventTypes = AccessibilityEvent.TYPE_VIEW_CLICKED or
                    AccessibilityEvent.TYPE_VIEW_LONG_CLICKED or
                    AccessibilityEvent.TYPE_VIEW_SELECTED or
                    AccessibilityEvent.TYPE_VIEW_FOCUSED or
                    AccessibilityEvent.TYPE_VIEW_TEXT_CHANGED or
                    AccessibilityEvent.TYPE_VIEW_TEXT_SELECTION_CHANGED or
                    AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED or
                    AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED or
                    AccessibilityEvent.TYPE_VIEW_SCROLLED
            
            // 反馈类型
            feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC
            
            // 通知超时
            notificationTimeout = 100
            
            // 标志
            flags = AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS or
                    AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS or
                    AccessibilityServiceInfo.FLAG_INCLUDE_NOT_IMPORTANT_VIEWS
            
            // 可以检索窗口内容
            canRetrieveWindowContent = true
        }
        
        // 启动浮动按钮服务
        startFloatingButtonService()
    }
    
    override fun onAccessibilityEvent(event: AccessibilityEvent) {
        when (event.eventType) {
            AccessibilityEvent.TYPE_VIEW_TEXT_SELECTION_CHANGED -> {
                handleTextSelectionEvent(event)
            }
            AccessibilityEvent.TYPE_VIEW_CLICKED -> {
                handleClickEvent(event)
            }
            AccessibilityEvent.TYPE_VIEW_LONG_CLICKED -> {
                handleLongClickEvent(event)
            }
            AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED -> {
                handleWindowContentChanged(event)
            }
        }
    }
    
    override fun onInterrupt() {
        Log.d(TAG, "服务中断")
    }
    
    override fun onUnbind(intent: Intent?): Boolean {
        Log.d(TAG, "服务解绑")
        isRunning = false
        instance = null
        stopFloatingButtonService()
        return super.onUnbind(intent)
    }
    
    override fun onDestroy() {
        super.onDestroy()
        Log.d(TAG, "服务销毁")
        isRunning = false
        instance = null
        serviceScope.cancel()
        stopClipboardMonitoring()
        stopFloatingButtonService()
    }
    
    // ==================== 事件处理 ====================
    
    /**
     * 处理文本选择事件
     */
    private fun handleTextSelectionEvent(event: AccessibilityEvent) {
        val source = event.source ?: return
        
        try {
            // 获取选中的文本
            val selectedText = extractSelectedText(source)
            
            if (selectedText.isNotBlank() && selectedText != lastSelectedText) {
                // 检查是否需要去重
                if (shouldProcessEvent("selection", selectedText)) {
                    lastSelectedText = selectedText
                    currentSelectedText = selectedText
                    lastSelectionTime = System.currentTimeMillis()
                    
                    Log.d(TAG, "检测到文本选择: $selectedText")
                    
                    // 触发振动反馈
                    if (prefsManager.getVibrateOnTrigger()) {
                        vibrate()
                    }
                    
                    // 显示浮动按钮
                    showFloatingButton(selectedText)
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "处理文本选择事件失败", e)
        } finally {
            source.recycle()
        }
    }
    
    /**
     * 处理点击事件
     */
    private fun handleClickEvent(event: AccessibilityEvent) {
        // 点击其他地方时隐藏浮动按钮
        handler.postDelayed({
            hideFloatingButton()
        }, 200)
    }
    
    /**
     * 处理长按事件
     */
    private fun handleLongClickEvent(event: AccessibilityEvent) {
        val source = event.source ?: return
        
        try {
            val text = source.text?.toString() ?: ""
            if (text.isNotBlank()) {
                Log.d(TAG, "检测到长按: $text")
                // 可以在这里添加长按特定的处理逻辑
            }
        } finally {
            source.recycle()
        }
    }
    
    /**
     * 处理窗口内容变化
     */
    private fun handleWindowContentChanged(event: AccessibilityEvent) {
        // 窗口内容变化时可能需要更新状态
    }
    
    // ==================== 剪贴板监听 ====================
    
    /**
     * 启动剪贴板监听
     */
    private fun startClipboardMonitoring() {
        clipboardManager.addPrimaryClipChangedListener(clipboardListener)
    }
    
    /**
     * 停止剪贴板监听
     */
    private fun stopClipboardMonitoring() {
        clipboardManager.removePrimaryClipChangedListener(clipboardListener)
    }
    
    /**
     * 剪贴板监听器
     */
    private val clipboardListener = ClipboardManager.OnPrimaryClipChangedListener {
        val currentTime = System.currentTimeMillis()
        
        // 检查去重时间窗口
        if (currentTime - lastClipboardTime < CLIPBOARD_DEBOUNCE_MS) {
            return@OnPrimaryClipChangedListener
        }
        
        val clipData = clipboardManager.primaryClip
        if (clipData != null && clipData.itemCount > 0) {
            val item = clipData.getItemAt(0)
            val text = item.text?.toString() ?: ""
            
            if (text.isNotBlank() && text != lastClipboardText && text != lastSelectedText) {
                lastClipboardText = text
                lastClipboardTime = currentTime
                
                Log.d(TAG, "检测到复制操作: $text")
                
                // 创建复制事件
                val copyEvent = TriggerEvent.CopyEvent(
                    copiedText = text,
                    packageName = getCurrentPackageName()
                )
                
                // 触发振动反馈
                if (prefsManager.getVibrateOnTrigger()) {
                    vibrate()
                }
                
                // 显示浮动按钮
                showFloatingButton(text)
            }
        }
    }
    
    // ==================== 浮动按钮 ====================
    
    /**
     * 启动浮动按钮服务
     */
    private fun startFloatingButtonService() {
        if (!prefsManager.getShowFloatingButton()) return
        
        val intent = Intent(this, FloatingButtonService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(intent)
        } else {
            startService(intent)
        }
    }
    
    /**
     * 停止浮动按钮服务
     */
    private fun stopFloatingButtonService() {
        val intent = Intent(this, FloatingButtonService::class.java)
        stopService(intent)
    }
    
    /**
     * 显示浮动按钮
     */
    private fun showFloatingButton(text: String) {
        if (!prefsManager.getShowFloatingButton()) return
        
        // 发送广播通知浮动按钮服务
        val intent = Intent(FloatingButtonService.ACTION_SHOW_BUTTON).apply {
            setPackage(packageName)
            putExtra(FloatingButtonService.EXTRA_SELECTED_TEXT, text)
        }
        sendBroadcast(intent)
    }
    
    /**
     * 隐藏浮动按钮
     */
    private fun hideFloatingButton() {
        val intent = Intent(FloatingButtonService.ACTION_HIDE_BUTTON).apply {
            setPackage(packageName)
        }
        sendBroadcast(intent)
    }
    
    // ==================== 工具方法 ====================
    
    /**
     * 提取选中的文本
     */
    private fun extractSelectedText(node: AccessibilityNodeInfo): String {
        // 尝试获取选中的文本
        val text = node.text?.toString() ?: ""
        
        // 如果文本不为空，检查是否有选择范围
        if (text.isNotEmpty()) {
            // 获取文本选择范围
            val selectionStart = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                node.textSelectionStart
            } else {
                -1
            }
            
            val selectionEnd = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                node.textSelectionEnd
            } else {
                -1
            }
            
            // 如果有有效的选择范围，提取选中的文本
            if (selectionStart >= 0 && selectionEnd > selectionStart && selectionEnd <= text.length) {
                return text.substring(selectionStart, selectionEnd)
            }
        }
        
        return text
    }
    
    /**
     * 检查是否应该处理该事件（去重）
     */
    private fun shouldProcessEvent(eventType: String, content: String): Boolean {
        val key = "$eventType:$content"
        val currentTime = System.currentTimeMillis()
        val lastTime = lastProcessedEvents[key] ?: 0
        
        return if (currentTime - lastTime > DEBOUNCE_MS) {
            lastProcessedEvents[key] = currentTime
            // 清理旧记录
            cleanupOldEvents()
            true
        } else {
            false
        }
    }
    
    /**
     * 清理旧的事件记录
     */
    private fun cleanupOldEvents() {
        val currentTime = System.currentTimeMillis()
        lastProcessedEvents.entries.removeIf { entry ->
            currentTime - entry.value > DEBOUNCE_MS * 2
        }
    }
    
    /**
     * 触发振动
     */
    private fun vibrate() {
        try {
            val vibrator = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                val vibratorManager = getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as VibratorManager
                vibratorManager.defaultVibrator
            } else {
                @Suppress("DEPRECATION")
                getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
            }
            
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                vibrator.vibrate(VibrationEffect.createOneShot(50, VibrationEffect.DEFAULT_AMPLITUDE))
            } else {
                @Suppress("DEPRECATION")
                vibrator.vibrate(50)
            }
        } catch (e: Exception) {
            Log.e(TAG, "振动失败", e)
        }
    }
    
    /**
     * 获取当前包名
     */
    private fun getCurrentPackageName(): String {
        return rootInActiveWindow?.packageName?.toString() ?: ""
    }
    
    /**
     * 执行AI操作
     */
    fun performAIOperation(text: String, mode: OperationMode) {
        serviceScope.launch {
            val intent = Intent(this@TextAccessibilityService, ResultDialogActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
                putExtra(ResultDialogActivity.EXTRA_TEXT, text)
                putExtra(ResultDialogActivity.EXTRA_MODE, mode.name)
            }
            startActivity(intent)
        }
    }
}
