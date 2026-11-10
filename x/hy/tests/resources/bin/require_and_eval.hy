(defmacro require-test-macros []
  (hy.read f"(require {hy.__package__}.tests.resources.macros [test-macro])"))

(require-test-macros)

(print (hy.eval '(do (test-macro) (cut "zabc" blah None))))
