import './UploadPage.css'

export default function UploadPage() {
    return (
        <div className="upload-container">
            <div className="alert-box">
                Missing Value Alert: x row
            </div>
            <div className="preview-box">
                <p>Please Upload a File Below</p>
            </div>
            <div className="upload-box">
                <p>Drag or Upload a file here</p>
            </div>
            <div className="chatbot-icon">💬</div>
        </div>
    )
}