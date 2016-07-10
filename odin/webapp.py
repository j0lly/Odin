import flask
from flask import request
from .store import OpenDnsModel
from .core import findip

app = flask.Flask(__name__)

@app.route('/show/<ip>')
def sync_resolve(ip):
    s = OpenDnsModel(ip)
    s.dns_scan()
    return flask.jsonify(s.attribute_values)

@app.route('/scan/')
def net_scan():
    result = {}
    try:
        ip_range = request.args.get('range')
    except:
        return 'no range parameter specified!'
    try:
        ips = findip(ip_range)
    except:
        return 'invalid ip range provided!'
    for ip in ips:
        s = OpenDnsModel(ip)
        s.dns_scan()
        result.update({s.ip: s.attribute_values})
    return flask.jsonify(result)

