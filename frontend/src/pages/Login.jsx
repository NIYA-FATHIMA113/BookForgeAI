import { useState } from "react";
import { Link } from "react-router-dom";
import { apiRequest } from "../services/api";
import { useAuth } from "../context/AuthContext";
import "./Auth.css";
function Login() {
    
  const [username, setUsername] = useState("");
  const { login } = useAuth();
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (event) => {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      const data = await apiRequest("/api/auth/login/", {
        method: "POST",
        body: JSON.stringify({
          username,
          password,
        }),
      });

      login(data.access, data.refresh);

        window.location.href = "/dashboard";
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="auth-page">
      <section className="auth-card" aria-labelledby="login-title">
        <Link className="auth-brand" to="/" aria-label="BookForge AI home">
          <span className="auth-brand-mark">B</span>
          <span>BookForge <span>AI</span></span>
        </Link>

        <div className="auth-heading">
          <p className="auth-eyebrow">OWNER WORKSPACE</p>
          <h1 id="login-title">Welcome back</h1>
          <p>Sign in to manage your bookings and business.</p>
        </div>

        {error && <p className="auth-error" role="alert">{error}</p>}

        <form className="auth-form" onSubmit={handleLogin}>
          <div className="auth-field">
            <label htmlFor="login-username">Username</label>
            <input
              id="login-username"
              name="username"
              type="text"
              autoComplete="username"
              required
            value={username}
            onChange={(event) =>
              setUsername(event.target.value)
            }
              placeholder="Your username"
            />
          </div>

          <div className="auth-field">
            <label htmlFor="login-password">Password</label>
            <div className="auth-password-wrap">
              <input
                id="login-password"
                name="password"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                required
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Your password"
              />
              <button
                className="auth-password-toggle"
                type="button"
                onClick={() => setShowPassword((visible) => !visible)}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            </div>
          </div>

        <button
          className="auth-submit"
          type="submit"
          disabled={loading}
        >
          {loading ? "Signing in…" : "Sign in"}
        </button>
      </form>

        <p className="auth-footer">
          New to BookForge? <Link to="/register">Create an account</Link>
        </p>
      </section>
      <p className="auth-note">A simpler way to run your bookings.</p>
    </main>
  );
}

export default Login;
