from lamium import Session, URL, Resource, Unit
from mock import MagicMock
import requests_mock
from six.moves.urllib import parse as urlsplit
import six


class BaseTest(object):

    # I feel a little bad for using
    def setup_method(self, method):
        self.responses = requests_mock.mock()
        self.responses.start()

    def teardown_method(self, method):
        self.responses.stop()


class TestUnit(BaseTest):

    def test_at(self):
        unit = Unit(Session(), 'http://sixtyten.org/')
        newunit = unit.at('http://sixtyten.org/polo/')
        assert isinstance(newunit, Unit)
        assert newunit.__url__ == 'http://sixtyten.org/polo/'

    def test_call(self):
        conn = MagicMock(spec=Session)
        conn.format_url.return_value = 'http://www.sixtyten.org/blah'
        unit = Unit(conn, 'http://www.sixtyten.org/')
        newunit = unit(8, a='b')
        conn.format_url.assert_called_once_with(
            'http://www.sixtyten.org/', (8,), {'a': 'b'})
        assert isinstance(newunit, Unit)
        assert newunit.__url__ == 'http://www.sixtyten.org/blah'

    # No idea how this is meant to work in Python 3.
    def test_str_unicode(self):
        unit = Unit(Session(), 'http://www.sixtyten.org/')
        assert str(unit) == 'http://www.sixtyten.org/'
        if six.PY2:
            assert unicode(unit) == u'http://www.sixtyten.org/'

    def test_repr(self):
        unit = Unit(Session(), 'http://www.sixtyten.org/')
        assert repr(unit) == '<Unit for http://www.sixtyten.org/>'


class TestURL(BaseTest):

    def test_location_chaining(self):
        s = Session()
        here = URL(s, 'http://sixtyten.org/')
        there42 = here.there(42)
        assert isinstance(there42, URL)
        assert there42.__url__ == 'http://sixtyten.org/there/42'

    def test_get_GET_proxying(self):
        s = Session()
        docproxy = MagicMock(spec=Session)
        s.resource_class.return_value=docproxy
        l = URL(s, 'http://sixtyten.org/mydoc/')

        #l.get(myparam=True)
        #docproxy.get.assert_called_once_with(myparam=True)
        #assert not docproxy.GET.called
        #docproxy.reset_mock()

        l.GET(timeout=10)
        docproxy.GET.assert_called_once_with(timeout=10)
        assert not docproxy.get.called


class TestResource(BaseTest):

    def test_url(self):
        s = Session()
        r = Resource(s, 'http://sixtyten.org/documents/43/')
        assert isinstance(r.URL, URL)
        assert r.URL.__url__ == r.__url__

    def test_VERB_methods(self):
        link = 'http://sixtyten.org/verby/'
        data = dict(up='down', left='right')

        c = MagicMock(spec=Session)
        r = Resource(c, link)

        r.DELETE(timeout=3)
        c.request.assert_called_once_with('DELETE', link, data=None, timeout=3)
        c.reset_mock()

        r.GET(timeout=4)
        c.request.assert_called_once_with('GET', link, data=None, timeout=4)
        c.reset_mock()

        r.PATCH(data, timeout=5)
        c.request.assert_called_once_with('PATCH', link, data=data, timeout=5)
        c.reset_mock()

        r.POST(data, timeout=6)
        c.request.assert_called_once_with('POST', link, data=data, timeout=6)
        c.reset_mock()

        r.PUT(data, timeout=7)
        c.request.assert_called_once_with('PUT', link, data=data, timeout=7)
        c.reset_mock()
