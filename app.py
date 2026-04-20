from flask import Flask, render_template, request, url_for , redirect, flash, session
from controller.config import Config
from controller.database import db
from controller.models import User, Subject, Quiz, Question, Attempt, Activity


app = Flask(__name__, template_folder="templates", static_folder="static")
app.config.from_object(Config)
db.init_app(app)
with app.app_context():
    db.create_all()
    admin = User.query.filter_by(role="admin").first()
    if not admin: admin = User(username="admin", password="anshverma1975", role="admin")
    db.session.add(admin)
    db.session.commit()
    # username = "admin"
    # password = "anshverma1975"
    # role = "admin"

#to make sure only admins can enter the admin dashboard and its subsequent pages
def admin_access():
    if "user_id" not in session:
        flash("Please login first")
        return redirect(url_for("landing"))

    if session.get("role") != "admin":
        flash("You are not authorized to access this page")
        return redirect(url_for("home"))

    return True

@app.route("/")
def landing():
    if "user_id" in session:
        if session.get("role") == "admin":
            return redirect(url_for("admin_dashboard"))
        elif session.get("role") == "student":
            return redirect(url_for("home"))
    return render_template("landing.html")

@app.route("/home")
@app.route("/dashboard")
def home():
    user_id = session.get("user_id")
    if not user_id:
        flash("Please login first")
        return redirect(url_for("landing"))
    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))
    
    subjects_count = Subject.query.count()
    quizzes_count = Quiz.query.count()
    questions_count = Question.query.count()
    attempted_count = Attempt.query.filter_by(user_id=user_id).count()

    activities = (
        Activity.query
        .filter_by(user_id=user_id)
        .order_by(Activity.timestamp.desc())
        .limit(5)
        .all()
    )


    return render_template(
        "user_dashboard.html",subjects_count=subjects_count, quizzes_count=quizzes_count, questions_count=questions_count, attempted_count=attempted_count,activities=activities   
    )



#loginn route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')


        user = User.query.filter_by(username=username).first()

        if not user or user.password != password:
            flash("Invalid credentials")
            return redirect(url_for('login'))

        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role

        if user.role == "admin":
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('home'))


    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash("All fields required")
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("User already exists")
            return redirect(url_for('login'))

        new_user = User(username=username, password=password, role="student")
        db.session.add(new_user)
        db.session.commit()
        log_activity(type="system",message=f"User {username} Registered",user_id=new_user.id)

        flash("Registered successfully, please login")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('role', None)
    #session.clear()
    flash("Logged out successfully")
    return redirect(url_for('landing'))

def log_activity(type, message, user_id=None):
    activity = Activity(
        type=type,
        message=message,
        user_id=user_id
    )
    db.session.add(activity)
    db.session.commit()

@app.route('/admin')
def admin_dashboard():
    if "user_id" not in session:
        flash("Please login first")
        return redirect(url_for("landing"))
    if session.get('role') != "admin":
        flash("You are not authorized to access this page")
        return redirect(url_for("landing"))
    
    users_count = User.query.count()
    subjects_count = Subject.query.count()
    quizzes_count = Quiz.query.count()
    questions_count = Question.query.count()
    activities = (Activity.query.order_by(Activity.timestamp.desc()).limit(5).all())
    

    return render_template("admin_dashboard.html",users_count=users_count,subjects_count=subjects_count,quizzes_count=quizzes_count,questions_count=questions_count,activities=activities)



@app.route('/admin/subjects')
def admin_subjects():
    if not admin_access():
        return redirect(url_for("home"))

    subjects = Subject.query.order_by(Subject.id.desc()).all()

    subject_data = []
    for s in subjects:
        subject_data.append({
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "quiz_count": len(s.quizzes),
            "created": s.id  
        })

    return render_template("admin_subjects.html", subjects=subject_data)

@app.route("/admin/subjects/new")
def new_subject():
    if not admin_access():
        return redirect(url_for("landing"))
    return render_template("create_subject.html")

@app.route("/admin/subjects/create", methods=["POST"])
def create_subject():
    if not admin_access():
        return redirect(url_for("landing"))

    name = request.form.get("name")
    description = request.form.get("description")

    if not name:
        flash("Subject name is required")
        return redirect(url_for("new_subject"))

    subject = Subject(name=name, description=description)
    db.session.add(subject)
    db.session.commit()

    log_activity(
        type="subject",
        message=f"Created subject '{name}'",
        user_id=session["user_id"]
    )

    flash("Subject created")
    return redirect(url_for("admin_subjects"))

@app.route("/admin/subjects/delete/<int:id>", methods=["POST"])
def delete_subject(id):
    if not admin_access():
        return redirect(url_for("landing"))

    subject = Subject.query.get_or_404(id)
    name = subject.name

    db.session.delete(subject)
    db.session.commit()

    log_activity(
        type="subject",
        message=f"Deleted subject '{name}'",
        user_id=session["user_id"]
    )

    flash("Subject deleted")
    return redirect(url_for("admin_subjects"))
    

@app.route("/admin/subjects/edit/<int:id>")
def edit_subject(id):
    if not admin_access():
        return redirect(url_for("landing"))

    subject = Subject.query.get_or_404(id)
    return render_template("edit_subject.html", subject=subject)
    







if __name__ == "__main__":
    app.run(debug=True) 