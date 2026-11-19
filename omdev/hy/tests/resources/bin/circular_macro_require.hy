(defmacro bar [expr]
  `(print (.upper ~expr)))

(defmacro foo [expr]
  `(do ~(hy.read f"(require {hy.__package__}.tests.resources.bin.circular-macro-require [bar])")
       (bar ~expr)))

(foo "wowie")
