import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import "./Popup.css"

export default function Popup({message, status}) {
    const [visible, setVisible] = useState(false);
    useEffect (() => {
        if (!message) return;
        setVisible(true);
        const timer = setTimeout(() => {
            setVisible(false);
        }, 4000)
        return () => clearTimeout(timer);
    }, [message])

    return (
        <AnimatePresence>
            {visible && (
                <motion.div
                    initial={{opacity:0, y: -20, x:20}}
                    animate={{opacity:1, y: 0, x:0}}
                    exit={{opacity:0, y: -20, x:20}}
                    transition={{duration: 0.25}}
                    className={`Popup-container ${status}`}>
                    <p className="Popup-message">{status}: {message}</p>
                </motion.div>
            )}
        </AnimatePresence>
    )
}