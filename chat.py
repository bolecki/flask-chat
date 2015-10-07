import flask
import redis
import os
import re
import time

from shutil import copyfile
from passlib.hash import sha256_crypt
from werkzeug import secure_filename

app = flask.Flask(__name__)
app.secret_key = 'V\xb8\x1fPR$\x82~\xe1\xbd\t\x0fq\t\xe9\xd8\x13\xea}\x91H\xa2\xd0o'
red = redis.StrictRedis(host="db")

# Image upload info
UPLOAD_FOLDER = '/tmp/workdir/static/images/'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Placeholder id
chat_id = "02e8ifno32"

def handle_message(message, user):
    '''
        Parse the message and determine how to proceed.

        This will either return a value to close the
        stream, or return a message to broadcast to all
        connections.

        Cases:
            '/quit' - return a value to quit the stream
            '</br><center' - this is a header message
                check to see if it is associated with the
                current user
            '^<b>.*</b>: ' - this is a regular message
                check to see if it is associated with the
                current user

        If the message is associated with the current
        user, append it to the redis DB chat list.

        Each stream will process these messages.
        In order to verify that we do not create
        duplicates in the database, we must ensure that
        it is only added once.  This is done by checking
        the associated user.
    '''
    text = str(message['data'])

    # HTML encode to avoid XSS attacks
    text = text.replace("<", "&lt;").replace(">", "&gt;")

    # Check to see if the user is leaving
    if text[0:5] == "/quit":
        if text[6:] == user:
            return "quit"

    # Format header message
    if text[0:7] == "/header":
        text = '</br><center class="{user}" style="font-size:1.5em;font-weight:bold;">{message}</center>'.format(user=user, message=text[8:])

    # Format action message
    elif text[0:4] == "/act":
        text = '<b>{user}</b>: <strong>{message}</strong>'.format(user=user, message=text[5:])

    # Format default message
    else:
        text = '<b>{user}</b>: {message}'.format(user=user, message=text)

    msg_user_m = re.search('^<b>(.*)</b>: ', text)
    mine = False

    # Check to see if it is a header message
    if '</br><center' in text:
        if 'class="{user}"'.format(user=user) in text:
            mine = True

    # Check to see who the user user
    if msg_user_m:
        msg_user = msg_user_m.group(1)
        mine = True if msg_user == user else False

    # Add the message to the DB if the user matches
    # and return the message back to the event_stream()
    if message['type'] != 'subscribe':
        if mine:
            red.rpush(chat_id + ":chat", text)
        return 'data: {text}\n\n'.format(text=text)


def event_stream(user):
    '''
        Create an event stream for each user.

        Create a redis publish/subscribe object
        and subscribe to the 'chat' channel.  Listen
        to the connection, pass message parsing off
        to the handle_message method, and yield data
        whenever applicable.  Yielded data will be sent
        to the chat channel.

        The first thing this method does is publish
        a quit message for the current user.  Since
        this is a new stream, it will enforce that only
        one stream is ever associated with a user.
        Any other connection with this username will be
        disconnected.
    '''

    # Disconnect all other sessions with this username
    red.publish('chat', u'/quit %s' % (user))

    # Subscribe to the chat, listen, and yield messages
    # to clients
    pubsub = red.pubsub()
    pubsub.subscribe('chat')
    for message in pubsub.listen():
        parsed = handle_message(message, user)
        if parsed:
            if parsed == "quit":
                break
            else:
                yield parsed


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
        # HTML encode to avoid XSS attacks
        user = flask.request.form['user'].replace("<", "&lt;").replace(">", "&gt;")

        # Check to see if the user exists
        if red.exists(user.lower()):

            # If they exist, authenticate and redirect
            if sha256_crypt.verify(flask.request.form['pwd'], red.hget(user.lower(), 'pwd')):
                flask.session['user'] = user
                return flask.redirect('/')
            else:
                # Reload and provide error on auth failure
                return flask.render_template('login.html', username=user, error=True)
        else:
            # If user does not exist, create account and redurect
            red.hmset(user.lower(), {'name':user,'pwd':sha256_crypt.encrypt(flask.request.form['pwd'])})
            flask.session['user'] = user
            return flask.redirect('/')

    return flask.render_template('login.html', username="", error=False)


@app.route('/post', methods=['POST'])
def post():
    '''
        Publish new messages to the event_stream().

        Return status 204 as the event_stream() will
        pickup the information from redis and provide
        new content.
    '''
    # Publish the message to chat
    red.publish('chat', flask.request.form['message'])

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

        This is triggered with the Javascript
        window.onbeforeunload function in the
        template/index.html file.
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

        # Check to make sure the file is allowed
        if file and allowed_file(file.filename):

            # Create secure filename
            filename = str(time.time()).split(".")[0] + "-" + secure_filename(file.filename)
            rel_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # Save the file
            file.save(rel_path)

            # Remove the file if corrupt
            if os.stat(rel_path).st_size < 1:
                os.remove(rel_path)

    # Get all images
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
