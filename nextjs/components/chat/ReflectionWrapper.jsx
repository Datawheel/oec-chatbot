import axios from 'axios';
const NEXT_PUBLIC_CHAT_API = process.env.NEXT_PUBLIC_CHAT_API;
/**
 * 
 */
async function* getIterableStream(body) {
    const reader = body.getReader()
    const decoder = new TextDecoder()
  
    while (true) {
      const { value, done } = await reader.read()
      if (done) {
        break
      }
      const decodedChunk = decoder.decode(value, { stream: true })
      yield decodedChunk
    }
}

export const generateStream = async (data) => {
    const _URL = `http://127.0.0.1:8000/wrap/${data}`
    try {
        const response = await fetch( _URL, { method: 'GET',})
    } catch(error) {
        console.error(error);
    }
    return getIterableStream(response.body) 
}


export default async function ReflectionWrap(input, handleTable, updater, setLoading) {
    const _URL = `http://127.0.0.1:8000/wrap/${input}`


    try {
        const response = await fetch(_URL, {
            method: 'GET'
        });

        if(response.body){
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            while (true) {
                const {done, value} = await reader.read();
                if (done){
                    break;
                }
                const str = decoder.decode(value);
                try {
                    const jsonStr = str.replace(/^data: /, '').trim();
                    const resp = JSON.parse(jsonStr);
                    if (resp.content.length === 3 ) {
                        handleTable(resp.content[0]);
                        updater((prevMessages) => [...prevMessages, { text: resp.content[2], user: false }]);
                    } else {
                        updater((prevMessages) => [...prevMessages, { text: resp.content, user: false }]);
                    }

                } catch (error) {
                    console.error(error);
                    setLoading(false);
                } 
            }
            setLoading(false);
        }
    } catch (error) {
        console.error(error);
        setLoading(false);
    }
    

}

//const sse = new EventSource('[SSE', {withCredentials: true})

