import React, { useState } from 'react';
import styles from './chatbot.module.css';
import Langbot from './Langbot';


const Chatbot = () => {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);


  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    const userMessage = { text: input, user: true };
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    const aiMessage = { text: '...', user: false };
    setMessages((prevMessages) => [...prevMessages, aiMessage]);

    const response = await Langbot(input, setMessages);

    console.log(response);
    
    const newAiMessage = [{ text: response.content, user: false }];
    if (response.hasOwnProperty('question')) {
      newAiMessage.push({ text: response.question, user: false });
    }
    setMessages((prevMessages) => [...prevMessages.slice(0, -1), ...newAiMessage]);
    setInput('');
  };
  

  return (
    <div className={styles.chatbotContainer}>
      <div className={styles.chatbotMessages}>
        {messages.map((message, index) => (
          <div
            key={index}
            className={`${styles.message} ${message.user ? styles.userMessage : styles.aiMessage}`}
          >
            {message.text}
          </div>
        ))}
      </div>
      <form className={styles.chatbotInputForm} onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your question..."
        />
        <button type="submit">Send</button>
      </form>
    </div>
  );
};
export default Chatbot;