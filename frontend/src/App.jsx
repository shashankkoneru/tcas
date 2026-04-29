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
    "Show me the universe test distribution"
  ],
  "FUZZING": [
    "Did fuzzing find any crashes?",
    "What did AFL discover?"
  ]
};

function App() {
  // state to track which view we are on ('home', 'about', or 'aboutUs), start at home
  const [currentView, setCurrentView] = useState('home'); 
  
  const [openCategory, setOpenCategory] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [inputText, setInputText] = useState(""); 
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading, currentView]); 

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

  const handleSendInput = () => {
    handleAskQuestion(inputText);
    setInputText(""); 
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
            <h1 
              className="logo" 
              onClick={() => setCurrentView('home')}
              style={{ cursor: 'pointer' }}
            >
              CS 4130
            </h1>
            <nav className="nav-links">
              <a 
                href="#" 
                onClick={(e) => {
                  e.preventDefault();
                  setCurrentView('about');
                }}
              >
                About TCAS
              </a>
              <a href="#" onClick={(e)=>{
                e.preventDefault();
                setCurrentView('aboutUs')
              }} >About Us</a>
            </nav>
          </div>
          <div className="header-buttons">
            <button className="btn btn-call-graph">Call Graphs</button>
            <button className="btn btn-cfg">Control Flow Graphs</button>
          </div>
        </header>

        {/* Show Home/About TCAS/About Us */}
        {currentView === 'home' ? (
          
          /* Home View*/
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

        ) : currentView === 'about' ? (

          /* about TCAS view */
          <div className="about-layout">
            <h2>What is TCAS?</h2>
            <p>
              The Traffic Alert and Collision Avoidance System (TCAS) is an aircraft collision avoidance system 
              designed to reduce the incidence of mid-air collisions between aircraft. It monitors the airspace 
              around an aircraft for other aircraft equipped with a corresponding active transponder, independent 
              of air traffic control.
            </p>
            <p>
              When a potential threat is detected, TCAS provides the pilots with visual and audible advisories. 
              These include Traffic Advisories (TAs), which alert the crew to a nearby aircraft, and Resolution 
              Advisories (RAs), which command the crew to maneuver the aircraft (e.g., "Climb", "Descend") to 
              maintain safe separation.
            </p>
            <p>
              This static analysis project explores a simplified version of the TCAS resolution logic, analyzing 
              its control flow, data dependencies, and coverage characteristics.
            </p>
          </div>

        ) : (
          /* about us view */
          <div className="about-layout">
            <h2>About Us</h2>
            <p>
              We are a team of 5 undergraduate COMS 4130 students. 
            </p>
          </div>
        )}

      </div>
    </div>
  );
}

export default App;