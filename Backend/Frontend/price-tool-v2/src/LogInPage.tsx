import { useState, useEffect } from "react";
import { Lock, Mail } from "lucide-react";
import { useNavigate } from "react-router-dom";

// Map backend role to display role (must match Home checks: "LOCAL USER", "REGIONAL USER", etc.)
function toDisplayRole(role: string): string {
  const r = (role || "").toLowerCase();
  if (r === "local") return "LOCAL USER";
  if (r === "regional") return "REGIONAL USER";
  if (r === "global") return "GLOBAL USER";
  if (r === "admin") return "ADMIN USER";
  return role || "User";
}

function LogInPage({ setLoggedInUser }) {
  const navigate = useNavigate();
  const [users, setUsers] = useState<Array<{ id: number; email: string; name?: string; role: string; country?: string; therapeutic_area?: string }>>([]);
  const [usersLoading, setUsersLoading] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("/api/users")
      .then((res) => res.ok ? res.json() : { users: [] })
      .then((data) => {
        setUsers(data.users || []);
      })
      .catch(() => setUsers([]))
      .finally(() => setUsersLoading(false));
  }, []);

  const handleLogin = () => {
    const user = users.find((u) => u.email === email);
    if (user) {
      setLoggedInUser({
        id: user.id,
        email: user.email,
        name: user.name,
        role: toDisplayRole(user.role),
      });
      setError("");
      navigate("/Home");
    } else {
      setError("User not found. Use an email from the list (backend must be running).");
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
          <p className="mb-1">Select user (backend must be running). Password ignored for testing.</p>
          {usersLoading ? (
            <p className="text-left text-gray-700">Loading users...</p>
          ) : users.length > 0 ? (
            <p className="text-left text-gray-700">
              Seed users: {users.map((u) => u.email).join(", ")} — type any email above and click Login.
            </p>
          ) : (
            <p className="text-left text-red-600">Could not load users. Is the backend running on port 5000?</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default LogInPage;