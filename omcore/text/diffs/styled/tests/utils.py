from .... import styled as st
from ...themes import DIFF_STYLE_THEME


##


MODIFIED_DIFF = """\
diff --git a/foo.py b/foo.py
index 1111111..2222222 100644
--- a/foo.py
+++ b/foo.py
@@ -1,3 +1,4 @@ def greet
 def greet(name):
-    message = f"Hello, {name}!"
+    message = f"Hello, {name}."
+    print(message)
     return message
"""


def style_at(text: st.StyledText, position: int) -> st.ResolvedStyle:
    offset = 0
    for run in text.resolved_runs(DIFF_STYLE_THEME):
        if offset <= position < offset + len(run.text):
            return run.style
        offset += len(run.text)
    raise IndexError(position)
