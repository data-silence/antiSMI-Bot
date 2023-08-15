import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DB_ASMI = os.getenv("DB_ASMI")
DB_TM = os.getenv("DB_TM")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")

TOKEN = os.getenv("TOKEN")

# main news databases
asmi = create_engine(
    f'postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_ASMI}', pool_pre_ping=True)
# archive database, contains news for more than 20 years
time_machine = create_engine(
    f'postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_TM}', pool_pre_ping=True)


class DataBaseMixin:
    """
    Contains a set of universal functions for working with databases
    Содержит набор универсальных функций для работы с базами данных
    """

    @staticmethod
    def get(query: str, engine) -> list[dict]:
        """
        db -> data as a list of dicts

        Accepts a query in the database and returns the result of its execution
        Принимает запрос в БД и возвращает результат его исполнения
        """
        with engine.begin() as conn:
            query_text = text(query)
            result_set = conn.execute(query_text)
            results_as_dict = result_set.mappings().all()
            return results_as_dict
