from datetime import datetime
import mysql.connector
import pymysql
# import database as db
import databasemysql as dbmysql 
from wtforms import Form, StringField, PasswordField, validators
import omr
from flask_fontawesome import FontAwesome
import shutil
import time
from werkzeug.utils import secure_filename
import os
import pandas as pd
from flask import jsonify
import mysql.connector as db_mysql
from flask import request
import base64

from flask import render_template
import json
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


from flask import (
    Flask,
    session,
    flash,
    request,
    redirect,
    render_template,
    url_for
)


app = Flask(__name__)
fa = FontAwesome(app)

app.secret_key = "secret_key"
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
ANSWER_LETTERS = {0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: 'E', 5: '-', 6: 'X'}

# CLASSES


class RegistrationForm(Form):
    name = StringField('Name', [validators.Length(min=2, max=35)])
    surname = StringField('Surname', [validators.Length(min=2, max=35)])
    email = StringField('Email', [validators.Length(min=6, max=100)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo(
            'password', message='The passwords you entered do not match!')
    ])
    confirm = PasswordField('Re-enter the password')


class LoginForm(Form):
    email = StringField('Email', [validators.Length(min=6, max=100)])
    password = PasswordField('Password', [validators.DataRequired()])

# FUNCTIONS


#function for item analysis

def item_analysis(response_df):
    # Example item analysis, replace this with your actual item analysis code
    item_difficulty = response_df.mean(axis=0)
    item_discrimination = response_df.corrwith(response_df['Total_Score'])
    
    
    # print("Item Difficulty:", item_difficulty)
    # print("Item Discrimination:", item_discrimination)
    return item_difficulty, item_discrimination
#end of function





