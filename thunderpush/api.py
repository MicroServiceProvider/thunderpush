import logging
import tornado.web
from thunderpush.sortingstation import SortingStation

logger = logging.getLogger()

try:
    import json
except ImportError:
    import simplejson as json 

def is_authenticated(f):
    """ Decorator used to check if a valid api key has been provided. """

    def run_check(self, *args, **kwargs):
        try:
            apisecret = self.request.headers['X-Thunder-Secret-Key']
        except KeyError:
            self.response({
                "status": "error", "message": "Missing apisecret header."
            }, 400)

            return

        ss = SortingStation.instance()
        messenger = ss.get_messenger_by_apikey(kwargs['apikey'])

        if not messenger or messenger.apisecret != apisecret:  
            self.response({
                "status": "error", "message": "Wrong API key/secret."
            }, 401)

            return

        # pass messenger instance to handler
        kwargs['messenger'] = messenger

        f(self, *args, **kwargs)
    return run_check

class ThunderApiHandler(tornado.web.RequestHandler):
    def response(self, data, code=200):
        self.write(json.dumps(data) + "\n")
        self.set_status(code)

class ChannelMessageHandler(ThunderApiHandler):
    """ Handler used for sending messages to channels. """

    @is_authenticated
    def post(self, *args, **kwargs):
        messenger = kwargs['messenger']
        channel = kwargs['channel']

        count = messenger.send_to_channel(channel, self.request.body)
        self.response({"status": "ok", "count": count})

        logger.debug("Message has been sent to %d users." % count)

class UserCountHandler(ThunderApiHandler):
    """ Retrieves the number of users online. """

    @is_authenticated
    def get(self, *args, **kwargs):
        messenger = kwargs['messenger']

        self.response({"status": "ok", "count": messenger.get_user_count()})