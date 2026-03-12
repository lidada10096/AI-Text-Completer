package com.aitextassistant.service

import android.app.Activity
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.util.Log
import android.view.View
import android.view.WindowManager
import android.view.inputmethod.InputMethodManager
import android.widget.ProgressBar
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.lifecycle.lifecycleScope
import com.aitextassistant.data.PreferencesManager
import com.aitextassistant.model.OperationMode
import com.aitextassistant.model.RequestResult
import com.google.android.material.button.MaterialButton
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.google.android.material.textfield.TextInputEditText
import kotlinx.coroutines.flow.collect
import kotlinx.coroutines.launch

/**
 * 结果对话框Activity
 * 显示AI处理结果
 */
class ResultDialogActivity : Activity() {
    
    companion object {
        private const val TAG = "ResultDialogActivity"
        
        const val EXTRA_TEXT = "extra_text"
        const val EXTRA_MODE = "extra_mode"
    }
    
    private lateinit var prefsManager: PreferencesManager
    private lateinit var aiService: AIService
    
    private var currentMode: OperationMode = OperationMode.COMPLETION
    private var currentText: String = ""
    private var resultBuilder = StringBuilder()
    private var resultDialog: AlertDialog? = null
    private var resultTextView: TextInputEditText? = null
    private var progressBar: ProgressBar? = null
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // 设置浮动窗口样式
        window.setFlags(
            WindowManager.LayoutParams.FLAG_DIM_BEHIND,
            WindowManager.LayoutParams.FLAG_DIM_BEHIND
        )
        window.attributes.dimAmount = 0.5f
        
        // 设置窗口类型为对话框
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            window.setType(WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY)
        }
        
        prefsManager = PreferencesManager.getInstance(this)
        aiService = AIService.getInstance()
        
        // 获取传入的参数
        currentText = intent.getStringExtra(EXTRA_TEXT) ?: ""
        currentMode = OperationMode.valueOf(
            intent.getStringExtra(EXTRA_MODE) ?: OperationMode.COMPLETION.name
        )
        
        if (currentText.isBlank()) {
            Toast.makeText(this, "未检测到文本", Toast.LENGTH_SHORT).show()
            finish()
            return
        }
        
        // 显示处理对话框
        showProcessingDialog()
        
        // 执行AI操作
        performAIOperation()
    }
    
    override fun onDestroy() {
        super.onDestroy()
        resultDialog?.dismiss()
        resultDialog = null
    }
    
    /**
     * 显示处理中对话框
     */
    private fun showProcessingDialog() {
        val dialogView = layoutInflater.inflate(com.aitextassistant.R.layout.dialog_processing, null)
        progressBar = dialogView.findViewById(com.aitextassistant.R.id.progressBar)
        
        resultDialog = MaterialAlertDialogBuilder(this, com.aitextassistant.R.style.Theme_AITextAssistant_Dialog)
            .setView(dialogView)
            .setCancelable(false)
            .setNegativeButton("取消") { _, _ ->
                finish()
            }
            .create()
        
        resultDialog?.show()
    }
    
    /**
     * 执行AI操作
     */
    private fun performAIOperation() {
        lifecycleScope.launch {
            val config = prefsManager.getRequestConfig()
            
            if (!prefsManager.isConfigValid()) {
                showErrorDialog("配置无效", "请先在设置中配置API Key和Base URL")
                return@launch
            }
            
            resultBuilder.clear()
            
            val flow = when (currentMode) {
                OperationMode.COMPLETION -> aiService.completeText(currentText, config)
                OperationMode.QUESTION_ANSWERING -> aiService.answerQuestion(currentText, config)
            }
            
            flow.collect { result ->
                when (result) {
                    is RequestResult.Streaming -> {
                        resultBuilder.append(result.chunk)
                        updateProcessingDialog(resultBuilder.toString())
                    }
                    is RequestResult.Success -> {
                        showResultDialog(resultBuilder.toString())
                    }
                    is RequestResult.Error -> {
                        showErrorDialog("请求失败", result.message)
                    }
                }
            }
        }
    }
    
    /**
     * 更新处理中对话框
     */
    private fun updateProcessingDialog(text: String) {
        runOnUiThread {
            val dialogView = resultDialog?.window?.decorView?.findViewById<View>(
                com.aitextassistant.R.id.progressText
            ) as? TextInputEditText
            dialogView?.setText(text)
            dialogView?.setSelection(text.length)
        }
    }
    
    /**
     * 显示结果对话框
     */
    private fun showResultDialog(result: String) {
        runOnUiThread {
            resultDialog?.dismiss()
            
            val dialogView = layoutInflater.inflate(com.aitextassistant.R.layout.dialog_result, null)
            resultTextView = dialogView.findViewById(com.aitextassistant.R.id.resultText)
            resultTextView?.setText(result)
            
            val title = when (currentMode) {
                OperationMode.COMPLETION -> "文本补全结果"
                OperationMode.QUESTION_ANSWERING -> "问答结果"
            }
            
            resultDialog = MaterialAlertDialogBuilder(this, com.aitextassistant.R.style.Theme_AITextAssistant_Dialog)
                .setTitle(title)
                .setView(dialogView)
                .setPositiveButton("复制") { _, _ ->
                    copyToClipboard(result)
                    finish()
                }
                .setNegativeButton("关闭") { _, _ ->
                    finish()
                }
                .setOnDismissListener {
                    finish()
                }
                .create()
            
            resultDialog?.show()
            
            // 自动复制结果
            if (prefsManager.getAutoCopyResult()) {
                copyToClipboard(result)
            }
        }
    }
    
    /**
     * 显示错误对话框
     */
    private fun showErrorDialog(title: String, message: String) {
        runOnUiThread {
            resultDialog?.dismiss()
            
            resultDialog = MaterialAlertDialogBuilder(this, com.aitextassistant.R.style.Theme_AITextAssistant_Dialog)
                .setTitle(title)
                .setMessage(message)
                .setPositiveButton("确定") { _, _ ->
                    finish()
                }
                .setCancelable(false)
                .create()
            
            resultDialog?.show()
        }
    }
    
    /**
     * 复制到剪贴板
     */
    private fun copyToClipboard(text: String) {
        val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        val clip = ClipData.newPlainText("AI结果", text)
        clipboard.setPrimaryClip(clip)
        Toast.makeText(this, "已复制到剪贴板", Toast.LENGTH_SHORT).show()
    }
}
