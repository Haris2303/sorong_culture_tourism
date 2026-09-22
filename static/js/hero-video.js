(function () {
  "use strict";

  var video = document.querySelector(".hero-video");
  if (!video) return;

  var prefersReducedMotion =
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var connection =
    navigator.connection || navigator.mozConnection || navigator.webkitConnection;
  var isSaveData = !!(connection && connection.saveData);
  var isSlowConnection = !!(
    connection && /^(slow-2g|2g)$/.test(connection.effectiveType || "")
  );

  if (prefersReducedMotion || isSaveData || isSlowConnection) {
    return;
  }

  function loadHeroVideo() {
    var src = video.getAttribute("data-src");
    if (!src) return;

    video.addEventListener(
      "canplay",
      function () {
        video.classList.add("is-loaded");
      },
      { once: true }
    );

    video.src = src;
    video.load();

    var playPromise = video.play();
    if (playPromise && typeof playPromise.catch === "function") {
      playPromise.catch(function () {
        // Autoplay diblokir browser — gambar latar statis tetap tampil.
      });
    }
  }

  // Baru mulai unduh video setelah seluruh halaman (gambar, CSS, dll)
  // selesai dimuat, supaya file video besar tidak menunda tampilan awal.
  if (document.readyState === "complete") {
    loadHeroVideo();
  } else {
    window.addEventListener("load", loadHeroVideo, { once: true });
  }
})();
