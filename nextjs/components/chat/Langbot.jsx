//import { ChatOpenAI } from "@langchain/openai";
import { ChatOllama } from "@langchain/community/chat_models/ollama";
import { Ollama } from '@langchain/community/llms/ollama';
import { ChatPromptTemplate, MessagesPlaceholder, PromptTemplate } from "@langchain/core/prompts";
import { ChatMessageHistory } from "langchain/stores/message/in_memory";
import { RunnableBranch, RunnableSequence, RunnablePassthrough, RunnableLambda, RunnableParallel } from '@langchain/core/runnables'
import { StringOutputParser } from "@langchain/core/output_parsers";
import axios from 'axios';
process.env["LANGCHAIN_VERBOSE"] = true;
const NEXT_PUBLIC_CHAT_API = process.env.NEXT_PUBLIC_CHAT_API;


//Models
const model = new ChatOllama({
    baseUrl: 'https://caleuche-ollama.datawheel.us',
    model: "llama2:7b-chat-q8_0",//'mixtral',
    temperature: 0,
    system: '',
    verbose:true
  });

const model_adv = new Ollama({
    baseUrl: 'https://caleuche-ollama.datawheel.us',
    model: 'mixtral:8x7b-instruct-v0.1-q4_K_M',
    temperature: 0,
    verbose:true
});
                            
//Prompts                              
const categories = ['Senate election', 'House election',
                'President election', 'Consumer Price Index', 
                'Freight movement', 'Other topic', 'Not a question'];

const baseCategoryPrompt = `You are an expert analyzing questions content. 
    Check if a question explicitly mentions all of the following elements:`;

const baseOutputPrompt = 
`. If it does reply '''COMPLETE'''. If it doesn't, the list of the missing elements. 
Answer in the following format: 
>>analysis: [your analysis]<<,
>>answer: [your answer]<<

Here is some examples:

question: How many dollars in electronics were transported from Texas to California during 2020 by truck?
>>analysis: The question explicitly mentions a product, a transport medium, and at least one state.<<,
>>answer: COMPLETE<<

question: Who is the president?
>>analysis: The question does not mention a political party and state or a candidate name.<<,
>>answer: missing political party, state and candidate name<<

Here is a question:\n{question}
`;

const electionVars = ['political party', 'US state', ' candidate name']

const category_prompts = [
    {
        'name':'Senate election',
        'metrics': ['number of votes'],
        'optional_vars': ['year'],
        'prompt_template':`${baseCategoryPrompt} ${electionVars} ${baseOutputPrompt}`,
        'examples':[
            'What candidate to senate from the republican party received the most amount of votes in California during the 2020 elections?']
    },
    {
        'name':'House election',
        'metrics': ['number of votes'],
        'optional_vars': ['year'],
        'prompt_template':`${baseCategoryPrompt} ${electionVars} ${baseOutputPrompt}`,
        'examples':[
            'What democrat candidate to the US house of representatives received the least amount of  votes in Washington during the 2010 elections?',
            'What party received the least amount of votes during the 2010 US house of representatives elections in the state of Washington?']
    },
    {
        'name':'President election',
        'metrics': ['number of votes'],
        'optional_vars': ['year'],
        'prompt_template':`${baseCategoryPrompt} ${electionVars} ${baseOutputPrompt}`,
        'examples': [
            'What candidates from the republican and democratic parties received the most amount of votes across the country during the 2016 presidential elections?']
    },
    {
        'name':'Consumer Price Index',
        'metrics': ['cuantity', 'price metric'],
        'optional_vars': ['year'],
        'prompt_template':`${baseCategoryPrompt} ${['product name', 'date']} ${baseOutputPrompt}`,
        'examples': [
            'How much was the CPI of eggs in January of 2013?',
            'How much was the YoY variation of the CPI of eggs in January of 2014?']
    },
    {
        'name':'Freight movement',
        'metrics': ['amount', 'money'],
        'optional_vars': ['year'],
        'prompt_template':`${baseCategoryPrompt} ${[
            'product name', 'state', 'transportation medium']} ${baseOutputPrompt}`, 
        'examples': [
            'How many dollars in electronics were transported from Texas to California during 2020 by truck?',
            'How many tons of plastic were moved from Texas to California by truck during 2021?']
    },
    {
        'name': 'Other topic',
        'prompt_template':'Say: >>>DataUSA does not have information about that topic, please ask another question<<<',
        'examples': ['What is the GDP per capita?'],
    },
    {
        'name': 'Not a question',
        'prompt_template':'Say: >>>please, write your query as a question<<<',
        'examples': ['hi, how are you?'],
    }
    
]


