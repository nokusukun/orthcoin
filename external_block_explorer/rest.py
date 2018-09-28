from flask import Flask, render_template, send_from_directory, abort, request, session, redirect, send_file, url_for, jsonify, Response
import flask
import os

app = Flask(__name__, static_url_path='/static', static_folder='static')



@app.route("/")
def index():
    return send_from_directory('templates', "explorer-all.html")

@app.route("/search")
def search_page():
    return send_from_directory('templates', "search.html")

@app.route("/login")
def login_page():
    return send_from_directory('templates', "login.html")

@app.route("/dashboard")
def dashboard_page():
    return send_from_directory('templates', "dashboard.html")

@app.route("/dashboard/places")
def dashboard_places_page():
    return send_from_directory('templates', "dashboard-places.html")

@app.route("/dashboard/places/new")
def dashboard_places_new_page():
    return send_from_directory('templates', "dashboard-places-new.html")

@app.route("/dashboard/places/new/test")
def dashboard_places_new_page_2():
    return send_from_directory('templates', "dashboard-places-new-test.html")

@app.route("/dashboard/places/edit")
def dashboard_places_edit_page():
    return send_from_directory('templates', "dashboard-places-edit.html")

@app.route("/dashboard/admin")
def dashboard_admin():
    return send_from_directory('templates', "dashboard-admin.html")

@app.route("/dashboard/admin/users")
def dashboard_admin_users():
    return send_from_directory('templates', "dashboard-admin-users.html")

@app.route("/dashboard/jeeproutes/new")
def dashboard_jeeproutes_new():
    return send_from_directory('templates', "dashboard-jeeproutes-new.html")

@app.route("/dashboard/jeeproutes")
def dashboard_jeeproutes():
    return send_from_directory('templates', "dashboard-jeeproutes.html")

@app.after_request
def after_request(response):
  response.headers.add('Access-Control-Allow-Origin', '*')
  response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
  response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
  return response

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 80))
    app.config['TEMPLATES_AUTO_RELOAD']=True
    app.run(host="0.0.0.0", port=port, debug=True,use_reloader=True)
    #waitress.serve(app, port=port)
    #app.run(host='0.0.0.0', port=port)