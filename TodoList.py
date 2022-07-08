## import all dependencies
import os
import pathlib
import json

import requests
from flask import Flask, session, request, Response, jsonify, abort, redirect
from pathlib import Path
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
from flask_sqlalchemy import SQLAlchemy

import sqlite3


# app initialize

app = Flask(__name__)
app.secret_key = "MySecretKey"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# copy the client id which is in the client_secret.json
GOOGLE_CLIENT_ID = "1089819441593-ruj5et2v4u43bf19k8558pf58bo2jf2i.apps.googleusercontent.com"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

# copy the scopes which is in the client_secret.json
flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="http://127.0.0.1:1234/callback"
)


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(100))
    status = db.Column(db.String(50))
    
class Item:
	id = ""
	task = ""
	status = ""
	
	def __init__(self, id, task, status):
		self.id = id
		self.task = task
		self.status = status
		
	def ListItem(self):
		Item = {"id":self.id, "task":self.task, "status":self.status}
		return Item
		
ToDoList = []

#### function to create / connect to database
def connect_to_db():
    conn = sqlite3.connect('db.sqlite')
    return conn

#function to create db table
def create_db_table():
    try:
        conn = connect_to_db()
        conn.execute('''
            CREATE TABLE Item (
                id INTEGER PRIMARY KEY NOT NULL,
                task TEXT NOT NULL,
                status TEXT NOT NULL
            );
        ''')
        
        conn.commit()
        print("Item table created successfully")
    except:
        print("Item table creation failed")
    finally:
        conn.close()
    
    
#### security function to prevent any access without login        
def login_is_required(function):
    def wrapper(*args, **kwargs):
    	if "google_id" not in session:
    	    return abort(401) # Athorization required
    	else:
    	    return function()
    return wrapper

#### index page with login button
@app.route("/")
def index():
    create_db_table()
    return "Welcome to my world <a href='/login'><button>Login</button></a>"

#### login page which will redirect to google login
@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

#### call back page after login    
@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )

    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    return redirect("/Home")
    
    
#### home page after login 
@app.route("/Home")
@login_is_required
def protected_area():
    db.create_all()
    return f"Hello {session['name']}! <br/> <a href='/Todo/List'><button>All Items</button></a> <br/> <a href='/logout'><button>Logout</button></a>"


#### logout page
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


#### Function to list all to do items
@app.route("/Todo/List")
def ListAll():
    print(request.method)
    todo_list = Todo.query.all()
    print(todo_list)
    
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Todo")
    results = cursor.fetchall()
    
    return jsonify(results)
    
#### function to create new to do item
@app.route("/Todo/Add", methods=["POST"])
def CreateNewToDoItem():
   item=Item(**request.get_json())
   ToDoList.append(item.ListItem())
   task = item.task
   new_item = Todo(task=task, status="Ready")
   
   db.session.add(new_item)
   db.session.commit()
   
   return Response('{"message":"success"}', status=201, mimetype='application/json')

#### function to list out one to do item by item id
@app.route("/Todo/List/<id>")
def GetItemById(id):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Todo WHERE id=?",(id))
    
    row = cursor.fetchall()
    return jsonify(row)
    
#### function to update to do item
@app.route("/Todo/Update", methods=["PUT"])
def UpdateTodoItem():
    item=Item(**request.get_json())
    isExist = False
    print(item.task)
    conn = connect_to_db()
    cursor = conn.cursor()
    
    sql_update_query = """Update ToDo SET task = ?, status = ? where id = ?"""
    data = (item.task, item.status, item.id)
    isExist = cursor.execute(sql_update_query, data)
    conn.commit()
    print("Record Updated successfully")
    cursor.close()
               
    if isExist:
        response = jsonify({"message":"item updated successfully"})
        response.status_code = 201
        return response
    else:
        response = jsonify({"message":"item not exist"})
        response.status_code = 404
        return response
 
 #### function to delete to do item       
@app.route("/Todo/List/<id>", methods=["DELETE"])
def DeleteItem(id):
    print(id)
    conn = connect_to_db()
    cursor = conn.cursor()
    
    sql_update_query = """DELETE FROM Todo WHERE id=?"""
    data = (id)
    cursor.execute(sql_update_query, data)
    conn.commit()
    cursor.close()
    response = jsonify({"message":"item updated successfully"})
    return response

### initiazation of running app.
if __name__ == "__main__":
    app.run(port=1234, host="0.0.0.0")
    db.create_all()
    print(request.method)
    
