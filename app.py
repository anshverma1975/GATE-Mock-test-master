from flask import Flask, render_template, request, url_for , redirect, flash, session
from controller.config import Config
from controller.database import db
from controller.models import User, Subject, Quiz, Question, Attempt, Activity, AttemptAnswer


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
        return False

    if session.get("role") != "admin":
        flash("You are not authorized to access this page")
        return False

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


    attempts = Attempt.query.filter_by(user_id=user_id).all()

    total_scored = 0
    total_possible = 0

    subject_scores = {}   # {subject_name: [scored, total]}

    for attempt in attempts:
        if not attempt.quiz:
            continue

        subject_name = attempt.quiz.subject.name

        scored = attempt.score or 0
        total = attempt.total_marks or 0

        total_scored += scored
        total_possible += total

        if subject_name not in subject_scores:
            subject_scores[subject_name] = [0, 0]

        subject_scores[subject_name][0] += scored
        subject_scores[subject_name][1] += total

    avg_score = 0
    if total_possible > 0:
        avg_score = round((total_scored / total_possible) * 100)

    # BEST + WEAK SUBJECT
    best_subject = "-"
    weak_subject = "-"

    best_pct = -1
    weak_pct = 101

    for subject, (scored, total) in subject_scores.items():
        if total == 0:
            continue

        pct = (scored / total) * 100

        if pct > best_pct:
            best_pct = pct
            best_subject = subject

        if pct < weak_pct:
            weak_pct = pct
            weak_subject = subject

    return render_template(
        "user_dashboard.html",
        subjects_count=subjects_count,
        quizzes_count=quizzes_count,
        questions_count=questions_count,
        attempted_count=attempted_count,
        activities=activities,
        avg_score=avg_score,
        best_subject=best_subject,
        weak_subject=weak_subject
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
    
@app.route("/admin/subjects/update/<int:id>", methods=["POST"])
def update_subject(id):
    if not admin_access():
        return redirect(url_for("landing"))

    subject = Subject.query.get_or_404(id)

    name = request.form.get("name")
    description = request.form.get("description")

    if not name:
        flash("Subject name is required")
        return redirect(url_for("edit_subject", id=id))

    subject.name = name
    subject.description = description

    db.session.commit()

    log_activity(
        type="subject",
        message=f"Updated subject '{name}'",
        user_id=session["user_id"]
    )

    flash("Subject updated successfully")
    return redirect(url_for("admin_subjects"))

@app.route("/admin/quizzes")
def admin_quizzes():
    if not admin_access():
        return redirect(url_for("landing"))
    quizzes = Quiz.query.order_by(Quiz.created_at.desc()).all()
    quiz_data = []
    for q in quizzes:
        quiz_data.append({
            "id": q.id,
            "title": q.title,
            "subject": q.subject.name,
            "question_count": len(q.questions),
            "created": q.created_at.strftime("%Y-%m-%d")
        })

    return render_template("admin_quizzes.html", quizzes=quiz_data)

#ye wala for making using the add new quiz button in admin quiz dashboard
@app.route("/admin/quizzes/new")
def new_quiz():
    if not admin_access():
        return redirect(url_for("landing"))

    subjects = Subject.query.all()
    if not subjects:
        flash("Create a subject first")
        return redirect(url_for("admin_subjects"))
    return render_template("create_quiz.html", subjects=subjects)

#this is to actually create the new quiz
@app.route("/admin/quizzes/create", methods=["POST"])
def create_quiz():
    if not admin_access():
        return redirect(url_for("landing"))

    title = request.form.get("title")
    subject_id = int(request.form.get("subject_id"))

    if not title or not subject_id:
        flash("All fields required")
        return redirect(url_for("new_quiz"))

    quiz = Quiz(title=title, subject_id=subject_id)
    db.session.add(quiz)
    db.session.commit()

    log_activity(
        type="quiz",
        message=f"Created quiz '{title}'",
        user_id=session["user_id"]
    )

    flash("Quiz created")
    return redirect(url_for("admin_quizzes"))

#to delete quizzes
@app.route("/admin/quizzes/delete/<int:id>", methods=["POST"])
def delete_quiz(id):
    if not admin_access():
        return redirect(url_for("landing"))

    quiz = Quiz.query.get_or_404(id)
    title = quiz.title

    db.session.delete(quiz)
    db.session.commit()

    log_activity(
        type="quiz",
        message=f"Deleted quiz '{title}'",
        user_id=session["user_id"]
    )

    flash("Quiz deleted")
    return redirect(url_for("admin_quizzes"))


@app.route("/admin/quizzes/view/<int:id>")
def view_quiz(id):
    if not admin_access():
        return redirect(url_for("home"))

    quiz = Quiz.query.get_or_404(id)
    return render_template("view_quiz.html", quiz=quiz)

@app.route("/admin/quizzes/edit/<int:id>")
def edit_quiz(id):
    if not admin_access():
        return redirect(url_for("home"))

    quiz = Quiz.query.get_or_404(id)

    return render_template("edit_quiz.html", quiz=quiz)

@app.route("/admin/quizzes/<int:quiz_id>/add_question", methods=["POST"])
def add_question(quiz_id):
    if not admin_access():
        return redirect(url_for("home"))

    text = request.form.get("text")
    option1 = request.form.get("option1")
    option2 = request.form.get("option2")
    option3 = request.form.get("option3")
    option4 = request.form.get("option4")
    correct = int(request.form.get("correct_option"))
    marks = int(request.form.get("marks") or 1)

    if not text or not correct:
        flash("Question and correct answer required")
        return redirect(url_for("edit_quiz", id=quiz_id))

    question = Question(
        quiz_id=quiz_id,
        question_text=text,
        option1=option1,
        option2=option2,
        option3=option3,
        option4=option4,
        correct_option=correct,
        marks=marks
    )

    db.session.add(question)
    db.session.commit()

    flash("Question added")
    return redirect(url_for("edit_quiz", id=quiz_id))

@app.route("/admin/questions/delete/<int:id>", methods=["POST"])
def delete_question(id):
    if not admin_access():
        return redirect(url_for("home"))

    question = Question.query.get_or_404(id)
    quiz_id = question.quiz_id

    db.session.delete(question)
    db.session.commit()

    flash("Question deleted")
    return redirect(url_for("view_quiz", id=quiz_id))

@app.route("/admin/questions/edit/<int:id>", methods=["GET", "POST"])
def edit_question(id):
    if not admin_access():
        return redirect(url_for("home"))

    question = Question.query.get_or_404(id)

    if request.method == "POST":
        question.question_text = request.form.get("text")
        question.option1 = request.form.get("option1")
        question.option2 = request.form.get("option2")
        question.option3 = request.form.get("option3")
        question.option4 = request.form.get("option4")
        question.correct_option = int(request.form.get("correct_option"))
        question.marks = int(request.form.get("marks") or 1)

        db.session.commit()

        flash("Question updated successfully")
        return redirect(url_for("view_quiz", id=question.quiz_id))

    return render_template("edit_question.html", question=question)


@app.route("/admin/questions/update/<int:id>", methods=["POST"])
def update_question(id):
    if not admin_access():
        return redirect(url_for("home"))

    question = Question.query.get_or_404(id)

    question.question_text = request.form.get("text")
    question.option1 = request.form.get("option1")
    question.option2 = request.form.get("option2")
    question.option3 = request.form.get("option3")
    question.option4 = request.form.get("option4")
    question.correct_option = int(request.form.get("correct_option"))
    question.marks = int(request.form.get("marks", 1))

    db.session.commit()

    flash("Question updated successfully")
    return redirect(url_for("edit_quiz", id=question.quiz_id))



@app.route("/admin/results")
def admin_results():
    if not admin_access():
        return redirect(url_for("home"))

    
    
    quiz_id = request.args.get("quiz_id")
    if quiz_id:
        attempts = Attempt.query.filter_by(quiz_id=quiz_id).all()
    else:
        attempts = Attempt.query.all()

    return render_template("admin_results.html", attempts=attempts)

@app.route("/profile")
def profile():
    if "user_id" not in session:
        flash("Please login first")
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])
    role = session.get("role")

    attempts_count = None
    avg_score = None

    if role == "student":
        attempts_count = Attempt.query.filter_by(user_id=user.id).count()

        avg_score = db.session.query(
            db.func.avg((Attempt.score / Attempt.total_marks) * 100)
        ).filter_by(user_id=user.id).scalar() or 0

    return render_template(
        "profile.html",
        user=user,
        role=role,
        attempts_count=attempts_count,
        avg_score=round(avg_score, 2) if avg_score else None
    )


