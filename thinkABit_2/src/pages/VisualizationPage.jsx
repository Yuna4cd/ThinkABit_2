import { useState } from 'react'
import { LineChart, Line, BarChart, Bar, PieChart, Pie, XAxis, YAxis, CartesianGrid, Tooltip, Legend, Cell } from 'recharts'
import './VisualizationPage.css'

const steps = [
    { name: 'Upload Data', content: 'Upload your CSV, Excel, or JSON file to get started.' },
    { name: 'Preview & Clean', content: 'Handle missing values and remove outliers from your dataset.' },
    { name: 'Explore Data', content: 'View summary statistics and distributions of your dataset.' },
    { name: 'Choose Chart', content: 'Select the best chart type for your data.' },
    { name: 'Customize', content: 'Customize your chart with labels, colors, and titles.' },
    { name: 'Export', content: 'Download your finished chart.' },
]

const sampleData = [
    { id: 1, name: 'Alice', subject: 'Math', score: 92 },
    { id: 2, name: 'Bob', subject: 'Math', score: null },
    { id: 3, name: 'Charlie', subject: 'Science', score: 78 },
    { id: 4, name: 'Diana', subject: 'Science', score: 150 },
    { id: 5, name: 'Eve', subject: 'English', score: null },
    { id: 6, name: 'Frank', subject: 'English', score: 85 },
    { id: 7, name: 'Grace', subject: 'Math', score: 4 },
    { id: 8, name: 'Henry', subject: 'Science', score: 88 },
]

const dummyData = [
    { name: 'Jan', value: 400 },
    { name: 'Feb', value: 300 },
    { name: 'Mar', value: 600 },
    { name: 'Apr', value: 200 },
    { name: 'May', value: 500 },
    { name: 'Jun', value: 350 },
]

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d']

export default function VisualizationPage() {
    const [activeStep, setActiveStep] = useState(1)
    const [activeChart, setActiveChart] = useState('Line')
    const [dataset, setDataset] = useState(sampleData)

    const handleFillMissing = () => {
        const avg = Math.round(
            dataset.filter(d => d.score !== null).reduce((sum, d) => sum + d.score, 0) /
            dataset.filter(d => d.score !== null).length
        )
        setDataset(dataset.map(d => d.score === null ? { ...d, score: avg } : d))
    }

    const handleRemoveMissing = () => {
        setDataset(dataset.filter(d => d.score !== null))
    }

    const handleRemoveOutliers = () => {
        setDataset(dataset.filter(d => d.score !== null && d.score >= 0 && d.score <= 100))
    }

    const getSummaryStats = () => {
        const validScores = dataset.filter(d => d.score !== null).map(d => d.score)
        const avg = Math.round(validScores.reduce((sum, s) => sum + s, 0) / validScores.length)
        const min = Math.min(...validScores)
        const max = Math.max(...validScores)
        const count = validScores.length

        const bySubject = ['Math', 'Science', 'English'].map(subject => ({
            name: subject,
            average: Math.round(
                dataset.filter(d => d.subject === subject && d.score !== null)
                    .reduce((sum, d) => sum + d.score, 0) /
                dataset.filter(d => d.subject === subject && d.score !== null).length
            )
        }))

        return { avg, min, max, count, bySubject }
    }

    const renderChart = () => {
        if (activeChart === 'Line') {
            return (
                <LineChart width={600} height={250} data={dummyData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="value" stroke="#8884d8" />
                </LineChart>
            )
        } else if (activeChart === 'Bar') {
            return (
                <BarChart width={600} height={250} data={dummyData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="value" fill="#8884d8" />
                </BarChart>
            )
        } else if (activeChart === 'Pie') {
            return (
                <PieChart width={400} height={250}>
                    <Pie data={dummyData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label>
                        {dummyData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                </PieChart>
            )
        }
    }

    const renderContent = () => {
        if (activeStep === 1) {
            const hasMissing = dataset.some(d => d.score === null)
            const hasOutliers = dataset.some(d => d.score !== null && (d.score > 100 || d.score < 0))

            return (
                <div className="preview-clean">
                    {hasMissing && (
                        <div className="alert-box">
                            ⚠️ Missing values detected in {dataset.filter(d => d.score === null).length} row(s)
                        </div>
                    )}
                    {hasOutliers && (
                        <div className="alert-box">
                            ⚠️ Outliers detected — scores outside 0-100 range
                        </div>
                    )}
                    <div className="clean-actions">
                        <button onClick={handleFillMissing} disabled={!hasMissing}>Fill Missing with Average</button>
                        <button onClick={handleRemoveMissing} disabled={!hasMissing}>Remove Missing Rows</button>
                        <button onClick={handleRemoveOutliers} disabled={!hasOutliers}>Remove Outliers</button>
                    </div>
                    <table className="dataset-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Name</th>
                                <th>Subject</th>
                                <th>Score</th>
                            </tr>
                        </thead>
                        <tbody>
                            {dataset.map(row => (
                                <tr key={row.id} className={row.score === null ? 'missing-row' : (row.score > 100 || row.score < 0) ? 'outlier-row' : ''}>
                                    <td>{row.id}</td>
                                    <td>{row.name}</td>
                                    <td>{row.subject}</td>
                                    <td>{row.score === null ? 'N/A' : row.score}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )
        }
        if (activeStep === 2) {
            const { avg, min, max, count, bySubject } = getSummaryStats()

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
            )
    }   
        if (activeStep === 3) {
            return (
                <div className="chart-workspace">
                    <div className="export-btn-container">
                        <button>Export</button>
                    </div>
                    <div className="chart-area">
                        {renderChart()}
                    </div>
                    <div className="chart-toggle">
                        <button className={activeChart === 'Line' ? 'active-chart' : ''} onClick={() => setActiveChart('Line')}>Line</button>
                        <button className={activeChart === 'Bar' ? 'active-chart' : ''} onClick={() => setActiveChart('Bar')}>Bar</button>
                        <button className={activeChart === 'Pie' ? 'active-chart' : ''} onClick={() => setActiveChart('Pie')}>Pie</button>
                    </div>
                </div>
            )
        }
        return <p className="step-content">{steps[activeStep].content}</p>
    }

    return (
        <div className="viz-page-container">
            <div className="sidebar">
                {steps.map((step, index) => (
                    <div
                        key={index}
                        className={`sidebar-item ${activeStep === index ? 'active-step' : ''}`}
                        onClick={() => setActiveStep(index)}
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
    )
}