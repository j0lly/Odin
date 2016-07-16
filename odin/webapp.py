import flask
import queue
from flask import request
from .store import OpenDnsModel, ThreadedModel
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
    threads = []
    my_queue = queue.Queue()
    try:
        ip_range = request.args.get('range')
    except:
        return 'no range parameter specified!'
    try:
        ips = findip(ip_range)
    except:
        return 'invalid ip range provided!'
    for ip in ips:
        s = ThreadedModel(ip, queue=my_queue)
        s.daemon=True
        threads.append(s)
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=4)
    while not my_queue.empty():
        chunk = my_queue.get()
        result.update({chunk['ip'] : chunk})
    return flask.jsonify(result)

