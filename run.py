"""Entry point. Local dev: python run.py. Production (Railway): gunicorn run:app"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000, threaded=True)
