# точка входа к работе с БД

from db_work import DB_Work


def main(name_db=None):
    db_work = DB_Work(name_db)
    user = -1
    print(f"Работа с БД {db_work.name_db}...\n")
    while user != 0:
        print(
            "Меню:\n"
            "1 - пересоздать БД;\n"
            "2 - очистить данные;\n"
            "0 - выйти."
        )
        try:
            user = int(input("Введите выбранный пункт меню: "))
        except Exception:
            user = -1
            print("Ошибка выбора. Повторите.\n")
            continue
        
        if user == 1:
            db_work.recreate_bd()
        elif user == 2:
            db_work.clean_data()
        elif user == 0:
            print("Завершение работы ^-^")
        else:
            user = -1
            print("Ошибка выбора. Повторите.\n")


if __name__ == "__main__":
    main()