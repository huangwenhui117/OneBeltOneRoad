from flask import Flask, render_template, request
from flask_socketio import SocketIO, send
import json
from pymongo import MongoClient

import game_engine


mongo_client = MongoClient("mongo")
db = mongo_client["proj"]
users_info_collection = db["users_info"]
app = Flask(__name__, static_url_path="/static")
app.config['SECRET'] = "secret!123"
socketio = SocketIO(app, cors_allowed_origins="*")

dic_users = {}

@app.route('/')
def index():  # put application's code here
    return render_template("index.html", amount_ready=str(len(game_engine.ready_list)))

@socketio.on('message')
def handle_message(message):
    # print("Received message: " + message)
    game_engine.alert_status = []
    if "User connected!" in message:
        game_engine.users.append(int(message.split(":")[0]))
        # print("Connect Successful")
    elif "User ready!" in message:
        user_id = int(message.split(":")[0])
        if user_id not in game_engine.ready_list:
            game_engine.ready_list.append(user_id)
            send(json.dumps(["ready", game_engine.ready_list]), broadcast=True)
        if len(game_engine.ready_list) == 4:
            for i in range(0, len(game_engine.ready_list)):
                game_engine.users_info[i]["user_id"] = game_engine.ready_list[i]
                game_engine.users = game_engine.ready_list
            
            # users_info_collection.insert_one({"datatype": "status", "users": game_engine.users_info})
            send(json.dumps(["start", {"roll_num": 1, "user": game_engine.users_info}]), broadcast=True)
    elif "sign in" in message:
        id, name, password = message_analysis(message)
        print(id + "'s username is:" + name + ", password is:" + password)
    elif "sign up" in message:
        id, name, password = message_analysis(message)
        print(id + "'s username is:" + name + ", password is:" + password)
    else:
        term_info = json.loads(message)
        roll_num = game_engine.roll_dice()
        ret_game_states = game_engine.game_func(term_info, roll_num)
        if type(ret_game_states) == str:
            
            # users_info_collection.delete_one({"datatype": "status"})
            send(json.dumps(["end", ret_game_states]))
        # for i in range(0, len(game_engine.ready_list)):
        #     ret_game_states[i]["user_id"] = game_engine.ready_list[i]
        send(json.dumps(["game", {"roll_num": roll_num, "user": ret_game_states}, game_engine.alert_status]), broadcast=True)

def message_analysis(message):
    name, password = "", ""
    user_id = str(message.split(":")[0])
    name = str(message.split(":")[2])
    password = str(message.split(":")[3])
    return user_id, name, password
    

if __name__ == '__main__':
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)
    # app.run()


