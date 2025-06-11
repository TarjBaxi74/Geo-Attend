// App.js

import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './components/Home';
import Login from './components/Login';
import Signup from './components/Signup';
import Dashboard from './components/Dashboard';
import Attendance from './components/Attendance';

const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />           {/* Home (welcome) page */}
        <Route path="/login" element={<Login />} />     {/* Login page */}
        <Route path="/signup" element={<Signup />} />   {/* Signup page */}
        <Route path="/dashboard" element={<Dashboard />} /> {/* After login/signup */}
        <Route path="/attendance" element={<Attendance />} /> {/* After login/signup */}
      </Routes>
    </Router>
  );
};

export default App;
