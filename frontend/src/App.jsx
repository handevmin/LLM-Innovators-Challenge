import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import CareerInfoPage from './pages/CareerInfoPage';
import TechStackPage from './pages/TechStackPage';
import InterviewTypePage from './pages/InterviewTypePage';
import InterviewAtmospherePage from './pages/InterviewAtmospherePage';
import AIInterviewSession from './pages/AIInterviewSession';
import AIFeedbackPage from './pages/AIFeedbackPage';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/career-info" element={<CareerInfoPage />} />
        <Route path="/tech-stack" element={<TechStackPage />} />
        <Route path="/interview-type" element={<InterviewTypePage />} />
        <Route path="/interview-atmosphere" element={<InterviewAtmospherePage />} />
        <Route path="/interview-session" element={<AIInterviewSession />} />
        <Route path="/feedback" element={<AIFeedbackPage />} />
      </Routes>
    </Router>
  );
}

export default App;