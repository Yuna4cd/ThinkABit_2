import { useEffect, useRef, useState } from "react";
import "./ChatBot.css";
import localStorage from "../context/localStorage.hook";

const defaultMessages = [{
    role: "assistant",
    text: "Hello, What can I help you?"
}]

export default function Chatbot() {
    const [isOpen, setIsOpen] = useState(false)
    const [input, setInput] = useState("")
    const [isLoading, setIsLoading] = useState(false)
    const [isConfirmingClear, setIsConfirmingClear] = useState(false)
    const [resp, setResp] = localStorage("chat_history", defaultMessages)
    const respEndRef = useRef(null)

    const [windowSize, setWindowSize] = useState({
        width: 380,
        height: 560,
    })

    const resizeStateRef = useRef(null)
        

    useEffect(() => {
        respEndRef.current?.scrollIntoView({behavior: "smooth"})
    }, [resp, isOpen])

    useEffect(() => {
        if (!isOpen) {
            setIsConfirmingClear(false)
        }
    }, [isOpen])



    const sendInput = async () => {
        const trim = input.trim()
        if (!trim || isLoading) return;
        setIsConfirmingClear(false)
        const userInput = {
            role: "user",
            text: trim
        }
        const updatedResp = [...resp, userInput]

        setResp(updatedResp)
        setInput("")
        setIsLoading(true)

        try {
            const datasetId = window.localStorage.getItem("dataset_id");
            const sessionId = window.localStorage.getItem("session_id");

            const reply = await fetch (`/api/v1/chat`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    message: trim,
                    history: updatedResp.map((r) => ({
                        role: r.role,
                        text: r.text
                    })),
                    dataset_id: datasetId,
                    session_id: sessionId,
                })
            })

            const data = await reply.json()

            if (!reply.ok) {
                throw new Error(data.detail || "Chat Api Request Failed")
            }

            setResp((prev) => [
                ...prev,
                {
                    role: "assistant",
                    text: data.reply || "No reply returned"            
                }
            ])
        } catch (error) {
            setResp((prev) => [
                ...prev,
                {
                    role: "assistant",
                    text: `Error: ${error.message}`            
                }
            ])
        } finally {
            setIsLoading(false)
        }
    }

    const handelKeyDown = (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            sendInput();
        }
    }

    // clear history message
    const handleClearHistoryClick = () => {
        if (!isConfirmingClear) {
            setIsConfirmingClear(true)
            return
        }

        window.localStorage.removeItem("chat_history")
        window.localStorage.removeItem("dataset_id");
        window.localStorage.removeItem("session_id");
        setResp(defaultMessages)
        setIsConfirmingClear(false)
    }

    // resize chatbot window
    const startResize = (direction) => (event) => {
        event.preventDefault()
        event.stopPropagation()

        resizeStateRef.current = {
            direction,
            startX: event.clientX,
            startY: event.clientY,
            startWidth: windowSize.width,
            startHeight: windowSize.height,
        }

        document.body.style.userSelect = "none"
        document.body.style.cursor = getResizeCursor(direction)

        window.addEventListener("mousemove", handleResizeMove)
        window.addEventListener("mouseup", stopResize)
    }

    const handleResizeMove = (event) => {
        if (!resizeStateRef.current) return

        const {
            direction,
            startX,
            startY,
            startWidth,
            startHeight,
        } = resizeStateRef.current

        let nextWidth = startWidth
        let nextHeight = startHeight

        const deltaX = event.clientX - startX
        const deltaY = event.clientY - startY

        if (direction.includes("right")) {
            nextWidth = startWidth + deltaX
        }

        if (direction.includes("left")) {
            nextWidth = startWidth - deltaX
        }

        if (direction.includes("bottom")) {
            nextHeight = startHeight + deltaY
        }

        if (direction.includes("top")) {
            nextHeight = startHeight - deltaY
        }

        const minWidth = 280
        const minHeight = 360
        const maxWidth = window.innerWidth - 32
        const maxHeight = window.innerHeight - 48

        setWindowSize({
            width: Math.min(Math.max(nextWidth, minWidth), maxWidth),
            height: Math.min(Math.max(nextHeight, minHeight), maxHeight),
        })
    }

    const stopResize = () => {
        resizeStateRef.current = null
        document.body.style.userSelect = ""
        document.body.style.cursor = ""

        window.removeEventListener("mousemove", handleResizeMove)
        window.removeEventListener("mouseup", stopResize)
    }

    const getResizeCursor = (direction) => {
        if (direction === "top" || direction === "bottom") return "ns-resize"
        if (direction === "left" || direction === "right") return "ew-resize"
        if (direction === "top-left" || direction === "bottom-right") return "nwse-resize"
        if (direction === "top-right" || direction === "bottom-left") return "nesw-resize"
        return "default"
    }

    return (
        <div className="chatbot-container">
            { isOpen ? 
            <div className="input-window" style={{width: `${windowSize.width}px`, height: `${windowSize.height}px`}}>
                {/* resize handles */}
                <div className="resize-handle resize-top" onMouseDown={startResize("top")} />
                <div className="resize-handle resize-left" onMouseDown={startResize("left")} />
                <div className="resize-handle resize-top-left" onMouseDown={startResize("top-left")} />
                
                <div className="window-header">
                    <div>
                        <strong>Gemini Chatbot</strong>
                    </div>
                    <div className="window-actions">
                        <button
                            className={`clear-history-btn ${isConfirmingClear ? "is-confirming" : ""}`}
                            onClick={handleClearHistoryClick}
                            disabled={isLoading}
                        >
                            {isConfirmingClear ? "Confirm Clear" : "Clear History"}
                        </button>
                        <button className="window-close" onClick={() => {setIsOpen(false)}}>
                            X
                        </button>
                    </div>
                </div>
                <div className="window-body">
                    {resp.map((msg, index) => (
                        <div className={`msg ${msg.role === "user" ? "msg-user" : "msg-assistant"}`} key={index}>
                            {msg.text}
                        </div>
                    ))}

                    {isLoading && (
                        <div className="loading">
                            Thinking...
                        </div>
                    )}
                    <div ref={respEndRef}/>
                </div>
                <div className="input-area">
                    <textarea
                        rows={2}
                        placeholder="Type you questions"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handelKeyDown}
                    />
                    <button onClick={sendInput} disabled={isLoading}>
                        Send
                    </button>
                </div>
            </div> 
            :
            <div className="chatbot-icon-btn">
                <button onClick={() => setIsOpen((prev) => !prev)} title="Open Chatbot">
                    💬
                </button>
            </div>}
        </div>
    )
}
