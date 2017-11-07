from flask import Flask, request, make_response
from slackclient import SlackClient
import os
import json
import requests

app = Flask(__name__)

SLACK_VERIFICATION_TOKEN = os.environ["SLACK_VERIFICATION_TOKEN"]
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_CHANNEL = os.environ["SLACK_CHANNEL"]
CLIENT = SlackClient(SLACK_BOT_TOKEN)

GROUPME_API = os.environ["GROUPME_API"]
GROUPME_BOT_ID = os.environ["GROUPME_BOT_ID"]

@app.route("/slack", methods=["POST"])
def slack_msg():
    event_data = json.loads(request.data)

    if "challenge" in event_data:
        return make_response(
            event_data.get("challenge"), 200, {"content_type": "application/json"}
        )

    if "event" in event_data:
        request_token = event_data.get("token")
        if SLACK_VERIFICATION_TOKEN != request_token:
            message = "Invalid Slack verification token"
            return make_response(message, 403)

        event_type = event_data["event"]["type"]
        if event_type == "message":
            msg = event_data["event"]
            # if msg["file"]:
            #     print json.dumps(msg["file"], indent=4)
                # public_file = CLIENT.api_call("files.sharedPublicURL", file=msg["file"]["id"])
            if msg.get("subtype") is None:
                user = CLIENT.api_call("users.info", user=msg["user"])
                user_name = user["user"]["profile"]["real_name_normalized"]
                msg_text = msg["text"]
                relay_text = "[%s]  %s" % (user_name, msg_text)
                res = requests.post("%s/bots/post" % GROUPME_API, params = {"bot_id": GROUPME_BOT_ID, "text": relay_text})
        # elif event_type == "file_created":
        #     print "hihiihi"
        #     obj_id = event_data["event"]["file_id"]
        #     obj = CLIENT.api_call("files.info", file=obj_id)
        #     print obj["file"]

        return make_response("", 200)

@app.route("/groupme", methods=["POST"])
def groupme_msg():
    event_data = json.loads(request.data)
    if event_data["sender_type"] == "user":
        user_name = event_data["name"]

        try:
            attach = event_data["attachments"][0]
            if attach["type"] == "image":
              CLIENT.api_call("chat.postMessage", channel=SLACK_CHANNEL, attachments=[{"text": "%s:" % user_name, "image_url": attach["url"]}])
        except Exception:
            pass

        msg_text = event_data["text"]
        if msg_text:
            relay_text = "*%s:* %s" % (user_name, msg_text)
            CLIENT.api_call("chat.postMessage", channel=SLACK_CHANNEL, text=relay_text)

    return make_response("", 200)


if __name__ == "__main__":
    app.run()
