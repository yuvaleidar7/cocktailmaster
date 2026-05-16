async function searchCocktails(userInput) {
    const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            message: userInput,
            history: [] // כאן תוכל לנהל את היסטוריית הצ'אט
        })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        console.log(chunk); // כאן אתה מקבל את המילים בזמן אמת!
        // הזרק את ה-chunk לתוך ה-HTML שלך כאן
    }
}