import React, { useState, useEffect, useRef } from 'react';

// API Configuration
const API_BASE = 'http://localhost:8000';

// Modern SVG Icon Components
const IconChat = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" className={className}><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
);
const IconResume = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" className={className}><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
);
const IconSearch = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" className={className}><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
);
const IconPrep = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" className={className}><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>
);
const IconTutorial = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" className={className}><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
);
const IconSalary = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" className={className}><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
);
const IconProfile = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" className={className}><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
);
const IconSettings = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" className={className}><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
);

// Global node names mapping
const NODE_LABELS = {
  router: 'Router',
  resume_builder: 'Resume Builder',
  job_search: 'Job Search',
  interview_prep: 'Interview Prep',
  mock_interview: 'Mock Interview',
  evaluation: 'Evaluation',
  tutorials: 'Tutorials',
  salary_negotiator: 'Salary Negotiator',
  general_qa: 'General Q&A',
  clarifier: 'Clarifier',
};

const NODE_COLORS = {
  router: '#818cf8',
  resume_builder: '#34d399',
  job_search: '#60a5fa',
  interview_prep: '#f59e0b',
  mock_interview: '#ec4899',
  evaluation: '#a78bfa',
  tutorials: '#38bdf8',
  salary_negotiator: '#4ade80',
  general_qa: '#94a3b8',
  clarifier: '#fb923c',
};

