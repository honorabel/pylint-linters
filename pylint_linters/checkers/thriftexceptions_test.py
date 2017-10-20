import astroid
from mock import MagicMock

from ..testutil import CheckerTestCase, Message

from .thriftexceptions import ThriftExceptionsChecker


class MockNodeModule(object):
    """Mock object to simulate the result of astroid's node.root()"""
    def __init__(self, name):
        self.name = name


class ThriftExceptionsCheckerTest(CheckerTestCase):

    CHECKER_CLASS = ThriftExceptionsChecker

    def _mock_node_module_name(self, node, module_path):
        node.root = MagicMock(return_value=MockNodeModule(name=module_path))

    def test_adds_message_if_not_in_server_module(self):
        nodes = astroid.extract_node('''
        class TException(object):
            pass
        class MyException(TException):
            pass
        class MyChildException(MyException):
            pass
            
        raise #@
        raise Exception('oops') #@        
        raise MyException() #@
        raise MyChildException() #@
        ''')
        for node in nodes:
            self._mock_node_module_name(node, 'some.random.module')

        with self.assertNoMessages():
            self.checker.visit_raise(nodes[0])
        with self.assertNoMessages():
            self.checker.visit_raise(nodes[1])

        message = Message.new('thrift-exception-outside-server', node=nodes[2])
        with self.assertAddsMessages(message):
            self.checker.visit_raise(nodes[2])

        message = Message.new('thrift-exception-outside-server', node=nodes[3])
        with self.assertAddsMessages(message):
            self.checker.visit_raise(nodes[3])

    def test_no_message_if_in_server_module(self):
        nodes = astroid.extract_node('''
        class TException(object):
            pass
        class MyException(TException):
            pass
        class MyChildException(MyException):
            pass

        raise #@
        raise Exception('oops') #@        
        raise MyException() #@
        raise MyChildException() #@
        ''')
        for node in nodes:
            self._mock_node_module_name(node, 'server.a.b.c')

        with self.assertNoMessages():
            self.checker.visit_raise(nodes[0])
        with self.assertNoMessages():
            self.checker.visit_raise(nodes[1])
        with self.assertNoMessages():
            self.checker.visit_raise(nodes[2])
        with self.assertNoMessages():
            self.checker.visit_raise(nodes[3])
