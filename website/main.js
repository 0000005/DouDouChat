const navToggle = document.querySelector(".nav-toggle");
const navDrawer = document.querySelector("[data-drawer]");

if (navToggle && navDrawer) {
  navToggle.addEventListener("click", () => {
    navDrawer.classList.toggle("open");
    navToggle.setAttribute(
      "aria-expanded",
      navDrawer.classList.contains("open").toString()
    );
  });

  navDrawer.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      navDrawer.classList.remove("open");
      navToggle.setAttribute("aria-expanded", "false");
    });
  });
}

const prefersReducedMotion = window.matchMedia(
  "(prefers-reduced-motion: reduce)"
).matches;

const revealElements = document.querySelectorAll(".reveal");
if (!prefersReducedMotion && revealElements.length) {
  const revealObserver = new IntersectionObserver(
    (entries, observer) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("in-view");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.2 }
  );

  revealElements.forEach((el) => revealObserver.observe(el));
} else {
  revealElements.forEach((el) => el.classList.add("in-view"));
}

const carouselTrack = document.querySelector("[data-carousel]");
const dots = document.querySelectorAll("[data-dots] .dot");
const prevBtn = document.querySelector(".carousel-btn.prev");
const nextBtn = document.querySelector(".carousel-btn.next");

if (carouselTrack && dots.length) {
  let index = 0;
  const items = carouselTrack.querySelectorAll(".carousel-item");

  const updateCarousel = (nextIndex) => {
    index = (nextIndex + items.length) % items.length;
    carouselTrack.style.transform = `translateX(-${index * 100}%)`;
    dots.forEach((dot, dotIndex) => {
      dot.classList.toggle("active", dotIndex === index);
    });
  };

  prevBtn?.addEventListener("click", () => updateCarousel(index - 1));
  nextBtn?.addEventListener("click", () => updateCarousel(index + 1));

  dots.forEach((dot, dotIndex) => {
    dot.addEventListener("click", () => updateCarousel(dotIndex));
  });

  updateCarousel(0);
}
