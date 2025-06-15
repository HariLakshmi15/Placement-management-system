from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import config
from datetime import date

app = Flask(__name__)
app.config['MYSQL_HOST'] = config.MYSQL_HOST
app.config['MYSQL_USER'] = config.MYSQL_USER
app.config['MYSQL_PASSWORD'] = config.MYSQL_PASSWORD
app.config['MYSQL_DB'] = config.MYSQL_DB
app.secret_key = config.SECRET_KEY

mysql = MySQL(app)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        roll_number = request.form['roll_number']
        password = generate_password_hash(request.form['password'])
        branch = request.form['branch']
        cgpa = request.form['cgpa']
        cur = mysql.connection.cursor()
        cur.execute("""INSERT INTO students (name, email, roll_number, password, branch, cgpa)
                        VALUES (%s, %s, %s, %s, %s, %s)""", (name, email, roll_number, password, branch, cgpa))
        mysql.connection.commit()
        cur.close()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM students WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()
        if user and check_password_hash(user[4], password):
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('student_login.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM admins WHERE email=%s AND password=%s", (email, password))
        admin = cur.fetchone()
        cur.close()
        if admin:
            session['admin_id'] = admin[0]
            session['admin_name'] = admin[1]
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials', 'danger')
    return render_template('admin_login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    return redirect(url_for('student_login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    return render_template('dashboard.html', name=session['user_name'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/companies')
def companies():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM companies")
    companies = cur.fetchall()
    cur.execute("SELECT cgpa FROM students WHERE student_id=%s", (session['user_id'],))
    student_cgpa = cur.fetchone()[0]
    cur.close()
    return render_template('companies.html', companies=companies, student_cgpa=student_cgpa)

@app.route('/apply/<int:company_id>')
def apply(company_id):
    if 'user_id' not in session:
        return redirect(url_for('home'))
    cur = mysql.connection.cursor()
    # Check if already applied
    cur.execute("SELECT * FROM applications WHERE student_id=%s AND company_id=%s", (session['user_id'], company_id))
    if cur.fetchone():
        flash('Already applied to this company.', 'warning')
        return redirect(url_for('companies'))
    cur.execute("INSERT INTO applications (student_id, company_id, status, applied_date) VALUES (%s, %s, %s, %s)",
                (session['user_id'], company_id, 'Applied', date.today()))
    mysql.connection.commit()
    cur.close()
    flash('Application submitted!', 'success')
    return redirect(url_for('companies'))

@app.route('/my_applications')
def my_applications():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    cur = mysql.connection.cursor()
    cur.execute("""SELECT c.name, c.role, a.status, a.applied_date
                     FROM applications a
                     JOIN companies c ON a.company_id = c.company_id
                     WHERE a.student_id = %s""", (session['user_id'],))
    applications = cur.fetchall()
    cur.close()
    return render_template('my_applications.html', applications=applications)

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html', admin_name=session['admin_name'])

@app.route('/admin/add_company', methods=['GET', 'POST'])
def add_company():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        name = request.form['name']
        role = request.form['role']
        ctc = request.form['ctc']
        eligibility_cgpa = request.form['eligibility_cgpa']
        eligibility_branch = request.form['eligibility_branch']
        placement_date = request.form['placement_date']
        cur = mysql.connection.cursor()
        cur.execute("""INSERT INTO companies (name, role, ctc, eligibility_cgpa, eligibility_branch, placement_date)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (name, role, ctc, eligibility_cgpa, eligibility_branch, placement_date))
        mysql.connection.commit()
        cur.close()
        flash('Company added!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('add_company.html')

@app.route('/admin/applications')
def admin_applications():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    cur = mysql.connection.cursor()
    cur.execute("""SELECT a.application_id, s.name, c.name, a.status, a.applied_date
                     FROM applications a
                     JOIN students s ON a.student_id = s.student_id
                     JOIN companies c ON a.company_id = c.company_id""")
    applications = cur.fetchall()
    cur.close()
    return render_template('admin_applications.html', applications=applications)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('student_login'))
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        branch = request.form['branch']
        cgpa = request.form['cgpa']
        cur.execute("UPDATE students SET name=%s, email=%s, branch=%s, cgpa=%s WHERE student_id=%s",
                    (name, email, branch, cgpa, session['user_id']))
        mysql.connection.commit()
        flash('Profile updated successfully!', 'success')
    cur.execute("SELECT name, email, roll_number, branch, cgpa FROM students WHERE student_id=%s", (session['user_id'],))
    student = cur.fetchone()
    cur.close()
    return render_template('profile.html', student=student)

@app.route('/admin/database')
def admin_database():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    cur = mysql.connection.cursor()
    cur.execute("SELECT student_id, name, email, roll_number, branch, cgpa FROM students")
    students = cur.fetchall()
    cur.execute("SELECT * FROM companies")
    companies = cur.fetchall()
    cur.execute("""SELECT a.application_id, s.name, c.name, a.status, a.applied_date
                   FROM applications a
                   JOIN students s ON a.student_id = s.student_id
                   JOIN companies c ON a.company_id = c.company_id""")
    applications = cur.fetchall()
    cur.close()
    return render_template('admin_database.html', students=students, companies=companies, applications=applications)

@app.route('/admin/update_status/<int:application_id>', methods=['POST'])
def update_status(application_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    new_status = request.form['status']
    cur = mysql.connection.cursor()
    cur.execute("SELECT student_id, company_id FROM applications WHERE application_id=%s", (application_id,))
    result = cur.fetchone()
    if result:
        student_id, company_id = result
        cur.execute("SELECT cgpa FROM students WHERE student_id=%s", (student_id,))
        student_cgpa = cur.fetchone()[0]
        cur.execute("SELECT eligibility_cgpa FROM companies WHERE company_id=%s", (company_id,))
        company_cgpa = cur.fetchone()[0]
        if new_status in ['Eligible', 'Selected'] and student_cgpa < company_cgpa:
            new_status = 'Rejected'
            flash('Student CGPA is below eligibility. Status set to Rejected.', 'warning')
    cur.execute("UPDATE applications SET status=%s WHERE application_id=%s", (new_status, application_id))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('admin_applications'))

@app.route('/admin/edit_company/<int:company_id>', methods=['GET', 'POST'])
def edit_company(company_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        name = request.form['name']
        role = request.form['role']
        ctc = request.form['ctc']
        eligibility_cgpa = request.form['eligibility_cgpa']
        eligibility_branch = request.form['eligibility_branch']
        placement_date = request.form['placement_date']
        cur.execute("""UPDATE companies SET name=%s, role=%s, ctc=%s, eligibility_cgpa=%s, eligibility_branch=%s, placement_date=%s
                       WHERE company_id=%s""",
                    (name, role, ctc, eligibility_cgpa, eligibility_branch, placement_date, company_id))
        mysql.connection.commit()
        cur.close()
        flash('Company updated!', 'success')
        return redirect(url_for('admin_database'))
    cur.execute("SELECT * FROM companies WHERE company_id=%s", (company_id,))
    company = cur.fetchone()
    cur.close()
    return render_template('edit_company.html', company=company)

@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO admins (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
        mysql.connection.commit()
        cur.close()
        flash('Admin registration successful!', 'success')
        return redirect(url_for('admin_login'))
    return render_template('admin_register.html')

if __name__ == '__main__':
    app.run(debug=True) 