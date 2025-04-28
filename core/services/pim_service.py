from core.utils import KnowledgeGraph, EntropyCalculator, AIGenerator
from core.models import DiagnosisSession, DiseaseProb, SymptomProb, RelationDiseaseSymptom

from typing import Dict, List, Tuple, Optional


class PIMService:
    def __init__(self, N_limit: int = 10):
        """
        初始化PIM服务
        :param N_limit: 最大问诊轮次限制
        """
        self.kg = KnowledgeGraph()  # 知识图谱
        self.ec = EntropyCalculator()  # 熵计算工具
        self.N_limit = N_limit  # 最大问诊轮次
        self.EPSILON = 1e-10

    # ====================== 调用 ai ======================
    def _call_ai_get_diseases(self, text: str) -> List[str]:
        """调用 AI 获取初始疾病列表"""
        ai = AIGenerator()
        prompt = f"列出疾病：根据患者描述【{text}】，列出最可能的几种疾病名称（JSON格式），不可超过 10 种"
        response = ai.generate_json_response(prompt, key="diseases")
        return response["diseases"]

    def _call_ai_generate_question(self, symptom: str, diseases: Dict[str, float]) -> str:
        """调用 AI 生成症状询问问题"""
        ai = AIGenerator()
        d_name = "、".join(list(diseases.keys()))
        prompt = (
            "直接生成问题，不要生成其他多余的语句：\n"
            f"针对相关疾病【{d_name}】，将症状【{symptom}】转化为患者能理解的口语化问题（与这些疾病要紧密相关）。"
            f"询问患者是否有出现【{symptom}】相关的症状。"
        )
        return ai.generate_text_response(prompt)

    def _call_ai_yes_or_no(self, text: str, symptom: str, question: str) -> Dict[str, bool]:
        """
        调用AI分析患者‘是否’偏向
        :return {'Symptom': True}
        """
        ai = AIGenerator()
        prompt = f"针对问题【{question}】分析患者的回答【{text}】，提取病状【{symptom}】是否出现，是: 则 'True' 否: 则 'False'"
        is_symptom = ai.generate_bool_response(prompt, key=symptom)
        return {k: bool(is_symptom[k]) for k in is_symptom}

    # ====================== 核心功能 ======================
    def start_new_session(self, patient_desc: str, session_id: str) -> Dict:
        """
        开始新问诊会话（使用 DiseaseProb 表的先验概率）
        :param session_id: 会话 id
        :param patient_desc: 患者初始症状描述
        :return: 初始会话数据 {'patient_response':..., 'diseases':..., 'IEG':...}
        """
        # 1. 获取初始疾病列表
        diseases = self._call_ai_get_diseases(patient_desc)
        matched_diseases = self.kg.search_precise(diseases)

        # 2. 获得 sd_relation 疾病-症状关系 dict
        sd_relation = RelationDiseaseSymptom.sd_relation(disease_list=matched_diseases)

        # 3. 计算初始IEG
        ieg_init = self.ec.calculate_ieg(sd_relation=sd_relation, session_id=session_id)

        # 4. 疾病更新
        diseases = self.ec.get_disease_prob(sd_relation=sd_relation, session_id=session_id)

        session_init = {
            'patient_response': patient_desc,
            'diseases': diseases,
            'IEG': ieg_init,
        }

        return session_init

    def next_round(self, patient_ans: str, session_id: str, symptom_response: bool, symptom: str) -> Dict:
        """下一轮对话"""
        query_dict = DiagnosisSession.objects.get(session_id=session_id)
        old_disease_prob = query_dict.diseases[-1]

        sd_relation = RelationDiseaseSymptom.sd_relation(disease_list=list(old_disease_prob.keys()))
        new_ieg = self.ec.calculate_ieg(sd_relation=sd_relation, session_id=session_id)

        # 新概率
        new_diseases_prob = self.ec.updated_disease_prob(session_id, symptom_response, symptom)

        session_data = {
            'patient_response': patient_ans,
            'diseases': new_diseases_prob,
            'IEG': new_ieg
        }
        return session_data

    def generate_question(self, IEG: Dict[str, float], diseases: Dict[str, float]) -> str:
        symptom_opt = max(IEG)
        for k in IEG:
            if IEG[k] > IEG[symptom_opt]:
                symptom_opt = k
        return self._call_ai_generate_question(symptom=symptom_opt, diseases=diseases)

    def is_symptom_occurrence(self, patient_ans: str, symptom: str, question: str) -> Dict[str, bool]:
        return self._call_ai_yes_or_no(text=patient_ans, symptom=symptom, question=question)

    # ====================== 停止询问 ======================
    def should_stop(self, session_id: str) -> bool:
        """
        判断是否终止问诊
        :param session_id: 当前会话 id
        :return: 是否终止
        """
        session = DiagnosisSession.objects.get(session_id=session_id)
        ieg = session.IEG

        if len(ieg) >= self.N_limit:
            return True

        # 2. IEG收敛 (最后两个症状的 IEG 变化小于阈值)
        if len(ieg) >= 3:
            last = max(ieg[-1].values())
            mid = max(ieg[-2].values())
            pre = max(ieg[-3].values())

            diff2 = abs(last - mid) / (mid + self.EPSILON)
            diff1 = abs(mid - pre) / (pre + self.EPSILON)

            if diff1 > diff2:
                return True

        return False

# def _generate_final_report(self, session: DiagnosisSession) -> Dict:
#     """
#     生成最终诊断报告
#     :param session: 当前会话
#     :return: 诊断报告
#     """
#     top_diseases = sorted(
#         session.diseases.items(),
#         key=lambda x: x[1],
#         reverse=True
#     )[:3]  # 取概率最高的3种疾病
#
#     return {
#         'session_id': session.session_id,
#         'diagnosis': [
#             {'disease': d[0], 'probability': d[1]}
#             for d in top_diseases
#         ],
#         'recommendation': self._generate_recommendation(top_diseases[0][0])
#     }
#
# def _generate_recommendation(self, disease: str) -> str:
#     """
#     生成治疗建议
#     :param disease: 疾病名称
#     :return: 建议文本
#     """
#     from core.utils.ai_integration import AIGenerator
#     ai = AIGenerator()
#     prompt = f"为疾病【{disease}】生成简要治疗建议，使用通俗易懂的语言"
#     return ai.generate_text_response(prompt)
