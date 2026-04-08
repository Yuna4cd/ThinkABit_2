import { useNavigate } from 'react-router-dom'
import { useState } from 'react'
import Popup from '../components/Popup'
import Chatbot from '../components/ChatBot'
import './UploadPage.css'


export default function UploadPage() {
  const navigate = useNavigate();
  const [popup, setPopup] = useState({ message: "", status: "" });
  const [uploading, setUploading] = useState(false);

  // send file to backend and receive error message
  const handelUpload = async (file) => {
    const formData = new FormData();
    formData.append("file", file);
    setUploading(true);

    try {
      const resp = await fetch("/api/v1/upload", {
        method: "POST",
        body: formData,
      });

      const data = await resp.json();

      if (resp.status === 201) {
        navigate("/visualization", { state: { uploadData: data } });
      } else {
        setPopup({
          message: data.error?.message || "Upload failed",
          status: "error",
        });
        setUploading(false);
      }
    } catch (error) {
      setPopup({ message: "handleUpload function error", status: "501" });
      setUploading(false);
    }
  };

    return (
        <div className="upload-container">
            <div className='test-btns'>
                <button onClick={() => setPopup({message: 'upload error', status: 'error'})}>
                    Test Error
                </button>
                <button onClick={() => setPopup({message: 'file warning', status: 'warning'})}>
                    Test Warning
                </button>
                <button onClick={() => setPopup({message: 'upload success', status: 'success'})}>
                    Test Success
                </button>
            </div>
            <Popup message={popup.message} status={popup.status}/>
            <div className="preview-box">
                {!uploading ? (
                    <>
                    <p>Please Upload a File Below</p>
                    <input type='file' onChange={(e) => handelUpload(e.target.files[0])}/>
                    <button onClick={() => setUploading(true)}>
                        Upload
                    </button>
                    </>
                ) : (
                    <>
                        <div>System Is Processing File...</div>
                        <button onClick={() => setUploading(false)}>
                            Un-Upload
                        </button>
                    </>
                )}
            </div>
            <div className="upload-box" onClick={() => navigate('/visualization')}>
                <p>Go Visualization!</p>
            </div>
            <Chatbot />
        </div>
    )
}
