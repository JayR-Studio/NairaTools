// NAVBAR
const menuToggle = document.getElementById("menu-toggle");
const navLinks = document.getElementById("nav-links");

if (menuToggle && navLinks) {
    menuToggle.addEventListener("click", function () {
        navLinks.classList.toggle("active");
    });
}

//Animator
const heroImages = document.querySelectorAll(".hero-answer-image");
let currentHeroImage = 0;

setInterval(() => {
    heroImages[currentHeroImage].classList.remove("active");

    currentHeroImage = (currentHeroImage + 1) % heroImages.length;

    heroImages[currentHeroImage].classList.add("active");
}, 2500);