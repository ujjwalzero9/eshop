import psycopg2
from psycopg2 import OperationalError

def check_postgres_connection():
    try:

        print("strating connection")
        conn = psycopg2.connect(
            dbname="postgres",
            user="eshop_admin",
            password="av6SiWVNMjPYzj5QGfuC",
            host="eshop-postgres.cpim68m449v4.eu-north-1.rds.amazonaws.com",
            port="5432"
        )
        print("✅ Connected successfully to PostgreSQL RDS!")
        conn.close()
    except OperationalError as e:
        print("❌ Failed to connect:")
        print(e)

check_postgres_connection()
