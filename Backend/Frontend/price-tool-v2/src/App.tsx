import { Routes, Route, Navigate } from "react-router-dom";
import Product from "./Product"
import Home from "./Home";
import LogInPage from "./LogInPage";
import NavBar from "./NavBar";
import { useState } from "react";
import { ProfilePage } from "./ProfilePage";
import SummaryPage from "./SummaryPage";
import PriceProposalPage from "./PriceProposalPage";
import FinancialsPage from "./FinancialsPage";
import RecommendationPage from "./RecommendationPage";
import AdminPage from "./AdminPage";


function App() {
  const [loggedInUser, setLoggedInUser] = useState<{
  id?: number;
  role: string;
  email: string;
  name?: string;
  phone?: string;
  location?: string;
  joinDate?: string;
} | null>(null);


  const handleLogout = () => {
    setLoggedInUser(null);
  };

  return (
    <Routes>
      <Route path="/" element={<LogInPage setLoggedInUser={setLoggedInUser} />} />
      
      <Route
        path="/Home"
        element={
          loggedInUser ? (
            <>
              <NavBar onLogout={handleLogout} loggedInUser={loggedInUser} />
              <Home loggedInUser={loggedInUser} />
            </>
          ) : (
            <Navigate to="/" />
          )
        }
      >
        <Route index element={<SummaryPage />} />
        <Route path="PriceProposalPage" element={<PriceProposalPage />} />
        <Route path="FinancialsPage" element={<FinancialsPage />} />
        <Route path="RecommendationPage" element={<RecommendationPage />} />
        <Route path="AdminPage" element={<AdminPage loggedInUser={loggedInUser} />} />
        </Route>
            <Route
        path="/Product"
        element={
          loggedInUser ? (
            <>
              <NavBar onLogout={handleLogout} loggedInUser={loggedInUser} />
              <Product loggedInUser={loggedInUser} />
            </>
          ) : (
            <Navigate to="/" />
          )
        }
      />
      <Route
  path="/ProfilePage"
  element={
    loggedInUser ? (
      <>
        <NavBar onLogout={handleLogout} loggedInUser={loggedInUser} />
        <ProfilePage loggedInUser={loggedInUser} />
      </>
    ) : (
      <Navigate to="/" />
    )
  }
/>



    </Routes>
  );
}

export default App;