from flask import Flask, render_template, request, url_for , redirect, flash, session
from controller.config import Config
from controller.database import db
from controller.models import User


app = Flask(__name__, template_folder="templates", static_folder="static")

app.secret_key = "quiz_master_dev_secret_123"
app.config.from_object(Config)
db.init_app(app)
with app.app_context():
    db.create_all()



@app.route("/")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    return f"Welcome {session['username']}"

    #return render_template("user_dashboard.html")   


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

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        flash("Registered successfully, please login")
        return redirect(url_for('login'))

    return render_template('register.html')










if __name__ == "__main__":
    app.run(debug=True)