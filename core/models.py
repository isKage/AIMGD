import uuid
from django.db import models
from typing import List, Dict, Optional
from decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist


class DiagnosisSession(models.Model):
    """
    整合后的诊断会话表，包含完整问诊流程数据
    字段说明：
    - session_id: 唯一会话标识（自动生成）
    - patient_response: 患者每次的回答（JSON格式存储历史）
    - ai_response: AI每次的提问（JSON格式存储历史）
    - diseases: 当前疾病概率分布（JSON格式）
    - IEG: 当前信息熵增益值（JSON格式）
    - ans_to_symptom: 患者对症状的回答记录（JSON格式）
    - created_at: 创建时间
    - updated_at: 最后更新时间
    """
    session_id = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="会话ID",
        default=uuid.uuid4
    )
    patient_response = models.JSONField(
        default=list,
        verbose_name="患者回答记录",
        help_text="格式: ['response1', 'response2', 'response3', 'response4', ...]"
    )
    ai_response = models.JSONField(
        default=list,
        verbose_name="AI提问记录",
        help_text="格式: ['question1', 'question2', 'question3', 'question4', ...]"
    )
    diseases = models.JSONField(
        default=list,
        verbose_name="疾病概率分布",
        help_text="格式: [{'D1':0.5, 'D2':0.3, ...}, {'D1': 0.6, 'D2': 0.2, ...}, ...]"
    )
    IEG = models.JSONField(
        default=list,
        verbose_name="信息熵增益",
        help_text="格式: [{'S1':0.8, 'S2':0.6, ...}, {'S1':0.8, 'S3':0.6, ...}, ...]"
    )
    ans_to_symptom = models.JSONField(
        default=dict,
        verbose_name="症状回答记录",
        help_text="格式: {'S1':True, 'S2':False, ...}"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = 'diagnosis_session'
        verbose_name = "诊断会话"
        verbose_name_plural = verbose_name

    def append_patient_response(self, response: str):
        """向patient_response追加新的回答"""
        if not isinstance(self.patient_response, list):
            self.patient_response = []
        self.patient_response.append(response)
        self.save()

    def append_ai_response(self, response: str):
        """向ai_response追加新的提问"""
        if not isinstance(self.ai_response, list):
            self.ai_response = []
        self.ai_response.append(response)
        self.save()

    def append_disease(self, disease_data: dict):
        """向diseases追加新的疾病概率分布"""
        if not isinstance(self.diseases, list):
            self.diseases = []
        self.diseases.append(disease_data)
        self.save()

    def append_IEG(self, ieg_data: dict):
        """向IEG追加新的信息熵增益数据"""
        if not isinstance(self.IEG, list):
            self.IEG = []
        self.IEG.append(ieg_data)
        self.save()

    def update_symptom_answer(self, symptom: str, answer: bool):
        """更新症状回答记录"""
        self.ans_to_symptom[symptom] = answer
        self.save()

    @property
    def last_ai_question(self) -> Optional[str]:
        """获取最后一条AI提问"""
        return self.ai_response[-1] if self.ai_response else None

    @property
    def last_patient_question(self) -> Optional[str]:
        """获取最后一条患者回答"""
        return self.patient_response[-1] if self.patient_response else None

    def save(self, *args, **kwargs):
        """重写save方法确保session_id存在"""
        if not self.session_id:
            self.session_id = str(uuid.uuid4())
        super().save(*args, **kwargs)

    def __str__(self):
        return f"会话 {self.session_id} ({self.updated_at})"


class SOAPNote(models.Model):
    session = models.OneToOneField(  # 改为一对一关系更合理
        DiagnosisSession,
        on_delete=models.CASCADE,
        verbose_name="关联会话",
        db_column='session_id',
        to_field='session_id',
        related_name='soap_note'  # 添加反向查询
    )
    initial = models.TextField(
        max_length=10000,
        verbose_name="初始记录"
    )
    soap = models.TextField(
        max_length=10000,
        verbose_name="soap记录"
    )
    final = models.TextField(
        max_length=10000,
        verbose_name="最终记录"
    )
    disease_name = models.CharField(
        max_length=100
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = 'soap_note'
        verbose_name = "SOAP记录"
        verbose_name_plural = verbose_name


class PSGReport(models.Model):
    session = models.OneToOneField(  # 改为一对一关系更合理
        DiagnosisSession,
        on_delete=models.CASCADE,
        verbose_name="关联会话",
        db_column='session_id',
        to_field='session_id',
        related_name='report'  # 添加反向查询
    )
    concise = models.TextField(
        max_length=10000,
        verbose_name="简单易懂报告"
    )
    final = models.TextField(
        max_length=10000,
        verbose_name="最终报告"
    )
    disease_name = models.CharField(
        max_length=100
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = 'psg_report'
        verbose_name = '患者报告'
        verbose_name_plural = verbose_name


class RelationDiseaseSymptom(models.Model):
    """疾病-病征对照表"""
    disease_name = models.CharField(max_length=255, verbose_name="疾病名称")
    symptom_list = models.JSONField(
        default=list,
        verbose_name='病征列表',
        help_text="格式: ['S1', 'S2', 'S3', 'S4', 'S5', ...]"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = 'relation_disease_symptom'
        managed = False
        verbose_name = '疾病-病征对照表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"Disease: {self.disease_name}, Symptom: {self.symptom_list}"

    @classmethod
    def search_symptom(cls, disease_name: str) -> List[str]:
        try:
            sample = cls.objects.get(disease_name=disease_name)
            return sample.symptom_list
        except ObjectDoesNotExist:
            return None

    @classmethod
    def sd_relation(cls, disease_list: List[str]) -> Dict[str, list]:
        query_set = cls.objects.filter(disease_name__in=disease_list)
        result = {
            query.disease_name: query.symptom_list for query in query_set
        }
        return result


class DiseaseProb(models.Model):
    """疾病概率表（已存在表结构保持不变）"""
    disease_name = models.CharField(max_length=255, verbose_name="疾病名称")
    probability = models.DecimalField(max_digits=20, decimal_places=10, verbose_name="概率")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = 'disease_prob'
        managed = False  # 关键设置：Django 不管理此表的迁移
        verbose_name = '疾病概率'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.disease_name} (P={self.probability})"

    @classmethod
    def _get_probabilities_Decimal(cls, disease_names: List[str]) -> Dict[str, Optional[Decimal]]:
        """
        根据疾病名称列表查询概率，返回字典 {'疾病': 概率}

        参数:
            disease_names: 疾病名称列表，如 ["高血压", "糖尿病"]

        返回:
            字典格式: {"高血压": 0.6, "糖尿病": 0.3, ...}
            如果疾病不存在，则值为 None
        """
        # 查询疾病概率
        prob_entries = cls.objects.filter(disease_name__in=disease_names)

        # 构建字典 {疾病: 概率}
        prob_dict = {entry.disease_name: entry.probability for entry in prob_entries}

        # 补充未找到的疾病（值为None）
        return {disease: prob_dict.get(disease) for disease in disease_names}

    @classmethod
    def get_prob(cls, disease_names: List[str]) -> Dict[str, Optional[float]]:
        prob_dict = cls._get_probabilities_Decimal(disease_names)
        return {k: float(v) if v is not None else None for k, v in prob_dict.items()}


class SymptomProb(models.Model):
    """病征概率表（已存在表结构保持不变）"""
    symptom_name = models.CharField(max_length=255, verbose_name="病征名称")
    probability = models.DecimalField(max_digits=20, decimal_places=10, verbose_name="概率")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = 'symptom_prob'
        managed = False  # 关键设置：Django 不管理此表的迁移
        verbose_name = '病征概率'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.symptom_name} (P={self.probability})"

    @classmethod
    def _get_probabilities_Decimal(cls, symptom_names: List[str]) -> Dict[str, Optional[Decimal]]:
        """
        根据病征名称列表查询概率，返回字典 {'病征': 概率}

        参数:
            symptom_names: 病征名称列表，如 ["头痛", "咳嗽"]

        返回:
            字典格式: {"头痛": 0.6, "咳嗽": 0.3, ...}
            如果病征不存在，则值为 None
        """
        # 查询病征概率
        prob_entries = cls.objects.filter(symptom_name__in=symptom_names)

        # 构建字典 {病征: 概率}
        prob_dict = {entry.symptom_name: entry.probability for entry in prob_entries}

        # 补充未找到的病征（值为None）
        return {symptom: prob_dict.get(symptom) for symptom in symptom_names}

    @classmethod
    def get_prob(cls, symptom_names: List[str]) -> Dict[str, Optional[float]]:
        prob_dict = cls._get_probabilities_Decimal(symptom_names)
        return {k: float(v) if v is not None else None for k, v in prob_dict.items()}
