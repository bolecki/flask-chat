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

# Image upload info
UPLOAD_FOLDER = '/tmp/workdir/static/images/'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Placeholder id
chat_id = "02e8ifno32"

def handle_message(message, mine):
    if mine:
        red.rpush(chat_id + ":chat", message['data'])
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
    '''
        Login page and authentication.

        If it is a GET request, render the login page.

        If it is a POST request, HTML encode the username
        to prevent XSS attacks.  Check if the user exists
        in redis.  If they do, verify creds and return the
        chat page, or provide authentication error and render
        login page again.  If the user does not exist, create
        a new account with the information provided, then
        proceed to the chat page.
    '''
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
    '''
        Process new user messages and publish to
        the event_stream().

        HTML encode messages to avoid XSS attacks, then
        format the actual HTML based on the message:
        header, action, or regular message.

        Return status 204 as the event_stream() will
        pickup the information from redis and provide
        new content.
    '''
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
    '''
        User disconnected.

        This is called when a user leaves the the chat
        page in order to reduce duplicate sessions.
        It will publish a message to the event_stream(),
        which will parse the message and close the stream.
        It passes the username to ensure that the correct
        stream is closed.
    '''
    user = flask.session.get('user', 'anonymous')
    red.publish('chat', u'/quit %s' % (user))


def allowed_file(filename):
    '''Return true if the file extension is allowed'''
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/images', methods=['GET', 'POST'])
def images():
    '''
        This page displays all user uploaded images.

        If it is a GET request: get a list of all files in the
        static/images directory and pass them to the
        render_template() function.

        If it is a POST request: verify that the file is
        allowed, create a unique and secure filename, and
        save the uploaded file.  If the file did not upload
        correctly (size < 1 byte) then remove the file.
        Proceed to refresh the page as if it was a GET request.
    '''
    if flask.request.method == 'POST':
        file = flask.request.files['file']
        if file and allowed_file(file.filename):
            filename = str(time.time()).split(".")[0] + "-" + secure_filename(file.filename)
            rel_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(rel_path)
            if os.stat(rel_path).st_size < 1:
                os.remove(rel_path)
    files = sorted(os.listdir(app.config['UPLOAD_FOLDER']))[::-1]
    files.remove('.gitignore')
    return flask.render_template('images.html', files=files)


@app.route('/stream')
def stream():
    '''
        A client is requesting a new data stream.

        Return a new event_stream() with the useras a parameter.
        Specify the type as text/event-stream.
    '''
    return flask.Response(event_stream(flask.session.get('user', 'anonymous')),
                          mimetype="text/event-stream")


@app.route('/')
def home():
    '''
        If the user is not logged in, route them to the login page.
        Otherwise, render the chat page with all messages from redis db
    '''
    if 'user' not in flask.session:
        return flask.redirect('/login')
    messages = red.lrange(chat_id + ":chat", 0, -1)
    return flask.render_template('index.html', messages=messages)


@app.after_request
def add_header(response):
    '''
        Add headers to make sure the client does not
        cache any pages.  Caching will cause page refreshes
        to ignore updated stream data.
    '''
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1
    response.headers["Pragma"] = "no-cache" # HTTP 1.0
    response.headers["Expires"] = "0" # Proxies
    return response


if __name__ == '__main__':
    app.debug = True
    app.run()
