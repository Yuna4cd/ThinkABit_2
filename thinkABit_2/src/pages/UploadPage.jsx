import { useNavigate } from 'react-router-dom'
import './UploadPage.css'

export default function UploadPage() {
    const navigate = useNavigate()

    return (
        <div className="upload-container">
            <div className="alert-box">
                Missing Value Alert: x row
            </div>
            <div className="preview-box">
                <p>Please Upload a File Below</p>
            </div>
            <div className="upload-box" onClick={() => navigate('/visualization')}>
                <p>Drag or Upload a file here</p>
            </div>
            <div className="chatbot-icon">💬</div>
        </div>
    )
}