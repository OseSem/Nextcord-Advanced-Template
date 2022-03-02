import json

with open("botconfig/config.json") as cf:
    config = json.load(cf)

with open("botconfig/token.0") as tf:
    bot_token = tf.read()

class botconfig:
    def config(returner):
        return config[f'{returner}']
    def token():
        return bot_token