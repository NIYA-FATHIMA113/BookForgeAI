import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./OwnerNavigation.css";
function OwnerNavigation() {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/", { replace: true });
  };

  return (
    <nav className="owner-navigation" aria-label="Owner dashboard navigation">
      <div className="owner-navigation-links">
        <NavLink to="/dashboard" end>Dashboard</NavLink>
        <NavLink to="/dashboard/services">Services</NavLink>
        <NavLink to="/dashboard/resources">Resources</NavLink>
        <NavLink to="/dashboard/hours">Business Hours</NavLink>
        <NavLink to="/dashboard/bookings">Bookings</NavLink>
      </div>
      <button type="button" onClick={handleLogout}>Log out</button>
    </nav>
  );
}

export default OwnerNavigation;
