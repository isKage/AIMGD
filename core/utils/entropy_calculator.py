import numpy as np
from typing import Dict, List, Tuple
from core.models import DiagnosisSession, DiseaseProb, SymptomProb, RelationDiseaseSymptom


class EntropyCalculator:
    """改进后的信息熵增益计算工具类"""

    def __init__(self):
        self.epsilon = 1e-10  # 用于数值稳定的小常数
        self.MIN_PROB_THRESHOLD = 0.001  # 最小保留概率

    def calculate_ieg(self,
                      sd_relation: Dict[str, List[str]],
                      session_id=None) -> Dict[str, float]:
        """
        计算初始IEG值（改进版）
        :param sd_relation: 疾病-症状关系 {'D1':['S1','S2'], ...}
        :param session_id: 会话 id
        :return: IEG字典 {'S1':0.8, ...}
        """
        # 获取需要排除的症状
        drop_symptoms = []
        if session_id:
            session = DiagnosisSession.objects.get(session_id=session_id)
            drop_symptoms = list(session.ans_to_symptom.keys()) if session.ans_to_symptom else []

        # 构建疾病-症状矩阵
        sd_matrix, disease_names, symptoms_names = self._sd_matrix(
            sd_relation,
            drop_symptoms=drop_symptoms if drop_symptoms else None
        )

        # 获取并归一化疾病概率
        p_l_dict = self.get_disease_prob(sd_relation, session_id)
        p_l = self._safe_normalize(np.array(list(p_l_dict.values()), dtype=float))

        # 获取症状概率并归一化
        rho_k = SymptomProb.get_prob(symptoms_names)
        total_rho = max(np.sum([rho_k[k] for k in rho_k]), self.epsilon)  # 防止除零

        # 归一化疾病-症状矩阵（行归一）
        sd_matrix = self._safe_normalize(sd_matrix.astype(float), axis=1)

        # 计算初始熵
        H_0 = -np.sum(p_l * np.log(p_l + self.epsilon))

        # 计算每个症状的IEG
        ieg_dict = {}
        for col, s_name in enumerate(symptoms_names):
            try:
                H_cond = self.calculate_one_ieg(
                    rho_k[s_name] / total_rho,
                    p_l=p_l,
                    p_k_l=sd_matrix[:, col]
                )
                ieg = abs((H_0 - H_cond) / max(H_0, self.epsilon))  # 防止除零
                ieg_dict[s_name] = ieg
            except Exception as e:
                print(f"计算症状 {s_name} 的IEG时出错: {str(e)}")
                ieg_dict[s_name] = 0.0  # 出错时默认值

        return ieg_dict

    def get_disease_prob(self,
                         sd_relation: Dict[str, list],
                         session_id=None) -> Dict[str, float]:
        """
        安全获取疾病概率（改进版）
        :param sd_relation: 疾病-病征对照字典
        :param session_id: 会话id
        :return: 归一化的疾病概率字典
        """
        if not session_id:
            _, disease_names, _ = self._sd_matrix(sd_relation)
            p_l = DiseaseProb.get_prob(disease_names)
        else:
            session = DiagnosisSession.objects.get(session_id=session_id)
            if session.diseases:
                p_l = session.diseases[-1]
            else:
                _, disease_names, _ = self._sd_matrix(sd_relation)
                p_l = DiseaseProb.get_prob(disease_names)

        # 归一化处理
        prob_sum = max(np.sum(list(p_l.values())), self.epsilon)
        return {k: max(v, 0.0) / prob_sum for k, v in p_l.items()}  # 确保概率非负

    def calculate_one_ieg(self,
                          rho_k: float,
                          p_l: np.array,
                          p_k_l: np.array) -> float:
        """
        计算单个症状的条件熵（改进版）
        """
        # 避免无关疾病的概率直接归零，避免过拟合
        rho_k = np.clip(rho_k, 0.01, 0.99)  # 限制极端概率值

        # 使用对数空间计算避免数值下溢
        log_p_l_k = np.log(p_k_l + self.epsilon) + np.log(p_l + self.epsilon) - np.log(rho_k)
        log_pn_l_k = np.log(1.0 - p_k_l + self.epsilon) + np.log(p_l + self.epsilon) - np.log(1.0 - rho_k)

        # 指数归一化
        p_l_k = np.exp(log_p_l_k - np.max(log_p_l_k))
        pn_l_k = np.exp(log_pn_l_k - np.max(log_pn_l_k))

        # 安全归一化
        p_l_k = self._safe_normalize(p_l_k)
        pn_l_k = self._safe_normalize(pn_l_k)

        # 计算条件熵
        H_occ = -np.sum(p_l_k * np.log(p_l_k + self.epsilon))
        H_nok = -np.sum(pn_l_k * np.log(pn_l_k + self.epsilon))
        H_cond = rho_k * H_occ + (1.0 - rho_k) * H_nok

        return H_cond

    def updated_disease_prob(self,
                             session_id: str,
                             symptom_response: bool,
                             symptom: str) -> Dict[str, float]:
        """
        返回更新后的疾病概率（改进版）
        """
        session = DiagnosisSession.objects.get(session_id=session_id)
        old_disease_prob = session.diseases[-1] if session.diseases else {}
        disease_names = list(old_disease_prob.keys())

        # 获取当前症状列表
        old_symptoms_names = list(session.IEG[-1].keys()) if session.IEG else []
        initial_symptoms_names = list(session.IEG[0].keys()) if session.IEG else []
        drop_symptoms = [d for d in initial_symptoms_names if d not in old_symptoms_names]

        # 归一化当前疾病概率
        p_l = self._safe_normalize(np.array(list(old_disease_prob.values()), dtype=float))

        # 获取症状概率
        rho_k_dict = SymptomProb.get_prob(old_symptoms_names) if old_symptoms_names else {}
        total_rho = max(np.sum(list(rho_k_dict.values())), self.epsilon)
        rho_k = rho_k_dict.get(symptom, 0.0) / total_rho

        # 构建疾病-症状关系矩阵
        sd_relation = RelationDiseaseSymptom.sd_relation(disease_names)
        sd_matrix, _, _ = self._sd_matrix(sd_relation, drop_symptoms=drop_symptoms)

        # 找到目标症状的列
        p_k_l = np.ones(len(disease_names), dtype=float)
        if symptom in old_symptoms_names:
            symptom_idx = old_symptoms_names.index(symptom)
            p_k_l = sd_matrix[:, symptom_idx]

        # 计算更新后的概率
        rho_k = np.clip(rho_k, self.epsilon, 1.0 - self.epsilon)
        if symptom_response:
            new_probs = p_k_l * p_l / rho_k
        else:
            new_probs = (1 - p_k_l) * p_l / (1 - rho_k)

        # 软化处理：保留最小概率阈值
        min_prob = self.MIN_PROB_THRESHOLD
        new_probs = np.clip(new_probs, min_prob, None)

        # 重新归一化
        new_probs = self._safe_normalize(new_probs)

        return {d_name: float(new_probs[i]) for i, d_name in enumerate(disease_names)}

    def _safe_normalize(self, arr: np.array, axis=None) -> np.array:
        """
        安全的归一化函数，防止除以零
        """
        arr = np.nan_to_num(arr, nan=0.0, posinf=1.0, neginf=0.0)  # 处理异常值
        arr = np.clip(arr, 0.0, None)  # 确保非负

        if axis is not None:
            sums = np.sum(arr, axis=axis, keepdims=True)
        else:
            sums = np.sum(arr)

        sums = np.where(sums <= 0, 1.0, sums)  # 防止除零
        return arr / sums

    def _get_symptoms(self, sd_relation: Dict[str, List[str]]) -> List[str]:
        """获取所有症状列表"""
        return list({s for symptoms in sd_relation.values() for s in symptoms})

    def _get_diseases(self, sd_relation: Dict[str, List[str]]) -> List[str]:
        """获取所有疾病列表"""
        return list(sd_relation.keys())

    def _sd_matrix(self,
                   sd_relation: Dict[str, List[str]],
                   drop_symptoms: List[str] = None) -> Tuple[np.ndarray, List[str], List[str]]:
        """
        构建疾病-症状关系矩阵（改进版）
        """
        all_symptoms = [s for s in self._get_symptoms(sd_relation)
                        if not drop_symptoms or s not in drop_symptoms]
        all_diseases = self._get_diseases(sd_relation)

        # 构建症状到索引的映射
        symptom_to_idx = {s: idx for idx, s in enumerate(all_symptoms)}

        # 初始化并填充矩阵
        sd_matrix = np.zeros((len(all_diseases), len(all_symptoms)), dtype=int)
        for i, (disease, symptoms) in enumerate(sd_relation.items()):
            for s in symptoms:
                if s in symptom_to_idx:
                    sd_matrix[i, symptom_to_idx[s]] = 1

        return sd_matrix, all_diseases, all_symptoms
