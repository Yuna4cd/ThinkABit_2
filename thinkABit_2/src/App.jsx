import { Routes, Route, useLocation } from 'react-router-dom'
import HomePage from './pages/HomePage'
import './App.css'
import UploadPage from './pages/UploadPage'
import VisualizationPage from './pages/VisualizationPage'
import DocumentsPage from './pages/DocumentsPage'
import Navbar from './components/Navbar'

function App() {

  return (
    <div className='App'>
      <Navbar />
      <Routes>
        <Route path='/' element={<HomePage />} />
        <Route path='/upload' element={<UploadPage />} />
        <Route path='/documents' element={<DocumentsPage />} />
        <Route path='/visualization' element={<VisualizationPage />} />
      </Routes>
    </div>
  )
}

export default App
