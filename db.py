import aiosqlite

DATABASE = "service_rentals.db"

# Инициализация базы данных
async def init_db():
    async with aiosqlite.connect(DATABASE) as db:
        # Создание таблицы помещений
        await db.execute("""
            CREATE TABLE IF NOT EXISTS premises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                price REAL NOT NULL,
                availability TEXT NOT NULL
            )
        """)
        # Создание таблицы бронирования
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER,
                slot TEXT,
                FOREIGN KEY (tenant_id) REFERENCES users (id)
            )
        """)
        await db.commit()

# Функция для получения подключения к базе данных
async def get_db():
    return await aiosqlite.connect(DATABASE)