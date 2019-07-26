import json
import os
import sqlite3
from collections import namedtuple
from contextlib import contextmanager
from csv import reader
from multiprocessing import Process, Queue

from rauth import OAuth2Service, OAuth1Service

from IGNORE_scheme_debug import Buffer, tokenize_lines, debug_eval, scheme_read

import black
import requests
from flask import Flask, jsonify, make_response, redirect, request

from formatter import scm_reformat

CSV = "https://docs.google.com/spreadsheets/u/1/d/1v3N9fak7a-pf70zBhAIUuzplRw84NdLP5ptrhq_fKnI/export?format=csv&id=1-1v3N9fak7a-pf70zBhAIUuzplRw84NdLP5ptrhq_fKnI&gid=0"

app = Flask(__name__, static_url_path='', static_folder="")
ServerFile = namedtuple("ServerFile", ["short_link", "full_name", "url", "data", "discoverable"])


@contextmanager
def connect_db():
    conn = sqlite3.connect("shortlinks.db")
    try:
        def db(*args):
            try:
                if isinstance(args[1][0], str):
                    raise TypeError
            except (IndexError, TypeError):
                return conn.cursor().execute(*args)
            else:
                return conn.cursor().executemany(*args)
        yield db
    finally:
        conn.commit()
        conn.close()


@app.route('/')
def root():
    return app.send_static_file('./index.html')


@app.route('/<path>')
def load_file(path):
    raw = get_raw(path, True)
    filename = os.path.basename(path)
    if filename.startswith("IGNORE"):
        return None
    if raw is None:
        return app.send_static_file(path)
    data = bytes(json.dumps({"fileName": raw["full_name"], "data": raw["data"]}), "utf-8")

    response = make_response(redirect("/", code=302))
    response.set_cookie("load", value=data)
    return response


@app.route('/<path>/raw')
def get_raw(path, internal=False):
    with connect_db() as db:
        ret = db("SELECT * FROM links WHERE short_link=?;", [path]).fetchone()
        if ret is not None:
            out = ServerFile(*ret)._asdict()
        else:
            out = None
        if internal:
            return out
        else:
            return jsonify(out)


@app.route('/api/pytutor', methods=['POST'])
def pytutor_proxy():
    response = requests.post("http://pythontutor.com/web_exec_py3.py", data={
        "user_script": request.form["code"],
    })
    return response.text


@app.route("/api/black", methods=["POST"])
def black_proxy():
    try:
        return jsonify({"success": True, "code": black.format_str(request.form["code"], mode=black.FileMode()) + "\n"})
    except Exception as e:
        return jsonify({"success": False, "error": repr(e)})


@app.route("/api/_refresh")
def refresh():
    response = requests.get(CSV)
    parsed = reader(response.text.split("\n"))
    next(parsed)  # discard headers
    all_files = []
    for line in parsed:
        short_link, full_name, url, discoverable, *_ = line
        data = requests.get(url).text
        file = ServerFile(short_link, full_name, url, data, discoverable)
        all_files.append(file)

    with connect_db() as db:
        db("DROP TABLE IF EXISTS links")
        db("CREATE TABLE links (short_link, url, data, full_name, discoverable)")
        db("INSERT INTO links VALUES (?, ?, ?, ?, ?)", all_files)

    return jsonify(all_files)


@app.route('/api/scm_debug', methods=['POST'])
def scm_debug():
    code = request.form["code"]
    q = Queue()
    p = Process(target=scm_worker, args=(code, q))
    p.start()
    p.join(10)
    if not q.empty():
        return jsonify(q.get())


@app.route('/api/scm_format', methods=['POST'])
def scm_format():
    try:
        return jsonify({"success": True, "code": scm_reformat(request.form["code"])})
    except Exception as e:
        return jsonify({"success": False, "error": repr(e)})


def scm_worker(code, queue):
    try:
        buff = Buffer(tokenize_lines(code.split("\n")))
        exprs = []
        while buff.current():
            exprs.append(scheme_read(buff))
        out = debug_eval(exprs)
    except Exception as err:
        print("ParseError:", err)
        raise

    queue.put(out)


@app.route('/redirect/ok_auth')
def ok_auth():
    okpy = OAuth2Service()


if __name__ == "__main__":
    app.run()
