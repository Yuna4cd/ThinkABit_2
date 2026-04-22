import { useState, useRef, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Cell,
} from "recharts";
import html2canvas from "html2canvas";
import jsPDF from "jspdf";
import "./VisualizationPage.css";


const steps = [
  {
    name: "Upload Data",
    content: "Upload your CSV, Excel, or JSON file to get started.",
  },
  {
    name: "Preview & Clean",
    content: "Handle missing values and remove outliers from your dataset.",
  },
  {
    name: "Explore Data",
    content: "View summary statistics and distributions of your dataset.",
  },
  {
    name: "Choose Chart",
    content: "Select the best chart type for your data.",
  },
  {
    name: "Customize",
    content: "Customize your chart with labels, colors, and titles.",
  },
  { name: "Export", content: "Download your finished chart." },
];

const sampleData = [
  { id: 1, name: "Alice", subject: "Math", score: 92 },
  { id: 2, name: "Bob", subject: "Math", score: null },
  { id: 3, name: "Charlie", subject: "Science", score: 78 },
  { id: 4, name: "Diana", subject: "Science", score: 150 },
  { id: 5, name: "Eve", subject: "English", score: null },
  { id: 6, name: "Frank", subject: "English", score: 85 },
  { id: 7, name: "Grace", subject: "Math", score: 4 },
  { id: 8, name: "Henry", subject: "Science", score: 88 },
];

const COLORS = [
  "#0088FE",
  "#FFBB28",
  "#FF8042",
  "#a855f7",
  "#22c55e",
  "#ef4444",
  "#f97316",
  "#06b6d4",
];

