from flask import Flask
from patient.test import test
app = Flask(__name__)


@app.route("/")
def hello():
    return "Hello, World!"


if __name__ == "__main__":
    test()
    app.run(debug=True)
