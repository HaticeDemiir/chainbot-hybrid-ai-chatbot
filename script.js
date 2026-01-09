document.getElementById('send-button').addEventListener('click', function() {
    const userMessage = document.getElementById('user-input').value;

    if (userMessage.trim() === "") return;

    // Mesajı ekle
    appendMessage(userMessage, 'user');

    // Chatbot'a mesaj gönder
    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: userMessage })
    })
    .then(response => response.json())
    .then(data => {
        const botReply = data.response;
        appendMessage(botReply, 'bot');
    })
    .catch(error => {
        console.error('Error:', error);
        appendMessage("Bir hata oluştu, lütfen tekrar deneyin.", 'bot');
    });

    // Input kutusunu temizle
    document.getElementById('user-input').value = "";
});

function appendMessage(message, sender) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('chat-message');
    messageElement.classList.add(sender);
    messageElement.innerHTML = `<span class="${sender}">${sender === 'user' ? '👤' : '🤖'}: ${message}</span>`;
    document.getElementById('chat-box').appendChild(messageElement);
    document.getElementById('chat-box').scrollTop = document.getElementById('chat-box').scrollHeight;
}
