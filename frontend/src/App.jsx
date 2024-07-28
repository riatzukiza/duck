import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import {Debounce} from 'react-throttle';


function wait(ms) {
    return new Promise(resolve => {
        setTimeout(resolve, ms);
    });
}

const ChromaSearch = ({handleSearch}) => {
    const [data, setData] = useState({documents:[[""]]});
    const [search_term, setSearchTerm] = useState("bots");
    const [result_limit, setResultLimit] = useState(100);
    const [collection, setCollection] = useState("search_results");
    const [isSearching, setIsSearching] = useState(false);

    useEffect(() => {
        if (collection.length > 3 && search_term.length > 3 && !isSearching) {

            const fetchData = setTimeout(() => {
                return axios.get(`/search_results/${collection}/?search=${search_term}?limit=${result_limit}`)
                    .then(response => setData(response.data))
                    .catch(error => console.error(error))
            },1000)
            return () => clearTimeout(fetchData);

        }
    }, [collection,search_term]);

    return (
        <div>
            <div>
                <h1>Chroma Collection</h1>
                <input
                    type="text"
                    value={collection}
                    onChange={(e) => {
                        setCollection(e.target.value);
                    }}
                />

                    <input
                        type="text"
                        value={search_term}
                        onChange={(e) => setSearchTerm(e.target.value)} />

                <input
                    type="text"
                    value={result_limit}
                    onChange={(e) => setResultLimit(e.target.value)} />

            </div>
            {data.documents[0].map(handleSearch) }
        </div>
    );
}
const ReadCollection = ({handleDocType}) => {
    const [data, setData] = useState([]);
    const [collection, setCollection] = useState('discord_messages');
    const [channel, setChannel] = useState('duck-bot');
    const [user_name, setUserName] = useState('');
    const [timer, setTimer] = useState(null);

    useEffect(() => {

        if(!timer){
            setTimer(setTimeout(() => {
                axios.get(`/collections/${collection}/?limit=100&channel_name=${channel}&user_name=${user_name}`)
                    .then(response => {
                        setData(response.data);
                    })
                    .catch(error => {
                        console.error(error);
                    })
                    .finally(() => {
                        setTimer(null);
                    });
            }, 1000));
        }
    }, [collection,channel,user_name]);


    return (
        <div>
            <div>

          <h1>Read Collection</h1>
          <input
            type="text"
            value={collection}
            onChange={(e) => setCollection(e.target.value)}
          />

          <input
            type="text"
            value={channel}
            onChange={(e) => setChannel(e.target.value)}
          />

          <input
            type="text"
            value={user_name}
            onChange={(e) => setUserName(e.target.value)}
          />
            </div>
        {data.map(handleDocType) }
        </div>
    );
};

function handleDiscordMessage(data,index) {
    const item=data;
    const body=`${item.author_name} said at ${item.created_at} in ${item.channel_name}:

${item.content} `;
    return (
        <div style={{"float":"left", width:"500px",border:"solid"}}>
          <ReactMarkdown >
            {body}
            </ReactMarkdown>
        </div>
    );
}

const handleSearch = (data,index) => {
    return (
        <div style={{"float":"left", width:"500px",border:"solid"}}>
            <ReactMarkdown >
                {data}
            </ReactMarkdown>
        </div>
    );

}


const App = () => {
    return (
        <div>
            <div style={{"float":"left", width:"500px",border:"solid"}}>
                <ReadCollection handleDocType={handleDiscordMessage}/>
            </div>

            <div style={{"float":"left", width:"500px",border:"solid"}}>
                <ReadCollection handleDocType={handleDiscordMessage}/>
            </div>

            <div style={{"float":"left", width:"500px",border:"solid"}}>
                <ChromaSearch handleSearch={handleSearch}/>
            </div>
        </div>
    );
};

export default App;
