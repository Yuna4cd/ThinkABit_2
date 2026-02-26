import { NavLink, Link } from 'react-router-dom'
import './Navbar.css'

export default function Navbar() {
    return (
        <nav>
            <Link to="/" className="logo-link">ThinkABit</Link>
            <div>
                <NavLink to="/upload">Visualization</NavLink>
                <NavLink to="/documents">Documents</NavLink>
            </div>
            <div>Username</div>
        </nav>
    )
}