def createUploadDirectory():
    path = os.getcwd()
    UPLOAD_FOLDER = os.path.join(
        path, 'static/uploads/') + str(int(time.time()))
    if not os.path.isdir(UPLOAD_FOLDER):
        os.mkdir(UPLOAD_FOLDER)
    session['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def deleteUploadDirectory():
    if 'UPLOAD_FOLDER' in session:
        # print("Deleting directory: " + session['UPLOAD_FOLDER'])
        if os.path.isdir(session['UPLOAD_FOLDER']):
            shutil.rmtree(session['UPLOAD_FOLDER'])
        session['UPLOAD_FOLDER'] = ''
    if 'SCORES' in session:
        session['SCORES'] = ''


def allowed_file(filename):
    return '.' in filename and filename.rsplit(
        '.', 1)[1].lower() in ALLOWED_EXTENSIONS


def isLoggedIn():
    if 'login' in session:
        return session['login']
    else:
        return False


def getUser():
    temp = session['user']
    user = {
        "first_name": temp[2],  # Change "name" to "first_name"
        "last_name": temp[1],   # Change "surname" to "last_name"
        "email": temp[6],
        "password": temp[7]
    }
    return user


# RENDER TEMPLATES

@app.route('/api/score-analytics-v2')
def score_analytics_v2():
    try:
        # Modify the SQL query to select data from the specific table
        query = "SELECT  exam_records_id, correct_answer  FROM exam_records"
        
        # Fetch data from the database using dbmysql module
        data = dbmysql.fetch_data(query)

        # Process the fetched data to prepare for visualization
        labels = []
        data_points = []

        for row in data:
            labels.append(row[0])  # Assuming the first column contains labels
            data_points.append(row[1])  # Assuming the second column contains data points

        chart_data = {
            'labels': labels,
            'data': data_points
        }

        return jsonify(chart_data)

    except Exception as error:
        print("Error fetching score analytics data:", error)
        return jsonify({'error': 'Failed to fetch grade analytics data'})


@app.route('/api/examinees-analytics-v2')
def examinees_analytics_v2():
    try:
        # Modify the SQL query to count the number of IDs in the records table
        query = "SELECT COUNT(exam_id) FROM exam_records"
        
        # Fetch data from the database using dbmysql module
        data = dbmysql.fetch_data(query)

        # Process the fetched data to prepare for visualization
        number_of_examinees = data[0][0]  # Extract the count from the first row of the first column

        chart_data = {
            'number_of_examinees': number_of_examinees,
        }

        return jsonify(chart_data)

    except Exception as error:
        print("Error fetching examinees analytics data:", error)
        return jsonify({'error': 'Failed to fetch examinees analytics data'})

#DELETE ANALYTICS
        # In your Flask app
# In your Flask app

@app.route('/api/delete-score-analytics', methods=['POST'])
def delete_score_analytics():
    try:
        # Perform deletion of the entire table from the database
        # Adjust the query according to your database schema
        dbmysql.execute("DROP TABLE exam_records")
        
        return jsonify({'success': True})
    except Exception as error:
        return jsonify({'error': str(error)}), 500




@app.route('/api/status-analytics-v2')
def status_analytics_v2():
    try:
        # Modify the SQL query to count the number of examinees who passed the test (score >= 50%)
        passed_query = "SELECT COUNT(exam_records_id) FROM exam_records WHERE correct_answer >= 10"

        # Fetch data from the database for passed examinees
        passed_data = dbmysql.fetch_data(passed_query)

        # Extract the count of passed examinees
        passed_count = passed_data[0][0] if passed_data else 0

        # Modify the SQL query to count the number of examinees who failed the test (score < 50%)
        failed_query = "SELECT COUNT(exam_records_id) FROM exam_records WHERE correct_answer < 10"

        # Fetch data from the database for failed examinees
        failed_data = dbmysql.fetch_data(failed_query)

        # Extract the count of failed examinees
        failed_count = failed_data[0][0] if failed_data else 0

        # Prepare data to be returned as JSON
        chart_data = {
            'passed': passed_count,
            'failed': failed_count
        }

        return jsonify(chart_data)

    except Exception as error:
        print("Error fetching examinees analytics data:", error)
        return jsonify({'error': 'Failed to fetch examinees analytics data'})





@app.route('/register', methods=['GET', 'POST'])
@app.route('/register/', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        user = (form.name.data, form.surname.data, form.email.data,
                form.password.data)
        if dbmysql.register(user[0], user[1], user[2], user[3]):
            flash('Registration successful, you can log in', 'success')
            # print("Registration successful")
            return redirect(url_for('login'), code=302)
        flash(
            'Registration could not be completed, because you have not registered with the same password \
                ',
            'error')
    return render_template(
        'register.html', form=form, page='register', login=isLoggedIn())


@app.route('/login', methods=['GET', 'POST'])
@app.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        user = (form.email.data, form.password.data)
        if dbmysql.login(user[0], user[1]):
            session['login'] = True
            session['user'] = dbmysql.getUserByEmail(user[0])
            flash('You have successfully logged in.', 'success')
            return redirect('/')
        flash('Login failed, please check your email and password!', 'error')
    return                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                render_template(
        'login.html', form=form, page='login', login=isLoggedIn())


@app.route('/')
def run():
    session.pop('_flashes', None)
    if 'UPLOAD_FOLDER' in session:
        deleteUploadDirectory()
        session.pop('UPLOAD_FOLDER', None)
    return render_template('index.html', page='index', login=isLoggedIn())


@app.route('/usage')
def usage():
    deleteUploadDirectory()
    session.pop('_flashes', None)
    return render_template('usage.html', page='usage', login=isLoggedIn())


@app.route('/uploadAnswerKey')
def upload_answer():
    if isLoggedIn():
        deleteUploadDirectory()
        createUploadDirectory()
        return render_template('uploadAnswerKey.html', login=isLoggedIn())
    else:
        flash('You must log in to perform this operation!', 'error')
        return redirect(url_for('login'))

@app.route('/completed')
def completed():
    if isLoggedIn():
        # Retrieve the DataFrame with response data (replace this with your actual data retrieval logic)
        response_data = {
            'Item1': [1, 0, 1, 1, 0],
            'Item2': [0, 1, 1, 0, 1],
            'Total_Score': [2, 1, 2, 2, 1]
        }
        response_df = pd.DataFrame(response_data)

        # Perform item analysis
        item_difficulty, item_discrimination = item_analysis(response_df)

        # Calculate total wrong answers
        total_wrong_answers = {}
        for i in range(len(session['ANSWERS_STR'])):
            item_number = i + 1
            count = 0
            for key, value in session['SCORES'].items():
                if value[0][i] != session['ANSWERS_STR'][i]:
                    count += 1
            total_wrong_answers[item_number] = count

        # Calculate total correct answers
        total_correct_answers = {}
        for i in range(len(session['ANSWERS_STR'])):
            item_number = i + 1
            count = 0
            for key, value in session['SCORES'].items():
                if value[0][i] == session['ANSWERS_STR'][i]:
                    count += 1
            total_correct_answers[item_number] = count

        return render_template(
            'completed.html',
            scores=session['SCORES'],
            answer_key=session['ANSWERS_STR'],
            login=isLoggedIn(),
            item_difficulty=item_difficulty,
            item_discrimination=item_discrimination,
            total_wrong_answers=total_wrong_answers,
            total_correct_answers=total_correct_answers,
            total_papers=len(session['SCORES'])  # Ensure total_papers is passed as well
        )
    else:
        flash('You must log in to perform this operation!', 'error')
        return redirect(url_for('login'))


@app.route('/uploadPapers')
def upload_form():
    if isLoggedIn():
        return render_template('uploadPapers.html',
                               answer_key=session['ANSWERS_STR'],
                               login=isLoggedIn())
    else:
        flash('You must log in to perform this operation!', 'error')
        return redirect(url_for('login'))


@app.route('/account')
@app.route('/account/')
def account():
    if isLoggedIn():
        session.pop('_flashes', None)
        exam_operations = list()
        temp = dbmysql.getOperationsByEmail(getUser()["email"])
        if temp is not None:
            exam_operations = list(temp)
            for ind, op in enumerate(exam_operations):
                exam_operations[ind] = list(op)
                exam_operations[ind].append(datetime.fromtimestamp(
                    int(op[0])))
                exam_records = dbmysql.getRecordsById(op[0])
                if exam_records is not None:
                    exam_operations[ind].append(len(exam_records))
                else:
                    exam_operations[ind].append(0)  # or any default value if no records found
        return render_template(
            'account.html', user=getUser(),
            exam_operations=exam_operations, page='account', login=isLoggedIn())
    else:
        flash('You must log in to perform this operation!', 'error')
        return redirect(url_for('login'))



@app.route('/detail')
def detail():
    if isLoggedIn():
        session.pop('_flashes', None)
        exam_id = request.args.get('exam_id')
        answer_key = dbmysql.getOperationById(exam_id)[1]
        exam_records = list()
        temp = dbmysql.getRecordsById(id)
        if temp is not None:
            exam_records = list(temp)
        return render_template(
            'detail.html', user=getUser(),
            exam_records=exam_records, answer_key=answer_key, page='detail',
            login=isLoggedIn())
    else:
        flash('You must log in to perform this operation!!', 'error')
        return redirect(url_for('login'))

# REDIRECTS


@app.route('/logout', methods=['GET', 'POST'])
@app.route('/logout/', methods=['GET', 'POST'])
def logout():
    if 'login' in session:
        session.pop('login', None)
    if 'user' in session:
        session.pop('user', None)
    flash('You have successfully logged out', 'success')
    return redirect('/')


def swapAnswerKeys(input_str):
    chars = list(input_str)
    for i in range(0, len(chars) - 1, 2):
        chars[i], chars[i + 1] = chars[i + 1], chars[i]
    swapped_str = ''.join(chars)
    return swapped_str

def swapAnswerKeys(input_str):
    chars = list(input_str)
    for i in range(0, len(chars) - 1, 2):
        chars[i], chars[i + 1] = chars[i + 1], chars[i]
    swapped_str = ''.join(chars)
    return swapped_str

@app.route('/uploadAnswerKey', methods=['POST'])
def uploadAnswerKey():
    if isLoggedIn():
        try:
            file = request.files.get('file')
            ANSWER_KEY = list()
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(session['UPLOAD_FOLDER'], filename))

                ANSWER_KEY = omr.getAnswers(
                    session['UPLOAD_FOLDER'] + '/' + filename)
                session['ANSWER_KEY'] = ANSWER_KEY

                ANSWERS_STR = ''
                for ans in ANSWER_KEY:
                    ANSWERS_STR += (ANSWER_LETTERS[ans])

                swapped_ANSWERS_STR = swapAnswerKeys(ANSWERS_STR)  # Swap the answer key
                session['ANSWERS_STR'] = swapped_ANSWERS_STR  # Update session variable with swapped answer string
            else:
                deleteUploadDirectory()
                flash(
                    'The file extension you uploaded is not supported. \
                        Supported file extensions (.jpg .png .jpeg) \
                            to use',
                    'error')
                return redirect(request.url)
        except Exception:
            deleteUploadDirectory()
            flash('The answer key you uploaded was not accepted because it did not meet the standards \
                our request cannot be processed. Please send a request that meets the standards. \
                    "use the answer key.', 'error')
            return redirect(request.url)
        flash('The answer key was successfully uploaded.', 'success')
        return redirect('/uploadPapers')
    else:
        flash('You must log in to perform this operation!', 'error')
        return redirect(url_for('login'))





def swapAnswerKeys(input_str):
    chars = list(input_str)
    
    # Iterate through the string two characters at a time and swap them
    for i in range(0, len(chars) - 1, 2):
        chars[i], chars[i + 1] = chars[i + 1], chars[i]
    
    # Convert the list back to a string
    swapped_str = ''.join(chars)
    
    return swapped_str


def get_database_connection():
    # Replace these values with your actual database credentials
    host = 'localhost'
    user = 'root'
    password = ''
    database = 'omr'

    # Establish a connection to the database
    connection = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )

    return connection


