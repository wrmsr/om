# """
# Round-trips the whole standard library of the running interpreter through the printer. Files using syntax newer than
# python 3.8 are skipped, as are f-strings that cannot be expressed under 3.8's quoting rules.
# """
# import ast
# import os.path
# import sysconfig
#
# from ..expressions import UnsupportedNodeError
# from ..literals import UnrepresentableFStringError
# from ..minifying import print_minified
# from ..transforms import strip_literal_statements
# from ..verification import verify_roundtrip
#
#
# def _iter_stdlib_sources():
#     for dp, dns, fns in os.walk(sysconfig.get_paths()['stdlib']):
#         dns[:] = [d for d in dns if d not in ('site-packages', '__pycache__')]
#         for fn in fns:
#             if fn.endswith('.py'):
#                 yield os.path.join(dp, fn)
#
#
# def test_stdlib():
#     checked = skipped = 0
#
#     for p in _iter_stdlib_sources():
#         try:
#             with open(p, encoding='utf-8') as f:
#                 tree = ast.parse(f.read())
#         except (SyntaxError, ValueError, UnicodeDecodeError):
#             continue
#
#         strip_literal_statements(tree)
#
#         try:
#             out = print_minified(tree)
#         except (UnsupportedNodeError, UnrepresentableFStringError):
#             skipped += 1
#             continue
#
#         verify_roundtrip(tree, out)
#         compile(out, p, 'exec')
#         checked += 1
#
#     assert checked > 100
#     assert skipped < checked // 10
