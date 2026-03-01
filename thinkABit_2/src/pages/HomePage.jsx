import './HomePage.css'

export default function HomePage() {
    return (
        <div className="home-container">
            <div className="sidebar">
                <div className="sidebar-item">Upload Data</div>
                <div className="sidebar-item">Explore Data</div>
                <div className="sidebar-item">Choose Chart</div>
                <div className="sidebar-item">Customize</div>
                <div className="sidebar-item">Export</div>
            </div>
            <div className="main-content">
                <p>dummy text</p>
            </div>
        </div>
    )
}