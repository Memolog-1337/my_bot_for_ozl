import sqlite3
import pandas as pd


def init_db():
    conn = sqlite3.connect("db.db")
    cursor = conn.cursor()
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS suppliers
        (id INTEGER PRIMARY KEY, 
        manufacturer TEXT NOT NULL,
        supplier TEXT NOT NULL,
        score INTEGER NOT NULL)"""
    )
    conn.commit()
    cursor.close()
    conn.close()


def add_row_to_db(manufacturers, suppliers):

    conn = sqlite3.connect("db.db")
    cursor = conn.cursor()

    for i in range(len(suppliers)):
        manufacturer = str(manufacturers[i])
        supplier = suppliers[i]
        manufacturer = manufacturer.lower()

        if ' ' in manufacturer:
            manufacturer = manufacturer.replace(' ', '')

        cursor.execute(
            """SELECT id, score FROM suppliers WHERE manufacturer = ? AND supplier = ?""",
            (manufacturer, supplier)
        )
        row = cursor.fetchone()

        if not row:
            cursor.execute(
                """INSERT INTO suppliers (manufacturer, supplier, score) VALUES(?, ?, ?);""",
                (manufacturer, supplier, 1)
            )

        else:
            cursor.execute(
                """UPDATE suppliers SET score = ? WHERE id = ?""",
                (row[1] + 1, row[0])
            )
        print(f'{manufacturer} is {supplier} DONE!')

    conn.commit()
    cursor.close()
    conn.close()


def get_data_from_db(manufacturer):
    manufacturer = manufacturer.lower()

    if ' ' in manufacturer:
        manufacturer = manufacturer.split()[0]

    conn = sqlite3.connect("db.db")
    cursor = conn.cursor()
    cursor.execute(
        f"""SELECT manufacturer, supplier, score FROM suppliers WHERE manufacturer LIKE '%{manufacturer}%' ORDER BY score DESC"""
    )
    rows = cursor.fetchall()

    result = ('*Производитель | Поставщик | Счет* \n'
              + '\n'.join(['| '.join(map(str, row)) for row in rows]))

    cursor.close()
    conn.close()
    return result


def main():
    init_db()

    with open('data.xlsx', 'rb') as input_excel:
        input_excel = pd.read_excel(
            input_excel,
            sheet_name='Sheet1'
        )

    suppliers = input_excel['Supplier']
    manufacturiers = input_excel['Manufacturer']

    add_row_to_db(manufacturiers, suppliers)

    print('Done!')


if __name__ == '__main__':
    main()
