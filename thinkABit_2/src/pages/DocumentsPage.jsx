import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import "./DocumentsPage.css";

const chartIcon = (filename) => {
  if (!filename) return "📁";
  const ext = filename.split(".").pop().toLowerCase();
  if (ext === "csv") return "📊";
  if (ext === "xlsx" || ext === "xls") return "📈";
  if (ext === "json") return "📋";
  return "📁";
};

export default function DocumentsPage() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);

  useEffect(() => {
    const saved = JSON.parse(localStorage.getItem("projects") || "[]");
    setProjects(saved);
  }, []);

  const handleOpen = (project) => {
    localStorage.setItem("lastProject", JSON.stringify(project));
    navigate("/visualization", {
      state: {
        uploadData: project.uploadData,
        settings: project.settings,
      },
    });
  };

  const handleDelete = (id) => {
    const updated = projects.filter((p) => p.id !== id);
    setProjects(updated);
    localStorage.setItem("projects", JSON.stringify(updated));
  };

  return (
    <div className="documents-container">
      <div className="documents-header">
        <h2>My Projects</h2>
        <button className="new-project-btn" onClick={() => navigate("/upload")}>
          + New Project
        </button>
      </div>
      {projects.length === 0 ? (
        <div className="empty-state">
          <p>No saved projects yet.</p>
          <button
            className="new-project-btn"
            onClick={() => navigate("/upload")}
          >
            + Create Your First Project
          </button>
        </div>
      ) : (
        <div className="projects-grid">
          {projects.map((project) => (
            <div key={project.id} className="project-card">
              <div className="project-icon">{chartIcon(project.filename)}</div>
              <div className="project-info">
                <h3>{project.filename}</h3>
                <div className="project-meta">
                  <span className="project-date">
                    Uploaded: {project.uploadDate}
                  </span>
                </div>
              </div>
              <div className="project-actions">
                <button
                  className="open-btn"
                  onClick={() => handleOpen(project)}
                >
                  Open
                </button>
                <button
                  className="delete-btn"
                  onClick={() => handleDelete(project.id)}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
