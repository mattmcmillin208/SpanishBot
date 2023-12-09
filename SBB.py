import sqlite3
import random

def create_table(cursor):
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY,
            category_name TEXT NOT NULL
        )
    ''')

    # Add the "Outdoors," "Drinks," and "Clothes" categories
    categories_to_add = ['Outdoors', 'Drinks', 'Clothes']
    for category_name in categories_to_add:
        cursor.execute('''
            INSERT OR IGNORE INTO categories (category_name)
            VALUES (?)
        ''', (category_name,))

    # Remove duplicate categories
    cursor.execute('''
        DELETE FROM categories
        WHERE category_id NOT IN (
            SELECT MIN(category_id)
            FROM categories
            GROUP BY category_name
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS words (
            word_id INTEGER PRIMARY KEY,
            user_id TEXT NOT NULL,
            word_in_spanish TEXT NOT NULL,
            english TEXT NOT NULL,
            category_id INTEGER,
            FOREIGN KEY (category_id) REFERENCES categories(category_id)
        )
    ''')

def add(cursor, user_id, word_in_spanish, english, category_id=None):
    cursor.execute('''
        INSERT INTO words (user_id, word_in_spanish, english, category_id)
        VALUES (?, ?, ?, ?)
    ''', (user_id, word_in_spanish, english, category_id))

def add_category(cursor, category_name):
    cursor.execute('''
        INSERT OR IGNORE INTO categories (category_name)
        VALUES (?)
    ''', (category_name,))

def view(cursor, user_id, category_id=None):
    if not category_id:
        print("\nCategories to choose from:")
        cursor.execute("SELECT * FROM categories")
        categories = cursor.fetchall()
        for cat_id, cat_name in categories:
            print(f"{cat_id}. {cat_name}")

        # Add the "Clothes" category to the options
        print(f"{len(categories) + 1}. Clothes")

        category_input = input("\nChoose a category (enter the number), 'all' to view all, or press Enter to go back: ")

        if category_input.lower() == 'all':
            # View all categories
            cursor.execute('''
                SELECT category_name, word_in_spanish, english
                FROM words
                JOIN categories ON words.category_id = categories.category_id
                WHERE user_id = ?
            ''', (user_id,))
        elif category_input.isdigit() and 1 <= int(category_input) <= len(categories) + 1:
            # View a specific category
            category_id = int(category_input)
            if category_id == len(categories) + 1:
                # View the "Clothes" category
                cursor.execute('''
                    SELECT word_in_spanish, english
                    FROM words
                    WHERE user_id = ? AND category_id = (
                        SELECT category_id FROM categories WHERE category_name = 'Clothes'
                    )
                ''', (user_id,))
            else:
                cursor.execute('''
                    SELECT word_in_spanish, english
                    FROM words
                    WHERE user_id = ? AND category_id = ?
                ''', (user_id, category_id))
        else:
            print("Invalid category selection.")
            return

    words = cursor.fetchall()

    print(f"\nYour Words:")
    for row in words:
        if category_input.lower() == 'all':
            category_name, word_in_spanish, english = row
            print(f"\nCategory: {category_name}")
        else:
            word_in_spanish, english = row

        print(f"\nSpanish: {word_in_spanish}")
        print(f"   English: {english}\n")

    print(f"Total Words: {len(words)}")

def quiz(cursor, user_id):
    cursor.execute('''
        SELECT word_in_spanish, english
        FROM words
        WHERE user_id = ?
    ''', (user_id,))

    words = cursor.fetchall()

    if not words:
        print("You don't have any words to quiz. Add some words first!")
        return

    random.shuffle(words)

    correct_answers = 0
    incorrect_answers = 0
    wrong_answers_list = []

    for word_in_spanish, english in words:
        print(f"\nWord in Spanish: {word_in_spanish}")
        user_answer = input(f"   English: ")
        if user_answer.lower() == english.lower():
            print("Correct!\n")
            correct_answers += 1
        else:
            print(f"Incorrect. The correct answer is {english}.\n")
            incorrect_answers += 1
            wrong_answers_list.append((word_in_spanish, english))

    print(f"\nQuiz Results:")
    print(f"Correct Answers: {correct_answers}")
    print(f"Incorrect Answers: {incorrect_answers}")

    view_wrong_answers = input("Do you want to view wrong answers? (yes/no): ")
    if view_wrong_answers.lower() == 'yes':
        print("\nWrong Answers:")
        for word_in_spanish, correct_answer in wrong_answers_list:
            print(f"\nWord in Spanish: {word_in_spanish}")
            print(f"   Correct Answer: {correct_answer}\n")

    retake_quiz = input("Do you want to retake the quiz with wrong answers? (yes/no): ")
    if retake_quiz.lower() == 'yes':
        quiz(cursor, user_id)

def main():
    conn = sqlite3.connect('language_bot.db')
    cursor = conn.cursor()

    create_table(cursor)

    users = {'matt': 'matt', 'user2': 'password2'}

    def authenticate_user():
        username = input("Enter your username: ")
        password = input("Enter your password: ")

        if username in users and users[username] == password:
            print("Authentication successful!")
            return username
        else:
            print("Authentication failed. Please try again.")
            return None

    authenticated_user = authenticate_user()

    if authenticated_user:
        while True:
            command = input("Enter a command (add, view, quiz): ")

            if command == 'add':
                word_in_spanish = input("Enter the word in Spanish: ")
                english = input("Enter the English translation: ")

                # Display categories for selection
                print("\nCategories to choose from:")
                cursor.execute("SELECT * FROM categories")
                categories = cursor.fetchall()
                for cat_id, cat_name in categories:
                    print(f"{cat_id}. {cat_name}")

                category_input = input("Choose a category (enter the number) or press Enter to skip: ")

                # Check if the entered category_input is valid
                valid_category = any(cat[0] == int(category_input) for cat in categories)
                while category_input and not valid_category:
                    print("Invalid category. Please choose a valid category.")
                    category_input = input("Choose a category (enter the number) or press Enter to skip: ")
                    valid_category = any(cat[0] == int(category_input) for cat in categories)

                add(cursor, authenticated_user, word_in_spanish, english, category_input)
                print("Word added successfully!")

            elif command == 'view':
                view(cursor, authenticated_user)

            elif command == 'quiz':
                quiz(cursor, authenticated_user)

            else:
                print("Invalid command. Try again.")

            # Commit changes after each command
            conn.commit()

        # Commit changes and close the connection before exiting
        conn.commit()
        conn.close()

if __name__ == "__main__":
    main()
