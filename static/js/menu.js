// Menu principal: botão hambúrguer (telemóvel) e submenus (clique/toque e teclado).
document.addEventListener("DOMContentLoaded", () => {
  const menu = document.getElementById("menu-principal");
  const hamburguer = document.querySelector(".menu-botao");
  const botoesSub = menu.querySelectorAll(".tem-sub > button");

  const fecharSubmenus = (exceto) => {
    botoesSub.forEach((b) => {
      if (b !== exceto) b.setAttribute("aria-expanded", "false");
    });
  };

  hamburguer.addEventListener("click", () => {
    const aberto = hamburguer.getAttribute("aria-expanded") === "true";
    hamburguer.setAttribute("aria-expanded", String(!aberto));
    hamburguer.setAttribute("aria-label", aberto ? "Abrir menu" : "Fechar menu");
    menu.classList.toggle("aberto", !aberto);
  });

  botoesSub.forEach((botao) => {
    botao.addEventListener("click", (e) => {
      e.stopPropagation();
      const aberto = botao.getAttribute("aria-expanded") === "true";
      fecharSubmenus(botao);
      botao.setAttribute("aria-expanded", String(!aberto));
    });
  });

  document.addEventListener("click", (e) => {
    if (!menu.contains(e.target)) fecharSubmenus();
  });

  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    const aberto = menu.querySelector('.tem-sub > button[aria-expanded="true"]');
    fecharSubmenus();
    if (aberto) aberto.focus();
  });
});
