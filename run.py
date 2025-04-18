from app import create_app
from flask import redirect

app = create_app()

# Add a direct root route handler
@app.route('/')
def index():
    return redirect('/home')

if __name__ == '__main__':
    
    app.run(debug=True)