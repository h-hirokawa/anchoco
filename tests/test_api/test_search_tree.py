from __future__ import absolute_import
import pytest
from textwrap import dedent

from anchoco import api


def test_common_directive_only():
    src = dedent('''\
        - vars:
          become: true
        - a''')
    target = api.Script(src, line=2, column=3)._search_tree()
    assert {k for k in target if target[k]} == {'play', 'block', 'task', 'module'}


def test_single_play():
    src = dedent('''\
        ---
        - name
          tasks:
        ''')
    target = api.Script(src, line=1, column=6)._search_tree()
    assert {k for k in target if target[k]} == {'play'}


def test_second_play():
    src = dedent('''\
        ---
        - name: name
          tasks:
        - nam''')
    target = api.Script(src, line=1, column=6)._search_tree()
    assert {k for k, v in target.items() if v} == {'play'}


def test_block():
    src = dedent('''\
        ---
        - block:
          a''')
    target = api.Script(src)._search_tree()
    assert {k for k, v in target.items() if v} == {'block'}


def test_role():
    src = dedent('''\
        ---
        - name: play
          roles:
            - a''')
    script = api.Script(src)
    print(script.data.tree)
    target = script._search_tree()
    assert {k for k, v in target.items() if v} == {'role'}


def test_task_and_module_name():
    src = dedent('''\
        ---
        - m
        - register: registed''')
    script = api.Script(src, line=1, column=3)
    print(script.data.tree)
    target = script._search_tree()
    assert {k for k, v in target.items() if v} == {'task', 'module'}
