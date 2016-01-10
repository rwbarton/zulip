from __future__ import absolute_import

from django.http import HttpResponse, HttpResponseNotAllowed
from django.conf import settings
import ujson

class HttpResponseUnauthorized(HttpResponse):
    status_code = 401

    def __init__(self, realm):
        HttpResponse.__init__(self)
        self["WWW-Authenticate"] = 'Basic realm="%s"' % (realm,)

def json_unauthorized(message):
    resp = HttpResponseUnauthorized("zulip")
    resp.content = ujson.dumps({"result": "error",
                                "msg": message}) + "\n"
    return resp

def json_method_not_allowed(methods):
    resp = HttpResponseNotAllowed(methods)
    resp.content = ujson.dumps({"result": "error",
        "msg": "Method Not Allowed",
        "allowed_methods": methods})
    return resp

def json_response(res_type="success", msg="", data={}, status=200):
    content = {"result": res_type, "msg": msg}
    content.update(data)
    resp = HttpResponse(content=ujson.dumps(content) + "\n",
                        content_type='application/json', status=status)
    # See Note [JSON load balancing and CORS]
    resp['Access-Control-Allow-Origin'] = settings.EXTERNAL_URI_SCHEME + \
                                          settings.EXTERNAL_HOST
    resp['Access-Control-Allow-Credentials'] = 'true'
    return resp

def json_success(data={}):
    return json_response(data=data)

def json_error(msg, data={}, status=400):
    return json_response(res_type="error", msg=msg, data=data, status=status)

def json_unhandled_exception():
    return json_response(res_type="error", msg="Internal server error", status=500)


# Note [JSON load balancing and CORS]
#
# We would like to be able to load balance between several different
# Zulip server hostnames when making JSON requests from the web
# client. This might be either for actual load balancing, or just to
# work around browser per-server connection limits: there is always a
# request to /json/get_events in progress, so if all those requests
# use the same host name, and if a user has more than about six tabs
# open to Zulip, some of those tabs will stop working.
#
# Typically the Zulip web client will be served from a hostname like
# zulip.example.com, and the JSON queries will be served from
# hostnames like e28.zulip.example.com.
#
# In order to make correctly authenticated XMLHttpRequests against a
# Zulip JSON server at a different hostname than the web client was
# loaded from, we must take care of the following CORS-related issues:
#
#  * We need to set the domain on our cookies to include the JSON
#    server hostname, like '.zulip.example.com'. This is currently
#    done by setting the 'cookie_domain' setting in zulip.conf.
#
#  * We need to set the withCredentials attribute when we perform an
#    XMLHttpRequest, so that the browser will send our cookies.
#
#  * We need to ensure that we also send a matching CSRF token either
#    in the X-CSRFToken header or in the request body. Setting a
#    custom header requires an extra OPTIONS request, so we send it in
#    the request body instead.
#
#  * We need to set the Access-Control-Allow-Origin and
#    Access-Control-Allow-Credentials headers in our JSON responses,
#    or the browser will not make the response available to the web
#    client.
#
# For more information on CORS, see
# https://developer.mozilla.org/en-US/docs/Web/HTTP/Access_control_CORS#Requests_with_credentials
