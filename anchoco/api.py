# coding: UTF-8
from __future__ import absolute_import
import os.path
import re
import six
from ansible import constants as C
from ansible.playbook import Play
from ansible.playbook.block import Block
from ansible.playbook.role import Role
from ansible.playbook.task import Task
from ansible.plugins import module_loader
from collections import defaultdict
from yaml.scanner import ScannerError
from .objects import Directive, Module
from .yaml import AnchocoLoader

TASK_LIST_DIRECTIVES = ('tasks', 'pre_tasks', 'post_tasks', 'handlers')
BLOCK_LIST_DIRECTIVES = ('block', 'rescue', 'always')
ROLE_LIST_DIRECTIVES = ('roles',)
MODULE_NAME_DIRECTIVES = ('action', 'local_action')


def _list_all_directives():
    directives = {}
    for aclass in [Play, Role, Block, Task]:
        aobj = aclass()

        for x in aobj.__dict__['_attributes']:
            if 'private' in x and x.private:
                continue
            else:
                if x == 'loop':
                    x = 'with_'
                elif x == 'action':
                    directives.setdefault('local_action', []).append(aclass)
                directives.setdefault(x, []).append(aclass)
    result = {}
    for k, v in directives.items():
        obj = Directive(k, v)
        for aclass in v:
            result.setdefault(aclass, set()).add(obj)
    return result


all_directives = _list_all_directives()


def _list_all_modules():
    modules = set()
    module_paths = module_loader._get_paths()
    for path in module_paths:
        if path is not None:
            modules.update(_find_modules_in_path(path))
    return modules


def _find_modules_in_path(path):
    if os.path.isdir(path):
        for module in os.listdir(path):
            fullpath = os.path.join(path, module)
            if module.startswith('.'):
                continue
            elif os.path.isdir(fullpath):
                _find_modules_in_path(fullpath)
                continue
            elif module.startswith('__'):
                continue
            elif any(module.endswith(x) for x in C.BLACKLIST_EXTS):
                continue
            elif module in C.IGNORE_FILES:
                continue
            elif module.startswith('_'):
                module = module.replace('_', '', 1)
            module_name = os.path.splitext(module)[0]  # removes the extension
            module_path = module_loader.find_plugin(
                module_name, mod_type='.py', ignore_deprecated=True)
            yield Module(module_name, path=module_path)


all_modules = _list_all_modules()


def _filter_ansible_objs_by_name(objs, pattern):
    return [obj for obj in objs if pattern in getattr(obj, 'name', '')]


class Script(object):
    def __init__(self, source, line=None, column=None, path='<string>'):
        lines = source.splitlines()
        if line is None:
            line = len(lines) - 1
        if column is None:
            column = len(lines[-1])
        self.data = self._load_yaml(source, path, line, column)

    def completions(self):
        completion_funcs = defaultdict(lambda: lambda pattern: set(), dict(
            play=lambda pattern: _filter_ansible_objs_by_name(all_directives[Play], pattern),
            task=lambda pattern: _filter_ansible_objs_by_name(all_directives[Task], pattern),
            role=lambda pattern: _filter_ansible_objs_by_name(all_directives[Role], pattern),
            block=lambda pattern: _filter_ansible_objs_by_name(all_directives[Block], pattern),
            module=lambda pattern: _filter_ansible_objs_by_name(all_modules, pattern),
        ))

        result = set()
        for k, v in self._search_tree().items():
            if v:
                result.update(completion_funcs[k](self.data.tree[-1]))
        return result

    def _load_yaml(self, source, file_name, line, column):
        loader = AnchocoLoader(source, file_name, line, column)
        try:
            data = loader.get_single_data()
            if isinstance(data.tree[-1], (dict, list)):
                data.tree.append(None)
            return data
        except ScannerError as e:
            ci = getattr(e.context_mark, 'index', 0)
            pi = getattr(e.problem_mark, 'index', 0)
            regex_mode = re.MULTILINE
            if "could not find expected ':'" in e.problem:
                regexp = r'\s'
                inserted_str = ':'
            elif (
                    e.context == "while scanning a quoted scalar" and
                    e.problem == 'found unexpected end of stream'
            ):
                regexp = r'$'
                inserted_str = source[e.context_mark.index]
                regex_mode = 0
            elif e.problem in ("mapping values are not allowed in this context",
                               "mapping values are not allowed here"):
                ci = len(''.join(source.splitlines(True)[:e.problem_mark.line - 1]))
                regexp = r'$'
                inserted_str = ':'
            else:
                raise
            m = re.search(regexp, source[ci:pi], regex_mode)
            insert_index = (ci + m.start()) if m else pi
            new_source = source[:insert_index] + inserted_str + source[insert_index:]
            return self._load_yaml(new_source, file_name, line, column)
        finally:
            loader.dispose()

    def _search_tree(self):
        result = defaultdict(lambda: False)

        if not hasattr(self.data, 'tree'):
            return result
        tree = self.data.tree
        if tree and isinstance(tree[0], list):
            # 補完対象がトップレベルのPlay, Task, Blockである場合
            if (len(tree) == 2 or (len(tree) == 3 and isinstance(tree[1], dict))):
                result['task'] = result['play'] = result['block'] = True
                for n in tree[0]:
                    if not isinstance(n, dict):
                        continue
                    for directive in n.keys():
                        directive_result = {'play': True, 'block': True, 'task': True}
                        for dclass, dname in ((Play, 'play'), (Block, 'block'), (Task, 'task')):
                            if directive not in [d.name for d in all_directives[dclass]]:
                                directive_result[dname] = False
                        exclusion_targets = [k for k, v in directive_result.items() if not v]
                        if len(exclusion_targets) < 3:
                            for t in exclusion_targets:
                                result[t] = False
                if not [result[target] for target in ('task', 'play', 'block') if result[target]]:
                    result['task'] = result['play'] = result['block'] = True
            # Taskのリストを含むディレクティブ内の補完
            if len(tree) >= 5 and (isinstance(tree[-3], six.text_type) or
                                   isinstance(tree[-4], six.text_type)):
                parent = tree[-3] if isinstance(tree[-3], six.text_type) else tree[-4]
                if parent in TASK_LIST_DIRECTIVES:
                    result['task'] = True
                elif parent in BLOCK_LIST_DIRECTIVES:
                    result['task'] = True
                    result['block'] = False
                elif parent in ROLE_LIST_DIRECTIVES:
                    result['role'] = True
            # モジュール名のみを補完
            if len(tree) >= 4 and tree[-2] in MODULE_NAME_DIRECTIVES:
                result['module'] = True
            # モジュール引数を補完
            if len(tree) >= 4 and (isinstance(tree[-2], six.text_type) or
                                   isinstance(tree[-3], six.text_type)):
                module_index = -2 if isinstance(tree[-2], six.text_type) else -3
                module_name = tree[module_index]
                if module_name == 'args':
                    module_name_candidates = tree[module_index - 1].keys()
                else:
                    module_name_candidates = [module_name]
                for m in all_modules:
                    for c in module_name_candidates:
                        if m.name == c:
                            result['module_arg'] = m
                            break
        # Taskディレクティブが補完対象である場合、モジュール名とBlockディレクティブも補完対象に含める
        if 'module' not in result:
            result['module'] = result['task']
        if 'block' not in result:
            result['block'] = result['task']
        # 既存ディレクティブ内にBlock専用のディレクティブがあった場合、Task用ディレクティブを無効化
        if result['task'] and isinstance(tree[-2], dict):
            if [k for k in tree[-2].keys() if k in BLOCK_LIST_DIRECTIVES]:
                result['task'] = False
        return result
