import { NavLink, Link, useNavigate, useLocation } from "react-router-dom";
import "./Navbar.css";
import logo from "../assets/thinkabit_logo.png";

export default function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();
  const user = { name: "username", avator: "../assets/react.svg" };

  const handleVisualizationClick = (e) => {
    e.preventDefault();
    const lastProject = JSON.parse(
      localStorage.getItem("lastProject") || "null",
    );
    if (lastProject) {
      navigate("/visualization", {
        state: {
          uploadData: lastProject.uploadData,
          settings: lastProject.settings,
        },
      });
    } else {
      navigate("/documents");
    }
  };

  const isVisualizationActive =
    location.pathname === "/visualization" || location.pathname === "/upload";

  return (
    <nav>
      <Link to="/" className="logo-link">
        <img src={logo} alt="logo" className="logo-img" />
      </Link>
      <div className="nav-btn">
        <a
          href="#"
          className={isVisualizationActive ? "active" : ""}
          onClick={handleVisualizationClick}
        >
          Visualization
          <i className="fa-solid fa-chart-area"></i>
        </a>
        <NavLink to="/documents">
          Documents
          <i className="fa-solid fa-file"></i>
        </NavLink>
      </div>
      <div className="user-section">
        <span>{user.name}</span>
        <img src={user.avator} alt="avator" className="avator" />
      </div>
    </nav>
  );
}
