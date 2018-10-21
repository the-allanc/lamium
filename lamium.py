__version__ = '0.1'

__all__ = [
    'Resource', 'URL', 'Session', 'exceptions',
]

import crookbook
import requests
import requests.exceptions
import six
from six.moves.urllib import parse as urlparse

@crookbook.described('for {0.__url__}')
class Unit(object):

    '''Base class where common Lamium objects share code - not intended
    to be inherited directly outside of this module.'''

    def __init__(self, session, url):
        if not (isinstance(session, Session)):
            err = 'session must be a Lamium session object, not %s' % type(session)
            raise ValueError(err)
        if not isinstance(url, six.string_types):
            err = 'url must be a string type, not %s' % type(url)
        self.__session__ = session
        self.__url__ = url

    def __call__(self, *args, **kwargs):
        '''Merge additional parameters against the current object to create a
        new instance of the same class combining the two. This will use
        Session.format_url.'''
        fmt = self.__session__.format_url
        url = fmt(self.__url__, args, kwargs)
        return self.at(url)

    # Subclasses should use this to build another object of a similar
    # type at the given URL. By default, it presumes it can construct
    # an object of the same class as itself, passing the connection
    # object and the URL path as positional arguments.
    def at(self, url):
        '''Constructs another instance of the same class which points
        to the provided URL - it will be linked to the same underlying
        session.'''
        return self.__class__(self.__session__, url)

    def __str__(self):
        return self.__url__


@crookbook.essence('__session__ __url__', mutable=False)
class URL(Unit):

    '''Lightweight object used for easy construction of URLs, which can then
       be easily turned into a Resource object.'''

    @property
    def deURL(self):
        return self.__session__.at(self.__url__)

    def __getattr__(self, name):
        if name in self.__session__.__resource_delegates__:
            return getattr(self.deURL, name)
        if name.startswith('__') and name.endswith('__'):
            raise AttributeError("%r: %s" % (self, name))
        return self(name)

_verb_func = '''
def {0}(self, *args, **kwargs):
    """Alias for session.{0} which passes the URL of this object as the
    first argument."""
    return self.request("{0}", *args, **kwargs)
'''

_verb_nobody_func = '''
def {0}(self, **kwargs):
    """XXX."""
    return self.load_response(self.request("{1}", **kwargs))
'''

_verb_body_func = '''
def {0}(self, *args, **kwargs):
    """XXX."""
    return self.send_request("{1}", *args, **kwargs)
'''

class LamiumResourceMeta(type):
    
    def __init__(cls, name, bases, nmspec):
        super(LamiumResourceMeta, cls).__init__(name, bases, nmspec)
        compiled = {}

        for verb in cls.__verbs__:
            if hasattr(cls, verb):
                continue
            fcode = compile(_verb_func.format(verb), '<lamium_dynfunc>', 'exec')
            compiled[verb] = fcode
        
        for verb in cls.__verbs__:
            mverb = verb.lower()
            if hasattr(cls, mverb):
                continue
            functmpl = _verb_body_func if verb in cls.__verbs_with_bodies__ else _verb_body_func
            fcode = compile(functmpl.format(mverb, verb), '<lamium_dynfunc>', 'exec')
            compiled[mverb] = fcode

        ns = {}
        for method_name, fcode in compiled.items():
            eval(fcode, {}, ns)
            setattr(cls, method_name, ns[method_name])

#del _verb_func, _verb_body_func, _verb_nobody_func

class BaseResource(six.with_metaclass(LamiumResourceMeta, Unit)):
    
    # How do you do frozensets these days?
    __verbs__ = 'DELETE GET HEAD PATCH POST PUT'.split()
    __verbs_with_bodies__ = 'PATCH POST PUT'.split()

    @property
    def URL(self):
        return URL(self.__session__, self.__url__)

    def request(self, method, *args, **kwargs):
        return self.__session__.request(method, self.__url__, *args, **kwargs)

    def at(self, url):
        return self.__session__.at(self.__url__)

    # send_request will be defined in superclass, won't have "response" or
    # notfound behaviour. That'll be defined by us.
    def send_request(self, method, *args, **kwargs):
        kwargs = self._merge_request_params(*args, **kwargs)
        return self.load_response(self.request(method, **kwargs))

    def load_response(self, response):
        return response

    def _merge_request_params(self, data, options):
        if data is not None:
            if 'data' in options:
                raise ValueError('cannot define data as positional and keyword argument')
            kwargs['data'] = data
        return kwargs

_NOTGIVEN = object()

class Resource(BaseResource):

    def get(self, *args, **kwargs):
        # Emulating Tortilla here.
        if args:
            return self(*args).get(**kwargs)
            
        return super(Resource, self).get(**kwargs)

    def send_request(self, method, data=None, response=False, **kwargs):
        params = self._process_parameters(data, **kwargs)
        resp = self.request(**params)
        if response:
            return resp
            
        try:
            return self.load_response(resp)
        except (self.exceptions.NotFound, self.exceptions.Gone):
            if notfound is not _NOTGIVEN:
                return notfound
            raise

    def load_response(self, response):
        if 400 <= response.status_code < 600:
            self.raise_for_status(response)
        return response

    def raise_for_status(self, response):
        raise self.exceptions.exception_for_code(response.status_code)(response)

    def _merge_request_params(self, data, options):
        if data is None:
            if 'json' in options:
                raise ValueError('cannot define json as positional and keyword argument')
            return {'json': options}
        return options


class Session(object):

    resource_class = BaseResource

    def __init__(self, req_sess=None):
        self.req_sess = req_sess or requests.Session()
        self.__resource_delegates__ = frozenset(
            list(self.resource_class.__verbs__) +
            [x.lower() for x in self.resource_class.__verbs__] +
            ['request']
        )

    def request(self, method, url, *args, **kwargs):
        return self.req_sess.request(method, url, *args, **kwargs)

    def format_url(self, url, positionals, named):
        if not (named or positionals):
            e = 'requires at least one positional argument or keyword parameter'
            raise ValueError(e)

        # First, deal with positionals.
        if positionals:
            elements = []
            for positional in positionals:
                if not isinstance(positional, six.integer_types + six.string_types):
                    err = 'element is not a string or integer type: %r'
                    raise ValueError(err % positional)
                elements.append(six.text_type(positional))

            # The element added is intended to be a child one. As such, it needs
            # to have a trailing slash to work correctly. Furthermore, we have
            # to drop anything like query string parameters.
            parts = urlparse.urlparse(url)
            if not parts.path.endswith('/'):
                elements.insert(0, '')
            url = urlparse.urlunparse(
                list(parts[:2]) + [parts.path + '/'.join(elements)] + ['', '', ''])

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
