"""functional/non regression tests for pylint

Adapted from:
https://github.com/PyCQA/pylint/blob/master/pylint/testutils.py
"""
from __future__ import print_function

import collections
import contextlib
from os import linesep, getcwd, sep
from os.path import abspath, dirname
import sys
import unittest

import six
from six.moves import StringIO

from pylint import checkers
from pylint.utils import PyLintASTWalker
from pylint.reporters import BaseReporter
from pylint.interfaces import IReporter
from pylint.lint import PyLinter

# Utils

SYS_VERS_STR = '%d%d%d' % sys.version_info[:3]
TITLE_UNDERLINES = ['', '=', '-', '.']
PREFIX = abspath(dirname(__file__))
PY3K = sys.version_info[0] == 3


class TestReporter(BaseReporter):
    """reporter storing plain text messages"""

    __implements__ = IReporter

    def __init__(self): # pylint: disable=super-init-not-called
        self.message_ids = {}
        self.reset()
        self.path_strip_prefix = getcwd() + sep

    def reset(self):
        self.out = StringIO()
        self.messages = []

    def handle_message(self, msg):
        """manage message of different type and in the context of path """
        obj = msg.obj
        line = msg.line
        msg_id = msg.msg_id
        msg = msg.msg
        self.message_ids[msg_id] = 1
        if obj:
            obj = ':%s' % obj
        sigle = msg_id[0]
        if PY3K and linesep != '\n':
            # 2to3 writes os.linesep instead of using
            # the previosly used line separators
            msg = msg.replace('\r\n', '\n')
        self.messages.append('%s:%3s%s: %s' % (sigle, line, obj, msg))

    def finalize(self):
        self.messages.sort()
        for msg in self.messages:
            print(msg, file=self.out)
        result = self.out.getvalue()
        self.reset()
        return result

    # pylint: disable=unused-argument
    def on_set_current_module(self, module, filepath):
        pass
    # pylint: enable=unused-argument

    def display_reports(self, layout):
        """ignore layouts"""

    _display = None


class MinimalTestReporter(BaseReporter):

    def handle_message(self, msg):
        self.messages.append(msg)

    def on_set_current_module(self, module, filepath):
        self.messages = []

    _display = None


class Message(collections.namedtuple(
        'Message', ['msg_id', 'line', 'node', 'args', 'confidence'])):
    @classmethod
    def new(cls, msg_id, line=None, node=None, args=None, confidence=None):
        return Message(
            msg_id=msg_id,
            line=line,
            node=node,
            args=args,
            confidence=confidence)

    def __eq__(self, other):
        if isinstance(other, Message):
            if self.confidence and other.confidence:
                return super(Message, self).__eq__(other)
            return self[:-1] == other[:-1]
        return NotImplemented  # pragma: no cover

    __hash__ = None


class UnittestLinter(object):
    """A fake linter class to capture checker messages."""
    # pylint: disable=unused-argument, no-self-use

    def __init__(self):
        self._messages = []
        self.stats = {}

    def release_messages(self):
        try:
            return self._messages
        finally:
            self._messages = []

    def add_message(self, msg_id, line=None, node=None, args=None, confidence=None):
        self._messages.append(Message.new(msg_id, line, node, args, confidence))

    def is_message_enabled(self, *unused_args, **unused_kwargs):
        return True

    def add_stats(self, **kwargs):
        for name, value in six.iteritems(kwargs):
            self.stats[name] = value
        return self.stats

    @property
    def options_providers(self):
        return linter.options_providers


class CheckerTestCase(unittest.TestCase):
    """A base testcase class for unit testing individual checker classes."""
    CHECKER_CLASS = None
    CONFIG = {}

    def setUp(self):
        self.linter = UnittestLinter()
        self.checker = self.CHECKER_CLASS(self.linter) # pylint: disable=not-callable
        for key, value in six.iteritems(self.CONFIG):
            setattr(self.checker.config, key, value)
        self.checker.open()

    @contextlib.contextmanager
    def assertNoMessages(self):
        """Assert that no messages are added by the given method."""
        with self.assertAddsMessages():
            yield

    @contextlib.contextmanager
    def assertAddsMessages(self, *messages):
        """Assert that exactly the given method adds the given messages.
        The list of messages must exactly match *all* the messages added by the
        method. Additionally, we check to see whether the args in each message can
        actually be substituted into the message string.
        """
        yield
        got = self.linter.release_messages()
        msg = ('Expected messages did not match actual.\n'
               'Expected:\n%s\nGot:\n%s' % ('\n'.join(repr(m) for m in messages),
                                            '\n'.join(repr(m) for m in got)))
        assert list(messages) == got, msg

    def walk(self, node):
        """recursive walk on the given node"""
        walker = PyLintASTWalker(linter)
        walker.add_checker(self.checker)
        walker.walk(node)

# Init
test_reporter = TestReporter()
linter = PyLinter()
linter.set_reporter(test_reporter)
linter.config.persistent = 0
checkers.initialize(linter)
