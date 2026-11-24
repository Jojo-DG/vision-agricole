/* Vision Agricole – petits comportements du site (sans dépendance).
   Le site reste utilisable sans JavaScript : menu déplié, FAQ en <details>, captures en liens. */
(function () {
  "use strict";

  /* Menu mobile */
  var bouton = document.querySelector(".menu-bouton");
  var menu = document.getElementById("menu-principal");
  if (bouton && menu) {
    var fermer = function () {
      menu.classList.remove("ouvert");
      bouton.setAttribute("aria-expanded", "false");
      bouton.setAttribute("aria-label", "Ouvrir le menu");
    };
    bouton.addEventListener("click", function () {
      var ouvert = menu.classList.toggle("ouvert");
      bouton.setAttribute("aria-expanded", ouvert ? "true" : "false");
      bouton.setAttribute("aria-label", ouvert ? "Fermer le menu" : "Ouvrir le menu");
    });
    menu.addEventListener("click", function (e) {
      if (e.target.closest("a")) { fermer(); }
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && menu.classList.contains("ouvert")) { fermer(); bouton.focus(); }
    });
  }

  /* FAQ : une seule réponse ouverte à la fois */
  var questions = document.querySelectorAll(".faq details");
  questions.forEach(function (d) {
    d.addEventListener("toggle", function () {
      if (d.open) {
        questions.forEach(function (autre) { if (autre !== d) { autre.open = false; } });
      }
    });
  });

  /* Copie de l'empreinte SHA-256 */
  var copier = document.querySelector("[data-copier]");
  if (copier) {
    var cible = document.getElementById(copier.getAttribute("data-copier"));
    var etat = document.getElementById("etat-copie");
    copier.hidden = false;
    copier.addEventListener("click", function () {
      var texte = cible.textContent.trim();
      var ok = function () { if (etat) { etat.textContent = "Empreinte copiée."; } };
      var echec = function () {
        var sel = window.getSelection(), r = document.createRange();
        r.selectNodeContents(cible); sel.removeAllRanges(); sel.addRange(r);
        if (etat) { etat.textContent = "Empreinte sélectionnée : copiez-la avec Ctrl+C."; }
      };
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(texte).then(ok, echec);
      } else { echec(); }
    });
  }

  /* Visionneuse de captures (élément <dialog> natif) */
  var liens = document.querySelectorAll("a[data-visionneuse]");
  if (liens.length && typeof HTMLDialogElement === "function") {
    var dlg = document.createElement("dialog");
    dlg.className = "visionneuse";
    dlg.setAttribute("aria-label", "Capture agrandie");
    dlg.innerHTML =
      '<div class="visionneuse-corps">' +
      '<button type="button" class="fermer" aria-label="Fermer l\'image">' +
      '<svg class="icone" viewBox="0 0 24 24" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>' +
      '</button><img alt=""><p></p></div>';
    document.body.appendChild(dlg);
    var img = dlg.querySelector("img"), legende = dlg.querySelector("p");
    dlg.querySelector(".fermer").addEventListener("click", function () { dlg.close(); });
    dlg.addEventListener("click", function (e) { if (e.target === dlg) { dlg.close(); } });
    liens.forEach(function (a) {
      a.addEventListener("click", function (e) {
        e.preventDefault();
        var mini = a.querySelector("img");
        img.src = a.getAttribute("href");
        img.alt = mini ? mini.alt : "";
        legende.textContent = a.getAttribute("data-legende") || "";
        dlg.showModal();
      });
    });
  }
})();
