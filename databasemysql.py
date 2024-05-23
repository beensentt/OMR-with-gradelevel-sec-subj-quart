import mysql.connector
import hashlib



# Constants
SALT = "PasswordSalt"  # Replace this with your actual salt value

# Function to fetch data from the database
def fetch_data(query):
    # Define database connection details
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '',  # Update with your password
        'database': 'omr'   # Update with your database name
    }
    
    try:
        # Connect to the database
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Execute the query
        cursor.execute(query)

        # Fetch all rows
        data = cursor.fetchall()

        # Close cursor and connection
        cursor.close()
        connection.close()

        return data
    except mysql.connector.Error as error:
        print("Error fetching data from MySQL database:", error)
        return None

# DATABASE CONNECTION
def connectToDb():
    host = "localhost"
    user = "root"
    dbPass = ""
    database = "omr"

    try:
        # Connect to the MySQL server
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=dbPass,
            database=database
        )

        if connection.is_connected():
            print("Connected to the MySQL database")
            return connection

    except mysql.connector.Error as err:
        print(f"Error connecting to the database: {err}")
        return None


# Establish connection to the first database
connection = connectToDb()


def fetch_data_from_database():
    try:
        # Connect to your MySQL database
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='omr'
        )

        # Create a cursor to execute SQL queries
        cursor = connection.cursor()

        # Execute a query to fetch data
        query = "SELECT answer_key FROM exam_operations"
        cursor.execute(query)

        # Fetch all rows from the result set
        data = cursor.fetchall()

        # Close cursor and connection
        cursor.close()
        connection.close()

        return data

    except mysql.connector.Error as error:
        print("Error fetching data from MySQL database:", error)
        return None



## USERS

def hash_password(password):
    salted_password = password + SALT
    hashed_password = hashlib.md5(salted_password.encode()).hexdigest()
    return hashed_password

