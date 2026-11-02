import os

import psycopg
from dotenv import load_dotenv


def main() -> None:
    load_dotenv()

    with psycopg.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        connect_timeout=5,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_user, current_database();")
            username, database = cursor.fetchone()

    print(f"Connected as: {username}")
    print(f"Database: {database}")


if __name__ == "__main__":
    main()