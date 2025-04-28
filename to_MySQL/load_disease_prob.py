# 创建数据表 disease_prob
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

data_path = '../data/disease_prob_processed.csv'
with open(data_path, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    for row in reader:
        cursor.execute(
            "INSERT INTO disease_prob (disease_name, probability) VALUES (%s, %s)",
            (row[0], float(row[1]))
        )

connection.commit()
cursor.close()
connection.close()
