import os
import logging

import psycopg2
import psycopg2.extensions
from pymongo import MongoClient
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, Float, MetaData, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Задание по Psycopg2
# Необходимо с помощью Psycorg выполнить создание таблицы movies_top c помощью конструкции
# SELECT *  INTO movies_top FROM (ЗАПРОС);
#Где ЗАПРОС имеет следующий вид:

    #три поля: movieId (id фильма), ratings_num(число рейтингов), ratings_avg (средний рейтинг фильма)
    #В выборку должны попасть только фильмы, у которых средний рейтинг выше 3.


logger.info("Создаём подключёние к Postgres")
params = {
    "host": os.environ['APP_POSTGRES_HOST'],
    "port": os.environ['APP_POSTGRES_PORT'],
    "user": 'postgres'
}
conn = psycopg2.connect(**params)

# дополнительные настройки
psycopg2.extensions.register_type(
    psycopg2.extensions.UNICODE,
    conn
)
conn.set_isolation_level(
    psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT
)
cursor = conn.cursor()

# ВАШ КОД ЗДЕСЬ
user_item_query_config = {"MAX_ROW_NUMBER": 100000}

sql_str = (
	    """
	    WITH tmp_table
        AS (
	       SELECT
             movieid,
             AVG(rating) as ratings_avg, COUNT(rating) as ratings_num
           FROM ratings
           GROUP BY movieid
           HAVING AVG(rating) > 3 ORDER BY COUNT(rating) DESC)
              SELECT *  INTO movies_top FROM tmp_table
              LIMIT %(MAX_ROW_NUMBER)d
        """ % user_item_query_config
)
# таблица movies_top
# movieId (id фильма), ratings_num(число рейтингов), ratings_avg (средний рейтинг фильма)

cursor.execute(sql_str)
conn.commit()

# Проверка - выгружаем данные
cursor.execute("SELECT * FROM movies_top LIMIT 10")
logger.info(
    "Выгружаем данные из таблицы movies_top: (movieId, ratings_num, ratings_avg)\n{}".format(
        [i for i in cursor.fetchall()])
)

#2.1) выберите контент у которого больше 15 оценок (используйте filter)

#2.2) средний рейтинг больше 3.5 (filter ещё раз)

#2.3) отсортировать по среднему рейтингу (используйте order_by())

#id этих фильмов сохраняем в массив top_rated_content_ids

sql_str_2 = (
	"""
WITH tmp_table AS(SELECT movieid, ratings_avg, ratings_num FROM movies_top WHERE ratings_num>15 AND ratings_avg>3.5
ORDER BY ratings_avg DESC limit 5) SELECT *  INTO top_rated_content_ids FROM (
    SELECT array_agg(movieid) as movieid FROM tmp_table) as sample;
    """
)

cursor.execute(sql_str_2)
conn.commit()
# Проверка - выгружаем данные

cursor.execute("SELECT * FROM top_rated_content_ids")
logger.info(
    "Выгружаем movieid из таблицы top_rated_content_ids: \n{}".format(
        [i for i in cursor.fetchall()])
)


#Pymongo

#Нужно подключиться к Pymongo и выгрузить список тегов для списка популярного контента, полученный на предыдущем шаге.

#В выборку должны попать теги фильмов из массива top_rated_content_ids и модификатор $in.

mongo = MongoClient(**{
    'host': os.environ['APP_MONGO_HOST'],
    'port': int(os.environ['APP_MONGO_PORT'])
})

# Получите доступ к коллекции tags
db = mongo["movie"]
tags_collection = db['tags']

# id контента используйте для фильтрации - передайте его в модификатор $in внутри find
# в выборку должны попать теги фильмов из массива top_rated_content_ids
mongo_query = tags_collection.find(
        { 'movieId': { "$in": ["159817", "2937", "38304", "2330", "318"] } }
)
mongo_docs = [
    i for i in mongo_query
]

print("Достали документы из Mongo: {}".format(mongo_docs[:5]))

id_tags = [(i['id'], i['name']) for i in mongo_docs]




# Задание по Pandas
#Из списка выгруженных тегов составим Pandas DataFrame.

#4.1 Сгруппируйте по названию тега с помощью group_by

#4.2 Для каждого тега вычислите, в каком количестве фильмов он встречается

#4.3 Оставьте top-5 самых популярных тегов
# Постройте таблицу их тегов и определите top-5 самых популярных

# формируем DataFrame
tags_df = pd.DataFrame(id_tags, columns=['movieid', 'tags'])

# --------------------------------------------------------------
# Ваш код здесь
filtered_tags = tags_df.groupby('tags')[['movieid']].count().sort_values('movieid', ascending = False)
top_5_tags = filtered_tags.head(5)

print(top_5_tags)

logger.info("Домашка выполнена!")