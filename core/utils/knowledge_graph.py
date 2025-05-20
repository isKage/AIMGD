import os
import json
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from fuzzywuzzy import fuzz


@dataclass
class DiseaseInfo:
    """疾病信息数据类"""
    _id: str
    name: str
    desc: str
    category: List[str] = field(default_factory=list)
    prevent: str = ""
    cause: str = ""
    symptom: List[str] = field(default_factory=list)
    yibao_status: str = ""
    get_prob: str = ""
    get_way: str = ""
    acompany: List[str] = field(default_factory=list)
    cure_department: List[str] = field(default_factory=list)
    cure_way: List[str] = field(default_factory=list)
    cure_lasttime: str = ""
    cured_prob: str = ""
    cost_money: str = ""
    check: List[str] = field(default_factory=list)
    recommand_drug: List[str] = field(default_factory=list)
    drug_detail: List[str] = field(default_factory=list)
    easy_get: str = ""
    common_drug: List[str] = field(default_factory=list)
    do_eat: List[str] = field(default_factory=list)
    not_eat: List[str] = field(default_factory=list)
    recommand_eat: List[str] = field(default_factory=list)

    def to_dict(self):
        res = {
            '疾病名称': self.name,
            '检测项目': self.check,
            '所属科室': self.category,
            '治疗科室': self.cure_department,
            # '疾病描述': self.desc,
            '预防方式': self.prevent,
            # '病因': self.cause,
            # '病征': self.symptom,
            '并发症': self.acompany,
            '治疗方法': self.cure_way,
            # '治疗时间': self.cure_lasttime,
            '推荐药物': self.recommand_drug,
            '忌口': self.not_eat,
            '推荐饮食': self.recommand_eat
        }
        return res


class KnowledgeGraph:
    """疾病数据库类，用于加载和查询疾病信息"""

    def __init__(self, data_path: str = os.path.join(Path(__file__).parent.parent.parent, "data/medical.json")):
        self.info: Dict[str, DiseaseInfo] = {}
        self.load_from_json(data_path)

    def load_from_json(self, file_path: str):
        """从JSON文件加载疾病数据"""
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    disease_data = json.loads(line)
                    # 处理_id字段
                    disease_id = disease_data['_id']['$oid'] if '$oid' in disease_data['_id'] else disease_data['_id']

                    # 创建DiseaseInfo对象
                    disease = DiseaseInfo(
                        _id=disease_id,
                        name=disease_data.get('name', ''),
                        desc=disease_data.get('desc', ''),
                        category=disease_data.get('category', []),
                        prevent=disease_data.get('prevent', ''),
                        cause=disease_data.get('cause', ''),
                        symptom=disease_data.get('symptom', []),
                        yibao_status=disease_data.get('yibao_status', ''),
                        get_prob=disease_data.get('get_prob', ''),
                        get_way=disease_data.get('get_way', ''),
                        acompany=disease_data.get('acompany', []),
                        cure_department=disease_data.get('cure_department', []),
                        cure_way=disease_data.get('cure_way', []),
                        cure_lasttime=disease_data.get('cure_lasttime', ''),
                        cured_prob=disease_data.get('cured_prob', ''),
                        cost_money=disease_data.get('cost_money', ''),
                        check=disease_data.get('check', []),
                        recommand_drug=disease_data.get('recommand_drug', []),
                        drug_detail=disease_data.get('drug_detail', []),
                        easy_get=disease_data.get('easy_get', ''),
                        common_drug=disease_data.get('common_drug', []),
                        do_eat=disease_data.get('do_eat', []),
                        not_eat=disease_data.get('not_eat', []),
                        recommand_eat=disease_data.get('recommand_eat', [])
                    )

                    # 添加到字典
                    self.info[disease.name] = disease

    def _fuzzy_search(self, query: str, threshold: int = 75) -> List[Dict]:
        """
        模糊搜索疾病名称
        :param query: 查询字符串
        :param threshold: 相似度阈值(0-100)
        :return: 包含匹配结果的列表，按相似度排序
        """
        results = []
        query = query.lower().strip()

        for name, disease in self.info.items():
            # 使用多种模糊匹配算法
            ratio = fuzz.ratio(query, name.lower())
            partial_ratio = fuzz.partial_ratio(query, name.lower())
            token_sort_ratio = fuzz.token_sort_ratio(query, name.lower())

            # 取最高分
            score = max(ratio, partial_ratio, token_sort_ratio)

            if score >= threshold:
                results.append({
                    'disease': name,
                    'match_score': score,
                })

        # 按相似度降序排序
        return sorted(results, key=lambda x: x['match_score'], reverse=True)

    def search_diseases(self, query_list: List[str], threshold: int = 90):
        """模糊搜索"""
        matches_diseases = set()
        for query in query_list:
            results = self._fuzzy_search(query, threshold)
            for result in results:
                if result['disease'] not in matches_diseases:
                    matches_diseases.add(result['disease'])
                    break
        return matches_diseases

    def search_precise(self, query_list: List[str]):
        """精确搜索"""
        matches_diseases = set()
        for query in query_list:
            if query in self.info:
                matches_diseases.add(self.info[query].name)

        return matches_diseases

    def symptom_disease_relation(self, diseases):
        """
        生成疾病-特征关系
        :param diseases: 疾病列表 ['D1', 'D2', ...]
        :return: 返回一个字典，形如
        {
            'D1': ['S1', 'S2', ...],
            'D2': ['S1', 'S3', ...],
            ...
        }
        """
        sd_dict = {}
        for d in diseases:
            tmp_info = self.info[d]
            sd_dict[tmp_info.name] = tmp_info.symptom
        return sd_dict

    def all_disease(self):
        """返回所有疾病"""
        return self.info.keys()


if __name__ == '__main__':
    kg = KnowledgeGraph()

    d = ['运动性晕厥', '低血糖', '中暑', '贫血', '体位性低血压', '过度换气综合征', '心肌缺血', '脑供血不足', '脱水',
         '心律失常']
    disease_precise = kg.search_precise(d)
    print(disease_precise)

    disease_fuzzy = kg.search_diseases(d, threshold=90)
    print(disease_fuzzy)
    # res = kg.symptom_disease_relation(disease_precise)
    # print(res)
