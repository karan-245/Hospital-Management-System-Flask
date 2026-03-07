from flask import Flask, render_template, request, redirect, session, url_for
import mysql.connector
import os


app = Flask(__name__)
app.secret_key = "supersecretkey"

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password=os.getenv("DB_PASSWORD"),
        database="HospitalDB"
    )



@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid Credentials")

    return render_template("login.html")



@app.route("/dashboard")
def dashboard():
    if "logged_in" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM Patient")
    total_patients = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Doctor")
    total_doctors = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Appointment")
    total_appointments = cursor.fetchone()[0]

    conn.close()

    return render_template("dashboard.html",
                           patients=total_patients,
                           doctors=total_doctors,
                           appointments=total_appointments)



@app.route("/add_department", methods=["GET", "POST"])
def add_department():
    if request.method == "POST":
        name = request.form["name"]

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Department (dept_name) VALUES (%s)", (name,))
        conn.commit()
        conn.close()

        return redirect(url_for("view_departments"))

    return render_template("add_department.html")



@app.route("/view_departments")
def view_departments():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Department")
    data = cursor.fetchall()
    conn.close()

    return render_template("view_departments.html", departments=data)



@app.route("/add_doctor", methods=["GET", "POST"])
def add_doctor():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT dept_id, dept_name FROM Department")
    departments = cursor.fetchall()

    if request.method == "POST":
        name = request.form["name"]
        specialization = request.form["specialization"]
        dept_id = request.form["dept_id"]

        cursor.execute(
            "INSERT INTO Doctor (doctor_name, dept_id, specialization) VALUES (%s,%s,%s)",
            (name, dept_id, specialization)
        )
        conn.commit()
        conn.close()
        return redirect(url_for("view_doctors"))

    conn.close()
    return render_template("add_doctor.html", departments=departments)

# ---------------- VIEW DOCTOR ----------------

@app.route("/view_doctors")
def view_doctors():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT d.doctor_id, d.doctor_name, dep.dept_name, d.specialization
        FROM Doctor d
        JOIN Department dep ON d.dept_id = dep.dept_id
    """)
    data = cursor.fetchall()
    conn.close()

    return render_template("view_doctors.html", doctors=data)

# ---------------- ADD PATIENT ----------------

@app.route("/add_patient", methods=["GET", "POST"])
def add_patient():
    if request.method == "POST":
        name = request.form["name"]
        age = request.form["age"]
        gender = request.form["gender"]
        contact = request.form["contact"]

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Patient (patient_name, age, gender, contact_no) VALUES (%s,%s,%s,%s)",
            (name, age, gender, contact)
        )
        conn.commit()
        conn.close()

        return redirect(url_for("view_patients"))

    return render_template("add_patient.html")



@app.route("/view_patients")
def view_patients():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Patient")
    data = cursor.fetchall()
    conn.close()

    return render_template("view_patients.html", patients=data)


@app.route("/book_appointment", methods=["GET", "POST"])
def book_appointment():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT patient_id, patient_name FROM Patient")
    patients = cursor.fetchall()

    cursor.execute("SELECT doctor_id, doctor_name FROM Doctor")
    doctors = cursor.fetchall()

    if request.method == "POST":
        patient_id = request.form["patient_id"]
        doctor_id = request.form["doctor_id"]
        date = request.form["date"]
        time = request.form["time"]

        cursor.execute("""
            SELECT * FROM Appointment
            WHERE doctor_id=%s AND appointment_date=%s AND appointment_time=%s
        """, (doctor_id, date, time))

        if cursor.fetchone():
            conn.close()
            return "Doctor already booked!"

        cursor.execute("""
            INSERT INTO Appointment (patient_id, doctor_id, appointment_date, appointment_time)
            VALUES (%s,%s,%s,%s)
        """, (patient_id, doctor_id, date, time))
        conn.commit()
        conn.close()
        return redirect(url_for("view_appointments"))

    conn.close()
    return render_template("book_appointment.html",
                           patients=patients,
                           doctors=doctors)


@app.route("/view_appointments")
def view_appointments():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.appointment_id, p.patient_name, d.doctor_name,
               a.appointment_date, a.appointment_time
        FROM Appointment a
        JOIN Patient p ON a.patient_id = p.patient_id
        JOIN Doctor d ON a.doctor_id = d.doctor_id
    """)
    data = cursor.fetchall()
    conn.close()

    return render_template("view_appointments.html", appointments=data)



@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