// Inline Markdown to HTML Parser Helper
const parseMarkdown = (text) => {
  if (!text) return '';
  let html = text;

  // Escape HTML to prevent injection but keep our parsed tags
  html = html
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Preformatted Code blocks
  html = html.replace(/```(?:[a-zA-Z]+)?\n([\s\S]*?)\n```/g, (match, code) => {
    return `<pre style="background:#090d16; border:1px solid #1e293b; border-radius:8px; padding:12px; color:#e2e8f0; overflow-x:auto; font-family:monospace; font-size:0.85rem; margin-bottom:12px; line-height:1.4;">${code}</pre>`;
  });

  // Headers
  html = html.replace(/^### (.*?)$/gm, '<h4 style="color:#a5b4fc; margin-top:16px; margin-bottom:8px; font-size:1.05rem; font-weight:600;">$1</h4>');
  html = html.replace(/^## (.*?)$/gm, '<h3 style="color:#a5b4fc; margin-top:18px; margin-bottom:10px; font-size:1.2rem; font-weight:600;">$1</h3>');
  html = html.replace(/^# (.*?)$/gm, '<h2 style="color:#a5b4fc; margin-top:20px; margin-bottom:12px; font-size:1.35rem; font-weight:700;">$1</h2>');

  // Bold
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong style="color:#ffffff; font-weight:600;">$1</strong>');

  // Italic
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');

  // Links
  html = html.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" style="color:#818cf8; text-decoration:none; font-weight:500; border-bottom:1px dashed #818cf8; padding-bottom:1px;">$1</a>');

  // Lists
  const lines = html.split('\n');
  const processedLines = [];
  let inList = false;

  lines.forEach((line) => {
    const stripped = line.trim();
    const listMatch = line.match(/^(\s*)[-*\u2022]\s+(.*?)$/);
    if (listMatch) {
      const indent = listMatch[1].length;
      const content = listMatch[2];
      const style = indent === 0 
        ? "margin-bottom:6px; margin-left:20px;" 
        : `margin-bottom:4px; margin-left:${20 + indent * 8}px; list-style-type:circle;`;
      
      if (!inList) {
        processedLines.push('<ul style="margin-bottom:12px; padding-left:0; list-style-type:disc; color:#cbd5e1;">');
        inList = true;
      }
      processedLines.push(`<li style="${style}">${content}</li>`);
    } else {
      if (inList) {
        processedLines.push('</ul>');
        inList = false;
      }
      if (stripped) {
        if (!stripped.startsWith('<h') && !stripped.startsWith('<u') && !stripped.startsWith('</u') && !stripped.startsWith('<li') && !stripped.startsWith('<pre') && !stripped.startsWith('</pre')) {
          if (stripped.startsWith('&gt;')) {
            processedLines.push(`<blockquote style="border-left:4px solid #818cf8; padding-left:12px; color:#94a3b8; margin:8px 0; font-style:italic;">${stripped.substring(4).trim()}</blockquote>`);
          } else {
            processedLines.push(`<p style="margin-bottom:10px; line-height:1.6; color:#cbd5e1;">${stripped}</p>`);
          }
        } else {
          processedLines.push(line);
        }
      } else {
        processedLines.push('<div style="height:8px;"></div>');
      }
    }
  });

  if (inList) {
    processedLines.push('</ul>');
  }

  return processedLines.join('\n');
};

export default function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [threadId, setThreadId] = useState('');
  
  // Settings keys
  const [settings, setSettings] = useState({
    TOGETHER_API_KEY: '',
    GOOGLE_API_KEY: '',
    GOOGLE_CSE_ID: '',
  });

  // User profile
  const [userProfile, setUserProfile] = useState({
    name: '',
    job_title: '',
    experience: '',
    skills: '',
    resume_content: '',
  });

  // Chat State
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [graphTrace, setGraphTrace] = useState([]);
  const [loadingChat, setLoadingChat] = useState(false);
  const chatBottomRef = useRef(null);

  // Resume State
  const [resumeJobDesc, setResumeJobDesc] = useState('');
  const [resumeUserDetails, setResumeUserDetails] = useState('');
  const [resumeRefinement, setResumeRefinement] = useState('');
  const [resumeLoading, setResumeLoading] = useState(false);
  const [resumeActiveSubTab, setResumeActiveSubTab] = useState('generate');

  // Job Search State
  const [jobTitle, setJobTitle] = useState('');
  const [jobLocation, setJobLocation] = useState('');
  const [jobType, setJobType] = useState('Full-time');
  const [jobContext, setJobContext] = useState('');
  const [jobResults, setJobResults] = useState('');
  const [jobLoading, setJobLoading] = useState(false);

  // Interview Prep State
  const [ivJobTitle, setIvJobTitle] = useState('');
  const [ivExperience, setIvExperience] = useState('');
  const [ivFocusArea, setIvFocusArea] = useState('');
  const [ivPrepMode, setIvPrepMode] = useState('guide'); // guide | mock | evaluate
  const [ivPrepGuide, setIvPrepGuide] = useState('');
  const [ivLoading, setIvLoading] = useState(false);

  // Mock Interview State
  const [mockStarted, setMockStarted] = useState(false);
  const [mockHistory, setMockHistory] = useState([]);
  const [mockAnswer, setMockAnswer] = useState('');
  const [mockEvaluation, setMockEvaluation] = useState('');
  
  // Custom Transcript Evaluate State
  const [pastedTranscript, setPastedTranscript] = useState('');
  const [pastedEvaluation, setPastedEvaluation] = useState('');

  // Tutorials State
  const [tutorialTopic, setTutorialTopic] = useState('');
  const [tutorialBackground, setTutorialBackground] = useState('');
  const [tutorialOutput, setTutorialOutput] = useState('');
  const [tutorialLoading, setTutorialLoading] = useState(false);

  // Salary Negotiator State
  const [salJobTitle, setSalJobTitle] = useState('');
  const [salLocation, setSalLocation] = useState('');
  const [salExperience, setSalExperience] = useState('');
  const [salOffer, setSalOffer] = useState('');
  const [salCurrent, setSalCurrent] = useState('');
  const [salSkills, setSalSkills] = useState('');
  const [salPlaybook, setSalPlaybook] = useState('');
  const [salLoading, setSalLoading] = useState(false);

  // Initial load
  useEffect(() => {
    // Generate fresh thread id
    setThreadId(uuidv4());
    
    // Fetch settings from API
    fetch(`${API_BASE}/api/settings`)
      .then((res) => res.json())
      .then((data) => {
        setSettings(data);
      })
      .catch((err) => console.error("Error loading keys:", err));
  }, []);

  // Auto-scroll chat
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const uuidv4 = () => {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
      const r = (Math.random() * 16) | 0,
        v = c === 'x' ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  };

  const handleNewSession = () => {
    setThreadId(uuidv4());
    setChatMessages([]);
    setGraphTrace([]);
    setMockHistory([]);
    setMockStarted(false);
    setMockEvaluation('');
  };

  const handleSettingsSave = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/api/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      });
      const data = await res.json();
      if (data.status === 'success') {
        alert('Settings applied successfully!');
      }
    } catch (err) {
      alert('Error saving settings: ' + err.message);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!chatInput.trim() || loadingChat) return;

    const userMsg = { role: 'user', content: chatInput };
    setChatMessages((prev) => [...prev, userMsg]);
    setChatInput('');
    setLoadingChat(true);

    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMsg.content,
          thread_id: threadId,
          user_profile: userProfile,
          interview_history: chatMessages,
          interview_mode: mockStarted ? 'mock' : 'prep'
        }),
      });
      const data = await res.json();
      setGraphTrace(data.graph_trace || []);
      
      const assistantMsg = { 
        role: 'assistant', 
        content: data.agent_output, 
        agent: data.agent_output ? data.graph_trace[data.graph_trace.length - 1] : 'router',
        trace: data.graph_trace 
      };
      setChatMessages((prev) => [...prev, assistantMsg]);
      
      // Update profile context if backend synced anything
      if (data.user_profile) {
        setUserProfile((prev) => ({ ...prev, ...data.user_profile }));
      }
    } catch (err) {
      setChatMessages((prev) => [
        ...prev,
        { role: 'assistant', content: '❌ Error: Failed to communicate with the backend. Make sure the API server is running.' },
      ]);
    } finally {
      setLoadingChat(false);
    }
  };

  // Generate Resume
  const handleGenerateResume = async () => {
    if (!resumeJobDesc || !resumeUserDetails) {
      alert('Please fill in both fields.');
      return;
    }
    setResumeLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/resume/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_description: resumeJobDesc,
          user_details: resumeUserDetails,
        }),
      });
      const data = await res.json();
      setUserProfile((prev) => ({ ...prev, resume_content: data.latex }));
      setGraphTrace(data.graph_trace || []);
    } catch (err) {
      alert('Failed to generate resume: ' + err.message);
    } finally {
      setResumeLoading(false);
    }
  };

  // Refine Resume
  const handleRefineResume = async () => {
    if (!resumeRefinement) {
      alert('Please describe your changes.');
      return;
    }
    setResumeLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/resume/refine`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          previous_resume: userProfile.resume_content,
          refinement_request: resumeRefinement,
          job_description: resumeJobDesc,
        }),
      });
      const data = await res.json();
      setUserProfile((prev) => ({ ...prev, resume_content: data.latex }));
      setGraphTrace(data.graph_trace || []);
      setResumeRefinement('');
    } catch (err) {
      alert('Failed to refine resume: ' + err.message);
    } finally {
      setResumeLoading(false);
    }
  };

  // Search Jobs
  const handleJobSearch = async () => {
    if (!jobTitle || !jobLocation) {
      alert('Job Title and Location are required.');
      return;
    }
    setJobLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/job/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_title: jobTitle,
          location: jobLocation,
          job_type: jobType,
          user_context: jobContext || userProfile.skills,
        }),
      });
      const data = await res.json();
      setJobResults(data.output);
      setGraphTrace(data.graph_trace || []);
    } catch (err) {
      alert('Search failed: ' + err.message);
    } finally {
      setJobLoading(false);
    }
  };

  // Generate Prep Guide
  const handleGeneratePrepGuide = async () => {
    if (!ivJobTitle) {
      alert('Job Title is required.');
      return;
    }
    setIvLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/interview/prep`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_title: ivJobTitle,
          user_experience: ivExperience || userProfile.experience,
          user_name: userProfile.name || 'Candidate',
          focus_area: ivFocusArea,
        }),
      });
      const data = await res.json();
      setIvPrepGuide(data.output);
      setGraphTrace(data.graph_trace || []);
    } catch (err) {
      alert('Failed to build guide: ' + err.message);
    } finally {
      setIvLoading(false);
    }
  };

  // Mock Interview Start
  const handleStartMock = async () => {
    if (!ivJobTitle) {
      alert('Job Title is required to start.');
      return;
    }
    setIvLoading(true);
    setMockEvaluation('');
    try {
      const res = await fetch(`${API_BASE}/api/interview/mock/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_title: ivJobTitle,
          user_experience: ivExperience || userProfile.experience,
          user_name: userProfile.name || 'Candidate',
          thread_id: threadId,
        }),
      });
      const data = await res.json();
      setMockHistory(data.history || []);
      setMockStarted(true);
    } catch (err) {
      alert('Failed to start mock: ' + err.message);
    } finally {
      setIvLoading(false);
    }
  };

  // Mock Interview Answer submit
  const handleSendMockAnswer = async (e) => {
    e.preventDefault();
    if (!mockAnswer.trim() || ivLoading) return;

    const updatedHistory = [...mockHistory, { role: 'user', content: mockAnswer }];
    setMockHistory(updatedHistory);
    const candidateAnswer = mockAnswer;
    setMockAnswer('');
    setIvLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/interview/mock/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          answer: candidateAnswer,
          job_title: ivJobTitle,
          user_experience: ivExperience || userProfile.experience,
          user_name: userProfile.name || 'Candidate',
          history: updatedHistory,
          thread_id: threadId,
        }),
      });
      const data = await res.json();
      setMockHistory(data.history || []);
    } catch (err) {
      alert('Interviewer response failed: ' + err.message);
    } finally {
      setIvLoading(false);
    }
  };

  // Mock End and Evaluate
  const handleEndAndEvaluateMock = async () => {
    setIvLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/interview/mock/evaluate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_title: ivJobTitle,
          user_experience: ivExperience || userProfile.experience,
          user_name: userProfile.name || 'Candidate',
          history: mockHistory,
        }),
      });
      const data = await res.json();
      setMockEvaluation(data.evaluation);
      setMockStarted(false);
      setMockHistory([]);
    } catch (err) {
      alert('Evaluation failed: ' + err.message);
    } finally {
      setIvLoading(false);
    }
  };

  // Custom pasted transcript evaluate
  const handleEvaluateCustomTranscript = async () => {
    if (!ivJobTitle || !pastedTranscript) {
      alert('Job Title and transcript are required.');
      return;
    }
    setIvLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/interview/evaluate_transcript`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_title: ivJobTitle,
          user_experience: ivExperience || userProfile.experience,
          user_name: userProfile.name || 'Candidate',
          transcript: pastedTranscript,
        }),
      });
      const data = await res.json();
      setPastedEvaluation(data.evaluation);
    } catch (err) {
      alert('Pasted transcript evaluation failed: ' + err.message);
    } finally {
      setIvLoading(false);
    }
  };

  // Generate Tutorial
  const handleGenerateTutorial = async () => {
    if (!tutorialTopic) {
      alert('Please enter a topic.');
      return;
    }
    setTutorialLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/tutorials`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: tutorialTopic,
          user_background: tutorialBackground || userProfile.skills,
        }),
      });
      const data = await res.json();
      setTutorialOutput(data.output);
      setGraphTrace(data.graph_trace || []);
    } catch (err) {
      alert('Failed to build tutorial: ' + err.message);
    } finally {
      setTutorialLoading(false);
    }
  };

  // Generate Salary counter offer strategy
  const handleGenerateSalaryOffer = async () => {
    if (!salJobTitle) {
      alert('Job Title is required.');
      return;
    }
    setSalLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/salary/playbook`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_title: salJobTitle,
          location: salLocation,
          experience: salExperience,
          current_offer: salOffer,
          current_salary: salCurrent,
          skills: salSkills || userProfile.skills,
        }),
      });
      const data = await res.json();
      setSalPlaybook(data.output);
      setGraphTrace(['router', 'salary_negotiator']);
    } catch (err) {
      alert('Failed to generate salary playbook: ' + err.message);
    } finally {
      setSalLoading(false);
    }
  };

  return (
    <div className="app-container">
      {/* Navigation Sidebar */}
      <div className="sidebar">
        <div className="sidebar-logo">
          <span className="logo-badge">C</span>
          <div>
            <div className="logo-text">career.ai</div>
            <div className="sidebar-subtitle">Agentic Assistant</div>
          </div>
        </div>
        
        <div className="sidebar-divider" />
        
        <div className="sidebar-section-title">Navigation</div>
        <ul className="nav-list">
          <li>
            <button className={`nav-item-btn ${activeTab === 'chat' ? 'active' : ''}`} onClick={() => setActiveTab('chat')}>
              <IconChat className="nav-icon" /> Chat Assistant
            </button>
          </li>
          <li>
            <button className={`nav-item-btn ${activeTab === 'resume' ? 'active' : ''}`} onClick={() => setActiveTab('resume')}>
              <IconResume className="nav-icon" /> Resume Builder
            </button>
          </li>
          <li>
            <button className={`nav-item-btn ${activeTab === 'job' ? 'active' : ''}`} onClick={() => setActiveTab('job')}>
              <IconSearch className="nav-icon" /> Job Search
            </button>
          </li>
          <li>
            <button className={`nav-item-btn ${activeTab === 'interview' ? 'active' : ''}`} onClick={() => setActiveTab('interview')}>
              <IconPrep className="nav-icon" /> Interview Prep
            </button>
          </li>
          <li>
            <button className={`nav-item-btn ${activeTab === 'tutorials' ? 'active' : ''}`} onClick={() => setActiveTab('tutorials')}>
              <IconTutorial className="nav-icon" /> Tutorials
            </button>
          </li>
          <li>
            <button className={`nav-item-btn ${activeTab === 'salary' ? 'active' : ''}`} onClick={() => setActiveTab('salary')}>
              <IconSalary className="nav-icon" /> Salary Negotiator
            </button>
          </li>
          <li>
            <button className={`nav-item-btn ${activeTab === 'profile' ? 'active' : ''}`} onClick={() => setActiveTab('profile')}>
              <IconProfile className="nav-icon" /> Your Profile
            </button>
          </li>
        </ul>

        {/* Sidebar settings keys */}
        <div className="sidebar-footer">
          <div className="sidebar-divider" />
          <button className={`nav-item-btn ${activeTab === 'settings' ? 'active' : ''}`} onClick={() => setActiveTab('settings')}>
            <IconSettings className="nav-icon" /> Settings & Keys
          </button>
        </div>
      </div>

      {/* Main Panel */}
      <div className="main-workspace">
        {/* Render Active View Header */}
        {activeTab === 'chat' && (
          <div className="saas-header">
            <h1><IconChat className="header-icon" /> Chat Assistant</h1>
            <p>Ask anything career-related — I'll route you to the right specialist automatically.</p>
          </div>
        )}
        {activeTab === 'resume' && (
          <div className="saas-header">
            <h1><IconResume className="header-icon" /> Resume Builder</h1>
            <p>Generate ATS-optimized LaTeX resumes tailored to any job description.</p>
          </div>
        )}
        {activeTab === 'job' && (
          <div className="saas-header">
            <h1><IconSearch className="header-icon" /> Job Search</h1>
            <p>Find live job openings tailored to your profile.</p>
          </div>
        )}
        {activeTab === 'interview' && (
          <div className="saas-header">
            <h1><IconPrep className="header-icon" /> Interview Prep</h1>
            <p>Preparation guides, mock interviews, and scorecards.</p>
          </div>
        )}
        {activeTab === 'tutorials' && (
          <div className="saas-header">
            <h1><IconTutorial className="header-icon" /> Tutorials</h1>
            <p>Deep-dive, project-based learning on any tech topic.</p>
          </div>
        )}
        {activeTab === 'salary' && (
          <div className="saas-header">
            <h1><IconSalary className="header-icon" /> Salary Negotiator</h1>
            <p>Get counter-offer strategy playbooks and word-for-word scripts.</p>
          </div>
        )}
        {activeTab === 'profile' && (
          <div className="saas-header">
            <h1><IconProfile className="header-icon" /> Your Profile</h1>
            <p>Your career profile is shared across all specialist agents.</p>
          </div>
        )}
        {activeTab === 'settings' && (
          <div className="saas-header">
            <h1><IconSettings className="header-icon" /> Settings & Keys</h1>
            <p>Configure model keys and Google Search API settings.</p>
          </div>
        )}

        {/* Workspace Content */}
        <div className="workspace-content">
          
          {/* VIEW: Chat Assistant */}
          {activeTab === 'chat' && (
            <div className="chat-container">
              {/* Node highlights */}
              <div className="card" style={{ padding: '16px', marginBottom: '16px' }}>
                <div style={{ fontSize: '0.68rem', color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '8px', fontWeight: 600 }}>
                  🔗 Live Graph — Active Nodes Highlighted
                </div>
                <div className="trace-container">
                  {Object.entries(NODE_LABELS).map(([node, label], i) => (
                    <React.Fragment key={node}>
                      <span className={`trace-node ${graphTrace.includes(node) ? 'active' : ''}`} style={graphTrace.includes(node) ? { borderColor: NODE_COLORS[node], color: '#ffffff', background: `${NODE_COLORS[node]}1c` } : {}}>
                        {label}
                      </span>
                      {i < Object.keys(NODE_LABELS).length - 1 && <span className="trace-arrow">→</span>}
                    </React.Fragment>
                  ))}
                </div>
              </div>

              {/* Chat Thread */}
              <div className="card" style={{ flexGrow: 1, padding: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column', height: 'calc(100vh - 350px)' }}>
                <div style={{ padding: '12px 18px', background: '#161b27', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Session Thread: <code>{threadId.substring(0, 8)}...</code>
                  </span>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button className="btn-secondary" style={{ padding: '6px 12px', fontSize: '0.75rem' }} onClick={handleNewSession}>
                      New Session
                    </button>
                    <button className="btn-secondary" style={{ padding: '6px 12px', fontSize: '0.75rem', borderColor: 'var(--danger-color)', color: '#fda4af' }} onClick={() => setChatMessages([])}>
                      Clear Chat
                    </button>
                  </div>
                </div>

                <div className="chat-history">
                  {chatMessages.length === 0 && (
                    <div style={{ margin: 'auto', textAlign: 'center', color: 'var(--text-muted)', maxWidth: '400px' }}>
                      <div style={{ fontSize: '2.5rem', marginBottom: '12px', color: 'var(--accent-color)' }}>
                        <IconChat className="header-icon" style={{ margin: 0, width: '48px', height: '48px' }} />
                      </div>
                      <h4>Welcome to career.ai Assistant</h4>
                      <p style={{ fontSize: '0.82rem', marginTop: '6px' }}>Ask me about career strategies, resume updates, live jobs, mock preparation, or salary negotiations.</p>
                    </div>
                  )}

                  {chatMessages.map((msg, idx) => (
                    <div key={idx} className={`chat-message ${msg.role === 'user' ? 'user' : ''}`}>
                      <div className="chat-message-meta">
                        {msg.role === 'user' ? 'You' : `Agent: ${NODE_LABELS[msg.agent] || msg.agent || 'router'}`}
                      </div>
                      <div className="chat-message-content" dangerouslySetInnerHTML={{ __html: parseMarkdown(msg.content) }} />
                    </div>
                  ))}
                  
                  {loadingChat && (
                    <div className="chat-message" style={{ borderStyle: 'dashed' }}>
                      <div className="chat-message-meta">Agent: thinking...</div>
                      <div className="spinner" style={{ width: '20px', height: '20px', borderWidth: '2px' }} />
                    </div>
                  )}
                  <div ref={chatBottomRef} />
                </div>

                {/* Message input */}
                <form className="chat-input-container" onSubmit={handleSendMessage}>
                  <input
                    type="text"
                    className="chat-input"
                    placeholder="Ask about resume, jobs, interview preparation, salary strategies..."
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    disabled={loadingChat}
                  />
                  <button type="submit" className="btn-primary" disabled={loadingChat}>
                    Send
                  </button>
                </form>
              </div>
            </div>
          )}

          {/* VIEW: Resume Builder */}
          {activeTab === 'resume' && (
            <div className="split-pane">
              <div className="split-left">
                <ul className="tab-list">
                  <li>
                    <button className={`tab-btn ${resumeActiveSubTab === 'generate' ? 'active' : ''}`} onClick={() => setResumeActiveSubTab('generate')}>
                      Generate
                    </button>
                  </li>
                  <li>
                    <button className={`tab-btn ${resumeActiveSubTab === 'refine' ? 'active' : ''}`} onClick={() => setResumeActiveSubTab('refine')}>
                      Refine
                    </button>
                  </li>
                </ul>

                {resumeActiveSubTab === 'generate' ? (
                  <div className="card">
                    <h3 style={{ border: 'none', padding: 0 }}>Create tailored resume</h3>
                    <div className="form-group">
                      <label>Target Job Description</label>
                      <textarea
                        className="form-textarea"
                        placeholder="Paste full job details here..."
                        value={resumeJobDesc}
                        onChange={(e) => setResumeJobDesc(e.target.value)}
                        style={{ height: '140px' }}
                      />
                    </div>
                    <div className="form-group">
                      <label>Your Details (Background/Skills/Education)</label>
                      <textarea
                        className="form-textarea"
                        placeholder="List your background history, metrics, and details..."
                        value={resumeUserDetails}
                        onChange={(e) => setResumeUserDetails(e.target.value)}
                        style={{ height: '140px' }}
                      />
                    </div>
                    <button className="btn-primary" onClick={handleGenerateResume} disabled={resumeLoading}>
                      {resumeLoading ? 'Generating...' : 'Generate LaTeX Resume'}
                    </button>
                  </div>
                ) : (
                  <div className="card">
                    <h3 style={{ border: 'none', padding: 0 }}>Apply modifications</h3>
                    {!userProfile.resume_content ? (
                      <div className="alert alert-info">
                        Generate a resume in the <strong>Generate</strong> tab first before refining.
                      </div>
                    ) : (
                      <>
                        <div className="form-group">
                          <label>Describe changes you want</label>
                          <textarea
                            className="form-textarea"
                            placeholder="E.g., Add docker to skills section, rewrite details under Amazon, make summary more focused..."
                            value={resumeRefinement}
                            onChange={(e) => setResumeRefinement(e.target.value)}
                            style={{ height: '120px' }}
                          />
                        </div>
                        <div className="form-group">
                          <label>Job Description Context (Optional)</label>
                          <input
                            type="text"
                            className="form-input"
                            placeholder="Paste job details here to align refinements..."
                            value={resumeJobDesc}
                            onChange={(e) => setResumeJobDesc(e.target.value)}
                          />
                        </div>
                        <button className="btn-primary" onClick={handleRefineResume} disabled={resumeLoading}>
                          {resumeLoading ? 'Applying...' : 'Apply Refinements'}
                        </button>
                      </>
                    )}
                  </div>
                )}
              </div>

              {/* LaTeX Editor Panel */}
              <div className="split-right">
                <div className="code-viewer-container">
                  <div className="code-viewer-header">
                    <span>📄 LaTeX Source Code</span>
                    <button className="btn-secondary" style={{ padding: '4px 10px', fontSize: '0.72rem' }} onClick={() => {
                      navigator.clipboard.writeText(userProfile.resume_content);
                      alert('LaTeX code copied to clipboard!');
                    }} disabled={!userProfile.resume_content}>
                      Copy Code
                    </button>
                  </div>
                  <div className="code-viewer-content">
                    {resumeLoading ? (
                      <div className="spinner-container">
                        <div className="spinner" />
                      </div>
                    ) : userProfile.resume_content ? (
                      userProfile.resume_content
                    ) : (
                      <span style={{ color: 'var(--text-muted)' }}>Generate a resume on the left pane to view LaTeX source. You can compile this code directly into a PDF in Overleaf.</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* VIEW: Job Search */}
          {activeTab === 'job' && (
            <div className="grid-2">
              <div>
                <div className="card">
                  <div className="form-group">
                    <label>Job Title *</label>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="e.g. Software Engineer"
                      value={jobTitle}
                      onChange={(e) => setJobTitle(e.target.value)}
                    />
                  </div>
                  <div className="form-group">
                    <label>Location *</label>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="e.g. London or Remote"
                      value={jobLocation}
                      onChange={(e) => setJobLocation(e.target.value)}
                    />
                  </div>
                  <div className="form-group">
                    <label>Job Type</label>
                    <select className="form-select" value={jobType} onChange={(e) => setJobType(e.target.value)}>
                      <option>Full-time</option>
                      <option>Part-time</option>
                      <option>Contract</option>
                      <option>Internship</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Personal context (Skills / Target preferences)</label>
                    <textarea
                      className="form-textarea"
                      placeholder="List skills or experience targets to customize suggestions..."
                      value={jobContext}
                      onChange={(e) => setJobContext(e.target.value)}
                      style={{ height: '80px' }}
                    />
                  </div>
                  <button className="btn-primary" onClick={handleJobSearch} disabled={jobLoading}>
                    {jobLoading ? 'Searching...' : 'Search Jobs'}
                  </button>
                </div>
              </div>

              {/* Search Results Display */}
              <div>
                {jobLoading ? (
                  <div className="spinner-container" style={{ height: '300px' }}>
                    <div className="spinner" />
                  </div>
                ) : jobResults ? (
                  <div className="card">
                    <h3 style={{ border: 'none', padding: 0 }}>Listings Found</h3>
                    <div style={{ fontSize: '0.92rem', color: '#cbd5e1', lineHeight: '1.6' }} dangerouslySetInnerHTML={{ __html: parseMarkdown(jobResults) }} />
                  </div>
                ) : (
                  <div className="alert alert-info">
                    Specify job title and location to scan open positions. Results will format inside this dashboard card.
                  </div>
                )}
              </div>
            </div>
          )}

          {/* VIEW: Interview Prep */}
          {activeTab === 'interview' && (
            <div>
              <div className="card" style={{ marginBottom: '24px' }}>
                <div className="grid-3">
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label>Job Title *</label>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="e.g. Frontend Developer"
                      value={ivJobTitle}
                      onChange={(e) => setIvJobTitle(e.target.value)}
                    />
                  </div>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label>Your Experience</label>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="e.g. 3 years React developer"
                      value={ivExperience}
                      onChange={(e) => setIvExperience(e.target.value)}
                    />
                  </div>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label>Prep focus area</label>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="e.g. Behavioral, system design..."
                      value={ivFocusArea}
                      onChange={(e) => setIvFocusArea(e.target.value)}
                    />
                  </div>
                </div>

                <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button className={`tab-btn ${ivPrepMode === 'guide' ? 'active' : ''}`} onClick={() => setIvPrepMode('guide')}>
                      Prep Guide
                    </button>
                    <button className={`tab-btn ${ivPrepMode === 'mock' ? 'active' : ''}`} onClick={() => setIvPrepMode('mock')}>
                      Mock Interview
                    </button>
                    <button className={`tab-btn ${ivPrepMode === 'evaluate' ? 'active' : ''}`} onClick={() => setIvPrepMode('evaluate')}>
                      Evaluate Transcript
                    </button>
                  </div>
                </div>
              </div>

              {/* Sub-tab 1: Prep Guide */}
              {ivPrepMode === 'guide' && (
                <div>
                  <div style={{ marginBottom: '16px' }}>
                    <button className="btn-primary" onClick={handleGeneratePrepGuide} disabled={ivLoading}>
                      {ivLoading ? 'Generating...' : 'Generate Interview Prep Guide'}
                    </button>
                  </div>
                  {ivLoading ? (
                    <div className="spinner-container"><div className="spinner" /></div>
                  ) : ivPrepGuide ? (
                    <div className="card">
                      <h3>🎯 Custom Guide</h3>
                      <div dangerouslySetInnerHTML={{ __html: parseMarkdown(ivPrepGuide) }} />
                    </div>
                  ) : (
                    <div className="alert alert-info">Enter job title above and click Generate to build interview study cards.</div>
                  )}
                </div>
              )}

              {/* Sub-tab 2: Mock Interview Chat */}
              {ivPrepMode === 'mock' && (
                <div>
                  {!mockStarted && !mockEvaluation && (
                    <div className="card" style={{ textAlign: 'center', padding: '40px' }}>
                      <div style={{ fontSize: '3rem', marginBottom: '16px', color: 'var(--accent-color)' }}>
                        <IconPrep className="header-icon" style={{ margin: 0, width: '48px', height: '48px' }} />
                      </div>
                      <h3>AI Mock Interview Simulation</h3>
                      <p style={{ color: 'var(--text-muted)', marginBottom: '24px', maxWidth: '500px', margin: '0 auto 24px' }}>
                        The interviewer agent will run a realistic, 1-on-1 interview based on your job details. Answer each question dynamically to progress.
                      </p>
                      <button className="btn-primary" onClick={handleStartMock} disabled={ivLoading}>
                        {ivLoading ? 'Starting...' : 'Start Interview'}
                      </button>
                    </div>
                  )}

                  {mockStarted && (
                    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                      <div style={{ padding: '12px 18px', background: '#161b27', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Active Mock: {ivJobTitle}</span>
                        <div style={{ display: 'flex', gap: '8px' }}>
                          <button className="btn-secondary" style={{ padding: '6px 12px', fontSize: '0.72rem', borderColor: 'var(--danger-color)', color: '#fda4af' }} onClick={() => {
                            setMockStarted(false);
                            setMockHistory([]);
                          }}>
                            End Mock
                          </button>
                          <button className="btn-primary" style={{ padding: '6px 12px', fontSize: '0.72rem' }} onClick={handleEndAndEvaluateMock} disabled={ivLoading}>
                            End & Evaluate Performance
                          </button>
                        </div>
                      </div>

                      {/* Mock Conversation Stream */}
                      <div style={{ height: '350px', overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        {mockHistory.map((m, i) => (
                          <div key={i} className={`chat-message ${m.role === 'user' ? 'user' : ''}`}>
                            <div className="chat-message-meta">{m.role === 'user' ? 'You' : 'Interviewer'}</div>
                            <div className="chat-message-content" dangerouslySetInnerHTML={{ __html: parseMarkdown(m.content) }} />
                          </div>
                        ))}
                        {ivLoading && (
                          <div className="chat-message">
                            <div className="chat-message-meta">Interviewer is thinking...</div>
                            <div className="spinner" style={{ width: '20px', height: '20px', borderWidth: '2px' }} />
                          </div>
                        )}
                      </div>

                      <form className="chat-input-container" onSubmit={handleSendMockAnswer}>
                        <input
                          type="text"
                          className="chat-input"
                          placeholder="Type your response here..."
                          value={mockAnswer}
                          onChange={(e) => setMockAnswer(e.target.value)}
                          disabled={ivLoading}
                        />
                        <button type="submit" className="btn-primary" disabled={ivLoading}>
                          Submit Response
                        </button>
                      </form>
                    </div>
                  )}

                  {mockEvaluation && (
                    <div className="card">
                      <h3>Mock Evaluation Report</h3>
                      <div dangerouslySetInnerHTML={{ __html: parseMarkdown(mockEvaluation) }} />
                      <button className="btn-secondary" style={{ marginTop: '16px' }} onClick={() => setMockEvaluation('')}>
                        Start New Session
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Sub-tab 3: Custom transcript evaluation */}
              {ivPrepMode === 'evaluate' && (
                <div className="grid-2">
                  <div className="card">
                    <div className="form-group">
                      <label>Paste Interview Transcript</label>
                      <textarea
                        className="form-textarea"
                        placeholder="Interviewer: Tell me about yourself.&#10;Me: I have 3 years experience..."
                        value={pastedTranscript}
                        onChange={(e) => setPastedTranscript(e.target.value)}
                        style={{ height: '240px' }}
                      />
                    </div>
                    <button className="btn-primary" onClick={handleEvaluateCustomTranscript} disabled={ivLoading}>
                      {ivLoading ? 'Analyzing...' : 'Evaluate Custom Transcript'}
                    </button>
                  </div>

                  <div>
                    {ivLoading ? (
                      <div className="spinner-container"><div className="spinner" /></div>
                    ) : pastedEvaluation ? (
                      <div className="card">
                        <h3>Performance Evaluation</h3>
                        <div dangerouslySetInnerHTML={{ __html: parseMarkdown(pastedEvaluation) }} />
                      </div>
                    ) : (
                      <div className="alert alert-info">Paste an interview script on the left card to generate structured scorecard feedback.</div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* VIEW: Tutorials */}
          {activeTab === 'tutorials' && (
            <div className="grid-2">
              <div className="card">
                <div className="form-group">
                  <label>What topic do you want to learn?</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. LangGraph Agents, React hooks, Docker..."
                    value={tutorialTopic}
                    onChange={(e) => setTutorialTopic(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label>Your Background (Optional context)</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. Python beginner, node developer..."
                    value={tutorialBackground}
                    onChange={(e) => setTutorialBackground(e.target.value)}
                  />
                </div>
                <button className="btn-primary" onClick={handleGenerateTutorial} disabled={tutorialLoading}>
                  {tutorialLoading ? 'Building Course...' : 'Generate Tutorial'}
                </button>
              </div>

              <div>
                {tutorialLoading ? (
                  <div className="spinner-container"><div className="spinner" /></div>
                ) : tutorialOutput ? (
                  <div className="card">
                    <h3>Lesson Card</h3>
                    <div dangerouslySetInnerHTML={{ __html: parseMarkdown(tutorialOutput) }} />
                  </div>
                ) : (
                  <div className="alert alert-info">Enter a learning topic to construct project-based copy-pastable lessons.</div>
                )}
              </div>
            </div>
          )}

          {/* VIEW: Salary Negotiator */}
          {activeTab === 'salary' && (
            <div className="grid-2">
              <div className="card">
                <div className="alert alert-info" style={{ padding: '10px 14px', marginBottom: '16px', fontSize: '0.8rem' }}>
                  Tip: Provide as many offer coordinates as possible to build negotiation leverage.
                </div>
                <div className="form-group">
                  <label>Job Title *</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. Lead Engineer"
                    value={salJobTitle}
                    onChange={(e) => setSalJobTitle(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label>Location</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. San Francisco or Remote"
                    value={salLocation}
                    onChange={(e) => setSalLocation(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label>Years of Experience</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. 5"
                    value={salExperience}
                    onChange={(e) => setSalExperience(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label>Current/Expected Salary</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. $130,000"
                    value={salCurrent}
                    onChange={(e) => setSalCurrent(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label>Target Offer Details (Optional)</label>
                  <textarea
                    className="form-textarea"
                    placeholder="e.g. $150k base salary, $20k equity..."
                    value={salOffer}
                    onChange={(e) => setSalOffer(e.target.value)}
                    style={{ height: '70px' }}
                  />
                </div>
                <div className="form-group">
                  <label>Key Strengths / Differentiators</label>
                  <textarea
                    className="form-textarea"
                    placeholder="e.g. Managed 5 developers, optimized database queries by 40%..."
                    value={salSkills}
                    onChange={(e) => setSalSkills(e.target.value)}
                    style={{ height: '70px' }}
                  />
                </div>
                <button className="btn-primary" onClick={handleGenerateSalaryOffer} disabled={salLoading}>
                  {salLoading ? 'Building Playbook...' : 'Build Negotiation Playbook'}
                </button>
              </div>

              <div>
                {salLoading ? (
                  <div className="spinner-container"><div className="spinner" /></div>
                ) : salPlaybook ? (
                  <div className="card">
                    <h3>Counter offer strategy</h3>
                    <div dangerouslySetInnerHTML={{ __html: parseMarkdown(salPlaybook) }} />
                  </div>
                ) : (
                  <div className="alert alert-info">Provide offer numbers on the left card to compile market rates and script letters.</div>
                )}
              </div>
            </div>
          )}

          {/* VIEW: Profile */}
          {activeTab === 'profile' && (
            <div className="card">
              <h3>Edit Your Profile Context</h3>
              <div className="grid-2">
                <div>
                  <div className="form-group">
                    <label>Full Name</label>
                    <input
                      type="text"
                      className="form-input"
                      value={userProfile.name}
                      onChange={(e) => setUserProfile({ ...userProfile, name: e.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label>Current Title</label>
                    <input
                      type="text"
                      className="form-input"
                      value={userProfile.job_title}
                      onChange={(e) => setUserProfile({ ...userProfile, job_title: e.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label>Work Experience Summary</label>
                    <textarea
                      className="form-textarea"
                      value={userProfile.experience}
                      onChange={(e) => setUserProfile({ ...userProfile, experience: e.target.value })}
                      style={{ height: '120px' }}
                    />
                  </div>
                </div>

                <div>
                  <div className="form-group">
                    <label>Skills & Strengths</label>
                    <textarea
                      className="form-textarea"
                      value={userProfile.skills}
                      onChange={(e) => setUserProfile({ ...userProfile, skills: e.target.value })}
                      style={{ height: '100px' }}
                    />
                  </div>
                  {userProfile.resume_content && (
                    <div className="form-group">
                      <label>Saved LaTeX Resume</label>
                      <div className="alert alert-success" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span>LaTeX Resume Saved!</span>
                        <button className="btn-secondary" style={{ padding: '4px 10px', fontSize: '0.72rem' }} onClick={() => setUserProfile({ ...userProfile, resume_content: '' })}>
                          Clear Resume
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
              
              <button className="btn-primary" style={{ marginTop: '16px' }} onClick={() => alert('Profile context saved and synchronized across agents!')}>
                Save Profile Changes
              </button>
            </div>
          )}

          {/* VIEW: Settings */}
          {activeTab === 'settings' && (
            <div className="card">
              <h3>Config & Credentials</h3>
              <form onSubmit={handleSettingsSave}>
                <div className="form-group">
                  <label>Together AI API Key</label>
                  <input
                    type="password"
                    className="form-input"
                    placeholder="Enter Together API Key"
                    value={settings.TOGETHER_API_KEY}
                    onChange={(e) => setSettings({ ...settings, TOGETHER_API_KEY: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Google Search API Key</label>
                  <input
                    type="password"
                    className="form-input"
                    placeholder="Enter Google Search JSON API Key"
                    value={settings.GOOGLE_API_KEY}
                    onChange={(e) => setSettings({ ...settings, GOOGLE_API_KEY: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Google Search Engine ID (CSE ID)</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Enter Google CSE ID"
                    value={settings.GOOGLE_CSE_ID}
                    onChange={(e) => setSettings({ ...settings, GOOGLE_CSE_ID: e.target.value })}
                  />
                </div>
                <button type="submit" className="btn-primary" style={{ marginTop: '16px' }}>
                  Save and Apply Settings
                </button>
              </form>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
