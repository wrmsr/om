(defmacro bar [expr]
  `(print (.upper ~expr)))

(defmacro foo [expr]
  `(do (require x.hy.tests.resources.bin.circular-macro-require [bar])
       (bar ~expr)))

(foo "wowie")
