import re

from pylint.checkers import BaseChecker, utils
from pylint.interfaces import IAstroidChecker


MSGS = {
    'E9901': ('Import private module',
              'import-private-module',
              'Attempting to import a non-accessible private module.'
              'Instead, consider using that module\'s public api')
}


def _contains_private_module(importfrom_node):
    modname = importfrom_node.modname
    return (re.search('^_', modname) or re.search('\._', modname))


def _imports_from_parent(importfrom_node):
    return (importfrom_node.level and importfrom_node.level > 1)


class ImportPrivateChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'importprivate'
    priority = -1
    msgs = MSGS

    @utils.check_messages('import-private-module')
    def visit_importfrom(self, node):
        if _imports_from_parent(node) and _contains_private_module(node):
            self.add_message('import-private-module', node=node)


def register(linter):
    linter.register_checker(ImportPrivateChecker(linter))
