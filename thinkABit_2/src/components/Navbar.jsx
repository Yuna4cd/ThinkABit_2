import { Link } from 'react-router-dom'
import { NavLink } from 'react-router-dom'

export default function Navbar() {
    return (
        <nav>
            <div>ThinkABit</div>
            <div>
                <NavLink to="/">Visualization</NavLink>
                <NavLink to="/documents">Documents</NavLink>
            </div>
            <div>Username</div>
        </nav>
    )
}