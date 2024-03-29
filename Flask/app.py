from flask import Flask, render_template, url_for, session, abort, redirect
from authlib.integrations.flask_client import OAuth
import json
from urllib.parse import quote_plus, urlencode

app = Flask(__name__)

ip_keycloak_internal = 'keycloak'
ip_keycloak_external = 'localhost'
ip_keycloak = 'keycloak'

appConf = {
    "OAUTH2_CLIENT_ID": "test_web_app",
    "OAUTH2_CLIENT_SECRET": "FXv2ugPyXsF2hN46EoAL3bmvx5MiUdHf",
    # Uso dos issuer porque internamente el contenedor de Flask accede al container de keycloak por keycloak:8080
    # Y el usuario será redirigido a localhost:8080
    "OAUTH2_ISSUER_INTERNAL": f"http://localhost:8080/realms/myorg",
    "OAUTH2_ISSUER_EXTERNAL": f"http://localhost:8080/realms/myorg",
    # El issuer sin mas es el original
    "OAUTH2_ISSUER": f"http://keycloak:8080/realms/myorg",
    "FLASK_SECRET": "ALongRandomlyGeneratedString",
    "FLASK_PORT": 80
}

app.secret_key = appConf.get("FLASK_SECRET")

oauth = OAuth(app)
oauth.register(
    "myApp",
    client_id=appConf.get("OAUTH2_CLIENT_ID"),
    client_secret=appConf.get("OAUTH2_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
        'code_challenge_method': 'S256'    # enable PKCE
    },
    server_metadata_url=f'{appConf.get("OAUTH2_ISSUER_INTERNAL")}/.well-known/openid-configuration'
)


@app.route('/')
def home():
    return render_template('index.html', session=session.get("user"), pretty=json.dumps(session.get("user"), indent=4))

@app.route('/login')
def login():
    # check if session already present
    if "user" in session:
        abort(404)
    return oauth.myApp.authorize_redirect(redirect_uri=url_for("callback", _external=True))  #+ '/protocol/openid-connect/auth'

@app.route("/logout")
def logout():
    id_token = session["user"]["id_token"]
    session.clear()
    return redirect(
        appConf.get("OAUTH2_ISSUER_INTERNAL") + "/protocol/openid-connect/logout?"
            + urlencode(
            {
                "post_logout_redirect_uri": url_for("loggedout", _external=True),
                "id_token_hint": id_token
            },
            quote_via=quote_plus,
        )
    )

@app.route("/loggedout")
def loggedout():
    if "user" in session:
        abort(404)
    return redirect(url_for("home"))

@app.route('/callback')
def callback():
    token = oauth.myApp.authorize_access_token()
    session["user"] = token
    return redirect(url_for("home"))
    

@app.route('/login_okta')
def login_okta():
    # check if session already present
    if "user" in session:
        abort(404)
    return oauth.myApp.authorize_redirect(redirect_uri=appConf.get("OAUTH2_ISSUER_INTERNAL") + '/protocol/openid-connect/auth')



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
