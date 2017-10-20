import astroid

from ..testutil import CheckerTestCase, Message

from .importprivate import ImportPrivateChecker


class ImportPrivateCheckerTest(CheckerTestCase):
    CHECKER_CLASS = ImportPrivateChecker

    def test_valid_cases(self):
        valid_imports = '''
        from .a.b.c import Foo
        from .a._b.c import Foo
        from ._a.b.c import Foo
        from ..a.b.c import Foo
        from .. a.b.c import Foo
        '''.strip().split('\n')
        for line in valid_imports:
            node = astroid.extract_node(line)
            with self.assertNoMessages():
                self.checker.visit_importfrom(node)

    def test_invalid_cases(self):
        invalid_imports = '''
        from .._a.b.c import Foo
        from ..a._b.c import Foo
        from .. a._b.c import Foo
        '''.strip().split('\n')
        for line in invalid_imports:
            node = astroid.extract_node(line)
            message = Message.new('import-private-module', node=node)
            with self.assertAddsMessages(message):
                self.checker.visit_importfrom(node)
