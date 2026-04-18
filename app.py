from flask import Flask, render_template
from flask_login import LoginManager
from controller.config import Config
from controller.database import db
from controller import models 


app = Flask(__name__, template_folder="templates", static_folder="static")
app.config.from_object(Config)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)


@app.route("/")
def home():
    return "App Running"


if __name__ == "__main__":
    app.run(debug=True)