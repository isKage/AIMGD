from core.utils import KnowledgeGraph, EntropyCalculator, AIGenerator
from core.models import DiagnosisSession, SOAPNote, PSGReport

from typing import Dict, List, Tuple, Optional


class PSGService:
    def __init__(self, session: DiagnosisSession):
        self.session = session
        self.session_id = session.session_id
        self.disease_name = PSGReport.objects.get(session_id=self.session_id).disease_name
        self.ai = AIGenerator()
        self.kg = KnowledgeGraph()

    def generate_concise(self):
        info_dict = self._basic_info()
        return self.ai.generate_report(info_dict=info_dict)

    def generate_final(self):
        additional_info = self.kg.info[self.disease_name]
        additional_info = additional_info.to_dict()

        info_dict = {
            'disease_name': self.disease_name,
            'concise': PSGReport.objects.get(session_id=self.session_id).concise,
            'addition': additional_info
        }
        return self.ai.generate_report(info_dict=info_dict)

    def _basic_info(self):
        qa = self._qa()
        note = SOAPNote.objects.get(session_id=self.session_id).final
        info_dict = {
            'disease_name': self.disease_name,
            'soap': note,
            'qa': qa
        }
        return info_dict

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
