import { useState } from "react";
import { Lock, Mail } from "lucide-react";
import { useNavigate } from "react-router-dom";

function LogInPage({ setLoggedInUser }) {
  const navigate = useNavigate();
  const users = [
    { id: 1, email: "vishal@gmail.com", password: "vishal123", role: "LOCAL USER", name: "Vishal" },
    { id: 2, email: "rajesh@gmail.com", password: "rajesh123", role: "LOCAL USER", name: "Rajesh" },
    { id: 3, email: "rati@gmail.com", password: "rati123", role: "REGIONAL USER", name: "Rati" },
    { id: 4, email: "ramya@gmail.com", password: "ramya123", role: "REGIONAL USER", name: "Ramya" },
    { id: 5, email: "micheal@gmail.com", password: "global123", role: "GLOBAL USER", name: "Michael" },
    { id: 6, email: "sarah@gmail.com", password: "sarah123", role: "ADMIN USER", name: "Sarah" },
    { id: 6, email: "admin@gmail.com", password: "admin123", role: "ADMIN USER", name: "Admin" },
  ];

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleLogin = () => {
    const user = users.find(
      (u) => u.email === email && u.password === password
    );

    if (user) {
      setLoggedInUser(user);  
      setError("");
      navigate("/Home");
    } else {
      setError("Invalid email or password");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 via-purple-700 to-indigo-800 flex items-center justify-center p-4 sm:p-6 lg:p-8">
      <div className="bg-white rounded-2xl sm:rounded-3xl shadow-2xl p-6 sm:p-8 lg:p-10 w-full max-w-sm sm:max-w-md">
        <div className="text-center mb-6 sm:mb-8">
          <div className="w-16 h-16 sm:w-20 sm:h-20 bg-gradient-to-br from-purple-600 to-indigo-700 rounded-full mx-auto mb-4 sm:mb-5 flex items-center justify-center">
            <Lock size={32} className="sm:w-10 sm:h-10" color="white" />
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold text-gray-800 mb-2">Welcome Back</h2>
          <p className="text-sm sm:text-base text-gray-600">Please sign in to your account</p>
        </div>

        <div className="mb-4 sm:mb-5 relative">
          <Mail className="absolute left-3 sm:left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
          <input
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full pl-10 sm:pl-12 pr-3 sm:pr-4 py-3 sm:py-4 border-2 border-gray-200 rounded-lg sm:rounded-xl text-sm sm:text-base outline-none focus:border-purple-600 transition-colors"
          />
        </div>

        <div className="mb-4 sm:mb-5 relative">
          <Lock className="absolute left-3 sm:left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
          <input
            placeholder="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full pl-10 sm:pl-12 pr-3 sm:pr-4 py-3 sm:py-4 border-2 border-gray-200 rounded-lg sm:rounded-xl text-sm sm:text-base outline-none focus:border-purple-600 transition-colors"
          />
        </div>

        <button 
          onClick={handleLogin}
          className="w-full py-3 sm:py-4 bg-gradient-to-r from-purple-600 to-indigo-700 text-white rounded-lg sm:rounded-xl text-sm sm:text-base font-bold cursor-pointer transition-transform hover:scale-105 active:scale-95 mb-3 sm:mb-4"
        >
          Login
        </button>

        {error && (
          <p className="bg-red-50 border border-red-200 text-red-600 px-3 sm:px-4 py-2 sm:py-3 rounded-lg text-xs sm:text-sm text-center">
            {error}
          </p>
        )}

        <div className="text-center mt-4 sm:mt-5 text-xs sm:text-sm text-gray-600">
          <p className="mb-1">Demo logins (backend must be running):</p>
          <p className="text-left text-gray-700">Admin (Sarah): <strong>sarah@gmail.com</strong> / <strong>sarah123</strong></p>
          <p className="text-left text-gray-700">Local: vishal@gmail.com / vishal123 — Regional: rati@gmail.com / rati123 — Global: micheal@gmail.com / global123</p>
        </div>
      </div>
    </div>
  );
}

export default LogInPage;