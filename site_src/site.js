/* Koevalmis site script: language menu, countdown, answerable question cards, sticky button, waiting list. */
(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  // Language menu: close on outside click and on Escape
  const menu = $("details.langs");
  if (menu) {
    document.addEventListener("click", ev => { if (menu.open && !menu.contains(ev.target)) menu.open = false; });
    document.addEventListener("keydown", ev => {
      if (ev.key === "Escape" && menu.open) { menu.open = false; $("summary", menu).focus(); }
    });
  }

  // On phones the page menu scrolls sideways: bring the current page into view
  const nav = $("nav.main"), cur = $("nav.main [aria-current]");
  if (nav && cur && nav.scrollWidth > nav.clientWidth) {
    const r = cur.getBoundingClientRect(), n = nav.getBoundingClientRect();
    nav.scrollLeft += (r.left + r.width / 2) - (n.left + n.width / 2);
  }

  // Days until 1 March 2027 (the build writes a fallback number)
  $$("[data-days]").forEach(el => {
    const now = new Date();
    const d = Math.round((Date.UTC(2027, 2, 1) - Date.UTC(now.getFullYear(), now.getMonth(), now.getDate())) / 864e5);
    if (d > 0) el.textContent = d; else el.closest(".count").hidden = true;
  });

  // Finnish speech, only when the device has a Finnish voice
  let voice = null;
  const pick = () => {
    voice = speechSynthesis.getVoices().find(v => /^fi(-|_|$)/i.test(v.lang)) || null;
    $$("[data-say]").forEach(b => { b.hidden = !voice; });
  };
  if ("speechSynthesis" in window) { pick(); speechSynthesis.addEventListener("voiceschanged", pick); }
  const say = text => {
    if (!voice) return;
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.voice = voice; u.lang = voice.lang; u.rate = 0.9;
    speechSynthesis.speak(u);
  };

  // Answerable question cards (hero demo and practice pages)
  $$("[data-q]").forEach(card => {
    const right = +card.dataset.a;
    const opts = $$(".opt", card);
    const trBtn = $("[data-tr]", card);
    trBtn.addEventListener("click", () => {
      const on = trBtn.getAttribute("aria-pressed") !== "true";
      trBtn.setAttribute("aria-pressed", on);
      $$(".qtr, .otr", card).forEach(x => { x.hidden = !on; });
    });
    $("[data-say]", card).addEventListener("click", () => {
      say([$(".qtext [lang=fi]", card).textContent, ...opts.map(o => $("[lang=fi]", o).textContent)].join(". "));
    });
    opts.forEach(btn => btn.addEventListener("click", () => {
      const ok = +btn.dataset.i === right;
      opts.forEach(o => { o.disabled = true; });
      opts[right].classList.add("ok");
      if (!ok) btn.classList.add("no");
      const stamp = $(".stamp", card);
      stamp.textContent = ok ? "Oikein!" : "Väärin";
      stamp.className = "stamp on" + (ok ? "" : " no");
      card.classList.add("hit", "done");
      const res = $(".res", card);
      if (res) {
        const msg = $(".msg", res);
        msg.textContent = ok ? msg.dataset.ok : msg.dataset.no;
        res.hidden = false;
      }
      const det = $("details.ans-d", card);
      if (det) det.open = true;
      // keep keyboard focus inside the card after the buttons are disabled
      const next = $(".res .btn", card) || $("details.ans-d summary", card);
      if (next) next.focus({ preventScroll: true });
    }));
  });

  // Sticky "free level test" button on phones, shown once the whole hero has scrolled away
  const sticky = $(".sticky"), hero = $(".hero"), price = $("#price");
  if (sticky && hero && "IntersectionObserver" in window) {
    let heroSeen = true, priceSeen = false;
    const update = () => {
      const on = !heroSeen && !priceSeen;
      sticky.classList.toggle("on", on);
      sticky.inert = !on;
    };
    new IntersectionObserver(es => { heroSeen = es[0].isIntersecting; update(); }).observe(hero);
    if (price) new IntersectionObserver(es => { priceSeen = es[0].isIntersecting; update(); }).observe(price);
  }

  // Waiting list (Netlify Forms or Supabase, chosen at build time)
  const form = $("#wl"), cfgEl = $("#wl-config");
  if (form && cfgEl) {
    const C = JSON.parse(cfgEl.textContent);
    const m = $("#wlmsg"), em = $("#email"), cb = $("#consent");
    form.addEventListener("submit", async ev => {
      ev.preventDefault();
      if ($("#hp").value) return;
      const v = em.value.trim();
      const bad = !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(v);
      em.setAttribute("aria-invalid", bad);
      if (bad) { m.textContent = C.msg.wlBad; em.focus(); return; }
      if (!cb.checked) { m.textContent = C.msg.wlConsent; cb.focus(); return; }
      try {
        let r;
        if (C.provider === "netlify") {
          r = await fetch("/", { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: new URLSearchParams(new FormData(form)).toString() });
        } else {
          r = await fetch(C.url + "/rest/v1/waitlist", { method: "POST",
            headers: { apikey: C.key, Authorization: "Bearer " + C.key, "Content-Type": "application/json", Prefer: "return=minimal" },
            body: JSON.stringify({ email: v, lang: C.lang, consent: true }) });
        }
        const done = r.ok || r.status === 409;
        m.textContent = done ? C.msg.wlOk : C.msg.wlErr;
        if (done) form.reset();
      } catch (err) { m.textContent = C.msg.wlErr; }
    });
  }
})();
