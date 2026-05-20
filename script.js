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

    // Collect all checked chip values
    const checked = document.querySelectorAll('.tag-label input[type="checkbox"]:checked');
    const selected = Array.from(checked).map(cb => cb.value);

    // Combine chips + free-text into one query
    const combined = [...selected];
    if (freeText) combined.push(freeText);

    const userInput = combined.join(', ');
    if (!userInput) return;

    // --- ניהול מזהה סשן (Session ID) לטובת אנליטיקס ---
    if (!sessionStorage.getItem('cocktail_session_id')) {
        // יצירת מזהה רנדומלי ייחודי מבוסס זמן לסשן הנוכחי
        const randomId = 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        sessionStorage.setItem('cocktail_session_id', randomId);
    }
    const sessionId = sessionStorage.getItem('cocktail_session_id');

    // --- איסוף העדפת Dark Mode (אופציונלי - נשלח כחלק מההיסטוריה או מאפייני בקשה מורחבים אם תרצה) ---
    // כרגע בודק אם קיים class של dark-mode על ה-body או ה-html
    const isDarkMode = document.body.classList.contains('dark-mode') || document.documentElement.classList.contains('dark-mode');

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
            // הוספת ה-session_id לפיילוד שנשלח לשרת
            body: JSON.stringify({ 
                message: userInput, 
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