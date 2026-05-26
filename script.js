// --- לוגיקת פופ-אפ פתיחה ---
document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById('welcomeModal');
    
    // בדיקה האם המשתמש כבר אישר את החלון בעבר
    const hasSeenWelcome = localStorage.getItem('hasSeenWelcomeCM2');
    
    if (!hasSeenWelcome) {
        modal.classList.add('active');
        
        // כדי למנוע גלילה של הרקע כשהחלון פתוח
        document.body.style.overflow = 'hidden'; 
    }
});

function closeModal() {
    const modal = document.getElementById('welcomeModal');
    modal.classList.remove('active');
    
    // החזרת הגלילה למסך הראשי
    document.body.style.overflow = 'auto';
    
    // שמירת העובדה שהמשתמש קרא וסגר את החלון כדי שלא יקפוץ שוב
    localStorage.setItem('hasSeenWelcomeCM2', 'true');
}

async function searchCocktails() {
    const searchBtn = document.getElementById('searchBtn');
    const resultsArea = document.getElementById('resultsArea');
    const freeText = document.getElementById('ingredientsInput').value.trim();

    // 1. איסוף משקאות בסיס (רק מהקטגוריה הראשונה)
    const baseSpiritsChecked = document.querySelectorAll('.category:nth-of-type(1) .tag-label input[type="checkbox"]:checked');
    const selectedBaseSpirits = Array.from(baseSpiritsChecked).map(cb => cb.value);

    // 2. איסוף שאר המרכיבים (מכל שאר הקטגוריות, למעט הטעם)
    const otherChecked = document.querySelectorAll('.category:not(:nth-of-type(1)):not(:last-of-type) .tag-label input[type="checkbox"]:checked');
    const selectedOther = Array.from(otherChecked).map(cb => cb.value);

    // 3. הוספת טקסט חופשי לשאר המרכיבים אם הוזן
    if (freeText) selectedOther.push(freeText);

    // 4. איסוף הטעם
    const selectedFlavorRadio = document.querySelector('input[name="flavor"]:checked');
    const selectedFlavor = selectedFlavorRadio ? selectedFlavorRadio.value : "All";

    // עצירה אם לא נבחר כלום
    if (selectedBaseSpirits.length === 0 && selectedOther.length === 0 && selectedFlavor === "All") return;

    if (!sessionStorage.getItem('cocktail_session_id')) {
        const randomId = 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        sessionStorage.setItem('cocktail_session_id', randomId);
    }
    const sessionId = sessionStorage.getItem('cocktail_session_id');

    searchBtn.disabled = true;
    searchBtn.innerText = "Mixing... ⏳";
    searchBtn.style.opacity = "0.7";

    resultsArea.style.display = 'block';
    resultsArea.innerHTML = "Gathering components... ⏳";
    resultsArea.scrollIntoView({ behavior: 'smooth', block: 'start' });

    let accumulatedText = "";

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            // שולחים את משקאות הבסיס בנפרד משאר המרכיבים
            body: JSON.stringify({ 
                base_spirits: selectedBaseSpirits,
                other_ingredients: selectedOther,
                flavor: selectedFlavor,
                history: [],
                session_id: sessionId
            })
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
        let sanitizedText = accumulatedText.replace(/\\/g, '/');

        // הוספת ירידת שורה חצי-אוטומטית לפני Flavor Profile
        sanitizedText = sanitizedText.replace("Flavor Profile:", "\n\nFlavor Profile:");

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