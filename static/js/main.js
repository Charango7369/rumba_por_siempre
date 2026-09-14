const header = document.querySelector("[data-header]");
const nav = document.querySelector("[data-nav]");
const menuToggle = document.querySelector("[data-menu-toggle]");
const form = document.querySelector("[data-quote-form]");
const result = document.querySelector("[data-quote-result] strong");

const basePrices = {
  esencial: 1800,
  premium: 3200,
  pro: 5200,
};

const extraPrices = {
  pantallas: 900,
  humo: 350,
  animacion: 600,
  streaming: 800,
};

function updateHeader() {
  header.classList.toggle("is-scrolled", window.scrollY > 24);
}

function getFormData() {
  const data = new FormData(form);
  return {
    nombre: data.get("nombre")?.trim() || "",
    telefono: data.get("telefono")?.trim() || "",
    ciudad: data.get("ciudad")?.trim() || "",
    fecha: data.get("fecha") || "",
    tipo_evento: data.get("tipo_evento") || "Evento",
    invitados: Number(data.get("invitados") || 150),
    paquete: data.get("paquete") || "premium",
    extras: data.getAll("extras"),
  };
}

function calculateEstimate() {
  const data = getFormData();
  const base = basePrices[data.paquete] || basePrices.premium;
  const capacity = Math.max(0, data.invitados - 150);
  const capacityCost = Math.floor(capacity / 50) * 180;
  const extrasCost = data.extras.reduce((total, extra) => total + (extraPrices[extra] || 0), 0);
  return base + capacityCost + extrasCost;
}

function renderEstimate() {
  result.textContent = `Bs ${calculateEstimate().toLocaleString("es-BO")}`;
}

function buildWhatsappUrl(data, estimate) {
  const extras = data.extras.length ? data.extras.join(", ") : "sin extras";
  const message = [
    "Hola RxS, quiero reservar sonido y luces.",
    `Nombre: ${data.nombre}`,
    `Telefono: ${data.telefono}`,
    `Ciudad: ${data.ciudad}`,
    `Fecha: ${data.fecha}`,
    `Evento: ${data.tipo_evento}`,
    `Invitados: ${data.invitados}`,
    `Paquete: ${data.paquete}`,
    `Extras: ${extras}`,
    `Estimado: Bs ${estimate.toLocaleString("es-BO")}`,
  ].join("\n");

  return `https://wa.me/59172836437?text=${encodeURIComponent(message)}`;
}

window.addEventListener("scroll", updateHeader, { passive: true });
updateHeader();

menuToggle.addEventListener("click", () => {
  const isOpen = nav.classList.toggle("is-open");
  document.body.classList.toggle("menu-open", isOpen);
  menuToggle.setAttribute("aria-expanded", String(isOpen));
});

nav.addEventListener("click", (event) => {
  if (event.target.tagName !== "A") return;
  nav.classList.remove("is-open");
  document.body.classList.remove("menu-open");
  menuToggle.setAttribute("aria-expanded", "false");
});

form.addEventListener("input", renderEstimate);

form.addEventListener("submit", (event) => {
  event.preventDefault();
  if (!form.reportValidity()) return;

  const data = getFormData();
  const estimate = calculateEstimate();
  window.open(buildWhatsappUrl(data, estimate), "_blank", "noopener,noreferrer");
});

renderEstimate();