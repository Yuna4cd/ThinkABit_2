import { useNavigate } from 'react-router-dom'
import { useState } from 'react'
import Popup from '../components/Popup'
import './UploadPage.css'


export default function UploadPage() {
  const navigate = useNavigate();
  const [popup, setPopup] = useState({ message: "", status: "" });
  const [uploading, setUploading] = useState(false);

//   get session_id for chatbot access
  const getSessionId = () => {
    let session_id = window.localStorage.getItem("session_id")

    if (!session_id) {
        session_id = crypto.randomUUID();
        window.localStorage.setItem("session_id", session_id)
    }

    return session_id
  }

  // send file to backend and receive error message
  const handelUpload = async (file) => {
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);
    setUploading(true);

    // follow-up for session id
    const sessionId = getSessionId();
    formData.append("session_id", sessionId)

    try {
      const resp = await fetch("/api/v1/upload", {
        method: "POST",
        body: formData,
      });

      const data = await resp.json();

      if (resp.status === 201) {
        // Save to localStorage
        const existingProjects = JSON.parse(
          localStorage.getItem("projects") || "[]",
        );
        const newProject = {
          id: data.dataset_id,
          filename: file.name,
          uploadDate: new Date().toLocaleDateString(),
          uploadData: data,
        };
        existingProjects.push(newProject);
        localStorage.setItem("projects", JSON.stringify(existingProjects));
        window.localStorage.setItem("dataset_id", data.dataset_id);

        if (data.session_id) {
            window.localStorage.setItem("session_id", data.session_id)
        }

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
            <Popup message={popup.message} status={popup.status}/>
            <div className="preview-box">
                {!uploading ? (
                    <>
                    <p>Please Upload a File Below</p>
                    <input type='file' onChange={(e) => handelUpload(e.target.files[0])}/>
                    </>
                ) : (
                    <>
                        <div>System Is Processing File...</div>
                    </>
                )}
            </div>
        </div>
    )
}