@app.route('/uploadPapers', methods=['POST'])
def uploadPapers():
    if isLoggedIn():
        try:
            files = request.files.getlist('files[]')
            SCORES = {}
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(session['UPLOAD_FOLDER'], filename))

                    temp = list()
                    temp.clear()

                    ANSWERS_STR = ''
                    for ans in omr.getAnswers(
                            session['UPLOAD_FOLDER'] + '/' + filename):
                        ANSWERS_STR += (ANSWER_LETTERS[ans])
                    temp.append(ANSWERS_STR)

                    # Swap answer keys
                    last_ANSWERS_STR = swapAnswerKeys(ANSWERS_STR)

                    # print("Last Answer String:", last_ANSWERS_STR)

                    result = omr.getScores(
                        (session['UPLOAD_FOLDER'] + '/' + filename),
                        session['ANSWER_KEY'],
                        session['UPLOAD_FOLDER'])
                    temp.append(result[0])
                    # print(result[1])
                    temp.append('static' + (result[1].split('static')[1]))
                    temp.append(result[3])
                    temp.append(result[4])
                    temp.append(result[5])

                    SCORES[result[2]] = temp
                    """
                        scores[0] = answer options
                        scores[1] = point
                        scores[2] = name surname img
                        scores[3] = wrong
                        scores[4] = correct
                        scores[5] = empty
                        
                    """
                    # Add to the database using dbmysql
                    dbmysql.addOperation(session['UPLOAD_FOLDER'], getUser()[
                        "email"], session['ANSWERS_STR'])
                    dbmysql.addRecord(
                        session['UPLOAD_FOLDER'],
                        result[1],
                        result[3],
                        result[4],
                        result[5],
                        result[0],
                       last_ANSWERS_STR, result[2])
                else:
                    flash(
                        'The file extension you uploaded is not supported. \
                            Supported file extensions (.jpg .png .jpeg) \
                                to use',
                        'error')
                    return redirect(request.url)
        except Exception:
            flash('Among the exam papers you uploaded, there are those that meet the standards\
                Your request cannot be processed. Please fill in the required fields. \
                    Use papers that meet the standards."', 'error')
            return redirect(request.url)
        session['SCORES'] = SCORES
        flash('The files were successfully uploaded.', 'success')
        return redirect('/completed')
    else:
        flash('You must log in to perform this operation!"', 'error')
        return redirect(url_for('login'))
    
    
     
