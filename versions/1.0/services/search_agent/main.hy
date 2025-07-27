(import functools [cached_property])
(import duckduckgo-search [AsyncDDGS])
(import asyncio)
(import requests)
(import json)
(import mimetypes)
(import os)

;; (require macros.macros)


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

(setv search_queue ["research papers filetype:pdf" "Search term" "AI" "hacking" "bananas" "minecraft recipes"])

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

(defclass SearchResult []
  "A class for interacting with meta data returned from a search client."

  (init [_result_dict _base_path])

  (property _result self._result_dict)
  (property base_path self._base_path)

  (property href (.get self._result "href" (.get self._result "url")))
  (property sanitized_url (. href (replace "/" "_") (replace ":" "_") (replace "." "_")))

  (cprop response (SearchResultResponse self._result self.base_path)

  (property title (.get self._result "title"))
  (property description (.get self._result "description"))
  (property source (.get self._result "source"))
  (property date (.get self._result "date"))
  (property image (.get self._result "image"))
  (property thumbnail (.get self._result "thumbnail"))
  (property result_file_name (os.path.join self.base_path f"{self.title}.result.json"))

  (defn save [self path]
    "Save the results returned from the search client"

    (setv result_file_name (os.path.join path f"{self.result_file_name}.result.json"))

    (.dump json result (open  result_file_name "w") :indent 4)
    (.save self.response)

    ))

(defclass SearchResultResponse []
  "A class for interacting with the web page associated with a search result's source/href/url"
  (init [ _result _base_path])

  (cprop extension (get-extension self.response))
  (cprop response (.get requests self.href))
  (cprop headers (.get self.response "headers"))

  (property result self._result)
  (property href self.result.href)
  (property title self.result.title)
  (property base_path self._base_path)

  (property header_file_name (os.path.join self.base_path f"{self.result.title}.header.json"))
  (property body_file_name (os.path.join self.base_path f"{self.result.title}_body.{extension}"))

  (property sanitized_url (. self.href (replace "/" "_") (replace ":" "_") (replace "." "_")))
  (property sanitized_title (. self.title (replace "/" "_") (replace ":" "_") (replace "." "_")))

  (defn  save [self path]
    "Save the result dictionary and response (headers and response body) to the local file system for later use."

    (setv header_file_name (os.path.join path f"{self.sanitized_url}.header.json"))
    (setv body_file_name (os.path.join path f"{self.sanitized_url}_body.{extension}"))

    (.dump json headers (open  header_file_name "w") :indent 4)

    (with [f (open body_file_name "wb")]
      (.write f response.content))))

(defclass SearchClient []

  (init [ _base_path _search _delay])

  (property base_path self._base_path)
  (property request_delay self._delay)
  (property search self._search)

  (defn :async query [self query_string]
    (for [_result (await (self.search query_string))]
      (await (.save (SearchResult _result ))))))

(defn general_text_search [query]
  (.atext (AsyncDDGS) query
          :region "wt-wt"
          :safesearch "moderate"
          :max-results 10))
(defn pdf_text_search [query]
  (.atext (AsyncDDGS) f"{query} filetype:pdf"
          :region "wt-wt"
          :safesearch "moderate"
          :max-results 10))

(defn news_search [query]
  (fn [query]
    (.anews (AsyncDDGS) query
            :region "wt-wt"
            :safesearch "moderate"
            :max-results 10)))
(defn image_search [query]
  (.aimages (AsyncDDGS) query
            :region "wt-wt"
            :safesearch "moderate"
            :max-results 10))
(defn video_search [query]
  (.avideos (AsyncDDGS) query
            :region "wt-wt"
            :safesearch "moderate"
            :max-results 10))

(setv clients [(SearchClient "results/" general_text_search)
               (SearchClient "pdf_results/" pdf_text_search)
               (SearchClient "news_results/" news_search)
               (SearchClient "image_results/" image_search)
               (SearchClient "video_results/" video_search)])
(defn :async main []
  (for [query query_queue]
    (for [client clients]
      (await (.query client query)))))
