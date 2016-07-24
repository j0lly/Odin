import flask
import queue
from flask import request
from .store import OpenDnsModel, ThreadedModel
from .utils import findip

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
        ip_list = findip(ip_range)
    except:
        return 'invalid ip range provided!'
    #TODO add throttling
    for ip in ip_list:
        obj = ThreadedModel(ip, queue=my_queue)
        obj.daemon=True
        threads.append(obj)
    for thread in threads:
        thread.start()
        thread.join(timeout=4)

    while not my_queue.empty():
        ip_info = my_queue.get()
        result.update({ip_info['ip'] : ip_info})

    return flask.jsonify(result)