#Start of pdf exporting
class NoDataFoundError(Exception):
    pass

def generate_pdf_data(grade_level, section, subject, quarter):
    """
    Generate PDF data with linear data.

    Args:
    - grade_level (str): Grade level.
    - section (str): Section.
    - subject (str): Subject.
    - quarter (str): Quarter.

    Returns:
    - pdf_data (bytes): Generated PDF data.
    """
    pdf_data = b''  # Default empty PDF data
    
    try:
        # Example linear data processing
        data = {
            "Grade": grade_level,
            "Section": section,
            "Subject": subject,
            "Quarter": quarter,
        }
        
        if data:
            # Process the fetched data and generate PDF
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            c.setFont("Helvetica", 12)
            
            # Print linear data on PDF
            y_coordinate = 750
            for category, value in data.items():
                c.drawString(100, y_coordinate, f"{category}: {value}")
                y_coordinate -= 20
            
            c.save()
            pdf_data = buffer.getvalue()
            buffer.close()
        else:
            # If no data is found, raise a custom exception
            raise NoDataFoundError("No linear data found")
    except NoDataFoundError as error:
        print(f"Error generating PDF data: {error}")
    except Exception as error:
        print(f"Error generating PDF data: {error}")

    return pdf_data
#end of exporting


# Define a placeholder function for executing SQL queries (replace this with your actual implementation)
def execute_query(selected_item):
    try:
        # Replace these values with your actual database connection parameters
        host = 'localhost'
        user = 'root'
        password = ''
        database = 'omr'

        # Establish a connection to the database
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )

        cursor = connection.cursor()

        # Placeholder SQL queries based on the selected item
        if selected_item == "grade_level":
            query = "SELECT DISTINCT grade_level_name FROM grade_level"
        elif selected_item == "section":
            query = "SELECT DISTINCT section_name FROM section"
        elif selected_item == "subject":
            query = "SELECT DISTINCT subject_name FROM subject"
        elif selected_item == "quarter":
            query = "SELECT DISTINCT quarter_name FROM quarter"

        # Execute the SQL query
        cursor.execute(query)

        # Fetch all rows of the result
        rows = cursor.fetchall()

        # Close cursor and connection
        cursor.close()
        connection.close()

        # Return the fetched data
        return rows

    except Exception as e:
        print(f"Error executing SQL query: {e}")
        return []


