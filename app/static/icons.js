/* ValVuln AI — Ikon SVG Inline Seragam ("SEGEL")
 * Stroke seragam 1.6, tanpa emoji/PNG/icon-font, animasi hanya transform/opacity/stroke-dashoffset.
 */

const icons = {
  mark:
    '<circle cx="12" cy="12" r="9.5" fill="none" stroke="currentColor" stroke-width="1.6"/>' +
    '<rect x="8.75" y="6.75" width="6.5" height="10.5" rx="3.25" class="vv-draw" fill="none" stroke="currentColor" stroke-width="1.6"/>' +
    '<circle cx="12" cy="12" r="1.4" fill="currentColor" stroke="none"/>',
  seal:
    '<circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.6"/>' +
    '<rect x="9" y="7" width="6" height="10" rx="3" class="vv-draw" fill="none" stroke="currentColor" stroke-width="1.6"/>',
  gate:
    '<path class="vv-draw" d="M5 19V9a7 7 0 0 1 14 0v10" fill="none" stroke="currentColor" stroke-width="1.6"/>' +
    '<path d="M3 19h18M9 19v-7a3 3 0 0 1 6 0v7" fill="none" stroke="currentColor" stroke-width="1.6"/>',
  shield:
    '<path class="vv-draw" d="M12 3 19.5 6v5.4c0 4.7-3.1 8.6-7.5 10.1-4.4-1.5-7.5-5.4-7.5-10.1V6L12 3Z" fill="none" stroke="currentColor" stroke-width="1.6"/>',
  "shield-check":
    '<path class="vv-draw" d="M12 3 19.5 6v5.4c0 4.7-3.1 8.6-7.5 10.1-4.4-1.5-7.5-5.4-7.5-10.1V6L12 3Z" fill="none" stroke="currentColor" stroke-width="1.6"/>' +
    '<path d="m8.75 12.2 2.2 2.2 4.3-4.6" fill="none" stroke="currentColor" stroke-width="1.6"/>',
  "shield-alert":
    '<path class="vv-draw" d="M12 3 19.5 6v5.4c0 4.7-3.1 8.6-7.5 10.1-4.4-1.5-7.5-5.4-7.5-10.1V6L12 3Z" fill="none" stroke="currentColor" stroke-width="1.6"/>' +
    '<path d="M12 8.2v4.3M12 15.8h.01" fill="none" stroke="currentColor" stroke-width="1.6"/>',
  lock:
    '<rect x="5" y="10.5" width="14" height="10" rx="2" fill="none" stroke="currentColor" stroke-width="1.6"/>' +
    '<path class="vv-draw" d="M8 10.5V7.5a4 4 0 0 1 8 0v3" fill="none" stroke="currentColor" stroke-width="1.6"/>' +
    '<circle cx="12" cy="15.5" r="1.2" fill="currentColor" stroke="none"/>',
  chat:
    '<path class="vv-draw" d="M4.5 6.5A2.5 2.5 0 0 1 7 4h10a2.5 2.5 0 0 1 2.5 2.5v7A2.5 2.5 0 0 1 17 16H10l-4.5 3.5V16A2.5 2.5 0 0 1 4.5 13.5Z" fill="none" stroke="currentColor" stroke-width="1.6"/>',
  plus:
    '<path d="M12 5v14M5 12h14" fill="none" stroke="currentColor" stroke-width="1.6"/>',
  inbox:
    '<path d="M4 13.5 6.3 5h11.4L20 13.5V19a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 19Z" fill="none" stroke="currentColor" stroke-width="1.6"/>' +
    '<path d="M4 13.5h4.5l1.5 2h4l1.5-2H20" fill="none" stroke="currentColor" stroke-width="1.6"/>',
  sliders:
    '<path d="M4 7h16M4 17h16M9 4.5v5M15 14.5v5" fill="none" stroke="currentColor" stroke-width="1.6"/>',
  search:
    '<circle cx="10.8" cy="10.8" r="6" fill="none" stroke="currentColor" stroke-width="1.6"/>' +
    '<path d="m15.3 15.3 4.2 4.2" fill="none" stroke="currentColor" stroke-width="1.6"/>',
  book:
    '<path d="M4.5 5.5A2.5 2.5 0 0 1 7 3h12.5v16.5H7a2.5 2.5 0 0 0-2.5 2.5Z" fill="none" stroke="currentColor" stroke-width="1.6"/>' +
    '<path d="M4.5 17.5A2.5 2.5 0 0 1 7 15h12.5" fill="none" stroke="currentColor" stroke-width="1.6"/>',
  "arrow-up-right":
    '<path d="M7 17 17 7M9.5 7H17v7.5" fill="none" stroke="currentColor" stroke-width="1.6"/>',
  "arrow-right":
    '<path d="M4.5 12h15m-5.5-5.5 5.5 5.5-5.5 5.5" fill="none" stroke="currentColor" stroke-width="1.6"/>',
  "arrow-up":
    '<path d="M12 19.5v-15m-5.5 5.5L12 4.5l5.5 5.5" fill="none" stroke="currentColor" stroke-width="1.6"/>',
  sun:
    '<circle class="yesicon-sun-core" cx="12" cy="12" r="4.2" fill="none" stroke="currentColor" stroke-width="1.8"/>' +
    '<g class="yesicon-sun-rays" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">' +
    '<line x1="12" y1="2" x2="12" y2="4.5"/>' +
    '<line x1="12" y1="19.5" x2="12" y2="22"/>' +
    '<line x1="4.22" y1="4.22" x2="5.99" y2="5.99"/>' +
    '<line x1="18.01" y1="18.01" x2="19.78" y2="19.78"/>' +
    '<line x1="2" y1="12" x2="4.5" y2="12"/>' +
    '<line x1="19.5" y1="12" x2="22" y2="12"/>' +
    '<line x1="4.22" y1="19.78" x2="5.99" y2="18.01"/>' +
    '<line x1="18.01" y1="5.99" x2="19.78" y2="4.22"/>' +
    '</g>',
  moon:
    '<path class="yesicon-moon-crescent" d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79Z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>' +
    '<circle class="yesicon-star-1" cx="19" cy="5" r="1" fill="currentColor"/>' +
    '<circle class="yesicon-star-2" cx="16" cy="2.5" r="0.75" fill="currentColor"/>',
  menu:
    '<path d="M4 7.5h16M4 12h16M4 16.5h16" fill="none" stroke="currentColor" stroke-width="1.6"/>',
  close:
    '<path d="m6 6 12 12M18 6 6 18" fill="none" stroke="currentColor" stroke-width="1.6"/>',
  box:
    '<path class="vv-draw" d="m12 3 8 4.5v9L12 21l-8-4.5v-9L12 3Z" fill="none" stroke="currentColor" stroke-width="1.6"/>' +
    '<path d="m4 7.5 8 4.5 8-4.5M12 12v9" fill="none" stroke="currentColor" stroke-width="1.6"/>',
  chevrons:
    '<path d="m8 9.5 4-4 4 4M8 14.5l4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.6"/>',
  paperclip:
    '<path class="vv-draw" d="m16.5 7.5-7 7a2.5 2.5 0 0 1-3.5-3.5l8-8a4.2 4.2 0 1 1 6 6l-8.5 8.5a5.8 5.8 0 0 1-8.2-8.2l7-7" fill="none" stroke="currentColor" stroke-width="1.6"/>',
  upload:
    '<path d="M12 15.5V4.5m-4.5 4.5L12 4.5l4.5 4.5" fill="none" stroke="currentColor" stroke-width="1.6"/>' +
    '<path d="M4.5 16.5v2a1.5 1.5 0 0 0 1.5 1.5h12a1.5 1.5 0 0 0 1.5-1.5v-2" fill="none" stroke="currentColor" stroke-width="1.6"/>',
  download:
    '<path d="M12 4.5v11m-4.5-4.5L12 15.5l4.5-4.5" fill="none" stroke="currentColor" stroke-width="1.6"/>' +
    '<path d="M4.5 16.5v2a1.5 1.5 0 0 0 1.5 1.5h12a1.5 1.5 0 0 0 1.5-1.5v-2" fill="none" stroke="currentColor" stroke-width="1.6"/>',
  file:
    '<path d="M6.5 3.5h7l4.5 4.5v12.5a1 1 0 0 1-1 1h-10.5a1 1 0 0 1-1-1v-16a1 1 0 0 1 1-1Z" fill="none" stroke="currentColor" stroke-width="1.6"/>' +
    '<path d="M13.5 3.5V8H18" fill="none" stroke="currentColor" stroke-width="1.6"/>',
  "file-code":
    '<path d="M6.5 3.5h7l4.5 4.5v12.5a1 1 0 0 1-1 1h-10.5a1 1 0 0 1-1-1v-16a1 1 0 0 1 1-1Z" fill="none" stroke="currentColor" stroke-width="1.6"/>' +
    '<path d="m10 13-1.8 2 1.8 2M14 13l1.8 2-1.8 2" fill="none" stroke="currentColor" stroke-width="1.6"/>',
  terminal:
    '<rect x="3.5" y="4.5" width="17" height="15" rx="2" fill="none" stroke="currentColor" stroke-width="1.6"/>' +
    '<path d="m7.5 10 3 2.5-3 2.5M12.5 15h4" fill="none" stroke="currentColor" stroke-width="1.6"/>',
  activity:
    '<path class="vv-draw" d="M3 12h3.5l2.5-6 4 12 2.5-6H21" fill="none" stroke="currentColor" stroke-width="1.6"/>',
  layers:
    '<path d="m12 4 8.5 4.5L12 13 3.5 8.5 12 4Z" fill="none" stroke="currentColor" stroke-width="1.6"/>' +
    '<path d="m3.5 12.5 8.5 4.5 8.5-4.5M3.5 16.5 12 21l8.5-4.5" fill="none" stroke="currentColor" stroke-width="1.6"/>',
  "check-circle":
    '<circle cx="12" cy="12" r="8.5" fill="none" stroke="currentColor" stroke-width="1.6"/>' +
    '<path class="vv-draw" d="m8.7 12.2 2.2 2.2 4.4-4.6" fill="none" stroke="currentColor" stroke-width="1.6"/>',
  stop:
    '<circle cx="12" cy="12" r="8.5" fill="none" stroke="currentColor" stroke-width="1.6"/>' +
    '<rect x="9.2" y="9.2" width="5.6" height="5.6" rx="1" fill="none" stroke="currentColor" stroke-width="1.6"/>',
  refresh:
    '<path class="vv-draw" d="M19.5 11.5a7.5 7.5 0 1 0-2 5.3" fill="none" stroke="currentColor" stroke-width="1.6"/>' +
    '<path d="M19.5 6.5v5h-5" fill="none" stroke="currentColor" stroke-width="1.6"/>',
  eye:
    '<path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z" fill="none" stroke="currentColor" stroke-width="1.6"/>' +
    '<circle cx="12" cy="12" r="2.5" fill="none" stroke="currentColor" stroke-width="1.6"/>',
  server:
    '<rect x="4" y="4.5" width="16" height="6" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.6"/>' +
    '<rect x="4" y="13.5" width="16" height="6" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.6"/>' +
    '<circle cx="7.5" cy="7.5" r=".9" fill="currentColor" stroke="none"/>' +
    '<circle cx="7.5" cy="16.5" r=".9" fill="currentColor" stroke="none"/>',
  info:
    '<circle cx="12" cy="12" r="8.5" fill="none" stroke="currentColor" stroke-width="1.6"/>' +
    '<path d="M12 11v5M12 8h.01" fill="none" stroke="currentColor" stroke-width="1.6"/>',
  clock:
    '<circle cx="12" cy="12" r="8.5" fill="none" stroke="currentColor" stroke-width="1.6"/>' +
    '<path d="M12 7.5v4.8l3.2 1.8" fill="none" stroke="currentColor" stroke-width="1.6"/>',
  warning:
    '<path d="M12 4 20.5 19H3.5L12 4Z" fill="none" stroke="currentColor" stroke-width="1.6"/>' +
    '<path d="M12 10v4M12 16.5h.01" fill="none" stroke="currentColor" stroke-width="1.6"/>',
  logout:
    '<path d="M14.5 5H7a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h7.5" fill="none" stroke="currentColor" stroke-width="1.6"/>' +
    '<path d="M10.5 12h9m-3-3.5L20 12l-3.5 3.5" fill="none" stroke="currentColor" stroke-width="1.6"/>',
  sparkles:
    '<path class="vv-draw" d="M6.5 4.5h11a1.5 1.5 0 0 1 1.5 1.5v12a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 5 18V6a1.5 1.5 0 0 1 1.5-1.5Z" fill="none" stroke="currentColor" stroke-width="1.6"/>' +
    '<path d="M8.5 9.5h7M8.5 13h5" fill="none" stroke="currentColor" stroke-width="1.6"/>'
};

function makeSvg(key, extraClass = "") {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("fill", "none");
  svg.setAttribute("stroke", "currentColor");
  svg.setAttribute("stroke-width", "1.6");
  svg.setAttribute("stroke-linecap", "round");
  svg.setAttribute("stroke-linejoin", "round");
  svg.setAttribute("aria-hidden", "true");
  svg.classList.add("vv-svg", "yesicon");
  if (key === "sun") svg.classList.add("yesicon-sun");
  if (key === "moon") svg.classList.add("yesicon-moon");
  if (extraClass) {
    extraClass.split(/\s+/).filter(Boolean).forEach(cls => svg.classList.add(cls));
  }
  svg.innerHTML = icons[key] || icons.info;
  return svg;
}
