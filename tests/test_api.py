from __future__ import absolute_import
import unittest
from anchoco import api
from anchoco.objects import Directive, Module

SRC = '''---
- name
  tasks:
    - shel
    - name: comm
      action: comm
- name: "{{ sample play }}
  host
  dummy
 '''

SRC2 = '''---
- block:
    -
'''

SRC3 = '''---
- action: comm
'''

SRC4 = '''---
- yum:
    name: httpd
    s
'''

SRC5 = '''---
- command: echo hoge
  args:
    c
'''


class TestApiCompletions(unittest.TestCase):

    TEST_DATA = (
        # (src pos, tuple of modules included, exclusion modules, directives, exclusion directives)
        # (SRC, (1, 6), (), ('command',), ('name',), ('action',)),
        (SRC, (3, 10), ('shell', 'win_shell'), ('command',), (), ('action',)),
        (SRC, (4, 16), (), ('command',), (), ('action',)),
        (SRC, (5, 14), ('command', 'win_command',), ('shell',), (), ('action',)),
        (SRC, (7, 6), (), ('add_host',), ('hosts',), ('action',)),
    )

    def test_api_module_name_completions(self):
        for src, (line, column), modules, emodules, directives, edirectives in self.TEST_DATA:
            result = api.Script(src, line=line, column=column).completions()

            assert all([isinstance(m, (Module, Directive)) for m in result])

            module_names = [m.name for m in result if isinstance(m, Module)]
            for m in modules:
                assert m in module_names
            for m in emodules:
                assert m not in module_names

            directive_names = [d.name for d in result if isinstance(d, Directive)]
            for d in directives:
                assert d in directive_names
            for d in edirectives:
                assert d not in directive_names

    def test_api_search_tree_play(self):
        result = api.Script(SRC, line=1, column=6)._search_tree()
        assert result['task'] is False
        assert result['play'] is True

    def test_api_search_tree_block(self):
        src = '''---
- tasks:
    - block:
      a
'''
        result = api.Script(src, line=3, column=7)._search_tree()
        print(result)
        assert result['task'] is False
        assert result['block'] is True

    def test_api_search_tree_role(self):
        src = '''---
- roles:
    -
'''
        result = api.Script(src, line=2, column=5)._search_tree()
        print(result)
        assert result['task'] is False
        assert result['block'] is False
        assert result['role'] is True

    def test_api_search_tree_task(self):
        result = api.Script(SRC2, line=2, column=5)._search_tree()
        assert result['task'] is True
        assert result['block'] is False
        assert result['module'] is True
        assert result['play'] is False

    def test_api_search_tree_module(self):
        result = api.Script(SRC3, line=1, column=14)._search_tree()
        assert result['task'] is False
        assert result['module'] is True

    def test_api_search_tree_module_arg(self):
        script = api.Script(SRC4, line=3, column=5)
        result = script._search_tree()
        assert isinstance(result['module_arg'], Module)
        assert result['module_arg'].name == 'yum'

    def test_api_search_tree_module_arg_command(self):
        result = api.Script(SRC5, line=3, column=5)._search_tree()
        assert isinstance(result['module_arg'], Module)
        assert result['module_arg'].name == 'command'
