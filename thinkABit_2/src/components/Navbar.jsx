import { NavLink, Link } from 'react-router-dom'
import './Navbar.css'
import logo from '../assets/thinkabit_logo.png'

export default function Navbar() {

    const user = {
        name: 'username',
        avator: '../assets/react.svg', 
    }

    return (
        <nav>
            <Link to="/" className="logo-link"><img src={logo} alt='logo' className='logo-img'/></Link>
            <div className='nav-btn'>
                <NavLink to="/upload">Visualization<i class="fa-solid fa-chart-area"></i></NavLink>
                <NavLink to="/documents">Documents<i class="fa-solid fa-file"></i></NavLink>
            </div>
            <div className='user-section'>
                <span>{user.name}</span>
                <img src={user.avator} alt='avator' className='avator'/>
            </div>
        </nav>
    )
}