def fetch_dropdown_data_for_upload(query):
    try:
        # Execute the SQL query to fetch dropdown data
        dropdown_data = execute_query(query)

        # Extract dropdown options from the fetched data
        dropdown_options = [row[0] for row in dropdown_data]

        # Return dropdown options as JSON response
        return jsonify(dropdown_options)
    except Exception as e:
        # Handle any errors that occur during data fetching
        print(f"Error fetching dropdown data: {e}")
        return jsonify([])  # Return an empty list if an error occurs

     
     
     
      # Start of API integration for data fetching for dropdowns

def fetch_dropdown_data(query):
    try:
        data = dbmysql.fetch_data(query)
        dropdown_options = [row[0] for row in data]
        return jsonify(dropdown_options)
    except Exception as error:
        print(f"Error fetching data: {error}")
        return jsonify([])

@app.route('/grade_dropdown_data')
def grade_dropdown_data():
    query = "SELECT DISTINCT grade_level_name FROM grade_level"
    return fetch_dropdown_data(query)

@app.route('/section_dropdown_data')
def section_dropdown_data():
    query = "SELECT DISTINCT section_name FROM section"
    return fetch_dropdown_data(query)

@app.route('/subject_dropdown_data')
def subject_dropdown_data():
    query = "SELECT DISTINCT subject_name FROM subject"
    return fetch_dropdown_data(query)

