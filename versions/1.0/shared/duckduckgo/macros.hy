
(defmacro property [cls name & body]
  `(defn :property ~name [self]
     ~@body))

(defmacro cprop [cls name & body]
  `(defn :cached_property ~name [self]
     ~@body))

(defmacro init [cls prop_args]
"defines an init for a class that takes a list of properties"
  `(defn __init__ [self ~@prop_args]
    ~@(lfor prop_name prop_args
        `(setv (. self ~prop_name) ~prop_name))))
