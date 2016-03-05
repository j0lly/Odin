import flask

app = flask.Flask(__name__)

@app.route('/sync/<ip>')
def sync_resolve(ip):
    for resource in ip:
        try:
            s = resolver.Resolve(resource)
            dns = s.resolve()
        except:
            return flask.jsonify({resource: 'NaN'})
        try:
            version = s.version()
        except:
            pass
    res = {ip: {**dns, **version}}
    return flask.jsonify(**res)
