import { useEffect, useRef, useState } from "react";
import "./ChatBot.css";

export default function Chatbot() {
    const [isOpen, setIsOpen] = useState(false)
    const [input, setInput] = useState("")
    const [isLoading, setIsLoading] = useState(false)
    const [resp, setResp] = useState([{
        role: "assistant",
        text: "Hello, What can I help you?"
    }])
    const respEndRef = useRef(null)

    useEffect(() => {
        respEndRef.current?.scrollIntoView({behavior: "smooth"})
    }, [resp, isOpen])



    const sendInput = async () => {
        const trim = input.trim()
        if (!trim || isLoading) return;
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

            const reply = await fetch (`http://localhost:8000/api/v1/chat`, {
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

    return (
        <div className="chatbot-container">
            { isOpen ? 
            <div className="input-window" >
                <div className="window-header">
                    <div>
                        <strong>Gemini Chatbot</strong>
                    </div>
                    <button className="window-close" onClick={() => {setIsOpen(false)}}>
                        X
                    </button>
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
