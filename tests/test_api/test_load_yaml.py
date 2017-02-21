from __future__ import absolute_import
import pytest
from textwrap import dedent
from yaml.parser import ParserError

from anchoco import api


def test_colon_absence():
    src = dedent('''\
        ---
        - name: name
          hosts
        ''')
    script = api.Script(src)
    assert script.data == [{'name': 'name', 'hosts': None}]


def test_unquoted():
    src = dedent('''\
        ---
        - name: "hoge
            fuga
        ''')
    script = api.Script(src)
    assert script.data == [{'name': 'hoge fuga'}]


def test_unallowed_map():
    src = dedent('''\
        ---
        - name
          hosts: all
        ''')
    script = api.Script(src)
    assert script.data == [{'name': None, 'hosts': 'all'}]


def test_unhandled_error():
    src = dedent('''\
        ---
        - hosts
        hoge
        ''')
    with pytest.raises(ParserError):
        api.Script(src)


def test_blank_list():
    src = dedent('''\
        ---
        - hosts
        - ''')
    script = api.Script(src)
    assert script.data.tree == [['hosts', None], None]
