import re

def html_encode(text):
    '''Encode text to avoid XSS attacks.'''
    return text.replace("<", "&lt;").replace(">", "&gt;")


def generate_html(text, user):
    '''
        Format HTML based on the message type.

        Parameters:
            text - the message to be formatted
            user - the user that entered the message

        Output:
            text - the formatted message
            type - the message type (header, action, default)

        Cases:
            header  - large centered text with no username
            action  - bolded text similar to default
            default - plain message
    '''
    type = ''

    # Format header message
    if text[0:7] == "/header":
        type = "header"
        text = '</br><center class="{user}" style="font-size:1.5em;font-weight:bold;">{message}</center>'.format(user=user, message=text[8:])

    # Format action message
    elif text[0:4] == "/act":
        type = "action"
        text = '<b>{user}</b>: <strong>{message}</strong>'.format(user=user, message=text[5:])

    # Format default message
    else:
        type = "default"
        text = '<b>{user}</b>: {message}'.format(user=user, message=text)

    return text, type


def handle_message(message, stream_user):
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
    # Ignore the message if it is a subscription
    if message['type'] == 'subscribe':
        return

    # Convert text to a string
    text = str(message['data'])

    # HTML encode to avoid XSS attacks
    text = html_encode(text)

    # Check to see if the user is leaving
    if text[0:5] == "/quit":
        if text[6:] == stream_user:
            return "quit", True

    # Extract username
    sep = text.split("}|{")
    msg_user = sep[0]
    text = sep[1]

    # Generate HTML formatting
    text, type = generate_html(text, msg_user)

    # Determine if the message belongs to the stream user
    mine = True if msg_user == stream_user else False

    # Add the message to the DB if the user matches
    # and return the message back to the event_stream()
    return text, mine
