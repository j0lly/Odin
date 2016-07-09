import flask
from .store import OpenDnsModel

app = flask.Flask(__name__)

@app.route('/show/<ip>')
def sync_resolve(ip):
    s = OpenDnsModel(ip)
    s.dns_scan()
    return flask.jsonify(s.attribute_values)
