(import duckduckgo-search [AsyncDDGS])
(import asyncio)
(import requests)
(import json)
(import mimetypes)

(setv keywords ["research papers filetype:pdf" "Search term" "AI" "hacking" "bananas" "minecraft recipes"])
(setv search_results [])
(setv BASE_PATH "results/")

(print "searching for the following keywords:" keywords)

(defn get-extension [response]
  (let [content-type (.get response.headers "Content-Type")
        extension (if content-type
                      (mimetypes.guess-extension (. (.split content-type ";") [0]))
                      (.split href "." -1))]
    (if extension
        extension
        ".unknown")))


(defn :async main []
  (for [k keywords]
    (print f"Searching for {k}")
    (setv k_results [])

    (.append search_results k_results)

    (for [result (await (.atext (AsyncDDGS) k :region "wt-wt" :safesearch "moderate" :max-results 10))]

      (await (.sleep asyncio 1))

      (.append k_results result)
      (.dump json search_results (open "search_results.json" "w"))

      (setv href (. result ["href"]))

      (try
        (setv response (.get requests href))

        (setv headers (dict response.headers))

        (print (.dumps json headers :indent 4))

        (setv sanitized_url (. href (replace "/" "_") (replace ":" "_") (replace "." "_")) )

        (setv extension (get-extension response))
        (print extension)

        (when (and extension (.startswith extension "."))
          (setv extension (str (cut extension 1 (len extension)))))

        (print extension)

        (setv header_file_name f"{BASE_PATH}{sanitized_url}.header.json")
        (setv body_file_name f"{BASE_PATH}{sanitized_url}_body.{extension}")


        (.dump json headers (open  header_file_name "w") :indent 4)

        (with [f (open body_file_name "wb")]
          (.write f response.content))

        (print "Saved" href "to" body_file_name)
        (except [e Exception]
          (print f"Failed to fetch {href}: {e}")
          (continue))))))

(asyncio.run (main))
