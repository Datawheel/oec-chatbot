from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence, RunnablePassthrough

ollama_emb = OllamaEmbeddings(
    base_url= 'https://caleuche-ollama.datawheel.us',
    model="llama3",
)

model = Ollama(
    base_url= 'https://caleuche-ollama.datawheel.us',
    model= 'llama3:8b-instruct-q8_0',
  )


docs = [
        "Alpha is the first letter of Greek alphabet",
        "Beta is the second letter of Greek alphabet",
    ]



vectorstore = Chroma.from_texts(docs, ollama_emb)

retriever = vectorstore.as_retriever()


selector = PromptTemplate.from_template(
"""
Based on this information: {context}
Answer this question: {question}
"""
).pipe(model)


chain = ({'context': retriever, 'question': RunnablePassthrough()} | selector)

response =  chain.invoke({'question': 'which is the first letter?'})

print(response)