.. include:: ../README.rst
  :end-before: all-content-above-will-be-included-in-sphinx-docs

The Session object is the main starting point to using Lamium - all Resource and Location objects created via implicit use will link to the same session object. With a Session object, you can override how all requests work, as well as overriding the behaviour of how URL construction works. Each Session object will contain a requests.Session instance that all interactions will go through, so you can interact or replace this object to implement additional behaviours (such as caching).

Session objects have an 'at' method which allow you to create a Resource object linked to the session at a particular location. Resource objects have GET, POST, PUT etc. methods which are thin wrappers that delegate to the requests.Session.request call. Resource objects also have lower case variations of those methods ("get", "post", "put" etc.), and these is the main way to have more custom behaviours in the way that you send and receive data from these methods.

Here's a very basic example of a Session which will automatically decode json from responses and interpret keyword arguments as a JSON hash to be sent as part of a message body.

    >>> from lamium import Resource, Session
    >>> from json import dumps
    >>> from requests import Response
    >>>
    >>> class JSONResource(Resource):
    ...
    ...     def send_content(self, method, content, headers={}, **kwargs):
    ...         headers = headers.copy()
    ...         headers['Content-Type'] = 'application/json'
    ...         content = dumps(content)
    ...         return Resource.send_content(method, content, headers=headers, **kwargs)
    ...
    ...     def load_response(self, response):
    ...         result = Resource.load_response(self, response)
    ...         if isinstance(result, Response):
    ...             result = result.json()
    ...         return result
    ...
    >>> json_session = Session(resource_class=JSONResource)
    >>> httpbin = json_session.at('https://httpbin.org')
    >>> post_url = httpbin('post')
    >>>
    >>> # Interpret keyword parameters as the content to send.
    >>> result = post_url.post(a=1, b=2, c='d')
    >>>
    >>> # httpbin should echo what we've posted and confirm that the data was
    >>> # JSON encoded.
    >>> result['json'] == {'a': 1, 'b': 2, 'c': 'd'}
    True


If you set up a session like this, and then found a resource which didn't use JSON, then you can call the uppercase methods to bypass this behaviour and use requests API instead (you can handle the request encoding and response decoding manually). If you have a resource which accepts JSON, but sometimes generates a response which you wouldn't be able to decode (perhaps doesn't return JSON in response), then you could make a call like this:

    >>> result = post_url.post(dict(a=1, b=2, c='d'), response=True)

If you then find that the response is malformed, and want to allow your Resource object to decode it as per usual, then you can just use the load_response method directly.

That will use the request preparing behaviour of send_content, but return the raw response object from requests back to you to handle (this was based on a real world situation we had to deal with). Resource objects allow you to add more customisation and wrapping when dealing with APIs, but always provide you with a way to bypass this and deal with raw requests when you need to.

The base implementation of Resource provides one customisation by default - if a 4xx or 5xx response is returned, then an exception will be raised - similar to the raise_for_status method on response objects. However, Lamium provides more specific exception types for different types of responses - such as ServerError for 5xx responses, and NotFound for 404 responses.

Resource objects are callable, which allow extra path information and query string parameters to be appended to the existing URL - this allows you to easily build references to other resources. However, each Resource object has a "URL" property, which provides a Location object pointing to the same URL.

Location objects are "views" of Resource objects - they exist solely to allow a more convenient way to build URLs (by overriding __getattr__), as well as supporting the traditional way of constructing URLs, by calling the object. Each Location object will generate another Location object, all tied to the original session. Location objects have the same get/put/POST/PATCH etc. methods as Resource objects, and will delegate the calls to a Resource object. This means you can subclass Resource with custom behaviours, access the Location object to build references to other URLs, and then invoke the same methods and get the same behaviours on your custom Resource class.

Project Home
------------

You can browse the source code and file issues at the project repository_.

References
----------

.. toctree::
   :maxdepth: 1

   history
   setup

API
---

.. include:: api/main.rst


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

