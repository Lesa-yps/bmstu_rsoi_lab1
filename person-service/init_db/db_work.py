# класс для работы с БД (psycopg2)

import os
import logging
import psycopg2
from psycopg2 import sql, errors

import init_db.config as conf

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILENAME = os.path.join(BASE_DIR, "db_person.log")


class DB_Work:

    def __init__(self, name_db=None):
        self.__connection = None
        self.__cursor = None
        # настройка логгирования
        self._setup_logging()
        self.logger = logging.getLogger("DB_Work")
        self.name_db = name_db if name_db else conf.db_name
        # подключение к БД
        self.connect_to_db()


    # подключение к БД
    def connect_to_db(self):
        try:
            self.logger.info("Попытка подключения к PostgreSQL...")

            # подключение к рабочей БД
            self.__connection = psycopg2.connect(
                host=conf.host,
                user=conf.user,
                port=conf.port,
                password=conf.password,
                database=self.name_db,
            )
            self.__connection.autocommit = True
            self.__cursor = self.__connection.cursor()

            self.logger.info("Успешно начата работа с PostgreSQL. БД готова к работе.")

        except Exception as exc:
            self.__connection = None
            self.logger.error(f"Ошибка подключения: {exc}", exc_info=True)


    # настройка системы логгирования
    def _setup_logging(self):
        logging.basicConfig(
            level=logging.ERROR,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(LOG_FILENAME)],
        )


    # ---------- низкоуровневые операции ----------

    # выполнение sql запроса
    def __execute__(self, sql_query, params=None):
        try:
            self.__cursor.execute(sql_query, params)
        except errors.ForeignKeyViolation as e:
            raise RuntimeError("Неверная ссылка на связанные данные") from e
        except psycopg2.OperationalError as e:
            raise RuntimeError("База данных недоступна") from e


    # выполнение sql запроса из файла
    def execute_sql_file(self, sql_filename):
        file_path = os.path.join(BASE_DIR, os.path.basename(sql_filename))
        with open(file_path, "r", encoding="utf-8") as f:
            sql_query = f.read()
        self.__execute__(sql_query)


    # выполнение sql запроса (как переданной строки)
    def execute_sql_query(self, sql_query, params=None):
        self.__execute__(sql_query, params)


    # возвращает все строки результата запроса
    def fetch_all(self):
        return self.__cursor.fetchall()


    # возвращает одну строку результата запроса
    def fetch_one(self):
        return self.__cursor.fetchone()


    # ---------- транзакции ----------

    # начало новой транзакции
    def begin_transaction(self):
        if self.__connection:
            self.__connection.autocommit = False
            self.logger.info("Начало транзакции")


    # подтверждение текущей транзакции
    def commit(self):
        if self.__connection:
            self.__connection.commit()
            self.__connection.autocommit = True
            self.logger.info("Транзакция завершена")


    # откат текущей транзакции
    def rollback(self):
        if self.__connection:
            self.__connection.rollback()
            self.__connection.autocommit = True
            self.logger.warning("Транзакция отменена")


    # ---------- безопасное выполнение запросов ----------

    # безопасное выполнение запроса как строки (с откатом, если что)
    def execute_sql_query_safe(self, sql_query, params=None, isRaise=False):
        try:
            self.execute_sql_query(sql_query, params)
        except Exception as exc:
            self.__connection.rollback()
            if isRaise:
                raise exc


    # безопасное выполнение запроса из файла (с откатом, если что)
    def execute_sql_file_save(self, sql_filename, isRaise=False):
        try:
            self.execute_sql_file(sql_filename)
            self.logger.info("Запрос успешно выполнен")
        except Exception as exc:
            self.__connection.rollback()
            self.logger.error(f"Ошибка выполнения запроса: {exc}", exc_info=True)
            if isRaise:
                raise exc


    # ---------- сервисные ----------

    # пересоздание БД
    def recreate_bd(self,
                    create_filename="init_db/create.sql",
                    drop_all_from_db_filename="init_db/drop_all_from_db.sql"):
        self.execute_sql_file_save(drop_all_from_db_filename)
        self.execute_sql_file_save(create_filename)


    # очистка БД (без удаления)
    def clean_data(self, filename="init_db/clean_data.sql"):
        self.execute_sql_file_save(filename)


    # закрытие подключения к БД
    def close(self):
        if self.__cursor:
            self.__cursor.close()
        if self.__connection:
            self.__connection.close()


    # переподключение к БД
    def reset_connection(self):
        self.close()
        self.connect_to_db()


    # деструктор класса (с безопасным закрытием всех соединений)
    def __del__(self):
        if hasattr(self, "_DB_Work__connection") and self.__connection:
            if hasattr(self, "_DB_Work__cursor") and self.__cursor:
                self.__cursor.close()
            self.__connection.close()
            self.logger.info("PostgreSQL соединение закрыто.")