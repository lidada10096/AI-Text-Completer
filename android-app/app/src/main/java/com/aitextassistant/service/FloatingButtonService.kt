package com.aitextassistant.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.graphics.PixelFormat
import android.os.Build
import android.os.IBinder
import android.util.Log
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.view.animation.AnimationUtils
import android.widget.ImageButton
import android.widget.LinearLayout
import android.widget.PopupWindow
import android.widget.TextView
import androidx.core.app.NotificationCompat
import com.aitextassistant.R
import com.aitextassistant.model.OperationMode
import com.aitextassistant.ui.MainActivity

/**
 * 浮动按钮服务
 * 在其他应用上方显示浮动操作按钮
 */
class FloatingButtonService : Service() {
    
    companion object {
        private const val TAG = "FloatingButtonService"
        private const val NOTIFICATION_ID = 1001
        private const val CHANNEL_ID = "floating_button_channel"
        
        // 广播Action
        const val ACTION_SHOW_BUTTON = "com.aitextassistant.ACTION_SHOW_BUTTON"
        const val ACTION_HIDE_BUTTON = "com.aitextassistant.ACTION_HIDE_BUTTON"
        const val ACTION_STOP_SERVICE = "com.aitextassistant.ACTION_STOP_SERVICE"
        
        // Extra键
        const val EXTRA_SELECTED_TEXT = "selected_text"
    }
    
    private lateinit var windowManager: WindowManager
    private var floatingView: View? = null
    private var popupWindow: PopupWindow? = null
    private var currentSelectedText: String = ""
    
    // 窗口参数
    private var params: WindowManager.LayoutParams? = null
    
    // 广播接收器
    private lateinit var broadcastReceiver: BroadcastReceiver
    
