import csv
import json
import pymysql
from AIMGD.local_settings import DATABASES

from core.utils.knowledge_graph import KnowledgeGraph

connection = pymysql.connect(
    host='localhost',
    user='root',
    password=DATABASES['default']['PASSWORD'],
    database='aimgd'
)

cursor = connection.cursor()
kg = KnowledgeGraph()
all_disease = kg.all_disease()
sd_relation = kg.symptom_disease_relation(all_disease)
# sd_relation ={
#     'D1': ['S1', 'S2', 'S3'],
#     'D2': ['S4', 'S5', 'S6', 'S7', 'S8', 'S9', 'S10'],
#     'D3': ['S1', 'S2', 'S3'],
#     'D4': ['S1', 'S3', ...],
#     ...
# }
# 批量插入数据
sql = "INSERT INTO relation_disease_symptom (disease_name, symptom_list) VALUES (%s, %s)"

# 准备批量数据
batch_data = []
for disease_name, symptoms in sd_relation.items():
    # 确保症状列表是list类型，空列表也有效
    symptom_list = symptoms if isinstance(symptoms, list) else []
    batch_data.append((
        disease_name.strip(),
        json.dumps(symptom_list, ensure_ascii=False)
    ))

    # 执行批量插入
cursor.executemany(sql, batch_data)

connection.commit()
cursor.close()
connection.close()
