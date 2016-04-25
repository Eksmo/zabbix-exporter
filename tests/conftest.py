# coding: utf-8
from functools import partial

import pytest
from pytest_localserver.http import WSGIServer
from werkzeug.wrappers import Response, Request


def zabbix_fake_app(environ, start_response):
    request = Request(environ)
    request_body = request.get_data(as_text=True)

    if getattr(zabbix_fake_app, 'status', False):
        response = Response(status=zabbix_fake_app.status)
        response.data = zabbix_fake_app.content
        return response(environ, start_response)

    response = Response(status=200, headers=[('Content-type', 'application/json')])
    if '"method": "user.login"' in request_body:
        json_string = '{"jsonrpc":"2.0","result":"9287f336ffb611e586aa5e5517507c66","id":0}'
    elif '"method": "host.get"' in request_body:
        json_string = open('tests/fixtures/host.get_success.json').read()
    elif '"method": "item.get"' in request_body:
        json_string = open('tests/fixtures/items.get_success.json').read()
    else:
        json_string = 'Unrecognized test request'
    response.data = json_string
    return response(environ, start_response)


@pytest.fixture()
def zabbixserver(request):
    server = WSGIServer(application=zabbix_fake_app)
    server.start()
    request.addfinalizer(server.stop)
    def func():
        if getattr(server.app, 'status', None):
            del server.app.status
            del server.app.content
    request._addfinalizer(func, scope='function')
    def serve_content(self, content, status=200):
        self.app.content = content
        self.app.status = status
    server.serve_content = partial(serve_content, server)
    return server
