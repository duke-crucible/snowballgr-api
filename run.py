import os

from app.app import create_app

app = create_app(os.environ['SERVICE_APP_ENV'])

if __name__ == "__main__":
    app.run(debug=True, port=8000)
