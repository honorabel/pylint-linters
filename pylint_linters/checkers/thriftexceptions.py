import astroid
from pylint.checkers import BaseChecker, utils
from pylint.interfaces import IAstroidChecker


MSGS = {
    'E9901': ('Thrift exception',
              'thrift-exception-outside-server',
              'Only the API layer should raise Thrift exceptions. '
              'Instead, raise a regular Python exception, and convert '
              'it at the API handler.')
}


def _inherits_from_texception(node):
    if node.name == 'TException':
        return True
    for parent in node.ancestors(recurs=False):
        if _inherits_from_texception(parent):
            return True
    return False


class ThriftExceptionsChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'thriftex'
    priority = -1
    msgs = MSGS

    @utils.check_messages('thrift-exception-outside-server')
    def visit_raise(self, node):
        expr = node.exc
        try:
            if isinstance(expr, astroid.CallFunc):
                inferred_type = utils.safe_infer(expr.func)
                if isinstance(inferred_type, astroid.Class) and \
                        _inherits_from_texception(inferred_type):
                    module = node.root()
                    if not module.name.startswith('server'):
                        self.add_message('thrift-exception-outside-server', node=node)
        except astroid.InferenceError:
            # We couldn't guess the type of the expression.
            pass


def register(linter):
    linter.register_checker(ThriftExceptionsChecker(linter))
