import { useState } from "react";

// example: const [chartType, setChartType] = localStorage ("type", "linearGraph", (obj) => obj)
const localStorage = (key, initialValue, fromObject) => {
    const [storedValue, setStoredValue] = useState(() => {
        try {
            const item = window.localStorage.getItem(key)
            return item
                ? (fromObject ? fromObject(JSON.parse(item)) : JSON.parse(item))
                : initialValue
        } catch (error) {
            console.error(error)
            return initialValue
        }
    })

    const setValue = (value) => {
        try {
            setStoredValue((currentValue) => {
                const nextValue = value instanceof Function ? value(currentValue) : value
                window.localStorage.setItem(key, JSON.stringify(nextValue))
                return nextValue
            })
        } catch (error) {
            console.error(error)
        }
    }
    return [storedValue, setValue]
}

export default localStorage

