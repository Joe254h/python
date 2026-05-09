(function () {
  const rail = document.querySelector("#sideRail");
  const toggle = document.querySelector("#mobileToggle");
  const scrollTop = document.querySelector("#scrollTop");
  const navLinks = Array.from(document.querySelectorAll(".rail-nav a"));
  const sections = Array.from(document.querySelectorAll("main section[id]"));
  const copyButton = document.querySelector("#copyEmail");
  const copyStatus = document.querySelector("#copyStatus");
  const email = "sangura.j.nyongesa@aims-senegal.org";

  if (window.AOS) {
    AOS.init({
      duration: 650,
      easing: "ease-out-cubic",
      once: true,
      offset: 70
    });
  }

  const year = document.querySelector("#currentYear");
  if (year) {
    year.textContent = new Date().getFullYear();
  }

  if (toggle && rail) {
    toggle.addEventListener("click", () => {
      rail.classList.toggle("open");
      document.body.classList.toggle("nav-open", rail.classList.contains("open"));
    });
  }

  navLinks.forEach((link) => {
    link.addEventListener("click", () => {
      if (rail) {
        rail.classList.remove("open");
      }
      document.body.classList.remove("nav-open");
    });
  });

  if ("IntersectionObserver" in window && sections.length) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) {
          return;
        }

        navLinks.forEach((link) => link.classList.remove("active"));
        const active = document.querySelector(`.rail-nav a[href="#${entry.target.id}"]`);
        if (active) {
          active.classList.add("active");
        }
      });
    }, {
      rootMargin: "-35% 0px -55% 0px",
      threshold: 0
    });

    sections.forEach((section) => observer.observe(section));
  }

  window.addEventListener("scroll", () => {
    if (scrollTop) {
      scrollTop.classList.toggle("visible", window.scrollY > 520);
    }
  });

  document.querySelectorAll(".project-filters button").forEach((button) => {
    button.addEventListener("click", () => {
      const filter = button.dataset.filter;

      document.querySelectorAll(".project-filters button").forEach((item) => {
        item.classList.remove("active");
      });
      button.classList.add("active");

      document.querySelectorAll(".project-card").forEach((card) => {
        const categories = card.dataset.cat || "";
        card.classList.toggle("hidden", filter !== "all" && !categories.includes(filter));
      });
    });
  });

  if (copyButton && copyStatus) {
    copyButton.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(email);
        copyStatus.textContent = "Email copied to clipboard.";
      } catch (error) {
        copyStatus.textContent = email;
      }

      window.setTimeout(() => {
        copyStatus.textContent = "";
      }, 2800);
    });
  }
})();
