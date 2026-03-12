package com.aitextassistant.ui

import android.os.Bundle
import android.view.MenuItem
import android.view.View
import android.widget.ArrayAdapter
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.aitextassistant.R
import com.aitextassistant.data.PreferencesManager
import com.aitextassistant.databinding.ActivitySettingsBinding
import com.aitextassistant.service.AIService
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.google.android.material.slider.Slider
import com.google.android.material.snackbar.Snackbar
import kotlinx.coroutines.launch

/**
 * 设置Activity
 * 应用设置界面
 */
class SettingsActivity : AppCompatActivity() {
    
    private lateinit var binding: ActivitySettingsBinding
    private lateinit var prefsManager: PreferencesManager
    private lateinit var aiService: AIService
    
    private var availableModels = listOf(
        "gpt-3.5-turbo",
        "gpt-4",
        "gpt-4-turbo",
        "gpt-4o",
        "gpt-4o-mini"
    )
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivitySettingsBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        supportActionBar?.title = getString(R.string.settings_title)
        
        prefsManager = PreferencesManager.getInstance(this)
        aiService = AIService.getInstance()
        
        setupUI()
        loadSettings()
    }
    
    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        return when (item.itemId) {
            android.R.id.home -> {
                onBackPressed()
                true
            }
            else -> super.onOptionsItemSelected(item)
        }
    }
    
    /**
     * 设置UI
     */
    private fun setupUI() {
        // 模型选择
        setupModelSpinner()
        
        // 温度滑块
        binding.sliderTemperature.addOnChangeListener { _, value, _ ->
            binding.tvTemperatureValue.text = String.format("%.1f", value)
        }
        
        // 刷新模型按钮
        binding.btnRefreshModels.setOnClickListener {
            refreshModels()
        }
        
        // 保存按钮
        binding.btnSave.setOnClickListener {
            saveSettings()
        }
        
        // 重置按钮
        binding.btnReset.setOnClickListener {
            showResetConfirmDialog()
        }
        
        // 测试连接按钮
        binding.btnTestConnection.setOnClickListener {
            testConnection()
        }
    }
    
    /**
     * 设置模型下拉框
     */
    private fun setupModelSpinner() {
        val adapter = ArrayAdapter(
            this,
            android.R.layout.simple_dropdown_item_1line,
            availableModels
        )
        binding.spinnerModel.setAdapter(adapter)
    }
    
    /**
     * 加载设置
     */
    private fun loadSettings() {
        // API设置
        binding.etApiKey.setText(prefsManager.getApiKey())
        binding.etBaseUrl.setText(prefsManager.getBaseUrl())
        binding.etProxyUrl.setText(prefsManager.getProxyUrl())
        
        // 模型
        val currentModel = prefsManager.getModel()
        binding.spinnerModel.setText(currentModel, false)
        
        // 参数
        binding.sliderTemperature.value = prefsManager.getTemperature()
        binding.tvTemperatureValue.text = String.format("%.1f", prefsManager.getTemperature())
        
        binding.etMaxTokens.setText(prefsManager.getMaxTokens().toString())
        binding.etCompleteNumber.setText(prefsManager.getCompleteNumber().toString())
        
        // 提示词
        binding.etCompletePrompt.setText(prefsManager.getCompletePrompt())
        binding.etQaPrompt.setText(prefsManager.getQaPrompt())
        
        // 功能设置
        binding.switchFloatingButton.isChecked = prefsManager.getShowFloatingButton()
        binding.switchAutoCopy.isChecked = prefsManager.getAutoCopyResult()
        binding.switchVibrate.isChecked = prefsManager.getVibrateOnTrigger()
    }
    
    /**
     * 保存设置
     */
    private fun saveSettings() {
        // 验证输入
        val apiKey = binding.etApiKey.text.toString().trim()
        val baseUrl = binding.etBaseUrl.text.toString().trim()
        
        if (apiKey.isBlank()) {
            binding.tilApiKey.error = "API Key不能为空"
            return
        }
        binding.tilApiKey.error = null
        
        if (baseUrl.isBlank()) {
            binding.tilBaseUrl.error = "Base URL不能为空"
            return
        }
        binding.tilBaseUrl.error = null
        
        // 保存API设置
        prefsManager.setApiKey(apiKey)
        prefsManager.setBaseUrl(baseUrl)
        prefsManager.setProxyUrl(binding.etProxyUrl.text.toString().trim())
        
        // 保存模型
        prefsManager.setModel(binding.spinnerModel.text.toString())
        
        // 保存参数
        prefsManager.setTemperature(binding.sliderTemperature.value)
        
        val maxTokens = binding.etMaxTokens.text.toString().toIntOrNull() ?: 2000
        prefsManager.setMaxTokens(maxTokens)
        
        val completeNumber = binding.etCompleteNumber.text.toString().toIntOrNull() ?: 150
        prefsManager.setCompleteNumber(completeNumber)
        
        // 保存提示词
        prefsManager.setCompletePrompt(binding.etCompletePrompt.text.toString())
        prefsManager.setQaPrompt(binding.etQaPrompt.text.toString())
        
        // 保存功能设置
        prefsManager.setShowFloatingButton(binding.switchFloatingButton.isChecked)
        prefsManager.setAutoCopyResult(binding.switchAutoCopy.isChecked)
        prefsManager.setVibrateOnTrigger(binding.switchVibrate.isChecked)
        
        // 清除HTTP客户端缓存（配置变更后）
        aiService.clearHttpClient()
        
        Snackbar.make(binding.root, R.string.save_success, Snackbar.LENGTH_SHORT).show()
    }
    
    /**
     * 刷新模型列表
     */
    private fun refreshModels() {
        val apiKey = binding.etApiKey.text.toString().trim()
        val baseUrl = binding.etBaseUrl.text.toString().trim()
        
        if (apiKey.isBlank() || baseUrl.isBlank()) {
            Snackbar.make(binding.root, "请先填写API Key和Base URL", Snackbar.LENGTH_SHORT).show()
            return
        }
        
        binding.btnRefreshModels.isEnabled = false
        binding.progressBar.visibility = View.VISIBLE
        
        lifecycleScope.launch {
            try {
                val config = prefsManager.getRequestConfig()
                val result = aiService.getModels(config)
                
                result.onSuccess { models ->
                    if (models.isNotEmpty()) {
                        availableModels = models
                        setupModelSpinner()
                        Snackbar.make(binding.root, "成功获取 ${models.size} 个模型", Snackbar.LENGTH_SHORT).show()
                    } else {
                        Snackbar.make(binding.root, "未获取到模型列表", Snackbar.LENGTH_SHORT).show()
                    }
                }.onFailure { error ->
                    Snackbar.make(binding.root, "获取失败: ${error.message}", Snackbar.LENGTH_LONG).show()
                }
            } catch (e: Exception) {
                Snackbar.make(binding.root, "获取失败: ${e.message}", Snackbar.LENGTH_LONG).show()
            } finally {
                binding.btnRefreshModels.isEnabled = true
                binding.progressBar.visibility = View.GONE
            }
        }
    }
    
    /**
     * 测试连接
     */
    private fun testConnection() {
        val apiKey = binding.etApiKey.text.toString().trim()
        val baseUrl = binding.etBaseUrl.text.toString().trim()
        
        if (apiKey.isBlank() || baseUrl.isBlank()) {
            Snackbar.make(binding.root, "请先填写API Key和Base URL", Snackbar.LENGTH_SHORT).show()
            return
        }
        
        binding.btnTestConnection.isEnabled = false
        binding.progressBar.visibility = View.VISIBLE
        
        lifecycleScope.launch {
            try {
                val config = prefsManager.getRequestConfig()
                val result = aiService.callAPINonStream(
                    "你是一个测试助手",
                    "请回复\"连接成功\"",
                    config
                )
                
                when (result) {
                    is com.aitextassistant.model.RequestResult.Success -> {
                        MaterialAlertDialogBuilder(this@SettingsActivity)
                            .setTitle("连接成功")
                            .setMessage("API连接正常！\n\n回复内容：${result.text}")
                            .setPositiveButton("确定", null)
                            .show()
                    }
                    is com.aitextassistant.model.RequestResult.Error -> {
                        MaterialAlertDialogBuilder(this@SettingsActivity)
                            .setTitle("连接失败")
                            .setMessage("错误信息：${result.message}")
                            .setPositiveButton("确定", null)
                            .show()
                    }
                    else -> {}
                }
            } catch (e: Exception) {
                MaterialAlertDialogBuilder(this@SettingsActivity)
                    .setTitle("连接失败")
                    .setMessage("异常信息：${e.message}")
                    .setPositiveButton("确定", null)
                    .show()
            } finally {
                binding.btnTestConnection.isEnabled = true
                binding.progressBar.visibility = View.GONE
            }
        }
    }
    
    /**
     * 显示重置确认对话框
     */
    private fun showResetConfirmDialog() {
        MaterialAlertDialogBuilder(this)
            .setTitle("确认重置")
            .setMessage("确定要重置所有设置吗？此操作不可恢复。")
            .setPositiveButton("重置") { _, _ ->
                resetSettings()
            }
            .setNegativeButton("取消", null)
            .show()
    }
    
    /**
     * 重置设置
     */
    private fun resetSettings() {
        prefsManager.clearAll()
        loadSettings()
        Snackbar.make(binding.root, "设置已重置", Snackbar.LENGTH_SHORT).show()
    }
}