#user functions daalenge ab 

@app.route("/dashboard/subjects")
def student_subjects():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))
    
    subjects = Subject.query.all()
    return render_template("student_subjects.html", subjects=subjects)

@app.route("/student/subjects/<int:subject_id>/quizzes")
def student_subject_quizzes(subject_id):
    if "user_id" not in session:
        flash("Please login first")
        return redirect(url_for("login"))

    subject = Subject.query.get_or_404(subject_id)
    quizzes = Quiz.query.filter_by(subject_id=subject_id).all()

    return render_template("student_subject_quizzes.html",subject=subject,quizzes=quizzes)

@app.route("/dashboard/quizzes")
def student_all_quizzes():
    if "user_id" not in session:
        flash("Please login first")
        return redirect(url_for("login"))

    quizzes = Quiz.query.order_by(Quiz.created_at.desc()).all()

    return render_template("student_all_quizzes.html", quizzes=quizzes)

@app.route("/change_password", methods=["POST"])
def change_password():
    if "user_id" not in session:
        flash("Please login first")
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    current = request.form.get("current_password")
    new = request.form.get("new_password")
    confirm = request.form.get("confirm_password")

    if user.password != current:
        flash("Current password is incorrect")
        return redirect(url_for("profile"))

    if new != confirm:
        flash("Passwords do not match")
        return redirect(url_for("profile"))

    if not new or len(new) < 4:
        flash("Password too weak")
        return redirect(url_for("profile"))

    user.password = new
    db.session.commit()

    flash("Password updated successfully")
    return redirect(url_for("profile"))
