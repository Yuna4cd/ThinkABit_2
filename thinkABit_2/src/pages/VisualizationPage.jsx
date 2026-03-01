import { useState } from 'react'
import { LineChart, Line, BarChart, Bar, PieChart, Pie, XAxis, YAxis, CartesianGrid, Tooltip, Legend, Cell } from 'recharts'
import './VisualizationPage.css'

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
    const [activeChart, setActiveChart] = useState('Line')

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

    return (
        <div className="viz-container">
            <div className="export-btn-container">
                <button>Export</button>
            </div>
            <div className="chart-area">
                {renderChart()}
            </div>
            <div className="chart-toggle">
                <button
                    className={activeChart === 'Line' ? 'active-chart' : ''}
                    onClick={() => setActiveChart('Line')}>Line</button>
                <button
                    className={activeChart === 'Bar' ? 'active-chart' : ''}
                    onClick={() => setActiveChart('Bar')}>Bar</button>
                <button
                    className={activeChart === 'Pie' ? 'active-chart' : ''}
                    onClick={() => setActiveChart('Pie')}>Pie</button>
            </div>
            <div className="upload-btn-container">
                <button>Upload</button>
            </div>
            <div className="dataset-placeholder">
                <p>dataset placeholder</p>
            </div>
            <div className="chatbot-icon">💬</div>
        </div>
    )
}