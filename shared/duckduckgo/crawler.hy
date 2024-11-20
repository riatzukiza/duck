(import functools [cached_property])
(import duckduckgo-search [AsyncDDGS])
(import asyncio)
(import requests)
(import json)
(import mimetypes)

(setv keywords ["research papers filetype:pdf" "Search term" "AI" "hacking" "bananas" "minecraft recipes"])

(setv BASE_PATH "results/")

(defn get-extension [response]

  (let [content-type (.get response.headers "Content-Type")
        extension (if content-type
                      (mimetypes.guess-extension (. (.split content-type ";") [0]))
                      (.split href "." -1))]
    (if extension
        extension
        (if (and extension (.startswith extension "."))
          (str (cut extension 1 (len extension)))
          ".unknown")))) 

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
        `(setv (. self ~prop_name) ~prop_name)))))))

(defclass SearchResult []
  (init [_result])  
  (property href (.get self._result "href" (.get self._result "url")))
  (property sanitized_url (. href (replace "/" "_") (replace ":" "_") (replace "." "_")))
  (cprop extension (get-extension response))

  (cprop response (.get requests self.href))

  (property title (.get self._result "title"))
  (property description (.get self._result "description"))
  (property source (.get self._result "source"))
  (property date (.get self._result "date"))
  (property image (.get self._result "image"))
  (property thumbnail (.get self._result "thumbnail")))

(defclass SearchClient []

  (init [ _base_path _search])

  (defn :async search [self query]
    (for [_result (await (self._search query))]
      (await (.sleep asyncio 1))
      (try
        (let [result (SearchResult _result)]
          (print f"Searching for {query}")

          (print (.dumps json headers :indent 4))

          (setv sanitized_url (. href (replace "/" "_") (replace ":" "_") (replace "." "_")) )
          (setv extension (get-extension response))

          (setv header_file_name f"{self._base_path}{sanitized_url}.header.json")
          (setv result_file_name f"{self._base_path}{sanitized_url}.result.json")
          (setv body_file_name f"{self._base_path}{sanitized_url}_body.{extension}")

          (.dump json headers (open  header_file_name "w") :indent 4)
          (.dump json result (open  result_file_name "w") :indent 4)

          (with [f (open body_file_name "wb")]
            (.write f response.content))

          (print "Saved" href "to" body_file_name)

          (except [e Exception]
            (print f"Failed to fetch {href}: {e}")
            (continue)))))))

(setv text_search (SearchClient "results/" 
                                (fn [query] 
                                  (.atext (AsyncDDGS) query
                                          :region "wt-wt" 
                                          :safesearch "moderate" 
                                          :max-results 10))))
(setv news_search (SearchClient "news_results/" 
                                (fn [query] 
                                  (.anews (AsyncDDGS) query
                                          :region "wt-wt" 
                                          :safesearch "moderate" 
                                          :max-results 10))))
(setv image_search (SearchClient "image_results/" 
                                (fn [query] 
                                  (.aimages (AsyncDDGS) query
                                          :region "wt-wt" 
                                          :safesearch "moderate" 
                                          :max-results 10))))
(setv video_search (SearchClient "video_results/" 
                                (fn [query] 
                                  (.avideos (AsyncDDGS) query
                                          :region "wt-wt" 
                                          :safesearch "moderate" 
                                          :max-results 10))))