#quiz
@app.route("/student/quiz/<int:quiz_id>/attempt", methods=["GET", "POST"])
def attempt_quiz(quiz_id):
    if "user_id" not in session:
        flash("Please login first")
        return redirect(url_for("login"))

    if session.get("role") != "student":
        flash("Unauthorized access")
        return redirect(url_for("admin_dashboard"))

    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()

    if request.method == "POST":
        score = 0

        # ✅ calculate score
        for q in questions:
            selected = request.form.get(f"question_{q.id}")
            if selected and int(selected) == q.correct_option:
                score += (q.marks if q.marks else 1)

        # ✅ create attempt
        attempt = Attempt(
            user_id=session["user_id"],
            quiz_id=quiz_id,
            score=score,
            total_questions=len(questions),
            total_marks=sum(q.marks for q in questions)
        )

        db.session.add(attempt)
        db.session.commit()

        # ✅ store answers
        for q in questions:
            selected = request.form.get(f"question_{q.id}")
            answer = AttemptAnswer(
                attempt_id=attempt.id,
                question_id=q.id,
                selected_option=int(selected) if selected else None
            )
            db.session.add(answer)

        db.session.commit()

        # ✅ log
        log_activity(
            type="attempt",
            message=f"User {session['username']} scored {score}/{sum(q.marks for q in questions)} on {quiz.title}",
            user_id=session["user_id"]
        )

        flash("Quiz submitted successfully")

        return redirect(url_for("attempt_result", attempt_id=attempt.id))

    # ✅ GET request → show page
    return render_template("attempt_quiz.html", quiz=quiz, questions=questions)

@app.route("/student/attempt/<int:attempt_id>/result")
def attempt_result(attempt_id):
    if "user_id" not in session:
        flash("Please login first")
        return redirect(url_for("login"))

    attempt = Attempt.query.get_or_404(attempt_id)

    if attempt.user_id != session["user_id"]:
        flash("Unauthorized access")
        return redirect(url_for("home"))

    quiz = Quiz.query.get(attempt.quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz.id).all()

    answer_map = {
        a.question_id: a.selected_option
        for a in attempt.answers
    }

    correct = 0
    wrong = 0
    attempted = 0

    review_data = []

    for q in questions:
        selected = answer_map.get(q.id)

        if selected:
            attempted += 1

        is_correct = selected == q.correct_option

        if is_correct:
            correct += 1
        else:
            if selected:
                wrong += 1

        review_data.append({
            "question": q,
            "selected": selected,
            "correct": q.correct_option,
            "is_correct": is_correct
        })

    percentage = int((attempt.score / attempt.total_marks) * 100) if attempt.total_marks else 0

    return render_template(
        "attempt_result.html",
        quiz=quiz,
        attempt=attempt,
        correct=correct,
        wrong=wrong,
        attempted=attempted,
        percentage=percentage,
        review_data=review_data
    )


@app.route("/student/results")
def student_results():
    if "user_id" not in session:
        flash("Please login first")
        return redirect(url_for("login"))

    if session.get("role") != "student":
        flash("Unauthorized access")
        return redirect(url_for("admin_dashboard"))

    attempts = (
        Attempt.query
        .filter_by(user_id=session["user_id"])
        .order_by(Attempt.timestamp.desc())
        .all()
    )

    result_data = []

    for a in attempts:
        quiz = Quiz.query.get(a.quiz_id)
        subject = Subject.query.get(quiz.subject_id)

        percentage = int((a.score / a.total_marks) * 100) if a.total_marks else 0

        result_data.append({
            "attempt": a,
            "quiz": quiz,
            "subject": subject,
            "percentage": percentage
        })

    return render_template("student_results.html", results=result_data)


if __name__ == "__main__":
    app.run(debug=True) 