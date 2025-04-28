# 创建数据表 symptom_prob
import csv
import pymysql
from AIMGD.local_settings import DATABASES

connection = pymysql.connect(
    host='localhost',
    user='root',
    password=DATABASES['default']['PASSWORD'],
    database='aimgd'
)

cursor = connection.cursor()

data_path = '../data/symptom_prob_processed.csv'
with open(data_path, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    for row in reader:
        cursor.execute(
            "INSERT INTO symptom_prob (symptom_name, probability) VALUES (%s, %s)",
            (row[0], float(row[1]))
        )

connection.commit()
cursor.close()
connection.close()
