import identity.web
import requests
import os
from flask import Flask, redirect, render_template, request, session, url_for
from flask_session import Session
import OpenSSL.SSL
import subprocess
import tempfile
import ssl


# Paths to certificate file and key file
CERT_FILE = '/etc/letsencrypt/live/ast283.x310.net/fullchain.pem'
KEY_FILE = '/etc/letsencrypt/live/ast283.x310.net/privkey.pem'

# sudo privileges to read the contents of the certificate file and key file
cert_content = subprocess.check_output(['sudo', 'cat', CERT_FILE]).decode('utf-8')
key_content = subprocess.check_output(['sudo', 'cat', KEY_FILE]).decode('utf-8')

# Create temporary files and write certificate and key content to them
with tempfile.NamedTemporaryFile(delete=False) as cert_file:
    cert_file.write(cert_content.encode('utf-8'))
    cert_path = cert_file.name

with tempfile.NamedTemporaryFile(delete=False) as key_file:
    key_file.write(key_content.encode('utf-8'))
    key_path = key_file.name

# Create an SSL context
context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain(certfile=cert_path, keyfile=key_path)

# The following variables are required for the app to run.

# TODO: Use the Azure portal to register your application and generate client id and secret credentials.
CLIENT_ID = "228e74e3-85d9-44e1-8fa0-fbc5b96a0c3e"
CLIENT_SECRET = "" # Client Secret must be generated in the Azure portal

# TODO: Figure out your authentication authority id.
AUTHORITY = "https://login.microsoftonline.com/0cff9966-b3c0-4a41-9874-3c22e287ab4c"

# TODO: generate a secret. Used by flask session for protecting cookies.
SESSION_SECRET = "test"

# TODO: Figure out what scopes you need to use
SCOPES = ["User.Read", "User.ReadBasic.All", "User.ReadWrite"]

# TODO: Figure out the URO where Azure will redirect to after authentication. After deployment, this should
#  be on your server. The URI must match one you have configured in your application registration.
REDIRECT_URI = "http://localhost:5566/getAToken"

REDIRECT_PATH = "/getAToken"

app = Flask(__name__)

app.config['SECRET_KEY'] = SESSION_SECRET
app.config['SESSION_TYPE'] = 'filesystem'
app.config['TESTING'] = True
app.config['DEBUG'] = True
Session(app)

# The auth object provide methods for interacting with the Microsoft OpenID service.
auth = identity.web.Auth(session=session,
                         authority=AUTHORITY,
                         client_id=CLIENT_ID,
                         client_credential=CLIENT_SECRET)

@app.route("/login")
def login():
    # TODO: Use the auth object to log in.
    response = {}
    return render_template("login.html", **auth.log_in(
        scopes=SCOPES, # Have user consent to scopes during log-in
        redirect_uri=url_for("auth_response", _external=True), # Optional. If present, this absolute URL must match your app's redirect_uri registered in Microsoft Entra admin center
        prompt="select_account",  # Optional.
        ))


@app.route(REDIRECT_PATH)
def auth_response():
    # TODO: Use the flask request object and auth object to complete the authentication.
    result = auth.complete_log_in(request.args)
    if "error" in result:
        return render_template("auth_error.html", result=result)
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    # TODO: Use the auth object to log out and redirect to the home page
    return redirect(auth.log_out(url_for("index", _external=True)))


@app.route("/")
def index():
    # TODO: use the auth object to get the profile of the logged in user.
    if not auth.get_user():
        return redirect(url_for("login"))
    return render_template('index.html', user=auth.get_user())


@app.route("/profile", methods=["GET"])
def get_profile():

    # TODO: Check that the user is logged in and add credentials to the http request.
    token = auth.get_token_for_user(SCOPES)
    if "error" in token:
        return redirect(url_for("login"))

    result = requests.get(
        'https://graph.microsoft.com/v1.0/me',
        headers={'Authorization': 'Bearer ' + token['access_token']},
        timeout=30,
    )

    return render_template('profile.html', user=result.json(), result=None)

@app.route("/profile", methods=["POST"])
def post_profile():

    # TODO: check that the user is logged in and add credentials to the http request.
    token = auth.get_token_for_user(SCOPES)
    if "error" in token:
        return redirect(url_for("login"))
    
    user = auth.get_user()
    user["oid"]

    result = requests.patch(
        'https://graph.microsoft.com/v1.0/users/' + request.form.get("id"),
        json=request.form.to_dict(),
        headers={'Authorization': 'Bearer ' + token['access_token'],
                 'Content-Type': 'application/json'},
        timeout=30,
    )

    # TODO: add credentials to the http request.
    profile = requests.get(
        'https://graph.microsoft.com/v1.0/me',
        headers={'Authorization': 'Bearer ' + token['access_token']},
        timeout=30,
    )
    return render_template('profile.html',
                           user=profile.json(),
                           result=result)


@app.route("/users")
def get_users():

    # TODO: Check that user is logged in and add credentials to the request.
    token = auth.get_token_for_user(SCOPES)
    if "error" in token:
        return redirect(url_for("login"))

    result = requests.get(
        'https://graph.microsoft.com/v1.0/users',
        headers={'Authorization': 'Bearer ' + token['access_token']},
        timeout=30,
    )
    return render_template('users.html', result=result.json())


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5566, ssl_context=context)