def createUsersTable(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user(
                first_name TEXT,
                last_name TEXT,
                email TEXT NOT NULL,
                password TEXT
            )
        """)
        connection.commit()
        cursor.close()
    except mysql.connector.Error as err:
        print("Error:", err)
    else:
        return connection


def initializeUsersTable():
    connection = connectToDb()
    if connection:
        cursor = connection.cursor()
        createUsersTable(connection)
        return connection, cursor
    else:
        print("Failed to initialize user table.")
        return None, None


def register(first_name, last_name, email, password):
    con, cursor = initializeUsersTable()
    try:
        hashed_password = hash_password(password)
        cursor.execute("INSERT INTO user (first_name, last_name, email, password) VALUES (%s, %s, %s, %s)",
                       (first_name, last_name, email, hashed_password))
    except mysql.connector.Error as err:
        if err.errno == 1062:  # Check if the error is due to a duplicate key
            print("Error: Email already exists.")
        else:
            print("Error:", err)
        return False
    else:
        con.commit()
        con.close()
        return True


def login(email, password):
    con, cursor = initializeUsersTable()
    try:
        cursor.execute(
            "SELECT email, password FROM user WHERE email = %s", (email,))
        user = cursor.fetchone()
        if user and user[1] == hash_password(password):
            return True
        return False
    except mysql.connector.Error as err:
        print("Error:", err)
        return False
    finally:
        con.close()

def getUserByEmail(email):
    con, cursor = initializeUsersTable()
    try:
        cursor.execute("SELECT * FROM user WHERE email = %s", (email,))
        user = cursor.fetchone()
    except mysql.connector.Error as err:
        print("Error:", err)
        return None
    else:
        con.close()
        if not user:
            return None
        else:
            return user


def deleteUserByEmail(email):
    con, cursor = initializeUsersTable()
    try:
        cursor.execute("DELETE FROM user WHERE email = %s", (email,))
        con.commit()
    except mysql.connector.Error as err:
        print("Error:", err)
    finally:
        con.close()



## OPERATION

def createOperationsTable(connection):
    try:
        cursor = connection.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS exam_operations(exam_operations_id TEXT NOT NULL, email TEXT, answer_key TEXT, PRIMARY KEY (exam_operations_id(255)))")
        connection.commit()
        cursor.close()
        print("Operations table created successfully")
    except mysql.connector.Error as err:
        print("Error creating operations table:", err)
    else:
        return connection


def initializeOperationsTable():
    connection = connectToDb()
    if connection:
        cursor = connection.cursor()
        createOperationsTable(connection)
        return connection, cursor
    else:
        print("Failed to initialize exam_operations table.")
        return None, None


def getOperationsByEmail(email):
    con, cursor = initializeOperationsTable()
    try:
        cursor.execute("SELECT * FROM exam_operations WHERE email = %s", (email,))
        operations = cursor.fetchall()
    except mysql.connector.Error as err:
        print("Error:", err)
        return None
    else:
        con.close()
        if not operations:
            return None
        else:
            operations.reverse()
            return operations



def addOperation(exam_operations_id, email, answer_key):
    con, cursor = initializeOperationsTable()
    exam_operations_id = exam_operations_id.split('uploads/')[1]
    try:
        cursor.execute("INSERT INTO exam_operations (exam_operations_id, email, answer_key) VALUES (%s, %s, %s)",
                       (exam_operations_id, email, answer_key))
        con.commit()
    except mysql.connector.Error as err:
        if err.errno == 1062:  # Check if the error is due to a duplicate key
            print("Error: ID already exists.")
        else:
            print("Error:", err)
        return False
    finally: 
        con.close()
        return True



def getOperationById(exam_id):
    con, cursor = initializeOperationsTable()
    try:
        cursor.execute("SELECT * FROM exam_operations WHERE exam_id = %s", (exam_id,))
        record = cursor.fetchone()
    except mysql.connector.Error as err:
        print("Error:", err)
        return None
    else:
        con.close()
        if not record:
            return None
        else:
            return record


def deleteOperation(exam_id):
    con, cursor = initializeOperationsTable()
    try:
        cursor.execute("DELETE FROM exam_operations WHERE exam_id = %s", (exam_id,))
        con.commit()
    except mysql.connector.Error as err:
        print("Error:", err)
        return False
    finally:
        con.close()
        return True


##  RECORDS

def createRecordsTable(connection):
    try:
        cursor = connection.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS exam_records(exam_id TEXT, correct_answer INT, wrong_answer INT, empty_asnwer INT, score DOUBLE, answers TEXT, image TEXT)")
        connection.commit()
        cursor.close()
    except mysql.connector.Error as err:
        print("Error:", err)
    else:
        return connection


def initializeRecordsTable():
    connection = connectToDb()
    if connection:
        cursor = connection.cursor()
        createRecordsTable(connection)
        return connection, cursor
    else:
        print("Failed to initialize records table.")
        return None, None


def getRecordsById(exam_id):
    con, cursor = initializeRecordsTable()
    try:
        cursor.execute("SELECT * FROM exam_records WHERE exam_id = %s", (exam_id,))
        exam_records = cursor.fetchall()
    except mysql.connector.Error as err:
        print("Error:", err)
        return None
    else:
        con.close()
        if not exam_records:
            return None
        else:
            return exam_records

def addRecord(exam_id, exam_records_id, correct_answer, wrong_answer, empty_answer, score, answer, image):
    con, cursor = initializeRecordsTable()
    exam_id = exam_id.split('uploads/')[1]
    try:
        cursor.execute("INSERT INTO exam_records (exam_id, exam_records_id, correct_answer, wrong_answer, empty_answer, score, answer, image) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                       (exam_id, exam_records_id, correct_answer, wrong_answer, empty_answer, score, answer, image))
        con.commit()
    except mysql.connector.Error as err:
        print("Error:", err)
        return False
    else:
        con.close()
        return True


def delete_table():
    try:
        # Connect to the database
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='omr'
        )

        # Create a cursor object to execute SQL queries
        cursor = connection.cursor()

        # Check if the table exists
        cursor.execute("SHOW TABLES LIKE 'exam_records'")
        table_exists = cursor.fetchone()

        if table_exists:
            # Define the SQL query to drop the table
            drop_query = "DROP TABLE IF EXISTS exam_records"

            # Execute the SQL query to drop the table
            cursor.execute(drop_query)

            # Commit the changes to the database
            connection.commit()

            print("Table 'exam_records' deleted successfully.")
            return True
        else:
            print("Table 'exam_records' does not exist.")
            return False
    except mysql.connector.Error as error:
        print("Error deleting table from the database:", error)
        return False
    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()



# Function to add operation
def addOperation(exam_operations_id, email, answer_key):
    con, cursor = initializeOperationsTable()
    exam_operations_id = exam_operations_id.split('uploads/')[1]
    try:
        cursor.execute("INSERT INTO exam_operations (exam_operations_id, email, answer_key) VALUES (%s, %s, %s)",
                       (exam_operations_id, email, answer_key))
        con.commit()
    except mysql.connector.Error as err:
        if err.errno == 1062:  # Check if the error is due to a duplicate key
            print("Error: ID already exists.")
        else:
            print("Error:", err)
        return False
    finally: 
        con.close()



# Example usage:

# if connection:
#     # Do something with the connection
#     pass
# else:
#     print("Failed to connect to the database.")
