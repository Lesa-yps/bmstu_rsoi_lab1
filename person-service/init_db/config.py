# параметры подключения к рабочей БД

import os

host = os.getenv("DB_HOST", "localhost")
user = os.getenv("DB_USER", "program")
password = os.getenv("DB_PASSWORD", "test")
port = int(os.getenv("DB_PORT", "5431"))
db_name = os.getenv("DB_NAME", "persons")