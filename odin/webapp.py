# -*- coding: utf-8 -*-

"""api for Odin.

Defines an app object and serves few API endpoints"""

import queue
import flask
from flask import request, Response, Blueprint
import odin
from odin.store import OpenDnsModel
from odin.utils import (findip, run_scan,
                        generate_serialized_results, chunker)


# Default logging capabilities (logging nowhere)
log = odin.get_logger()

v1 = Blueprint('simple_page', __name__)

app = flask.Flask(__name__)
app.register_blueprint(v1, url_prefix='/v1')


@v1.route('/')
def get_all():
    """show open resolvers saved in the DB"""
    # Arbitrary limit default value of 50 results
    try:
        limit = int(request.args.get('limit', '50'))
        assert limit > 0
    except:
        return 'you need to pass a positive integet to limit parameter', 400

    query = OpenDnsModel.openresolvers_index.query(1,
                                                   limit=limit,
                                                   scan_index_forward=False)

    return Response(generate_serialized_results(
        query, output='json'),
                    mimetype='application/json')


@v1.route('/scan/<ip>', methods=['GET', 'POST'])
def scan_endpoint(ip):
    """Perform a single ip lookup

    :param ip: the ip passed in url
    :type ip: str
    """
    # TODO: sanity checks
    show = OpenDnsModel(ip)
    show.dns_scan()
    if request.method == 'POST':
        show.save()
        return flask.jsonify(show.serialize), 201
    return flask.jsonify(show.serialize)


@v1.route('/show/<ip>', methods=['GET'])
def show_endpoint(ip):
    """Perform a single get from dynamo

    :param ip: the ip passed in url
    :type ip: str
    """
    # TODO: sanity checks
    result = OpenDnsModel.get(ip)
    return flask.jsonify(result.serialize)


@v1.route('/batch', methods=['POST'])
def net_scan():
    """Perform a scan of a CIDR range provided as param and return it."""

    # FIXME moving to celery or similar
    my_queue = queue.Queue()
    ip_range = request.json
    try:
        network = ip_range['network']
    except Exception:
        return 'no range parameter specified!', 400
    try:
        ip_list = findip(network)
        ip_list = chunker(ip_list)
    except Exception:
        return 'invalid ip range provided!', 400

    try:
        # TODO add throttling, use celery
        result = []
        for obj in run_scan(my_queue, ip_list):
            result.append(obj)
    except:
        return 'failed to scan the ip list provided', 400
    try:
        with OpenDnsModel.batch_write() as batch:
            for ip in result:
                batch.save(ip)
    except:
        return 'batch failed to save to db', 400

    retval = {}
    for obj in result:
        retval.update({obj.ip: obj.serialize})
    return flask.jsonify(retval)
