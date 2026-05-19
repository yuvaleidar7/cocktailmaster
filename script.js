async function searchCocktails() {
    const searchBtn = document.getElementById('searchBtn');
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

    // --- שינויי UX ומובייל: השבתת הכפתור ועדכון הטקסט שלו בזמן עבודה ---
    searchBtn.disabled = true;
    searchBtn.innerText = "Mixing... ⏳";
    searchBtn.style.opacity = "0.7";

    resultsArea.style.display = 'block';
    resultsArea.innerHTML = "Gathering components... ⏳";
    
    // גלילה חלקה אוטומטית לעבר אזור התוצאות במובייל כדי לחסוך גלילה ידנית
    resultsArea.scrollIntoView({ behavior: 'smooth', block: 'start' });

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

            // החלפת לוכסנים הפוכים במידת הצורך עבור תמונות
            const sanitizedText = accumulatedText.replace(/\\/g, '/');

            // הצגת הטקסט והזרמתו בזמן אמת לעמוד
            resultsArea.innerHTML = marked.parse(sanitizedText);
        }

    } catch (error) {
        resultsArea.innerHTML = "⚠️ Error connecting to server: " + error.message;
    } finally {
        // --- שחרור הכפתור והחזרתו למצב המקור שלו בסיום הזרמת המידע או בשגיאה ---
        searchBtn.disabled = false;
        searchBtn.innerText = "🔍 Search Cocktails";
        searchBtn.style.opacity = "1";
    }
}