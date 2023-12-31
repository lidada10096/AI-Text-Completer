# AI Text Completer

AI智能文本补全与问答工具 - 选中文字，一键补全或提问。

## 功能特点

- 🚀 **文本补全**：选中文字，按 `Alt+`` 即可触发AI智能补全
- 💬 **AI问答**：选中文字，按 `Alt+1` 打开问答窗口，获取AI回答
- 🎯 **智能衔接**：补全时自动根据语境添加合适的标点符号
- 💻 **系统托盘**：最小化到系统托盘，不占用任务栏
- 🔄 **开机自启动**：支持设置开机自动启动
- ⚙️ **自定义Prompt**：可在UI中自定义系统提示词
- 🔒 **单实例运行**：防止重复打开多个程序
- 📊 **使用日志**：记录API调用历史，方便查看

## 使用方法

### 1. 配置文件
   - 复制 `config.example.json` 为 `config.json`
   - 填写你的 API Key 和其他配置

### 2. 运行程序
   - 双击 `AI-Text-Completer.exe` 运行
   - 程序会自动最小化到系统托盘

### 3. 文本补全
   - 在任意文本编辑器中选中文字
   - 按 `Alt+`` (反引号) 触发补全
   - 长按 `Ctrl` 键可停止补全

### 4. AI问答
   - 在任意位置选中问题文字
   - 按 `Alt+1` 打开问答窗口
   - AI会针对选中的文字给出详细回答
   - 支持一键复制回答内容

### 5. 打开设置
   - 双击系统托盘图标
   - 或右键托盘图标选择"打开程序UI界面"

## 快捷键说明

| 快捷键 | 功能 |
|--------|------|
| `Alt+`` | 文本补全 |
| `Alt+1` | AI问答 |
| 长按 `Ctrl` | 停止补全 |

## 配置说明

```json
{
  "platform": "openai",
  "api_key": "你的API密钥（支持多个key，用逗号分隔）",
  "base_url": "API地址",
  "https_proxy": "代理设置（可选）",
  "temperature": 0.9,
  "complete_number": 150,
  "model": "gpt-3.5-turbo",
  "max_tokens": 2000,
  "auto_start": false,
  "system_prompt": "系统提示词"
}
```

### 配置项说明

| 配置项 | 说明 |
|--------|------|
| platform | AI平台选择（openai等） |
| api_key | API密钥，支持多个key负载均衡 |
| base_url | API请求地址 |
| https_proxy | 代理设置（可选） |
| temperature | 生成温度，越高越随机 |
| complete_number | 补全字数上限 |
| model | 使用的模型名称 |
| max_tokens | 最大token数 |
| auto_start | 是否开机自启动 |
| system_prompt | 系统提示词 |

## 系统要求

- Windows 10/11
- Python 3.10+ (如从源码运行)

## 从源码运行

```bash
pip install -r requirements.txt
python main.py
```

## 打包成exe

```bash
python build_exe.py
```

生成的exe文件位于 `dist/AI-Text-Completer.exe`

## 注意事项

- `config.json` 包含敏感信息，已添加到 `.gitignore`，请勿提交到GitHub
- 使用 `config.example.json` 作为配置模板
- 支持多个API Key负载均衡，用逗号分隔即可

## License

MIT License
