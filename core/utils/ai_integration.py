import os
import json
from typing import Tuple
from openai import OpenAI

# from local_settings import settings # 测试用
from django.conf import settings  # django 设置


class AIGenerator:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.API_KEY,  # 从配置读取
            base_url=settings.BASE_URL
        )
        file_path = os.path.join(settings.BASE_DIR, 'prompt.json')
        with open(file_path, 'r') as f:
            self.prompt = json.load(f)

    # =============== PIM 生成问题、获取是否、返回 json 格式化 ===============
    def generate_json_response(self, prompt: str, key: str) -> dict:
        """生成结构化 JSON 响应（用于疾病列表提取）"""
        response = self.client.chat.completions.create(
            model=settings.MODEL,
            messages=[
                {"role": "system", "content": f"输出JSON，键值为 {key}"},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

    def generate_text_response(self, prompt: str) -> str:
        """生成自然语言文本（用于问题生成）"""
        response = self.client.chat.completions.create(
            model=settings.MODEL,
            messages=[
                {"role": "system", "content": "你是一位知识全面的医生，能够将专业化的术语解构成患者能理解的口语化表达。"},
                {"role": "user", "content": prompt}
            ],
        )
        return response.choices[0].message.content

    def generate_bool_response(self, prompt: str, key: str) -> dict:
        """分析是否，返回 {'S': 'True'}"""
        response = self.client.chat.completions.create(
            model=settings.MODEL,
            messages=[
                {"role": "system", "content": f"输出JSON，键为 '{key}'，值只能为 'True' 或 'False' 的布尔类型"},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

    # =============== CDG 生成记录 ===============
    def generate_soap_note(self, info: str, step: int = 2) -> str:
        """CDG 分阶段生成 SOAP"""
        prompt = self.prompt['cdg']

        if step == 2:
            final_prompt = prompt['soap'] + info
        else:
            final_prompt = prompt['supplementary'] + info

        response = self.client.chat.completions.create(
            model=settings.MODEL,
            messages=[
                {"role": "system", "content": prompt['system']},
                {"role": "user", "content": final_prompt}
            ],
        )
        return response.choices[0].message.content

    def generate_initial_note(self, info_dict: dict) -> Tuple[str, str]:
        """强化版初始记录生成（确保疾病名称严格匹配）"""
        # 加载提示模板
        prompt = self.prompt['cdg']

        # 准备疾病白名单
        disease_name = list(info_dict['disease'].keys())
        disease_str = "、".join(f'"{name}"' for name in disease_name)  # 格式化为："A"、"B"、"C"

        # 构建带格式约束的prompt
        final_prompt = (
            f"{prompt['initial']}\n"
            f"已知疾病列表（仅限以下名称，必须严格匹配）：\n{disease_str}\n\n"
            "请以JSON格式返回，包含两个字段：\n"
            "1. 'disease'：必须完全匹配上述疾病名称之一\n"
            "2. 'reason'：诊断依据分析\n"
            "=== 输入数据 ===\n"
            f"疾病概率：{info_dict['disease']}\n"
            f"问诊对话：{info_dict['qa']}"
        )

        # API调用（强制JSON模式）
        response = self.client.chat.completions.create(
            model=settings.MODEL,
            messages=[
                {
                    "role": "system",
                    "content": prompt['system'] + "\n必须严格使用提供的疾病名称，禁止任何修改或创造。"
                },
                {"role": "user", "content": final_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3  # 降低随机性
        )

        # 解析并验证结果
        try:
            res = json.loads(response.choices[0].message.content)
            selected_disease = res['disease']

            # 白名单验证
            if selected_disease not in disease_name:
                raise ValueError(f"AI返回了非白名单疾病：{selected_disease}")

            return selected_disease, res['reason']

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # 失败时自动选择概率最高的疾病
            fallback_disease = max(info_dict['disease'].items(), key=lambda x: x[1])[0]
            return fallback_disease, f"自动回退：{str(e)}"

    # =============== PSG 生成患者报告 ===============
    def generate_report(self, info_dict: dict) -> str:
        prompt = self.prompt['psg']
        additional_info = info_dict.get('addition', False)
        if not additional_info:
            # 首次生成简洁报告
            final_prompt = (
                f"{prompt['concise']}\n"
                f"疾病: {info_dict['disease_name']}\n"
                f"SOAP 格式的临床记录': {info_dict['soap']}\n"
                f"问诊对话内容': {info_dict['qa']}"
            )
        else:
            # 最终报告
            final_prompt = (
                f"{prompt['supplementary']}\n"
                f"疾病: {info_dict['disease_name']}\n"
                f"已有的转述内容: {info_dict['concise']}\n"
                f"补充信息: {additional_info}"
            )

        # ai 生成
        response = self.client.chat.completions.create(
            model=settings.MODEL,
            messages=[
                {"role": "system", "content": prompt['system']},
                {"role": "user", "content": final_prompt}
            ],
        )
        return response.choices[0].message.content


if __name__ == '__main__':
    path = settings.BASE_DIR
    print(path)

    file_path = os.path.join(settings.BASE_DIR, 'prompt.json')
    with open(file_path, 'r') as f:
        prompt = json.load(f)['cdg']

    print(prompt)

    # s = "咳嗽"
    # text = "我确实有点咳嗽，喉咙痛"
    # ai = AIGenerator()
    # prompt = f"分析患者的回答【{text}】，提取病状【{s}】是否出现，是: 则 'True' 否: 则 'False'"
    #
    # res = ai.generate_bool_response(prompt, key=s)
    # print(res)
    # print(type(res))
    # print(res[s])
    # print(type(res[s]))
    # print(type(bool(res[s])))

    # ================================================================================================================
    # import pathlib
    # import os
    #
    # path = os.path.join(pathlib.Path(__file__).parent.parent.parent, "data/diseases_name.txt")
    # with open(path, "r") as f:
    #     names = f.read()

    # ================================================================================================================
    # text = "我今年 25 岁，在剧烈运动后突然：头晕眼花，站不稳，乏力，没精打采。"
    # ai = AIGenerator()
    # prompt = f"根据患者描述【{text}】，列出最可能的几种疾病名称（JSON格式），不可超过 10 种。"
    # response = ai.generate_json_response(prompt, key="diseases")
    # res = response["diseases"]
    #
    # print(res)

    # ================================================================================================================
    # client = OpenAI(
    #     api_key=API_KEY,
    #     base_url=BASE_URL
    # )
    #
    # response = client.chat.completions.create(
    #     model=MODEL,
    #     messages=[
    #         {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
    #         {"role": "user", "content": "? 2020 年世界奥运会乒乓球男子和女子单打冠军分别是谁? "
    #                                     "Please respond in the format {\"男子冠军\": ..., \"女子冠军\": ...}"}
    #     ],
    #     response_format={"type": "json_object"}
    # )
    #
    # print(response.choices[0].message.content)
