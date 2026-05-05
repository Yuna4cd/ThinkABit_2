import { useState, useRef, useEffect, useCallback } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import html2canvas from "html2canvas";
import jsPDF from "jspdf";
import "./VisualizationPage.css";
import Plot from "react-plotly.js";

const steps = [
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
  { name: "Export", content: "Download your finished chart." },
  { name: "Create New Project", content: "" },
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

export default function VisualizationPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const uploadData = location.state?.uploadData;
  const savedSettings = location.state?.settings;

  useEffect(() => {
    if (!uploadData) navigate("/upload");
  }, []);

  if (!uploadData) return null;

  const chartRef = useRef(null);
  const fetchChartTimeout = useRef(null);
  const saveTimeout = useRef(null);

  const initialDataset = uploadData?.preview
    ? uploadData.preview.map((row, index) => ({ id: index + 1, ...row }))
    : sampleData;

  const columns = uploadData?.preview
    ? Object.keys(uploadData.preview[0])
    : ["name", "subject", "score"];

  const [activeStep, setActiveStep] = useState(0);
  const [activeChart, setActiveChart] = useState(
    savedSettings?.activeChart || "Bar",
  );
  const [dataset, setDataset] = useState(initialDataset);
  const [chartTitle, setChartTitle] = useState(
    savedSettings?.chartTitle || "Dataset Chart",
  );
  const [xAxisLabel, setXAxisLabel] = useState(
    savedSettings?.xAxisLabel || columns[0] || "X",
  );
  const [yAxisLabel, setYAxisLabel] = useState(
    savedSettings?.yAxisLabel || columns[1] || "Y",
  );
  const [xColumn, setXColumn] = useState(
    savedSettings?.xColumn || columns[0] || "",
  );
  const [yColumn, setYColumn] = useState(
    savedSettings?.yColumn || columns[1] || "",
  );
  const [summaryStats, setSummaryStats] = useState(null);
  const [correlation, setCorrelation] = useState(null);
  const [exploreLoading, setExploreLoading] = useState(false);
  const [plotlyData, setPlotlyData] = useState(null);
  const [chartLoading, setChartLoading] = useState(false);

  // Debounced localStorage save
  useEffect(() => {
    if (!uploadData) return;
    if (saveTimeout.current) clearTimeout(saveTimeout.current);
    saveTimeout.current = setTimeout(() => {
      const projects = JSON.parse(localStorage.getItem("projects") || "[]");
      const updated = projects.map((p) => {
        if (p.id === uploadData.dataset_id) {
          return {
            ...p,
            uploadData: {
              ...p.uploadData,
              preview: dataset.map(({ id, ...rest }) => rest),
            },
            settings: {
              activeChart,
              xColumn,
              yColumn,
              chartTitle,
              xAxisLabel,
              yAxisLabel,
            },
          };
        }
        return p;
      });
      localStorage.setItem("projects", JSON.stringify(updated));
    }, 1000);
  }, [
    dataset,
    activeChart,
    xColumn,
    yColumn,
    chartTitle,
    xAxisLabel,
    yAxisLabel,
  ]);

  // Fetch explore stats — only once or after cleaning
  useEffect(() => {
    if (activeStep !== 1 || !dataset.length) return;
    if (summaryStats && correlation) return;

    const fetchStats = async () => {
      setExploreLoading(true);
      const data = dataset.map(({ id, ...rest }) => rest);
      try {
        const [summaryRes, corrRes] = await Promise.all([
          fetch("/api/v1/analyze/summary", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ data }),
          }),
          fetch("/api/v1/analyze/correlation", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ data }),
          }),
        ]);
        const summaryData = await summaryRes.json();
        const corrData = await corrRes.json();
        setSummaryStats(summaryData.summary);
        setCorrelation(corrData);
      } catch (err) {
        console.error("Failed to fetch stats", err);
      } finally {
        setExploreLoading(false);
      }
    };

    fetchStats();
  }, [activeStep, summaryStats, correlation]);

  // Fetch chart — debounced
  useEffect(() => {
    if (activeStep !== 2 && activeStep !== 3) return;
    if (!dataset.length || !xColumn || !yColumn) return;
    if (fetchChartTimeout.current) clearTimeout(fetchChartTimeout.current);

    fetchChartTimeout.current = setTimeout(async () => {
      setChartLoading(true);
      try {
        const data = dataset.map(({ id, ...rest }) => rest);
        const res = await fetch("/api/v1/charts/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            data,
            x: xColumn,
            y: yColumn,
            chart_type: activeChart.toLowerCase(),
            title: chartTitle,
            width: 800,
            height: 450,
          }),
        });
        const json = await res.json();
        const parsed = JSON.parse(json);
        setPlotlyData(parsed);
      } catch (err) {
        console.error("Chart generation failed", err);
      } finally {
        setChartLoading(false);
      }
    }, 500);
  }, [activeStep, activeChart, xColumn, yColumn]);

  const hasMissing = dataset.some((row) =>
    columns.some((col) => row[col] === null || row[col] === undefined),
  );

  const handleFillMissing = () => {
    const numericCols = columns.filter((col) =>
      dataset.every(
        (d) =>
          d[col] === null || d[col] === undefined || !isNaN(Number(d[col])),
      ),
    );
    const updated = dataset.map((row) => {
      const newRow = { ...row };
      numericCols.forEach((col) => {
        if (newRow[col] === null || newRow[col] === undefined) {
          const vals = dataset.filter(
            (d) => d[col] !== null && d[col] !== undefined,
          );
          const avg = Math.round(
            vals.reduce((sum, d) => sum + Number(d[col]), 0) / vals.length,
          );
          newRow[col] = avg;
        }
      });
      return newRow;
    });
    setDataset(updated);
    setSummaryStats(null);
    setCorrelation(null);
  };

  const handleRemoveMissing = () => {
    setDataset(
      dataset.filter((row) =>
        columns.every((col) => row[col] !== null && row[col] !== undefined),
      ),
    );
    setSummaryStats(null);
    setCorrelation(null);
  };

  const handleRemoveOutliers = () => {
    const numericCols = columns.filter((col) =>
      dataset.every(
        (d) =>
          d[col] === null || d[col] === undefined || !isNaN(Number(d[col])),
      ),
    );
    setDataset(
      dataset.filter((row) =>
        numericCols.every((col) => {
          const val = Number(row[col]);
          const values = dataset
            .filter((d) => d[col] !== null && d[col] !== undefined)
            .map((d) => Number(d[col]));
          const mean = values.reduce((a, b) => a + b, 0) / values.length;
          const std = Math.sqrt(
            values.reduce((a, b) => a + Math.pow(b - mean, 2), 0) /
              values.length,
          );
          return Math.abs(val - mean) <= 3 * std;
        }),
      ),
    );
    setSummaryStats(null);
    setCorrelation(null);
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

  const handleExportCSV = () => {
    const headers = columns.join(",");
    const rows = dataset
      .map(({ id, ...rest }) => columns.map((col) => rest[col] ?? "").join(","))
      .join("\n");
    const csv = `${headers}\n${rows}`;
    const blob = new Blob([csv], { type: "text/csv" });
    const link = document.createElement("a");
    link.download = `${chartTitle}.csv`;
    link.href = URL.createObjectURL(blob);
    link.click();
  };

  const renderChart = () => {
    if (chartLoading) return <p>Loading chart...</p>;
    if (!plotlyData) return <p>Select columns to generate a chart.</p>;

    const xValues = Array.isArray(plotlyData.data[0]?.x)
      ? plotlyData.data[0].x
      : [];

    return (
      <Plot
        data={plotlyData.data}
        layout={{
          ...plotlyData.layout,
          paper_bgcolor: "transparent",
          plot_bgcolor: "transparent",
          font: { color: "#ffffff" },
          xaxis: {
            ...plotlyData.layout?.xaxis,
            type: "category",
            tickmode: xValues.length > 0 ? "array" : "auto",
            tickvals: xValues,
            ticktext: xValues.map(String),
          },
        }}
        config={{ responsive: true }}
      />
    );
  };

  const renderContent = () => {
    if (activeStep === 0) {
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

    if (activeStep === 1) {
      return (
        <div className="explore-data">
          {exploreLoading && <p>Loading statistics...</p>}
          {!exploreLoading && !summaryStats && (
            <p>No numeric data to analyze.</p>
          )}
          {summaryStats && (
            <>
              <h3>Summary Statistics</h3>
              <table className="dataset-table">
                <thead>
                  <tr>
                    <th>Column</th>
                    <th>Count</th>
                    <th>Missing</th>
                    <th>Mean</th>
                    <th>Median</th>
                    <th>Std</th>
                    <th>Min</th>
                    <th>Max</th>
                    <th>Q1</th>
                    <th>Q3</th>
                    <th>Skewness</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(summaryStats).map(([col, stats]) => (
                    <tr key={col}>
                      <td>{col}</td>
                      <td>{stats.count}</td>
                      <td>{stats.missing}</td>
                      <td>{stats.mean}</td>
                      <td>{stats.median}</td>
                      <td>{stats.std}</td>
                      <td>{stats.min}</td>
                      <td>{stats.max}</td>
                      <td>{stats.q1}</td>
                      <td>{stats.q3}</td>
                      <td>{stats.skewness}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
          {correlation && correlation.columns.length >= 2 && (
            <>
              <h3>Correlation Matrix</h3>
              <table className="dataset-table correlation-table">
                <thead>
                  <tr>
                    <th></th>
                    {correlation.columns.map((col) => (
                      <th key={col}>{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {correlation.columns.map((col) => (
                    <tr key={col}>
                      <td>
                        <strong>{col}</strong>
                      </td>
                      {correlation.columns.map((otherCol) => {
                        const entry = correlation.matrix.find(
                          (e) => e.col1 === col && e.col2 === otherCol,
                        );
                        const val = entry ? entry.correlation : 0;
                        const abs = Math.abs(val);
                        const bg =
                          col === otherCol
                            ? "#4f46e5"
                            : abs > 0.7
                              ? "#22c55e"
                              : abs > 0.4
                                ? "#f97316"
                                : "#374151";
                        return (
                          <td
                            key={otherCol}
                            style={{
                              backgroundColor: bg,
                              color: "white",
                              textAlign: "center",
                            }}
                          >
                            {val}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="correlation-legend">
                <span style={{ color: "#4f46e5" }}>■</span> Self &nbsp;
                <span style={{ color: "#22c55e" }}>■</span> Strong (&gt;0.7)
                &nbsp;
                <span style={{ color: "#f97316" }}>■</span> Moderate (0.4–0.7)
                &nbsp;
                <span style={{ color: "#374151" }}>■</span> Weak (&lt;0.4)
              </div>
            </>
          )}
        </div>
      );
    }

    if (activeStep === 2) {
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
            <div className="control-group">
              <label>Chart Title</label>
              <input
                type="text"
                value={chartTitle}
                onChange={(e) => setChartTitle(e.target.value)}
                placeholder="Enter chart title"
              />
            </div>
          </div>
          <div className="chart-toggle">
            {["Bar", "Line", "Scatter", "Pie", "Histogram", "Box"].map(
              (type) => (
                <button
                  key={type}
                  className={activeChart === type ? "active-chart" : ""}
                  onClick={() => setActiveChart(type)}
                >
                  {type}
                </button>
              ),
            )}
          </div>
          <div className="chart-area">{renderChart()}</div>
        </div>
      );
    }

    if (activeStep === 3) {
      return (
        <div className="export-section">
          <p>
            Download your chart as PNG or PDF, or export your cleaned dataset as
            CSV.
          </p>
          <div ref={chartRef} className="chart-area">
            {renderChart()}
          </div>
          <div className="export-buttons">
            <button onClick={handleExportPNG}>⬇ Export as PNG</button>
            <button onClick={handleExportPDF}>⬇ Export as PDF</button>
            <button onClick={handleExportCSV}>⬇ Export Data as CSV</button>
          </div>
        </div>
      );
    }

    return <p className="step-content">{steps[activeStep].content}</p>;
  };

  return (
    <div className="viz-page-container">
      <div className="sidebar">
        {steps.map((step, index) => (
          <div
            key={index}
            className={`sidebar-item ${activeStep === index ? "active-step" : ""}`}
            onClick={() => {
              if (index === steps.length - 1) {
                navigate("/upload");
              } else {
                setActiveStep(index);
              }
            }}
          >
            {step.name}
          </div>
        ))}
      </div>
      <div className="viz-main-content">
        <h2>{steps[activeStep].name}</h2>
        {renderContent()}
      </div>
      <div className="chatbot-icon">💬</div>
    </div>
  );
}
