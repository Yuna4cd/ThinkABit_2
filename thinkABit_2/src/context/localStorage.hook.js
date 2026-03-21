import { useState } from "react";

// example: const [chartType, setChartType] = localStorage ("type", "linearGraph", (obj) => obj)
const localStorage = (key, initialValue, fromObject) => {
    const [storedValue, setStoredValue] = useState(() => {
        try {
            const item = window.localStorage.getItem(key)
            return item
                ? fromObject(JSON.parse(item))
                : initialValue
        } catch (error) {
            console.error(error)
            return initialValue
        }
    })

    const setValue = (value) => {
        try {
            setStoredValue(value)
            window.localStorage.setItem(key, JSON.stringify(value))
        } catch (error) {
            console.error(error)
        }
    }
    return [storedValue, setValue]
}

export default localStorage

