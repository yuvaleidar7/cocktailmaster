async function searchCocktails() {
    const resultsArea = document.getElementById('resultsArea');
    const freeText = document.getElementById('ingredientsInput').value.trim();

    // Collect all checked chip values
    const checked = document.querySelectorAll('.tag-label input[type="checkbox"]:checked');
    const selected = Array.from(checked).map(cb => cb.value);

    // Combine chips + free-text into one query
    const combined = [...selected];
    if (freeText) combined.push(freeText);

    const userInput = combined.join(', ');
    if (!userInput) return;

    resultsArea.style.display = 'block';
    resultsArea.innerHTML = "Mixing your drinks... ⏳";
    let accumulatedText = "";

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: userInput, history: [] })
        });
        if (!response.ok) {
            resultsArea.innerHTML = "No matching recipes found or server error.";
            return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            accumulatedText += chunk;

            // הוסף את השורה הזו לפני ה-marked.parse:
            const sanitizedText = accumulatedText.replace(/\\/g, '/');

            // הצג את הטקסט הנקי
            resultsArea.innerHTML = marked.parse(sanitizedText);
        }

    } catch (error) {
        resultsArea.innerHTML = "⚠️ Error connecting to server: " + error.message;
    }
}