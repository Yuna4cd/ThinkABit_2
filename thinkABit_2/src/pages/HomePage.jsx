import { useNavigate } from 'react-router-dom'
import { useState } from 'react'
import './HomePage.css'

const steps = [
    { name: 'Upload Data', content: 'Upload your CSV, Excel, or JSON file to get started.' },
    { name: 'Preview & Clean', content: 'Handle missing values and remove outliers from your dataset.' },
    { name: 'Explore Data', content: 'View summary statistics and distributions of your dataset.' },
    { name: 'Choose Chart', content: 'Select the best chart type for your data.' },
    { name: 'Customize', content: 'Customize your chart with labels, colors, and titles.' },
    { name: 'Export', content: 'Download your finished chart.' },
]

export default function HomePage() {
    const [activeStep, setActiveStep] = useState(0)
    const navigate = useNavigate()

    const handleStepClick = (index) => {
        if (index === 0) {
            navigate('/upload')
        } else {
            setActiveStep(index)
        }
    }

    return (
        <div className="home-container">
            <div className="sidebar">
                {steps.map((step, index) => (
                    <div
                        key={index}
                        className={`sidebar-item ${activeStep === index ? 'active-step' : ''}`}
                        onClick={() => handleStepClick(index)}
                    >
                        {step.name}
                    </div>
                ))}
            </div>
            <div className="main-content">
                <p>{steps[activeStep].content}</p>
            </div>
        </div>
    )
}