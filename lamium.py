__version__ = '0.1'

__all__ = [
    'Resource', 'URL', 'Session', 'exceptions',
]

import requests
import requests.exceptions
import six
from six.moves.urllib import parse as urlparse

class Unit(object):

    '''Base class where common Lamium objects share code - not intended
    to be inherited directly outside of this module.'''

    def __init__(self, session, url):
        if not (isinstance(session, BaseSession)):
            err = 'session must be a Lamium session object, not %s' % type(session)
            raise ValueError(err)
        if not isinstance(url, six.string_types):
            err = 'url must be a string type, not %s' % type(url)
        self.__session__ = session
        self.__url__ = url

    def __call__(self, *args, **kwargs):
        '''Append additional '''
        fmt = self.__session__.format_url
        url = fmt(self.__url__, args, kwargs)
        return self.at(url)

    # Subclasses should use this to build another object of a similar
    # type at the given URL. By default, it presumes it can construct
    # an object of the same class as itself, passing the connection
    # object and the URL path as positional arguments.
    def at(self, url):
        '''I know where its at'''
        return self.__class__(self.__session__, url)

    def __str__(self):
        str_url = self.__url__
        if six.PY2 and isinstance(str_url, unicode):
            str_url = str_url.encode('utf-8')
        return str_url

    def __unicode__(self):
        return unicode(self.__url__)

    def __repr__(self):
        repr_me = '<{0.__class__.__name__} {0.__url__}>'.format(self)
        if six.PY2 and isinstance(repr_me, unicode):
            repr_me = repr_me.encode('utf-8', errors='ignore')
        return repr_me


class URL(Unit):

    '''Lightweight object used for easy construction of URLs, which can then
       be easily turned into a Resource object.'''

    @property
    def deURL(self):
        return self.__session__.at(self.__url__)

    def __getattr__(self, name):
        if name in self.__session__.__location_delegates__:
            return getattr(self.deURL, name)
        if name.startswith('__') and name.endswith('__'):
            raise AttributeError("%r: %s" % (self, name))
        return self(name)


_NOTGIVEN = object()

class BaseResource(Unit):

    @property
    def URL(self):
        return URL(self.__session__, self.__url__)

    def GET(self, **kwargs):
        '''Calls requests.get with the URL of this resource.'''
        return self.request('GET', **kwargs)

    def POST(self, data=None, **kwargs):
        '''Calls requests.post with the URL of this resource.'''
        return self.request('POST', data, **kwargs)

    def DELETE(self, **kwargs):
        '''Calls requests.delete with the URL of this resource.'''
        return self.request('DELETE', **kwargs)

    def HEAD(self, **kwargs):
        '''Calls requests.head with the URL of this resource.'''
        return self.request('HEAD', **kwargs)

    def PATCH(self, data=None, **kwargs):
        '''Calls requests.patch with the URL of this resource.'''
        return self.request('PATCH', data, **kwargs)

    def PUT(self, data=None, **kwargs):
        '''Calls requests.put with the URL of this resource.'''
        return self.request('PUT', data, **kwargs)

    def at(self, url):
        return self.__session__.at(self.__url__)


class BaseSession(object):

    __location_delegates__ = 'DELETE GET HEAD PATCH POST PUT'.split()
    resource_class = BaseResource

    def __init__(self, session=None):
        self.req_session = session or requests.Session()


class Resource(BaseResource):

    # aping tortilla here.
    def get(self, *args, **kwargs): # what about notfound=?
        if args:
            return self(*args).get(**kwargs)

        notfound = kwargs.pop('notfound', _NOTGIVEN)
        try:
            return self.load_response(self.GET(**kwargs))
        except (self.exceptions.NotFound, self.exceptions.Gone):
            if notfound is not _NOTGIVEN:
                return notfound
            raise

    def post(self, *args, **kwargs):
        content, options = self._process_parameters(args, kwargs)
        return self.send_content('POST', content, **options)

    def delete(self, **kwargs):
        return self.load_response(self.DELETE(**kwargs))

    def patch(self, *args, **kwargs):
        content, options = self._process_parameters(args, kwargs)
        return self.send_content('PATCH', content, **options)

    def put(self, *args, **kwargs):
        content, options = self._process_parameters(args, kwargs)
        return self.send_content('PUT', content, **options)

    def request(self, method, data=None, **kwargs):
        return self.__session__.request(method, self.__url__, data=data, **kwargs)

    def send_content(self, method, content, response=False, **kwargs):
        dispatcher = getattr(self, method)
        resp = dispatcher(data=content, **kwargs)
        if response:
            return resp
        return self.load_response(resp)

    def load_response(self, response):
        if 400 <= response.status_code < 600:
            self.raise_for_status(response)
        return response

    def raise_for_status(self, response):
        raise self.exceptions.exception_for_code(response.status_code)(response)

    def _process_parameters(self, args, kwargs):
        # What is the content we are going to send? If we use positional
        # arguments, then there should only be one, and all keyword arguments
        # are options to determine how we handle the request.
        if args:
            if len(args) == 1:
                content = args[0]
                options = kwargs
            else:
                raise ValueError('too many positional arguments for method')
        else:
            content = kwargs
            options = {}

        return content, options


