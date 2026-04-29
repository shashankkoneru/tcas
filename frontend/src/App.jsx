import React, { useState, useRef, useEffect } from 'react';
import './App.css';

const PREDEFINED_QUESTIONS = {
  "CALL GRAPH": [
    "Where is ALIM called?",
    "What does alt_sep_test call?",
    "Show me the call graph"
  ],
  "CONTROL FLOW GRAPH": [
    "How many blocks does Non_Crossing_Biased_Climb have?",
    "Does alt_sep_test have any loops?",
    "Show the CFG for ALIM"
  ],
  "DEPENDENCIES": [
    "Are Up_Separation and Down_Separation dependent?",
    "What does need_upward_RA depend on?",
    "Give me a dependency overview"
  ],
  "COVERAGE": [
    "What lines are not covered?",
    "What is the branch coverage?",
    "Show me the coverage summary"
  ],
  "TESTING": [
    "How many tests passed?",
    "Show me the test case breakdown",
    "Show me the universe test distribution",
    "What is the output distribution for all inputs?"
  ],
  "FUZZING": [
    "Did fuzzing find any crashes?",
    "What did AFL discover?"
  ]
};

function App() {
  const [openCategory, setOpenCategory] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [inputText, setInputText] = useState(""); // Track user input
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const toggleCategory = (category) => {
    setOpenCategory(openCategory === category ? null : category);
  };

  const handleAskQuestion = async (questionText) => {
    if (!questionText.trim()) return;

    setMessages(prev => [...prev, { role: 'user', content: questionText }]);
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:5000/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: questionText })
      });

      const data = await response.json();
      
      if (data.answer) {
        setMessages(prev => [...prev, { role: 'bot', content: data.answer }]);
      } else {
        setMessages(prev => [...prev, { role: 'bot', content: `Error: ${data.error}` }]);
      }
    } catch (error) {
      setMessages(prev => [...prev, { role: 'bot', content: "Failed to connect to the backend server. Make sure app.py is running on port 5000." }]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle typing and sending custom questions
  const handleSendInput = () => {
    handleAskQuestion(inputText);
    setInputText(""); // Clear the input box after sending
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleSendInput();
    }
  };

  return (
    <div className="page-wrapper">
      <div className="app-container">
        
        <header className="header">
          <div className="header-left">
            <h1 className="logo">CS 4130</h1>
            <nav className="nav-links">
              <a href="/about-tcas" target="_blank" rel="noopener noreferrer">About TCAS</a>
              <a href="/about-us" target="_blank" rel="noopener noreferrer">About Us</a>
            </nav>
          </div>
          <div className="header-buttons">
            <button className="btn btn-call-graph">Call Graphs</button>
            <button className="btn btn-cfg">Control Flow Graphs</button>
          </div>
        </header>

        <div className="main-layout">
          
          <aside className="sidebar">
            <h2 className="sidebar-title">Not sure what to ask?</h2>
            <p className="sidebar-subtitle">Choose from our list of predefined questions!</p>
            
            <div className="dropdown-container">
              {Object.keys(PREDEFINED_QUESTIONS).map((category) => (
                <div key={category} className="category-block">
                  <button 
                    className="category-btn" 
                    onClick={() => toggleCategory(category)}
                  >
                    <span>{category}</span>
                    <span className={`arrow ${openCategory === category ? 'open' : ''}`}>˅</span>
                  </button>
                  
                  {openCategory === category && (
                    <div className="question-list">
                      {PREDEFINED_QUESTIONS[category].map((q, idx) => (
                        <button 
                          key={idx} 
                          className="question-btn"
                          onClick={() => handleAskQuestion(q)}
                        >
                          {q}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </aside>

          <main className="chat-area">
            <div className="messages-container">
              {messages.length === 0 && (
                <div className="empty-state">
                  Select a question from the left or type your own to start analyzing TCAS!
                </div>
              )}
              
              {messages.map((msg, index) => (
                <div key={index} className={`message-wrapper ${msg.role}`}>
                  <div className={`message-bubble ${msg.role}`}>
                    {msg.content}
                  </div>
                </div>
              ))}
              
              {isLoading && (
                <div className="message-wrapper bot">
                  <div className="message-bubble bot loading">
                    Analyzing...
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="chat-input-wrapper">
              <div className="input-label">what would you like to know?</div>
              <div className="input-box">
                <input 
                  type="text" 
                  placeholder="Type a custom query here..."
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyDown={handleKeyDown}
                />
                <div className="send-icon" onClick={handleSendInput}>↗</div>
              </div>
            </div>
          </main>
        </div>

      </div>
    </div>
  );
}

export default App;