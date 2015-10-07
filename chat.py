import flask
import redis
import os
import re
import time

from shutil import copyfile
from passlib.hash import sha256_crypt
from werkzeug import secure_filename

app = flask.Flask(__name__)
app.secret_key = 'idontunderstandthepointofthislolhowdoesithelpsrslyplzsplain'
red = redis.StrictRedis(host="db")

UPLOAD_FOLDER = '/tmp/workdir/static/images/'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

game_id = "02e8ifno32"

def handle_message(message, mine):
    if mine:
        red.rpush(game_id + ":chat", message['data'])
    return 'data: %s\n\n' % message['data']


def event_stream(user):
    red.publish('chat', u'/quit %s' % (user))
    pubsub = red.pubsub()
    pubsub.subscribe('chat')
    for message in pubsub.listen():
        text = str(message['data'])
        if text[0:5] == "/quit":
            if text[6:] == user:
                break
        else:
            msg_user_m = re.search('^<b>(.*)</b>: ', text)
            mine = False
            if '</br><center' in text:
                if 'class="{user}"'.format(user=user) in text:
                    mine = True
            if msg_user_m:
                msg_user = msg_user_m.group(1)
                mine = True if msg_user == user else False
            if message['type'] != 'subscribe':
                yield handle_message(message, mine)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'POST':
        user = flask.request.form['user'].replace("<", "&lt;").replace(">", "&gt;")
        if red.exists(user.lower()):
            if sha256_crypt.verify(flask.request.form['pwd'], red.hget(user.lower(), 'pwd')):
                flask.session['user'] = user
                return flask.redirect('/')
            else:
                return flask.render_template('login.html', username=user, error=True)
        else:
            red.hmset(user.lower(), {'name':user,'pwd':sha256_crypt.encrypt(flask.request.form['pwd'])})
            flask.session['user'] = user
            return flask.redirect('/')
    return flask.render_template('login.html', username="", error=False)


@app.route('/post', methods=['POST'])
def post():
    message = flask.request.form['message'].replace("<", "&lt;").replace(">", "&gt;")
    user = flask.session.get('user', 'anonymous')
    if message[0:7] == "/header":
        red.publish('chat', u'</br><center class="%s" style="font-size:1.5em;font-weight:bold;">%s</center>' % (user, message[8:]))
    elif message[0:4] == "/act":
        red.publish('chat', u'<b>%s</b>: <strong>%s</strong>' % (user, message[5:]))
    else:
        red.publish('chat', u'<b>%s</b>: %s' % (user, message))
    return flask.Response(status=204)


@app.route('/quit')
def quit():
    user = flask.session.get('user', 'anonymous')
    red.publish('chat', u'/quit %s' % (user))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/images', methods=['GET', 'POST'])
def images():
    if flask.request.method == 'POST':
        file = flask.request.files['file']
        if file and allowed_file(file.filename):
            filename = str(time.time()).split(".")[0] + "-" + secure_filename(file.filename)
            rel_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(rel_path)
            if os.stat(rel_path).st_size < 1:
                os.remove(rel_path)
    files = sorted(os.listdir(app.config['UPLOAD_FOLDER']))[::-1]
    return flask.render_template('images.html', files=files)


@app.route('/stream')
def stream():
    return flask.Response(event_stream(flask.session.get('user', 'anonymous')),
                          mimetype="text/event-stream")


@app.route('/')
def home():
    if 'user' not in flask.session:
        return flask.redirect('/login')
    messages = red.lrange(game_id + ":chat", 0, -1)
    return flask.render_template('index.html', messages=messages)


@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1
    response.headers["Pragma"] = "no-cache" # HTTP 1.0
    response.headers["Expires"] = "0" # Proxies
    return response


if __name__ == '__main__':
    app.debug = True
    app.run()
