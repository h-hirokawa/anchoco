from __future__ import absolute_import
from ansible.parsing.yaml.constructor import AnsibleConstructor
from ansible.parsing.yaml.objects import AnsibleMapping
from yaml.constructor import ConstructorError
from yaml.nodes import ScalarNode, SequenceNode, MappingNode
from yaml.resolver import Resolver
try:
    from _yaml import CParser, CEmitter  # noqa
    HAVE_PYYAML_C = True
except ImportError:
    HAVE_PYYAML_C = False


class POS(object):
    def __init__(self, line, column):
        self.line = line
        self.column = column

    def __repr__(self):
        return '({}, {})'.format(self.line + 1, self.column + 1)


class YAMLConstructor(AnsibleConstructor):
    def __init__(self, *args, **kwargs):
        self.pos = POS(kwargs.pop('line'), kwargs.pop('column'))
        self.tree = []
        super(YAMLConstructor, self).__init__(*args, **kwargs)

    def get_single_data(self):
        node = self.get_single_node()
        if node is not None:
            data = self.construct_document(node)
            data.tree = self.tree
            return data
        return None

    def construct_scalar(self, node):
        if not isinstance(node, ScalarNode):
            raise ConstructorError(
                None, None,
                "expected a scalar node, but found %s" % node.id,
                node.start_mark)
        if self._node_is_in_range(node):
            self.tree.append(node.value)
        return node.value

    def construct_sequence(self, node, deep=False):
        if not isinstance(node, SequenceNode):
            raise ConstructorError(
                None, None,
                "expected a sequence node, but found %s" % node.id,
                node.start_mark)
        tree_count = len(self.tree)
        if self._node_is_in_range(node):
            self.tree.append(None)
        seq = [self.construct_object(child, deep=deep)
               for child in node.value]
        if self._node_is_in_range(node):
            self.tree[tree_count] = seq
        return seq

    def construct_mapping(self, node, deep=False):
        # Most of this is from yaml.constructor.SafeConstructor.  We replicate
        # it here so that we can warn users when they have duplicate dict keys
        # (pyyaml silently allows overwriting keys)
        if not isinstance(node, MappingNode):
            raise ConstructorError(
                None, None,
                "expected a mapping node, but found %s" % node.id,
                node.start_mark)
        self.flatten_mapping(node)
        mapping = AnsibleMapping()

        # Add our extra information to the returned value
        mapping.ansible_pos = self._node_position_info(node)

        if self._node_is_in_range(node):
            self.tree.append(mapping)

        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                hash(key)
            except TypeError as exc:
                raise ConstructorError(
                    "while constructing a mapping", node.start_mark,
                    "found unacceptable key (%s)" % exc, key_node.start_mark)
            if self._node_is_in_range(value_node):
                self.tree.append(key)
            value = self.construct_object(value_node, deep=deep)
            mapping[key] = value
        return mapping

    def _node_is_in_range(self, node):
        result = self.pos.line in range(node.start_mark.line, node.end_mark.line + 1) and (
            node.start_mark.line != node.end_mark.line or
            self.pos.column in range(node.start_mark.column, node.end_mark.column + 1)
        )
        return result


if HAVE_PYYAML_C:

    class AnchocoLoader(CParser, YAMLConstructor, Resolver):
        def __init__(self, stream, file_name=None, line=None, column=None, vault_password=None):
            CParser.__init__(self, stream)
            YAMLConstructor.__init__(self, file_name=file_name,
                                     line=line, column=column,
                                     vault_password=vault_password)
            Resolver.__init__(self)
else:
    from yaml.composer import Composer
    from yaml.reader import Reader
    from yaml.scanner import Scanner
    from yaml.parser import Parser

    class AnchocoLoader(Reader, Scanner, Parser, Composer, YAMLConstructor, Resolver):
        def __init__(self, stream, file_name=None, line=None, column=None, vault_password=None):
            Reader.__init__(self, stream)
            Scanner.__init__(self)
            Parser.__init__(self)
            Composer.__init__(self)
            YAMLConstructor.__init__(self, file_name=file_name,
                                     line=line, column=column,
                                     vault_password=vault_password)
            Resolver.__init__(self)
