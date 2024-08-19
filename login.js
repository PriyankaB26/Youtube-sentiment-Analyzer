// Select the sign-in and sign-up buttons and the container
const sign_in_btn = document.querySelector("#sign-in-btn");
const sign_up_btn = document.querySelector("#sign-up-btn");
const container = document.querySelector(".container");

// Toggle sign-up mode on clicking the sign-up button
sign_up_btn.addEventListener("click", () => {
  container.classList.add("sign-up-mode");
});

// Toggle sign-in mode on clicking the sign-in button
sign_in_btn.addEventListener("click", () => {
  container.classList.remove("sign-up-mode");
});

// Auto-hide flash messages after 3 seconds
setTimeout(function() {
  const flashMessages = document.querySelector('.flash-messages');
  if (flashMessages) {
    flashMessages.style.transition = 'opacity 0.5s ease-out';
    flashMessages.style.opacity = '0';
    setTimeout(() => flashMessages.remove(), 500); // Remove from DOM after fading out
  }
}, 3000); // 3 seconds
