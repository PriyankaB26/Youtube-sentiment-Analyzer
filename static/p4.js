document.addEventListener("DOMContentLoaded", function() {
    const modeChanger = document.querySelector("#mode-changer");
    const switchElement = document.querySelector(".switch");
    const featuresLink = document.querySelector("#features > a");
    const subMenu = document.querySelector("#features .sub-menu");

    modeChanger.addEventListener("click", function() {
        document.body.classList.toggle("dark-mode");
    });

    featuresLink.addEventListener("click", function(event) {
        event.preventDefault();
        subMenu.classList.toggle("show");
    });
});
