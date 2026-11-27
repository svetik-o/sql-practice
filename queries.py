import sqlite3

with sqlite3.connect("univercity.db") as conn:
    cursor=conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    # Включаем поддержку внешних ключей в SQLite
    cursor.execute("DROP TABLE IF EXISTS marks;")
    cursor.execute("DROP TABLE IF EXISTS enrollments;")# Удаляем старые таблицы, если они остались от прошлых заданий (сначала удаляем зависимую таблицу enrollments, затем основные)
    cursor.execute("DROP TABLE IF EXISTS students;")
    cursor.execute("DROP TABLE IF EXISTS courses;")

    cursor.execute("""CREATE TABLE students (id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL, email TEXT UNIQUE NOT NULL)""")# 1. Таблица студентов
    cursor.execute(""" CREATE TABLE courses (id INTEGER PRIMARY KEY AUTOINCREMENT,
               title TEXT NOT NULL, hours INTEGER NOT NULL) """)# 2. Таблица курсов

    cursor.execute("""CREATE TABLE enrollments (id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL, course_id INTEGER NOT NULL,
                enrolled_at TEXT NOT NULL, FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE)""")# 3. Таблица записей на курсы (связывает students и courses)
    print("Tables created successfully")

    students = [("Иван Петров", "ivan@example.com"),("Анна Смирнова", "anna@example.com"),
        ("Дмитрий Козлов", "dmitry@example.com"),]# 4. Заполняем таблицу студентов
    cursor.executemany("INSERT INTO students (name, email) VALUES (?, ?)",   students)

    courses = [("Python для начинающих", 40),("Базы данных и SQL", 32),
    ("Веб-разработка", 56),]# 5. Заполняем таблицу курсов (учитываем ваш столбец hours)
    cursor.executemany("INSERT INTO courses (title, hours) VALUES (?, ?)", courses)

    enrollments = [(1, 1, "2026-09-01"),  # Иван -> Python
                   (1, 2, "2026-09-05"),  # Иван -> SQL  (2, 2, "2026-09-02"),  # Анна -> SQL
        (3, 3, "2026-09-03"),]  # Дмитрий -> Веб-разработка# 6. Заполняем связующую таблицу enrollments (учитываем ваш столбец enrolled_at)
    cursor.executemany("INSERT INTO enrollments (student_id, course_id, enrolled_at) VALUES (?, ?, ?)",  enrollments)

    print("\nСписок зачислений на курсы:")# 7. Выполняем запрос с JOIN, объединяющий все три таблицы
    cursor.execute("""  SELECT   students.name,  students.email,
            courses.title,  courses.hours,  enrollments.enrolled_at
        FROM enrollments
        INNER JOIN students ON enrollments.student_id = students.id
        INNER JOIN courses ON enrollments.course_id = courses.id
        ORDER BY students.name ASC""")


    for name, email, title, hours, enrolled_at in cursor.fetchall():
        print(f"Ученик: {name} ({email}) | Курс: «{title}» ({hours} ч.) | Дата: {enrolled_at}")

    cursor.execute(""" CREATE INDEX IF NOT EXISTS idx_enrollments_student_id
        ON enrollments (student_id); """)# 8. Создаём индекс для внешнего ключа student_id в таблице enrollments
    # (SQLite не создаёт индексы для FOREIGN KEY автоматически, в отличие от PRIMARY KEY)

    cursor.execute(""" CREATE INDEX IF NOT EXISTS idx_students_name
        ON students (name); """)# Дополнительно можно создать индекс для поиска студентов по имени

    conn.commit()
    print("\nИндексы успешно созданы!")

    # Пример запроса, который теперь работает быстрее благодаря индексу idx_enrollments_student_id
    cursor.execute("""
        SELECT courses.title, enrollments.enrolled_at
        FROM enrollments
        INNER JOIN courses ON enrollments.course_id = courses.id
        WHERE enrollments.student_id = ?
    """, (1,))

    print("Курсы студента с ID = 1:", cursor.fetchall())

    cursor.execute("""CREATE TABLE IF NOT EXISTS marks (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL, course_id INTEGER NOT NULL,
                    score INTEGER NOT NULL CHECK(score BETWEEN 1 AND 5),
                    FOREIGN KEY (student_id) REFERENCES students (id),
                    FOREIGN KEY (course_id) REFERENCES courses (id))""")  # 3. Таблица записей на курсы (связывает students и courses)
    print("Table created successfully")

    # 2. Заполняем таблицу тестовыми оценками
    # (Убедитесь, что student_id 1, 2, 3 и course_id 1, 2 есть в ваших таблицах)
    sample_marks = [
        (1, 1, 5), (1, 1, 4), (1, 2, 5),  # Ученик 1
        (2, 1, 3), (2, 2, 4),  # Ученик 2
        (3, 1, 5), (3, 2, 5), (3, 2, 5)]# Ученик 3
    cursor.executemany("""INSERT INTO marks(student_id,course_id,score )VALUES(?,?,?)""",sample_marks )
    conn.commit()
    # 3. Выполняем все 5 запросов из задания
    # COUNT: Сколько всего оценок выставлено в базе?
    cursor.execute("SELECT COUNT(*) AS total_marks FROM marks")#(всего оценок)
    print("1. Всего оценок в базе:", cursor.fetchone()[0])

    # SUM: Какова сумма всех набранных баллов по всем предметам?
    cursor.execute("SELECT SUM(score) AS total_points FROM marks")#(всего баллов)
    print("2. Сумма всех баллов:", cursor.fetchone()[0])

    # AVG: Какой средний балл по всей школе?
    cursor.execute(
        "SELECT ROUND(AVG(score), 2) AS school_avg_score FROM marks")#(вшкольный средний балл)
    print("3. Средний балл по всем оценкам:", cursor.fetchone()[0])

    # GROUP BY: Сколько оценок и какой средний балл у каждого ученика?
    print("\n4. Статистика по каждому ученику (GROUP BY):")
    cursor.execute("""
        SELECT students.name, COUNT(marks.score) AS marks_count,
        ROUND(AVG(marks.score), 2) AS avg_score
        FROM marks
        INNER JOIN students ON marks.student_id = students.id
        GROUP BY students.id
    """)#(student_name (имя ученика), marks_count (количество оценок), avg_score (средний балл)
    for name, count, avg_score in cursor.fetchall():
        print(
            f"   Ученик: {name} | Оценок: {count} | Средний балл: {avg_score}")

    # HAVING: У каких учеников средний балл выше 4.5 (отличники)?
    print("\n5. Ученики со средним баллом выше 4.5 (HAVING):")
    cursor.execute("""
        SELECT students.name, ROUND(AVG(marks.score), 2) AS high_avg_score 
        FROM marks
        INNER JOIN students ON marks.student_id = students.id
        GROUP BY students.id
        HAVING AVG(marks.score) > 4.5
    """)#(высокий средний балл)
    for name, high_avg in cursor.fetchall():
        print(f"   Отличник: {name} | Средний балл: {high_avg}")
    conn.commit()

# Создайте учебный репозиторий и отдельную ветку для изменения.
# Оформите pull request, исправьте замечание и объедините ветку без потери истории.
# Решение ещё не отправлено.