import heapq

from core.utils import KnowledgeGraph, EntropyCalculator, AIGenerator
from core.models import DiagnosisSession, SOAPNote

from typing import Dict, List, Tuple, Optional


class CDGService:
    def __init__(self, session: DiagnosisSession, N_disease: int = 3):
        self.session = session
        self.session_id = session.session_id
        self.N_disease = N_disease
        self.ai = AIGenerator()
        self.kg = KnowledgeGraph()

    def generate_initial(self) -> Tuple[str, str]:
        """
        生成初始记录
        :return ("Disease", "initial note")
        """
        disease_prob = self.session.diseases[-1]  # {'D1':0.6, ...}
        if len(disease_prob) > self.N_disease:
            top_diseases = heapq.nlargest(
                self.N_disease,
                disease_prob.items(),
                key=lambda item: item[1]
            )
            disease_prob = dict(top_diseases)

        qa = self._qa()
        info_dict = {
            'disease': disease_prob,
            'qa': qa
        }

        return self.ai.generate_initial_note(info_dict=info_dict)

    def generate_soap(self):
        """生成soap格式"""
        initial_note = SOAPNote.objects.get(session_id=self.session_id).initial

        qa = self._qa()
        combined_info = {
            '初始临床记录': initial_note,
            '医患问诊对话内容': qa
        }
        return self.ai.generate_soap_note(info=str(combined_info), step=2)

    def generate_final(self, disease):
        """补充信息，生成最终记录"""
        soap_note = SOAPNote.objects.get(session_id=self.session_id).soap

        # 补充信息
        additional_info = self.kg.info[disease]
        additional_info = additional_info.to_dict()

        combined_info = {
            'soap格式临床记录': soap_note,
            '补充信息': additional_info
        }
        return self.ai.generate_soap_note(info=str(combined_info), step=3)

    # -------- 对话
    def _qa(self):
        """
        返回对话内容
        :return: {'对话i': {'问': '答'}, ...}
        """
        qa = {}  # 问答内容
        p_res = self.session.patient_response
        ai_res = self.session.ai_response
        if len(p_res) >= len(ai_res):  # 暂时不检查特殊情况
            for i in range(len(p_res)):
                if i == 0:
                    qa['对话1'] = {'患者初始描述': p_res[i]}
                else:
                    qa[f'对话{i + 1}'] = {'询问': ai_res[i - 1], '患者回答': p_res[i]}
        return qa
