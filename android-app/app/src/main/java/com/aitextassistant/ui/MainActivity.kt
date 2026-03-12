package com.aitextassistant.ui

import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.view.Menu
import android.view.MenuItem
import android.view.View
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import com.aitextassistant.R
import com.aitextassistant.data.PreferencesManager
import com.aitextassistant.databinding.ActivityMainBinding
import com.aitextassistant.service.TextAccessibilityService
import com.google.android.material.card.MaterialCardView
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

/**
 * 主Activity
 * 应用的主界面
 */
class MainActivity : AppCompatActivity() {
    
    companion object {
        private const val REQUEST_ACCESSIBILITY = 1001
        private const val REQUEST_OVERLAY_PERMISSION = 1002
    }
    
    private lateinit var binding: ActivityMainBinding
    private lateinit var prefsManager: PreferencesManager
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        prefsManager = PreferencesManager.getInstance(this)
        
        setupUI()
        checkPermissions()
    }
    
    override fun onResume() {
        super.onResume()
        updateServiceStatus()
    }
    
    override fun onCreateOptionsMenu(menu: Menu): Boolean {
        menuInflater.inflate(R.menu.menu_main, menu)
        return true
    }
    
    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        return when (item.itemId) {
            R.id.action_settings -> {
                openSettings()
                true
            }
            R.id.action_about -> {
                showAboutDialog()
                true
            }
            else -> super.onOptionsItemSelected(item)
        }
    }
    
    /**
     * 设置UI
     */
    private fun setupUI() {
        // 启用服务按钮
        binding.btnEnableService.setOnClickListener {
            openAccessibilitySettings()
        }
        
        // 打开设置按钮
        binding.btnOpenSettings.setOnClickListener {
            openSettings()
        }
        
        // 使用说明卡片点击
        binding.cardHowToUse.setOnClickListener {
            showHowToUseDialog()
        }
        
        // 检查权限按钮
        binding.btnCheckPermissions.setOnClickListener {
            checkPermissions()
        }
        
        // 快捷操作按钮
        binding.btnTestComplete.setOnClickListener {
            testFeature("补全")
        }
        
        binding.btnTestQA.setOnClickListener {
            testFeature("问答")
        }
    }
    
    /**
     * 更新服务状态显示
     */
    private fun updateServiceStatus() {
        val isServiceRunning = TextAccessibilityService.isRunning
        
        if (isServiceRunning) {
            binding.tvServiceStatus.text = getString(R.string.service_enabled)
            binding.tvServiceStatus.setTextColor(ContextCompat.getColor(this, R.color.success))
            binding.indicatorServiceStatus.setBackgroundColor(ContextCompat.getColor(this, R.color.success))
            binding.btnEnableService.text = "无障碍服务已启用"
            binding.btnEnableService.isEnabled = false
        } else {
            binding.tvServiceStatus.text = getString(R.string.service_disabled)
            binding.tvServiceStatus.setTextColor(ContextCompat.getColor(this, R.color.error))
            binding.indicatorServiceStatus.setBackgroundColor(ContextCompat.getColor(this, R.color.error))
            binding.btnEnableService.text = getString(R.string.enable_service)
            binding.btnEnableService.isEnabled = true
        }
    }
    
    /**
     * 检查权限
     */
    private fun checkPermissions() {
        val permissionsNeeded = mutableListOf<String>()
        
        // 检查无障碍服务
        if (!TextAccessibilityService.isRunning) {
            permissionsNeeded.add("无障碍服务")
        }
        
        // 检查悬浮窗权限
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            if (!Settings.canDrawOverlays(this)) {
                permissionsNeeded.add("悬浮窗权限")
            }
        }
        
        if (permissionsNeeded.isNotEmpty()) {
            showPermissionDialog(permissionsNeeded)
        }
        
        updateServiceStatus()
    }
    
    /**
     * 显示权限对话框
     */
    private fun showPermissionDialog(permissions: List<String>) {
        val message = buildString {
            append("应用需要以下权限才能正常工作：\n\n")
            permissions.forEach { append("• $it\n") }
            append("\n请在系统设置中开启这些权限。")
        }
        
        MaterialAlertDialogBuilder(this)
            .setTitle("需要权限")
            .setMessage(message)
            .setPositiveButton("去设置") { _, _ ->
                openAccessibilitySettings()
            }
            .setNegativeButton("稍后", null)
            .show()
    }
    
    /**
     * 打开无障碍设置
     */
    private fun openAccessibilitySettings() {
        val intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK
        }
        startActivityForResult(intent, REQUEST_ACCESSIBILITY)
        
        Toast.makeText(this, "请找到\"AI文本助手\"并开启服务", Toast.LENGTH_LONG).show()
    }
    
    /**
     * 打开设置
     */
    private fun openSettings() {
        val intent = Intent(this, SettingsActivity::class.java)
        startActivity(intent)
    }
    
    /**
     * 显示使用说明对话框
     */
    private fun showHowToUseDialog() {
        MaterialAlertDialogBuilder(this)
            .setTitle(R.string.usage_title)
            .setMessage(buildString {
                append("1. 启用无障碍服务\n")
                append("   点击\"启用无障碍服务\"按钮，在系统设置中开启AI文本助手\n\n")
                append("2. 配置API设置\n")
                append("   在设置中配置您的API Key和模型参数\n\n")
                append("3. 使用功能\n")
                append("   在任何应用中选中文本，点击浮动按钮选择补全或问答\n\n")
                append("提示：\n")
                append("• 选中文本后会自动显示浮动按钮\n")
                append("• 点击浮动按钮可选择补全或问答功能\n")
                append("• 支持拖拽浮动按钮调整位置")
            })
            .setPositiveButton("知道了", null)
            .show()
    }
    
    /**
     * 显示关于对话框
     */
    private fun showAboutDialog() {
        val versionName = packageManager.getPackageInfo(packageName, 0).versionName
        
        MaterialAlertDialogBuilder(this)
            .setTitle(R.string.app_name)
            .setMessage(buildString {
                append("版本: $versionName\n\n")
                append("AI文本助手是一款智能文本补全与问答工具，\n")
                append("通过无障碍服务检测您的操作，\n")
                append("提供便捷的AI辅助功能。\n\n")
                append("© 2024 AI Text Assistant")
            })
            .setPositiveButton("确定", null)
            .show()
    }
    
    /**
     * 测试功能
     */
    private fun testFeature(feature: String) {
        if (!TextAccessibilityService.isRunning) {
            Toast.makeText(this, "请先启用无障碍服务", Toast.LENGTH_SHORT).show()
            return
        }
        
        if (!prefsManager.isConfigValid()) {
            Toast.makeText(this, "请先配置API设置", Toast.LENGTH_SHORT).show()
            openSettings()
            return
        }
        
        Toast.makeText(this, "请在其他应用中选中文本测试$feature 功能", Toast.LENGTH_LONG).show()
    }
    
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        
        when (requestCode) {
            REQUEST_ACCESSIBILITY -> {
                // 延迟检查，因为服务启动需要时间
                lifecycleScope.launch {
                    delay(1000)
                    updateServiceStatus()
                }
            }
            REQUEST_OVERLAY_PERMISSION -> {
                checkPermissions()
            }
        }
    }
}
