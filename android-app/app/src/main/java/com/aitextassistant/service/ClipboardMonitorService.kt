package com.aitextassistant.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import com.aitextassistant.R
import com.aitextassistant.ui.MainActivity

/**
 * 剪贴板监听服务
 * 后台监听剪贴板变化
 */
class ClipboardMonitorService : Service() {
    
    companion object {
        private const val TAG = "ClipboardMonitorService"
        private const val NOTIFICATION_ID = 1002
        private const val CHANNEL_ID = "clipboard_monitor_channel"
    }
    
    private lateinit var clipboardManager: ClipboardManager
    private var lastClipboardText: String = ""
    
    private val clipboardListener = ClipboardManager.OnPrimaryClipChangedListener {
        val clipData = clipboardManager.primaryClip
        if (clipData != null && clipData.itemCount > 0) {
            val item = clipData.getItemAt(0)
            val text = item.text?.toString() ?: ""
            
            if (text.isNotBlank() && text != lastClipboardText) {
                lastClipboardText = text
                Log.d(TAG, "剪贴板变化: $text")
                // 可以在这里添加额外的处理逻辑
            }
        }
    }
    
    override fun onCreate() {
        super.onCreate()
        Log.d(TAG, "剪贴板监听服务创建")
        
        clipboardManager = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        
        // 创建通知渠道
        createNotificationChannel()
        
        // 启动前台服务
        startForeground(NOTIFICATION_ID, createNotification())
        
        // 注册剪贴板监听器
        clipboardManager.addPrimaryClipChangedListener(clipboardListener)
    }
    
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        Log.d(TAG, "剪贴板监听服务启动")
        return START_STICKY
    }
    
    override fun onBind(intent: Intent?): IBinder? = null
    
    override fun onDestroy() {
        super.onDestroy()
        Log.d(TAG, "剪贴板监听服务销毁")
        
        // 注销剪贴板监听器
        clipboardManager.removePrimaryClipChangedListener(clipboardListener)
    }
    
    /**
     * 创建通知渠道
     */
    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "剪贴板监听服务",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "监听剪贴板变化"
                setShowBadge(false)
            }
            
            val notificationManager = getSystemService(NotificationManager::class.java)
            notificationManager.createNotificationChannel(channel)
        }
    }
    
    /**
     * 创建通知
     */
    private fun createNotification(): Notification {
        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP
        }
        
        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            intent,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )
        
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("剪贴板监听服务")
            .setContentText("正在监听剪贴板变化")
            .setSmallIcon(R.drawable.ic_notification)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()
    }
}
