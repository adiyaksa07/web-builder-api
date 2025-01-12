from flask import Flask, request, jsonify
import pymysql.cursors

import json
import os

app = Flask(__name__)

ROUTE_FILE = "routes.json"

def load_routes():
    if os.path.exists(ROUTE_FILE):
        with open(ROUTE_FILE, "r") as f:
            return json.load(f)
    return {}

connection = pymysql.connect(host='localhost',
                             user='root',
                             password='',
                             database='roblox',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

def save_routes(routes):
    with open(ROUTE_FILE, "w") as f:
        json.dump(routes, f)

routes = load_routes()

@app.route("/get-like", methods=["POST"])
def get_like():
    data = request.get_json()
    username = data.get("username_players")

    if not username:
        return jsonify({"error": "Invalid data, 'username_players' is required"}), 400

    with connection.cursor() as cursor:
        
        sql = "SELECT username FROM players WHERE username = %s"
        cursor.execute(sql, (username,))
        fetch = cursor.fetchone()
        
        if fetch:
            sql = "SELECT likes FROM players WHERE username = %s"
            cursor.execute(sql, (username,))
            fetch = cursor.fetchone()
            data_like = fetch["likes"]
            return jsonify({"likes": f"{data_like}"}), 200
        else:
            print(f"Username {username} tidak ditemukan.")
            return jsonify({"error": f"tidak ditemukan data likes {username}"}), 404

@app.route("/set-html", methods=['POST'])
def set_html():
    data = request.get_json()
    owner = data.get("owner")
    url = data.get("url")
    html = data.get("html")

    if not owner:
        return jsonify({"error": "Invalid data, 'owner' is required"}), 400
    
    if owner == routes[url]["owner_blog"]:
        routes[url]["html"] = html

        save_routes(routes)

        return jsonify({"message": f"Route {routes[url]["html"]} added successfully!"}), 201
    else:
        return jsonify({"message": f"lu siapa?"}), 403

@app.route("/add-route", methods=["POST"])
def add_route():
    data = request.get_json()
    new_route = data.get("create_route")
    new_owner = data.get("who_owner")
    if not new_route:
        return jsonify({"error": "Invalid data, 'create_route' is required"}), 400

    if new_route in routes:
        return jsonify({"error": "Route already exists"}), 400

    routes[new_route] = {
        "owner_blog": new_owner,
        "html": f"Hello World, this my first website {new_owner}"
    }

    with connection.cursor() as cursor:
        sql = "INSERT INTO players (username, likes) VALUES (%s, %s)"
        cursor.execute(sql, (new_owner, 0,))
        connection.commit() 

    save_routes(routes)

    return jsonify({"message": f"Route {new_route} added successfully!"}), 201

@app.route("/")
def home():
    return "Welcome to the Flask Dynamic Route App!"

@app.route("/<path:dynamic_route>", methods=['GET', 'POST'])
def dynamic_handler(dynamic_route):
    if f"/{dynamic_route}" in routes:
        routes_data = routes[f"/{dynamic_route}"]
        if request.method == "POST":    
            if request.form.get("like") == "like":
                with connection.cursor() as cursor:

                    select_sql = "SELECT likes FROM players WHERE username = %s"
                    cursor.execute(select_sql, (routes_data["owner_blog"],))
                    data_like = cursor.fetchone()
                    
                    update_sql = "UPDATE players SET likes = %s WHERE username = %s"
                    cursor.execute(update_sql, (data_like['likes']+1, routes_data["owner_blog"],))
                    connection.commit()
       
        return f"""{routes_data["html"]} created by {routes_data["owner_blog"]}  <form method='post'><input type='submit' name='like' value='like'></input></form>""" +  " <script>  if ( window.history.replaceState ) {window.history.replaceState( null, null, window.location.href );} </script>"
   
    return "Route not found!", 404

if __name__ == "__main__":
    app.run(debug=True)
