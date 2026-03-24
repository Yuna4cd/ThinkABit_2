import "./DocumentsPage.css";

const savedProjects = [
  {
    id: 1,
    title: "Student Scores Overview",
    type: "Bar",
    date: "2026-03-01",
    description: "Average scores by subject for Spring 2026",
  },
  {
    id: 2,
    title: "Monthly Revenue Trend",
    type: "Line",
    date: "2026-03-05",
    description: "Revenue trends from Jan to Jun 2026",
  },
  {
    id: 3,
    title: "Subject Distribution",
    type: "Pie",
    date: "2026-03-10",
    description: "Distribution of students across subjects",
  },
  {
    id: 4,
    title: "Grade Comparison",
    type: "Bar",
    date: "2026-03-15",
    description: "Comparison of grades across different classes",
  },
];

const chartIcon = (type) => {
  if (type === "Bar") return "📊";
  if (type === "Line") return "📈";
  if (type === "Pie") return "🥧";
};

export default function DocumentsPage() {
  return (
    <div className="documents-container">
      <h2>Saved Projects</h2>
      <div className="projects-grid">
        {savedProjects.map((project) => (
          <div key={project.id} className="project-card">
            <div className="project-icon">{chartIcon(project.type)}</div>
            <div className="project-info">
              <h3>{project.title}</h3>
              <p className="project-description">{project.description}</p>
              <div className="project-meta">
                <span className="project-type">{project.type} Chart</span>
                <span className="project-date">{project.date}</span>
              </div>
            </div>
            <button className="download-btn">⬇ Download</button>
          </div>
        ))}
      </div>
    </div>
  );
}