export default function VisualizationPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const uploadData = location.state?.uploadData;

  useEffect(() => {
  if (!uploadData) {
    navigate("/upload");
  }
  }, []);

  if (!uploadData) return null; 

  const chartRef = useRef(null);

  const initialDataset = uploadData?.preview
    ? uploadData.preview.map((row, index) => ({ id: index + 1, ...row }))
    : sampleData;

  const columns = uploadData?.preview
    ? Object.keys(uploadData.preview[0])
    : ["name", "subject", "score"];

  const [activeStep, setActiveStep] = useState(1);
  const [activeChart, setActiveChart] = useState("Line");
  const [dataset, setDataset] = useState(initialDataset);
  const [chartTitle, setChartTitle] = useState("Dataset Chart");
  const [xAxisLabel, setXAxisLabel] = useState(columns[0] || "X");
  const [yAxisLabel, setYAxisLabel] = useState(columns[1] || "Y");
  const [chartColor, setChartColor] = useState("#8884d8");
  const [xColumn, setXColumn] = useState(columns[0] || "");
  const [yColumn, setYColumn] = useState(columns[1] || "");

  const hasMissing = uploadData
    ? uploadData.missing_summary?.rows_with_missing > 0
    : dataset.some((d) => d.score === null);

  const handleFillMissing = () => {
    const avg = Math.round(
      dataset
        .filter((d) => d.score !== null)
        .reduce((sum, d) => sum + d.score, 0) /
        dataset.filter((d) => d.score !== null).length,
    );
    setDataset(
      dataset.map((d) => (d.score === null ? { ...d, score: avg } : d)),
    );
  };

  const handleRemoveMissing = () => {
    setDataset(dataset.filter((d) => d.score !== null));
  };

  const handleRemoveOutliers = () => {
    setDataset(
      dataset.filter((d) => d.score !== null && d.score >= 0 && d.score <= 100),
    );
  };

  const getSummaryStats = () => {
    const validScores = dataset
      .filter((d) => d.score !== null)
      .map((d) => d.score);
    const avg = Math.round(
      validScores.reduce((sum, s) => sum + s, 0) / validScores.length,
    );
    const min = Math.min(...validScores);
    const max = Math.max(...validScores);
    const count = validScores.length;

    const bySubject = ["Math", "Science", "English"].map((subject) => ({
      name: subject,
      average: Math.round(
        dataset
          .filter((d) => d.subject === subject && d.score !== null)
          .reduce((sum, d) => sum + d.score, 0) /
          dataset.filter((d) => d.subject === subject && d.score !== null)
            .length,
      ),
    }));

    return { avg, min, max, count, bySubject };
  };

  const handleExportPNG = async () => {
    const canvas = await html2canvas(chartRef.current);
    const link = document.createElement("a");
    link.download = `${chartTitle}.png`;
    link.href = canvas.toDataURL();
    link.click();
  };

  const handleExportPDF = async () => {
    const canvas = await html2canvas(chartRef.current);
    const imgData = canvas.toDataURL("image/png");
    const pdf = new jsPDF("landscape");
    const width = pdf.internal.pageSize.getWidth();
    const height = (canvas.height * width) / canvas.width;
    pdf.addImage(imgData, "PNG", 0, 0, width, height);
    pdf.save(`${chartTitle}.pdf`);
  };

  const renderChart = () => {
    const chartData = dataset
      .filter((d) => d[yColumn] !== null && d[yColumn] !== undefined)
      .map((d) => ({ x: d[xColumn], y: Number(d[yColumn]) }));

    if (activeChart === "Line") {
      return (
        <LineChart width={800} height={350} data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="x"
            label={{ value: xAxisLabel, position: "insideBottom", offset: -5 }}
          />
          <YAxis
            label={{ value: yAxisLabel, angle: -90, position: "insideLeft" }}
          />
          <Tooltip />
          <Legend />
          <Line
            type="monotone"
            dataKey="y"
            stroke={chartColor}
            name={chartTitle}
          />
        </LineChart>
      );
    } else if (activeChart === "Bar") {
      return (
        <BarChart width={800} height={350} data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="x"
            label={{ value: xAxisLabel, position: "insideBottom", offset: -5 }}
          />
          <YAxis
            label={{ value: yAxisLabel, angle: -90, position: "insideLeft" }}
          />
          <Tooltip />
          <Legend />
          <Bar dataKey="y" fill={chartColor} name={chartTitle} />
        </BarChart>
      );
    } else if (activeChart === "Pie") {
      return (
        <PieChart width={600} height={380}>
          <Pie
            data={chartData}
            dataKey="y"
            nameKey="x"
            cx="50%"
            cy="48%"
            outerRadius={120}
            label
          >
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={COLORS[index % COLORS.length]}
              />
            ))}
          </Pie>
          <Tooltip />
          <Legend verticalAlign="bottom" height={36} />
        </PieChart>
      );
    }
  };

  const renderContent = () => {
    if (activeStep === 1) {
      const hasOutliers = dataset.some(
        (d) => d.score !== null && (d.score > 100 || d.score < 0),
      );

      return (
        <div className="preview-clean">
          {hasMissing && (
            <div className="alert-box">
              ⚠️ Missing values detected in{" "}
              {uploadData
                ? uploadData.missing_summary.rows_with_missing
                : dataset.filter((d) => d.score === null).length}{" "}
              row(s)
            </div>
          )}
          {hasOutliers && (
            <div className="alert-box">
              ⚠️ Outliers detected — scores outside 0-100 range
            </div>
          )}
          <div className="clean-actions">
            <button onClick={handleFillMissing} disabled={!hasMissing}>
              Fill Missing with Average
            </button>
            <button onClick={handleRemoveMissing} disabled={!hasMissing}>
              Remove Missing Rows
            </button>
            <button onClick={handleRemoveOutliers} disabled={!hasOutliers}>
              Remove Outliers
            </button>
          </div>
          <table className="dataset-table">
            <thead>
              <tr>
                <th>ID</th>
                {columns.map((col) => (
                  <th key={col}>{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {dataset.map((row) => (
                <tr key={row.id}>
                  <td>{row.id}</td>
                  {columns.map((col) => (
                    <td key={col}>{row[col] === null ? "N/A" : row[col]}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    }

    if (activeStep === 2) {
      if (uploadData) {
        const { shape, schema } = uploadData;

        return (
          <div className="explore-data">
            <div className="stats-grid">
              <div className="stat-card">
                <h3>Total Rows</h3>
                <p>{shape.rows}</p>
              </div>
              <div className="stat-card">
                <h3>Total Columns</h3>
                <p>{shape.columns}</p>
              </div>
              <div className="stat-card">
                <h3>Missing Cells</h3>
                <p>{uploadData.missing_summary.total_missing_cells}</p>
              </div>
              <div className="stat-card">
                <h3>Rows with Missing</h3>
                <p>{uploadData.missing_summary.rows_with_missing}</p>
              </div>
            </div>
            <h3>Column Overview</h3>
            <table className="dataset-table">
              <thead>
                <tr>
                  <th>Column</th>
                  <th>Type</th>
                  <th>Missing Values</th>
                </tr>
              </thead>
              <tbody>
                {schema.map((col) => (
                  <tr
                    key={col.name}
                    className={col.null_count > 0 ? "missing-row" : ""}
                  >
                    <td>{col.name}</td>
                    <td>{col.dtype}</td>
                    <td>{col.null_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      }

      const { avg, min, max, count, bySubject } = getSummaryStats();
      return (
        <div className="explore-data">
          <div className="stats-grid">
            <div className="stat-card">
              <h3>Total Records</h3>
              <p>{count}</p>
            </div>
            <div className="stat-card">
              <h3>Average Score</h3>
              <p>{avg}</p>
            </div>
            <div className="stat-card">
              <h3>Min Score</h3>
              <p>{min}</p>
            </div>
            <div className="stat-card">
              <h3>Max Score</h3>
              <p>{max}</p>
            </div>
          </div>
          <h3>Average Score by Subject</h3>
          <BarChart width={500} height={250} data={bySubject}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis domain={[0, 100]} />
            <Tooltip />
            <Legend />
            <Bar dataKey="average" fill="#8884d8" />
          </BarChart>
        </div>
      );
    }

    if (activeStep === 3) {
      return (
        <div className="chart-workspace">
          <div className="column-selectors">
            <div className="control-group">
              <label>X-Axis Column</label>
              <select
                value={xColumn}
                onChange={(e) => {
                  setXColumn(e.target.value);
                  setXAxisLabel(e.target.value);
                }}
              >
                {columns.map((col) => (
                  <option key={col} value={col}>
                    {col}
                  </option>
                ))}
              </select>
            </div>
            <div className="control-group">
              <label>Y-Axis Column</label>
              <select
                value={yColumn}
                onChange={(e) => {
                  setYColumn(e.target.value);
                  setYAxisLabel(e.target.value);
                }}
              >
                {columns.map((col) => (
                  <option key={col} value={col}>
                    {col}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="chart-toggle">
            <button
              className={activeChart === "Line" ? "active-chart" : ""}
              onClick={() => setActiveChart("Line")}
            >
              Line
            </button>
            <button
              className={activeChart === "Bar" ? "active-chart" : ""}
              onClick={() => setActiveChart("Bar")}
            >
              Bar
            </button>
            <button
              className={activeChart === "Pie" ? "active-chart" : ""}
              onClick={() => setActiveChart("Pie")}
            >
              Pie
            </button>
          </div>
          <div className="chart-area">{renderChart()}</div>
        </div>
      );
    }

    if (activeStep === 4) {
      return (
        <div className="customize-section">
          <div className="customize-controls">
            <div className="control-group">
              <label>Chart Title</label>
              <input
                type="text"
                value={chartTitle}
                onChange={(e) => setChartTitle(e.target.value)}
                placeholder="Enter chart title"
              />
            </div>
            <div className="control-group">
              <label>X-Axis Label</label>
              <input
                type="text"
                value={xAxisLabel}
                onChange={(e) => setXAxisLabel(e.target.value)}
                placeholder="Enter x-axis label"
              />
            </div>
            <div className="control-group">
              <label>Y-Axis Label</label>
              <input
                type="text"
                value={yAxisLabel}
                onChange={(e) => setYAxisLabel(e.target.value)}
                placeholder="Enter y-axis label"
              />
            </div>
            <div className="control-group">
              <label>Chart Color</label>
              <input
                type="color"
                value={chartColor}
                onChange={(e) => setChartColor(e.target.value)}
              />
            </div>
          </div>
          <h3>Preview</h3>
          <div className="chart-area">{renderChart()}</div>
          <div className="chart-toggle">
            <button
              className={activeChart === "Line" ? "active-chart" : ""}
              onClick={() => setActiveChart("Line")}
            >
              Line
            </button>
            <button
              className={activeChart === "Bar" ? "active-chart" : ""}
              onClick={() => setActiveChart("Bar")}
            >
              Bar
            </button>
            <button
              className={activeChart === "Pie" ? "active-chart" : ""}
              onClick={() => setActiveChart("Pie")}
            >
              Pie
            </button>
          </div>
        </div>
      );
    }

    if (activeStep === 5) {
      return (
        <div className="export-section">
          <p>Download your chart as PNG or PDF.</p>
          <div ref={chartRef} className="chart-area">
            {renderChart()}
          </div>
          <div className="export-buttons">
            <button onClick={handleExportPNG}>⬇ Export as PNG</button>
            <button onClick={handleExportPDF}>⬇ Export as PDF</button>
          </div>
        </div>
      );
    }

    return <p className="step-content">{steps[activeStep].content}</p>;
  };

  return (
    <div className="viz-page-container">
      <div className="sidebar">
  {steps.map((step, index) => {
    if (index === 0) {
      return (
        <div
          key={index}
          className="sidebar-item"
          onClick={() => navigate("/upload")}
        >
          Re-upload Data
        </div>
      );
    }
    if (!uploadData) return null;
    return (
      <div
        key={index}
        className={`sidebar-item ${activeStep === index ? "active-step" : ""}`}
        onClick={() => setActiveStep(index)}
      >
        {step.name}
      </div>
    );
  })}
</div>
      <div className="viz-main-content">
        <h2>{steps[activeStep].name}</h2>
        {renderContent()}
      </div>
      <div className="chatbot-icon">💬</div>
    </div>
  );
}