""" Views """
import logging
import traceback
from pyramid.httpexceptions import HTTPException, HTTPFound, HTTPServerError
from pyramid.settings import asbool
from pyramid.view import view_config
from pyramid_duh import addslash

from pypicloud import __version__
from pypicloud.route import Root


LOG = logging.getLogger(__name__)


@view_config(context=Root, request_method='GET', subpath=(),
             renderer='base.jinja2')
@addslash
def get_index(request):
    """ Render a home screen """
    authenticated_index = \
        request.registry.settings.get('pypi.authenticated_index', 'false')

    if 'true' == authenticated_index.lower() and request.userid is None:
        login_url = '{}/{}'.format(request.app_url().rstrip('/'), 'login')
        return HTTPFound(location=login_url)

    return {
        'version': __version__,
    }


@view_config(route_name='health', renderer='string')
def health_endpoint(request):
    """ Simple health endpoint """
    return 'OK'


@view_config(context=Exception, renderer='json')
@view_config(context=HTTPException, renderer='json')
def format_exception(context, request):
    """
    Catch all app exceptions and render them nicely

    This will keep the status code, but will always return parseable json

    Returns
    -------
    error : str
        Identifying error key
    message : str
        Human-readable error message
    stacktrace : str, optional
        If pyramid.debug = true, also return the stacktrace to the client

    """
    message = context.message if hasattr(context, 'message') else str(context)
    LOG.exception(message)
    if not request.path.startswith('/api/') and \
            not request.path.startswith('/admin/'):
        if isinstance(context, HTTPException):
            return context
        else:
            return HTTPServerError(message)
    error = {
        'error': getattr(context, 'error', 'unknown'),
        'message': message,
    }
    if asbool(request.registry.settings.get('pyramid.debug', False)):
        error['stacktrace'] = traceback.format_exc()
    request.response.status_code = getattr(context, 'status_code', 500)
    return error