class Session(BaseSession):

    __location_delegates__ = BaseSession.__location_delegates__ + 'delete get patch post put'.split()
    resource_class = Resource

    def request(self, method, url, **kwargs):

        try:
            return self.req_session.request(method, url, **kwargs)
        except requests.exceptions.Timeout:
            raise self.Timeout('{method} {path} [timeout={timeout}]'.format(
                method=method,
                path=urlparse.urlparse(url).path,
                timeout=kwargs['timeout'],
            ))

    def format_url(self, url, positionals, named):
        if not (named or positionals):
            e = 'requires at least one positional argument or keyword parameter'
            raise ValueError(e)
        if len(positionals) > 1: # Hmm.... why not allow multiple arguments?
            e = 'multiple positional arguments not supported' % len(positionals)
            raise ValueError(e)

        # First, deal with positionals.
        if positionals:
            element = positionals[0]
            if not isinstance(element, six.integer_types + six.string_types):
                err = 'element is not a string or integer type: %r'
                raise ValueError(err % element)
            element = six.text_type(element)

            # The element added is intended to be a child one. As such, it needs
            # to have a trailing slash to work correctly. Furthermore, we have
            # to drop anything like query string parameters.
            parts = urlparse.urlparse(url)
            if not parts.path.endswith('/'):
                element = '/' + element
            url = urlparse.urlunparse(
                list(parts[:2]) + [parts.path + element] + ['', '', ''])

        # Then any named parameters.
        if named:
            # If you don't want the original parameters, then you can overwrite
            # them by passing "params={}".
            urlparts = list(urlparse.urlparse(url))
            params_str = urlparse.urlencode(named, doseq=True)
            if urlparts[4]:
                urlparts[4] += '&' + params_str
            else:
                urlparts[4] = params_str
            url = urlparse.urlunparse(urlparts)

        return url

    def at(self, url):
        return self.resource_class(self, url)

    @classmethod
    def Root(cls, url, **kwargs):
        return cls(**kwargs).at(url)

# In a Python 3 only world, this would preferably be types.SimpleNamespace.
class exceptions(object):
    '''Namespace containing exception classes used by lamium module.'''

    class ErrorResponse(requests.exceptions.HTTPError):
        def __init__(self, response):
            self.status_code = response.status_code
            self.reason = response.raw.reason
            err = '{0.status_code} - {0.reason}'.format(self)
            requests.exceptions.HTTPError.__init__(self, err, response=response)

    class ClientError(ErrorResponse): pass
    class BadRequest(ClientError): pass
    class Unauthorized(ClientError): pass
    class Forbidden(ClientError): pass
    class NotFound(ClientError): pass
    class MethodNotAllowed(ClientError): pass
    class Conflict(ClientError): pass
    class Gone(ClientError): pass
    class ServerError(ErrorResponse): pass
    Timeout = requests.exceptions.Timeout

    @classmethod
    def exception_for_code(cls, code):

        # Do we have a specific class for this code?
        exc_class = {
            400: cls.BadRequest,
            401: cls.Unauthorized,
            403: cls.Forbidden,
            404: cls.NotFound,
            405: cls.MethodNotAllowed,
            409: cls.Conflict,
            410: cls.Gone,
        }.get(code, None)

        # If not, try something a bit more generic.
        if exc_class is None:
            exc_class = {
                4: cls.ClientError,
                5: cls.ServerError,
            }.get(code // 100, None)

        return exc_class or cls.ErrorResponse

Session.exceptions = Resource.exceptions = exceptions

#
# Exception handling.
#