    override fun onCreate() {
        super.onCreate()
        Log.d(TAG, "浮动按钮服务创建")
        
        windowManager = getSystemService(Context.WINDOW_SERVICE) as WindowManager
        
        // 注册广播接收器
        registerBroadcastReceiver()
        
        // 创建通知渠道并启动前台服务
        createNotificationChannel()
        startForeground(NOTIFICATION_ID, createNotification())
    }
    
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        Log.d(TAG, "浮动按钮服务启动")
        return START_STICKY
    }
    
    override fun onBind(intent: Intent?): IBinder? = null
    
    override fun onDestroy() {
        super.onDestroy()
        Log.d(TAG, "浮动按钮服务销毁")
        
        // 移除浮动视图
        removeFloatingView()
        
        // 注销广播接收器
        try {
            unregisterReceiver(broadcastReceiver)
        } catch (e: Exception) {
            Log.e(TAG, "注销广播接收器失败", e)
        }
    }
    
    /**
     * 注册广播接收器
     */
    private fun registerBroadcastReceiver() {
        broadcastReceiver = object : BroadcastReceiver() {
            override fun onReceive(context: Context, intent: Intent) {
                when (intent.action) {
                    ACTION_SHOW_BUTTON -> {
                        val text = intent.getStringExtra(EXTRA_SELECTED_TEXT) ?: ""
                        if (text.isNotBlank()) {
                            currentSelectedText = text
                            showFloatingButton()
                        }
                    }
                    ACTION_HIDE_BUTTON -> {
                        hideFloatingButton()
                    }
                    ACTION_STOP_SERVICE -> {
                        stopSelf()
                    }
                }
            }
        }
        
        val filter = IntentFilter().apply {
            addAction(ACTION_SHOW_BUTTON)
            addAction(ACTION_HIDE_BUTTON)
            addAction(ACTION_STOP_SERVICE)
        }
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            registerReceiver(broadcastReceiver, filter, Context.RECEIVER_NOT_EXPORTED)
        } else {
            registerReceiver(broadcastReceiver, filter)
        }
    }
    
    /**
     * 创建通知渠道
     */
    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                getString(R.string.notification_channel_name),
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = getString(R.string.notification_channel_desc)
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
            .setContentTitle(getString(R.string.notification_title))
            .setContentText(getString(R.string.notification_content))
            .setSmallIcon(R.drawable.ic_notification)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()
    }
    
    /**
     * 显示浮动按钮
     */
    private fun showFloatingButton() {
        // 如果已经显示，先移除
        removeFloatingView()
        
        // 创建浮动视图
        val inflater = LayoutInflater.from(this)
        floatingView = inflater.inflate(R.layout.layout_floating_button, null)
        
        // 设置窗口参数
        val layoutParams = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
            } else {
                @Suppress("DEPRECATION")
                WindowManager.LayoutParams.TYPE_PHONE
            },
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                    WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.END
            x = 32
            y = 200
        }
        
        params = layoutParams
        
        // 添加视图
        try {
            windowManager.addView(floatingView, layoutParams)
            
            // 设置点击事件
            setupFloatingButtonClick()
            
            // 设置拖拽功能
            setupDragFunctionality()
            
            // 添加动画
            floatingView?.startAnimation(
                AnimationUtils.loadAnimation(this, R.anim.fade_in_scale)
            )
            
        } catch (e: Exception) {
            Log.e(TAG, "显示浮动按钮失败", e)
        }
    }
    
    /**
     * 隐藏浮动按钮
     */
    private fun hideFloatingButton() {
        // 关闭弹出菜单
        popupWindow?.dismiss()
        popupWindow = null
        
        // 移除浮动视图
        removeFloatingView()
    }
    
    /**
     * 移除浮动视图
     */
    private fun removeFloatingView() {
        floatingView?.let {
            try {
                windowManager.removeView(it)
            } catch (e: Exception) {
                Log.e(TAG, "移除浮动视图失败", e)
            }
            floatingView = null
        }
    }
    
    /**
     * 设置浮动按钮点击事件
     */
    private fun setupFloatingButtonClick() {
        floatingView?.findViewById<ImageButton>(R.id.floatingButton)?.setOnClickListener {
            showOptionsPopup()
        }
    }
    
    /**
     * 显示选项弹出菜单
     */
    private fun showOptionsPopup() {
        // 如果已经显示，关闭它
        if (popupWindow?.isShowing == true) {
            popupWindow?.dismiss()
            return
        }
        
        // 创建弹出视图
        val inflater = LayoutInflater.from(this)
        val popupView = inflater.inflate(R.layout.layout_popup_menu, null)
        
        // 创建PopupWindow
        popupWindow = PopupWindow(
            popupView,
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            true
        ).apply {
            setBackgroundDrawable(null)
            isOutsideTouchable = true
            isFocusable = true
        }
        
        // 设置按钮点击事件
        popupView.findViewById<LinearLayout>(R.id.btnComplete)?.setOnClickListener {
            performAIOperation(OperationMode.COMPLETION)
            popupWindow?.dismiss()
        }
        
        popupView.findViewById<LinearLayout>(R.id.btnQA)?.setOnClickListener {
            performAIOperation(OperationMode.QUESTION_ANSWERING)
            popupWindow?.dismiss()
        }
        
        popupView.findViewById<LinearLayout>(R.id.btnCancel)?.setOnClickListener {
            popupWindow?.dismiss()
            hideFloatingButton()
        }
        
        // 显示弹出菜单
        floatingView?.let { anchor ->
            popupWindow?.showAsDropDown(anchor, 0, -anchor.height - 20)
        }
    }
    
    /**
     * 设置拖拽功能
     */
    private fun setupDragFunctionality() {
        var initialX = 0
        var initialY = 0
        var touchX = 0f
        var touchY = 0f
        
        floatingView?.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    initialX = params?.x ?: 0
                    initialY = params?.y ?: 0
                    touchX = event.rawX
                    touchY = event.rawY
                    false
                }
                MotionEvent.ACTION_MOVE -> {
                    params?.x = initialX + (touchX - event.rawX).toInt()
                    params?.y = initialY + (event.rawY - touchY).toInt()
                    
                    // 更新视图位置
                    if (floatingView != null) {
                        windowManager.updateViewLayout(floatingView, params)
                    }
                    true
                }
                else -> false
            }
        }
    }
    
    /**
     * 执行AI操作
     */
    private fun performAIOperation(mode: OperationMode) {
        // 隐藏浮动按钮
        hideFloatingButton()
        
        // 调用无障碍服务执行操作
        TextAccessibilityService.instance?.performAIOperation(currentSelectedText, mode)
    }
}
