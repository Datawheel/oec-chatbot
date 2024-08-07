const NEXT_PUBLIC_CHAT_API = process.env.NEXT_PUBLIC_CHAT_API;


/**
 * Handle streaming response from FASTAPI Datausa-chat API wrapper
 * @param {*} chatHistory question input
 * @param {*} formJSON current form_json state
 * @param {*} setFormJSON function to set the form_json state
 * @param {*} handleTable function to handle table response from API
 * @param {*} updater  function to handle setMessegas
 * @param {*} setLoading function to handle loading 
 */
export default async function ReflectionWrap(chatHistory, formJSON, handleTable, updater, setLoading) {
    
    const _URL = `${NEXT_PUBLIC_CHAT_API}wrap/`

    const body = JSON.stringify({
        query: chatHistory,
        form_json: formJSON.current
    });

    try {
        const response = await fetch(_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json', 
                'Connection': 'keep-alive',
                'Accept-Encoding': 'gzip; deflate; br'
              },
            body: body
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
                    console.log(jsonStr);
                    const resp = JSON.parse(jsonStr);

                    if (Object.hasOwn(resp,'content')){
                        updater((prevMessages) => [...prevMessages, { text: resp.content, user: false }])
                    }
                    if (Object.hasOwn(resp,'tesseract_api')){
                        handleTable(resp.tesseract_api);
                    }

                    if (Object.hasOwn(resp,'form_json')){
                        console.log(resp.form_json);
                        formJSON.current = resp.form_json;
                    }

                } catch (error) {
                    console.error(error);
                } 
            }
        }
    } catch (error) {
        console.error(error);   
    } finally {
        setLoading(false);
    }
    

}