@app.route('/quarter_dropdown_data')
def quarter_dropdown_data():
    query = "SELECT DISTINCT quarter_name FROM quarter"
    return fetch_dropdown_data(query)


# End of API for dropdowns


#start of immitation of the fetching data from the API

def fetch_dropdown_data_for_upload(query):
    try:
        data = dbmysql.fetch_data(query)
        dropdown_options = [row[0] for row in data]
        return jsonify(dropdown_options)
    except Exception as error:
        print(f"Error fetching data: {error}")
        return jsonify([])

@app.route('/Upload_grade_dropdown_data')
def Upload_grade_dropdown_data():
    query = "SELECT DISTINCT grade_level_name FROM grade_level"
    return fetch_dropdown_data_for_upload(query)

@app.route('/Upload_section_dropdown_data')
def Upload_section_dropdown_data():
    query = "SELECT DISTINCT section_name FROM section"
    return fetch_dropdown_data_for_upload(query)

@app.route('/Upload_subject_dropdown_data')
def Upload_subject_dropdown_data():
    query = "SELECT DISTINCT subject_name FROM subject"
    return fetch_dropdown_data_for_upload(query)

@app.route('/Upload_quarter_dropdown_data')
def Upload_quarter_dropdown_data():
    query = "SELECT DISTINCT quarter_name FROM quarter"
    return fetch_dropdown_data_for_upload(query)
#end of immitation ofthe above API

# Define a function to generate PDF data (replace this with your actual PDF generation logic)
@app.route('/generate_pdf/<grade_level>/<section>/<subject>/<quarter>', methods=['GET'])
def generate_pdf_by_params(grade_level, section, subject, quarter):
    pdf_data = generate_pdf_data(grade_level, section, subject, quarter)
    pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
    return jsonify({'pdfData': pdf_base64})


@app.route('/generate_pdf', methods=['GET'])
def generate_pdf_by_query_params():
    grade_level = request.args.get('grade_level')
    section = request.args.get('section')
    subject = request.args.get('subject')
    quarter = request.args.get('quarter')
    pdf_data = generate_pdf_data(grade_level, section, subject, quarter)
    pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
    return jsonify({'pdfData': pdf_base64})

# start of updating the grade_level, section, subject and quarter
# Configuration for MySQL connection
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'omr',
    'cursorclass': pymysql.cursors.DictCursor
}

# Function to update data in the database
def update_database(grade_level, section, subject, quarter):
    connection = pymysql.connect(**db_config)
    try:
        with connection.cursor() as cursor:
            # SQL to update exam_operations table
            operations_sql = "UPDATE exam_operations SET grade_level=%s, section=%s, subject=%s, quarter=%s"
            cursor.execute(operations_sql, (grade_level, section, subject, quarter))

            # SQL to update exam_records table
            records_sql = "UPDATE exam_records SET grade_level=%s, section=%s, subject=%s, quarter=%s"
            cursor.execute(records_sql, (grade_level, section, subject, quarter))
        connection.commit()
    finally:
        connection.close()

# Route for handling form submission
@app.route('/updateExamOperationsId', methods=['POST'])
def updateExamOperationsId():
    # Retrieve form data
    grade_level = request.form['grade_level']
    section = request.form['section']
    subject = request.form['subject']
    quarter = request.form['quarter']

    # Update data in the database
    update_database(grade_level, section, subject, quarter)
    
    return jsonify({'message': 'Update successful'})


if __name__ == "__main__":
    # app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)