// Chain

const class_parser = (info) => {
    let stringArray = info.split('>>');
    console.log(`In class_parser: ${stringArray}`);
    return {
        question: stringArray[stringArray.length-2],
        action: stringArray[stringArray.length-1]
    };
};

const classify_one = ChatPromptTemplate.fromTemplate(
    `Summarize the conversation in a single line question, then, classify the Summary in one 
    of these categories: ${categories}. Do it as shown in following examples: 
    
    >>conversation: '''[AI]:Hi, I'm ready to help;,[User]:Hi;''',
    >>Summary: 'Greetings.' 
    >>Category: 'not a question'

    >>conversation: '''[AI]:Hi, I'm ready to help;,[User]:Which party won the latest presidential election?;''',
    >>Summary: 'User's question is: Which party won the latest presidential election?'
    >>Category: 'President election'

    >>conversation: '''[AI]:Hi, I'm ready to help;,[User]:Who is the president?;,[User]:the current president;,[User]:of US''',
    >>Summary: 'User's question is: Who is the current president of US?'
    >>Category: 'President election'

    Now is your turn.
    >>conversation: '''{history}''',
    >>Summary: 
    `
).pipe(model).pipe(new StringOutputParser()).pipe(RunnableLambda.from(class_parser));

const route = (info) => {
    console.log(`In route: ${Object.keys(info)}`);
    for (const c of category_prompts.slice(0,-2)) {
        if (info.action.toLowerCase().includes(c.name.toLowerCase())) {
            console.log(`Class: ${c.name}`);
            return PromptTemplate.fromTemplate(c.prompt_template).pipe(model_adv);
        }
    };

    if(info.action.toLowerCase().includes('not a question')) {
        return 'Please, formulate a question';
    } else {
        return 'DataUSA does not have information regarding that topic, please ask another question';
    }
};

const action = async (init) => {
    const info = init.line;
    console.log(`In action fn: ${Object.keys(info).map(k => [k,info[k]])}`);
    let updater = init.input.updater;
    let handleTable = init.input.handleTable;

    if(info.action.toLowerCase().includes('>>answer: complete')){

        let controller = new AbortController();
        let resp = '...';
        let searchText = info.question.split(':');
        searchText = searchText[searchText.length-1];
        console.log(searchText);
        // http://localhost:3000/query/'
        // https://chat-api-dev.datausa.io/query/'
        const searchApi = (new URL(`/query/${searchText}`, NEXT_PUBLIC_CHAT_API)).href;
        axios.get(searchApi, {signal: controller.signal})
            .then((response) =>  {
                console.log(response);
                resp = response.data.query.answer;
                handleTable(response.data.query.url);
                updater((prevMessages) => [...prevMessages.slice(0, -1), { text: resp, user: false }]);
            }).catch((error) => {
                console.error(error);
                updater((prevMessages) => [...prevMessages.slice(0, -1), { text: 'Error!, try again', user: false }]);
            });
        return {
                content: "Good question! let's check the data...", 
                question: resp};
    } else {
        return {content: info.action};
    }
};

const altern_chain = RunnableSequence.from([
    RunnableParallel.from({
        line: RunnableSequence.from([
            classify_one,
            {
                question: (input) => input.question,
                action: RunnableLambda.from(route),
            },]),
        input: new RunnablePassthrough()
    }),
    RunnableLambda.from(action),
]);

const newChatMessageHistory = new ChatMessageHistory();
newChatMessageHistory.addAIMessage('Hi, ready to help you');
//newChatMessageHistory.addUserMessage('Who is the president?');

export default async function Langbot(newMessage, setMessages, handleTable) {

    newChatMessageHistory.addUserMessage(newMessage);
    
    return await altern_chain.invoke({
        //question: newMessage,
        history: (await newChatMessageHistory.getMessages()).map(
                m => `${m.lc_id[2]==='AIMessage'?' [AI]':' [User]'}:${m.content};`
            ),
        updater: setMessages,
        handleTable: handleTable,
    });
    
}
