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
            <a href="#" onClick={(e) => {
              e.preventDefault();
              setCurrentView('aboutUs');
            }}>
              About Us
            </a>
            <a
              href="https://github.com/shashankkoneru/tcas"
              target="_blank"
              rel="noreferrer"
            >
              GitHub
            </a>
          </nav>
          </div>
          <div className="header-buttons">
            <button
              className="btn btn-cfg"
              onClick={() => setCurrentView('cfg')}
            >
              Control Flow Graph
            </button>
            <button
              className="btn btn-call-graph"
              onClick={() => setCurrentView('callGraph')}
            >
              Interprocedural Control Flow Graph
            </button>
          </div>
        </header>

        {/* Show Home / About TCAS / About Us / Call Graph / CFG */}
        {currentView === 'home' ? (
          
          /* Home View */
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
                {/* <div className="input-label">what would you like to know?</div> */}
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
 
          /* About TCAS view */
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
 
        ) : currentView === 'aboutUs' ? (
 
          /* About Us view */
          <div className="about-layout">
            <h2>About Us</h2>
            <p>
              We are a team of 5 undergraduate students, attending Iowa State University, who are enrolled in COMS 4130 for the Spring 2026 semester!
            </p>
            <div className="graph-image-container">
              <img
                src="public/kennedy-about.jfif"
                alt="Kennedy Image"
                className="about-us-image"
              />
            </div>
            <p>
              Kennedy Wendl is a senior majoring in Computer Science and Data Science! 
              Outside of class, she loves to hangout with friends or go for a run. 
              Her favorite lesson from CS 4130 was learning how to draw a CFG. 
            </p>
             <div className="graph-image-container">
              <img
                src="public/kaitlyn-about.jfif"
                alt="Kaitlyn Image"
                className="about-us-image"
              />
            </div>
            <p>
              Kaitlyn Hoyme is a senior majoring in Computer Science with a minor in Data Science! 
              Outside of class, she loves to play sports and hangout with friends. 
              Her favorite lesson from CS 4130 was learning about data flow problems. 
            </p>
            <div className="graph-image-container">
              <img
                src="public/ryan-about.jfif"
                alt="Ryan Image"
                className="about-us-image"
              />
            </div>
            <p>
              Ryan Horsey is a junior majoring in Software Engineering with a minor in Data Science! 
              Outside of class, he loves to travel and try new foods. 
              His favorite lesson from CS 4130 was learning about abstract interpretation. 
            </p>
            <div className="graph-image-container">
              <img
                src="public/shashank-about.jfif"
                alt="Shashank Image"
                className="about-us-image"
              />
            </div>
            <p>
              Shashank Koneru is a junior majoring in Computer Science with a minor in Data Science! 
              Outside of class, he loves to watch movies and sports. 
              His favorite lesson from CS 4130 was learning about the various testing strategies. 
            </p>
            <p>
              Arnold Joy is a junior majoring in Software Engineering! 
              Outside of class, he loves to relax and hangout with his friends. 
              His favorite lesson from CS 4130 was learning about fuzzing. 
            </p>
          </div>
 
        ) : currentView === 'callGraph' ? (
 
          /* Call Graph view */
          <div className="about-layout">
            <h2>Interprocedural Control Flow Graph</h2>
            <p>
              The Interprocedural Control Flow Graph (ICFG) extends the CFG by connecting the control flow across all functions!
              The ICFG captures how execution transfers between call sites and their callees. 
              This allows us to reason about the program's behavior holistically, revealing cross-function dependencies and execution paths that wouldn't be visible when analyzing functions by themselves.
            </p>
            <div className="graph-image-container">
              <img
                src="public/tcas_icfg.png"
                alt="TCAS Control Flow Graph"
                className="graph-image"
              />
            </div>
          </div>
 
        ) : currentView === 'cfg' ? (
 
          /* Control Flow Graph view */
          <div className="about-layout">
            <h2>Control Flow Graph</h2>
            <p>
              The control flow graphs (CFGs) below visualize the flow of execution through the TCAS logic, with each node representing a basic block of instructions and edges representing possible execution paths. 
              Analyzing the CFGs allowed us to understand the program's branch structure and trace how logic flows through its various conditions and return paths!
            </p>
            <div className="graph-image-container">
              <img
                src="public/main_cfg.png"
                alt="TCAS Call Graph for Main"
                className="graph-image"
              />
              <img
                src="public/alt_sep_test_cfg.png"
                alt="TCAS Call Graph for Alt Sep Test"
                className="graph-image"
              />
              <img
                src="public/non_crossing_biased_climb_cfg.png"
                alt="TCAS Call Graph for Non Crossing Biased Climb"
                className="graph-image"
              />
              <img
                src="public/non_crossing_biased_descend_cfg.png"
                alt="TCAS Call Graph for Non Crossing Biased Descend"
                className="graph-image"
              />
            </div>
          </div>
 
        ) : null}

      </div>
    </div>
  );
}

export default App;