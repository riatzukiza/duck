from duckduckgo_search import AsyncDDGS
import asyncio
import requests
import json

keywords=['research papers filetype:pdf',"Search term","AI","hacking","bananas","minecraft recipes"]
search_results=[]
print("Searching for the following keywords: ",keywords)

async def main():
    for keyword in keywords:
        print(f"Searching for {keyword}")

        keyword_results=[]
        search_results.append(keyword_results)

        for result in (await AsyncDDGS().atext(keyword, region='wt-wt', safesearch='Moderate', max_results=10)):

            await asyncio.sleep(5)

            print(result)
            keyword_results.append(result)

            json.dump(search_results,open("search_result.json",'w'))

            href=result['href']

            response = requests.get(href)

            header_dict=dict(response.headers)
            print(json.dumps(header_dict,indent=4))

            json.dump(header_dict,open(f"{href.replace('/','_').replace(':','_').replace('.','_')}.header.json",'w'), indent=4)
            with open(f"{href.replace('/','_').replace(':','_').replace('.','_')}_body",'wb') as f:
                f.write(response.content)
            print("Saved",href)
    print("Done")
asyncio.run(main())
