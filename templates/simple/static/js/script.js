document.addEventListener('DOMContentLoaded', function() {
    const socialEmail = document.querySelector('.social-email'); // Replace '.your-class' with the class name you want to target

    socialEmail.addEventListener('click', function() {
        const email = 'FpbC5jb20='; 

        navigator.clipboard.writeText(atob('a2FybG9AbW' + email))
            .catch(function(error) {
                console.error('Failed to copy email to clipboard:', error);
            });

        const copiedEmail = document.getElementById('copied-email');
        copiedEmail.textContent = 'Copied email to clipboard!';

        setTimeout(function() {
            copiedEmail.textContent = '';
        }, 3000);
    });
});