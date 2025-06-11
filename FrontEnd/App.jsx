
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './Components/Home';
import Login from './Components/Login';
import Signup from './Components/Signup';
import Dashboard from './Components/Dashboard';
import Attendance from './Components/Attendance';
import Records from './Components/Records'; 
import AttendanceSummary from './Components/Records';
import UpdateInfo from './Components/UpdateInfo'; 
import ViewInfo from './Components/ViewInfo';
import AdminLogin from './Components/AdminLogin'; 
import CompanyRegister from './Components/CompanyRegister';
import TermsOfService from './Components/Terms';
import PrivacyPolicy from './Components/Policy';
import AboutUs from './Components/AboutUs'; 
import ContactUs from './Components/ContactUs';
const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />           
        <Route path="/login" element={<Login />} />     
        <Route path="/signup" element={<Signup />} />   
        <Route path="/dashboard" element={<Dashboard />} /> 
        <Route path="/attendance" element={<Attendance />} /> 
        <Route path="/records" element={<AttendanceSummary/>}/>
        <Route path="/update-info" element={<UpdateInfo />} />
        <Route path='/view-info' element={<ViewInfo />} /> 
        <Route path="/admin-login" element={<AdminLogin />} />
        <Route path="/register-company" element={<CompanyRegister />} />
        <Route path="/terms" element={<TermsOfService />} />
        <Route path="/privacy" element={<PrivacyPolicy />} />
        <Route path='/about' element={<AboutUs/>}/>
        <Route path='/contact' element={<ContactUs/>}/>
      </Routes>
    </Router>
  );
};

export default App;
