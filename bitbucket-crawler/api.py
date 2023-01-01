from pathlib import Path

from lib.storage.dto import *

import attrs
from flask import Flask, jsonify, request, Response
from sqlite_integrated import *


environment_variables = os.environ.copy()

DATABASE_DIR = environment_variables.get("DATABASE_DIR", None)
DATABASE_PATH = Path(os.getcwd()).joinpath(DATABASE_DIR)
DATABASE_FILE = os.path.join(DATABASE_PATH, "database.db")

app = Flask(__name__)


@app.route('/api/commits/by/author', methods=['GET'])
def disp():
    email = request.args.get('email')
    if email is None:
        resp = Response("Required parameter 'email' not set", status=500)
        return resp

    try:
        db = Database(DATABASE_FILE, new=False)

        fields = [
            'hash',
            'message',
            'summary',
            'date',
            'author',
            'email',
            'diff_link',
            'repo_url']
        commits_by_email = db.cursor.execute(
            f'SELECT {",".join(fields)} FROM commits WHERE email LIKE "{email}"').fetchall()
    except Exception:
        resp = Response("An error occurred finding commits by email", status=500)
        return resp

    if len(commits_by_email) == 0:
        return jsonify({'data': []})

    typed_commits = list(map(lambda c: attrs.asdict(
        Commit(hash=c[0], message=c[1],summary=c[2], date=c[3], author=c[4], email=c[5], diff_link=c[6], repo_url=c[7])), commits_by_email))

    return jsonify({'data': typed_commits})


# driver function
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
