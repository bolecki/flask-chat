import unittest
from chat import msg_handler

class MessageHandlerTests(unittest.TestCase):

    # Testing html_encode(text)
    def test_html_encode_equals(self):
        self.assertEqual(msg_handler.html_encode('<b>hi</b>'), '&lt;b&gt;hi&lt;/b&gt;')

    # Testing generate_html(text, user)
    def test_generate_html_default(self):
        self.assertEqual(msg_handler.generate_html('hi', 'test'), 
            ('<b>test</b>: hi', 'default'))

    def test_generate_html_action(self):
        self.assertEqual(msg_handler.generate_html('/act hi', 'test'), 
            ('<b>test</b>: <strong>hi</strong>', 'action'))

    def test_generate_html_header(self):
        self.assertEqual(msg_handler.generate_html('/header hi', 'test'), 
            ('</br><center class="test" style="font-size:1.5em;font-weight:bold;">hi</center>', 'header'))

    def test_generate_html_link(self):
        self.assertEqual(msg_handler.generate_html('/link hi', 'test'), 
            ('<b>test</b>: <a target="_blank" href="hi">hi</a>', 'link'))

    # Testing handle_message(message, stream_user)
    def test_handle_message_quit(self):
        message = {'type': 'message', 'data': '/quit test'}
        self.assertEqual(msg_handler.handle_message(message, 'test'), ('quit', True))

    def test_handle_message_subscribe(self):
        message = {'type': 'subscribe', 'data': '/quit test'}
        self.assertEqual(msg_handler.handle_message(message, 'test'), None)

    def test_handle_message_default_mine(self):
        message = {'type': 'message', 'data': 'test}|{hi'}
        self.assertEqual(msg_handler.handle_message(message, 'test'), 
            ('<b>test</b>: hi', True))

    def test_handle_message_default_not_mine(self):
        message = {'type': 'message', 'data': 'another}|{hi'}
        self.assertEqual(msg_handler.handle_message(message, 'test'), 
            ('<b>another</b>: hi', False))

    def test_handle_message_action_mine(self):
        message = {'type': 'message', 'data': 'test}|{/act hi'}
        self.assertEqual(msg_handler.handle_message(message, 'test'), 
            ('<b>test</b>: <strong>hi</strong>', True))

    def test_handle_message_action_not_mine(self):
        message = {'type': 'message', 'data': 'another}|{/act hi'}
        self.assertEqual(msg_handler.handle_message(message, 'test'), 
            ('<b>another</b>: <strong>hi</strong>', False))

    def test_handle_message_header_mine(self):
        message = {'type': 'message', 'data': 'test}|{/header hi'}
        self.assertEqual(msg_handler.handle_message(message, 'test'), 
            ('</br><center class="test" style="font-size:1.5em;font-weight:bold;">hi</center>', True))

    def test_handle_message_header_not_mine(self):
        message = {'type': 'message', 'data': 'another}|{/header hi'}
        self.assertEqual(msg_handler.handle_message(message, 'test'), 
            ('</br><center class="another" style="font-size:1.5em;font-weight:bold;">hi</center>', False))
