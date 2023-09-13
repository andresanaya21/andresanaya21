# Import Flask
from flask import Flask

# Create an instance of Flask
app = Flask(__name__)

# Define the home route
@app.route("/")
def home():
    # Return a simple message
    return "Hello, World!"

# Run the app if this file is executed
if __name__ == "__main__":
    app.run(debug=True)