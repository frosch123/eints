"""
Bottle authentication decorator.
"""
from webtranslate.bottle import request, abort, error, response, redirect
from webtranslate import users, config

@error(401)
def handle401(error):
    response.set_header('WWW-Authenticate', 'Basic realm="Web translator"')
    return 'Access denied'

METHODS = {'GET': 'read', 'POST': 'add', 'PUT': 'set', 'DELETE': 'del'}

def protected(page_name):
    """
    Decorator for adding basic authentication protection to a route.

    @param page_name: Name of the page being protected. Some of the parts may be
                      a pattern that has to be replaced with a real part when the
                      query is performed.
    @type  page_name: C{list} of C{str}
    """
    def decorator(func):
        def wrapper(*a, **ka):
            if request.auth is None:
                user, pwd = None, None
            else:
                user, pwd = request.auth

            pname = [ka.get(p, p) for p in page_name] + [METHODS.get(request.method, "-")]
            prjname = ka.get('prjname')
            lngname = ka.get('lngname')
            userauth = users.get_authentication(user, pwd, request.remote_addr)

            # We must read all uploaded content before returning a response.
            # Otherwise the connection may be closed by the server and the client aborts.
            for f in request.files:
                pass

            if userauth is None:
                # No authentication backend.
                abort(401, "Access denied")
            elif userauth.may_access(pname, prjname, lngname):
                # Access granted.
                return func(userauth, *a, **ka)
            elif not userauth.is_auth:
                # Not logged in.
                abort(401, "Access denied")
            elif prjname is not None and prjname in config.cache.projects:
                # Valid user, but insufficient permissions: Go to project page.
                redirect("/project/" + prjname.lower() + '?message=Access denied')
            else:
                # Valid user, no project context: Go to project list.
                redirect("/projects?message=Access denied")
            return
            
        return wrapper
    return decorator
