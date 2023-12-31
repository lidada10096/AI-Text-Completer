import json
import requests


def get_response_stream_generate_from_ChatGPT_API(text, apikey, message_history,
                                                  base_url, model, temperature, presence_penalty,
                                                  max_tokens, complete_number, system_prompt,
                                                  add_punctuation_rules=True):
    """
    从ChatGPT API获取回复
    :param text: 用户输入的文本
    :param apikey: API密钥
    :param message_history: 消息历史
    :param base_url: API基础URL
    :param model: 模型
    :param temperature: 温度
    :param presence_penalty: 惩罚
    :param max_tokens: 最大token数量
    :param complete_number: 补全字数限制
    :param system_prompt: 系统提示词
    :param add_punctuation_rules: 是否添加衔接符号规则（补全模式用True，问答模式用False）
    :return: 回复生成器
    """
    if not apikey:
        print("apikey is None or empty")
        return

    # 构建完整的系统提示词
    if add_punctuation_rules:
        # 补全模式：添加衔接符号规则
        full_system_prompt = f"""{system_prompt}

【重要规则】
1. 补全内容保持在{complete_number}字以内
2. 根据用户输入的语气，在补全内容开头自动添加合适的衔接符号：
   - 问句用"？"
   - 陈述句用"，"或"。"
   - 感叹句用"！"
   - 其他情况用合适的标点符号
3. 补全内容要自然流畅，与上下文衔接合理
"""
    else:
        # 问答模式：不添加衔接符号规则
        full_system_prompt = f"""{system_prompt}

【重要规则】
1. 回答内容保持在{complete_number}字以内
2. 直接回答问题，不要添加无关内容
3. 条理清晰，层次分明
"""

    message_prompt = [{"role": "system", "content": full_system_prompt}]
    message_context = message_prompt + [{"role": "user", "content": text}]

    header = {"Content-Type": "application/json",
              "Authorization": "Bearer " + apikey}

    data = {
        "model": model,
        "temperature": temperature,
        "presence_penalty": presence_penalty,
        "max_tokens": max_tokens,
        "messages": message_context,
        "stream": True
    }
    print("开始流式请求")
    # 请求接收流式数据 动态print
    try:
        response = requests.request("POST", base_url, headers=header, json=data, stream=True)

        def generate():
            stream_content = str()
            one_message = {"role": "assistant", "content": stream_content}
            message_history.append(one_message)
            i = 0
            for line in response.iter_lines():
                # print(str(line))
                line_str = str(line, encoding='utf-8')
                if line_str.startswith("data:"):
                    if line_str.startswith("data: [DONE]"):
                        return
                    line_json = json.loads(line_str[5:])
                    if 'choices' in line_json:
                        if len(line_json['choices']) > 0:
                            choice = line_json['choices'][0]
                            if 'delta' in choice:
                                delta = choice['delta']
                                if 'role' in delta:
                                    role = delta['role']
                                elif 'content' in delta:
                                    delta_content = delta['content']
                                    i += 1
                                    one_message['content'] = one_message['content'] + delta_content
                                    yield delta_content

                elif len(line_str.strip()) > 0:
                    print(line_str)
                    yield line_str

    except Exception as e:
        ee = e
        def generate():
            yield "request error:\n" + str(ee)

    return generate
