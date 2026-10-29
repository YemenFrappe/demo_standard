(() => {
	const SAR_SYMBOL = "\u00A7";
	const SAR_UNICODE_SYMBOL = "\u20C1";

	const getCurrentLanguage = () => frappe.boot?.user?.language || frappe.boot?.lang || "ar";

	const addLanguageToggle = () => {
		if (!frappe.session?.user || frappe.session.user === "Guest") return;
		if ($(".demo-language-toggle").length) return;

		const $userMenu = $(".dropdown-navbar-user");
		if (!$userMenu.length) return;

		const currentLanguage = getCurrentLanguage();
		const nextLanguage = currentLanguage === "ar" ? "en" : "ar";
		const label = currentLanguage === "ar" ? "English" : "\u0627\u0644\u0639\u0631\u0628\u064a\u0629";

		const $toggle = $(`
			<li class="nav-item demo-language-toggle">
				<a class="nav-link" href="#" title="${label}">${label}</a>
			</li>
		`);

		$toggle.on("click", "a", (event) => {
			event.preventDefault();
			frappe.call({
				method: "demo_standard.api.set_language",
				args: { language: nextLanguage },
				freeze: true,
				freeze_message: currentLanguage === "ar" ? "Switching to English..." : "\u062c\u0627\u0631\u064a \u0627\u0644\u062a\u062d\u0648\u064a\u0644 \u0625\u0644\u0649 \u0627\u0644\u0639\u0631\u0628\u064a\u0629...",
				callback: () => {
					document.cookie = `preferred_language=${nextLanguage};path=/;max-age=31536000`;
					window.location.reload();
				},
			});
		});

		$userMenu.before($toggle);
	};

	const bindLanguageToggle = () => {
		addLanguageToggle();
		$(document).on("page-change", addLanguageToggle);
		frappe.router?.on?.("change", addLanguageToggle);
	};

	const currencySelectors = [
		".currency",
		".money",
		"[data-fieldtype='Currency']",
		".number-widget-box",
		".query-report",
		".report-wrapper",
		".datatable",
		".frappe-list",
		".form-dashboard",
		".layout-main-section",
	].join(",");

	const normalizeCurrencyHtml = (value) => {
		if (typeof value !== "string") return value;
		return value
			.replace(/\$/g, SAR_SYMBOL)
			.replace(/SAR/g, SAR_SYMBOL)
			.replace(new RegExp(SAR_UNICODE_SYMBOL, "g"), SAR_SYMBOL);
	};

	const patchSaudiCurrencyFormatters = () => {
		if (frappe.boot) {
			frappe.boot.sysdefaults = frappe.boot.sysdefaults || {};
			frappe.boot.sysdefaults.currency = "SAR";
			frappe.boot.currency_symbols = frappe.boot.currency_symbols || {};
			frappe.boot.currency_symbols.SAR = SAR_SYMBOL;
			if (frappe.boot.currency_info?.SAR) {
				frappe.boot.currency_info.SAR.symbol = SAR_SYMBOL;
			}
		}

		const patch = (container, key) => {
			if (!container || typeof container[key] !== "function" || container[key].__swiss_corner_sar_patched) return;
			const original = container[key];
			const patched = function (...args) {
				return normalizeCurrencyHtml(original.apply(this, args));
			};
			patched.__swiss_corner_sar_patched = true;
			container[key] = patched;
		};

		patch(frappe.formatters, "Currency");
		patch(frappe.form?.formatters, "Currency");
		patch(frappe.utils, "format_currency");
		if (typeof window.format_currency === "function" && !window.format_currency.__swiss_corner_sar_patched) {
			const original = window.format_currency;
			window.format_currency = function (...args) {
				return normalizeCurrencyHtml(original.apply(this, args));
			};
			window.format_currency.__swiss_corner_sar_patched = true;
		}
	};

	const normalizeSaudiCurrencyText = (root = document.body) => {
		if (!root) return;
		const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
			acceptNode(node) {
				if (!node.nodeValue || (!node.nodeValue.includes("$") && !node.nodeValue.includes(SAR_UNICODE_SYMBOL))) {
					return NodeFilter.FILTER_REJECT;
				}
				const parent = node.parentElement;
				if (!parent || !parent.closest(currencySelectors)) return NodeFilter.FILTER_REJECT;
				if (!/[$\u20C1]\s*[\d,]+|[\d,]+\.\d+\s*[$\u20C1]/.test(node.nodeValue)) return NodeFilter.FILTER_REJECT;
				return NodeFilter.FILTER_ACCEPT;
			},
		});
		const nodes = [];
		while (walker.nextNode()) nodes.push(walker.currentNode);
		nodes.forEach((node) => {
			node.nodeValue = normalizeCurrencyHtml(node.nodeValue);
			node.parentElement?.classList.add("demo-saudi-currency");
		});
	};

	const bindSaudiCurrencyFix = () => {
		patchSaudiCurrencyFormatters();
		normalizeSaudiCurrencyText();
		$(document).on("page-change ajaxComplete shown.bs.tab", () => {
			patchSaudiCurrencyFormatters();
			normalizeSaudiCurrencyText();
		});
		frappe.router?.on?.("change", () => setTimeout(() => {
			patchSaudiCurrencyFormatters();
			normalizeSaudiCurrencyText();
		}, 250));
		const observer = new MutationObserver((mutations) => {
			for (const mutation of mutations) {
				for (const node of mutation.addedNodes) {
					if (node.nodeType === Node.ELEMENT_NODE) {
						patchSaudiCurrencyFormatters();
						normalizeSaudiCurrencyText(node);
					}
				}
			}
		});
		observer.observe(document.body, { childList: true, subtree: true });
	};

	const bindDemoPresentation = () => {
		const root = document.querySelector(".demo-presentation");
		if (!root || root.__demoPresentationBound) return;
		root.__demoPresentationBound = true;

		root.addEventListener("click", (event) => {
			const card = event.target.closest(".demo-pres-card");
			if (!card || !root.contains(card)) return;
			root.querySelectorAll(".demo-pres-card.is-active").forEach((item) => {
				if (item !== card) item.classList.remove("is-active");
			});
			card.classList.toggle("is-active");
		});

		root.addEventListener("keydown", (event) => {
			if (!["Enter", " "].includes(event.key)) return;
			const card = event.target.closest(".demo-pres-card");
			if (!card || !root.contains(card)) return;
			event.preventDefault();
			card.click();
		});
	};

	const bindDemoPresentationWhenReady = () => {
		bindDemoPresentation();
		$(document).on("page-change ajaxComplete shown.bs.tab", () => setTimeout(bindDemoPresentation, 100));
		frappe.router?.on?.("change", () => setTimeout(bindDemoPresentation, 250));
	};

	const isInternalDemoHref = (href) => href && (href === "/pos" || href.startsWith("/app/"));

	const getDeckState = (deck) => {
		const slides = Array.from(deck.querySelectorAll(".sc-slide"));
		const rawIndex = Number(deck.dataset.current || slides.findIndex((slide) => slide.classList.contains("is-active")) || 0);
		const current = Math.max(0, Math.min(slides.length - 1, rawIndex));
		return { slides, current };
	};

	const getCurrentOpenHref = (deck) => {
		const { slides, current } = getDeckState(deck);
		const activeSlide = slides[current];
		const firstAction = activeSlide?.querySelector(".sc-slide-action[data-href], .sc-open-link[data-href]");
		return firstAction?.dataset.href || activeSlide?.dataset.open || "";
	};

	const renderScDeck = (deck, index) => {
		if (!deck) return;
		const slides = Array.from(deck.querySelectorAll(".sc-slide"));
		if (!slides.length) return;
		const current = Math.max(0, Math.min(slides.length - 1, Number(index ?? deck.dataset.current ?? 0)));
		const progress = deck.querySelector(".sc-progress-fill");
		const counter = deck.querySelector(".sc-counter");
		const titlePills = Array.from(deck.querySelectorAll(".sc-slide-titles span"));
		const prevBtn = deck.querySelector('[data-action="prev"], .sc-prev');
		const nextBtn = deck.querySelector('[data-action="next"], .sc-next-footer');
		const openBtn = deck.querySelector('[data-action="open"], .sc-open-current');

		deck.dataset.current = String(current);
		slides.forEach((slide, slideIndex) => slide.classList.toggle("is-active", slideIndex === current));
		titlePills.forEach((pill, pillIndex) => pill.classList.toggle("is-active", pillIndex === current));
		if (counter) counter.textContent = `${current + 1} / ${slides.length}`;
		if (progress) progress.style.width = `${((current + 1) / slides.length) * 100}%`;
		if (prevBtn) prevBtn.disabled = current === 0;
		if (nextBtn) nextBtn.disabled = current === slides.length - 1;

		const href = getCurrentOpenHref(deck);
		if (openBtn) {
			openBtn.disabled = !isInternalDemoHref(href);
			openBtn.dataset.href = href || "";
		}
	};

	const goScDeck = (deck, deltaOrIndex, absolute = false) => {
		const { current } = getDeckState(deck);
		renderScDeck(deck, absolute ? deltaOrIndex : current + deltaOrIndex);
	};

	const openInternalHref = (href) => {
		if (!isInternalDemoHref(href)) return;
		window.location.href = href;
	};

	const toggleScPresentationMode = (button) => {
		document.body.classList.toggle("sc-presentation-mode");
		const active = document.body.classList.contains("sc-presentation-mode");
		document.querySelectorAll(".sc-present-toggle, .sc-present-mode-button").forEach((item) => {
			item.textContent = active ? "إنهاء وضع العرض" : "وضع العرض";
		});
		if (button) button.blur();
	};

	const handleScDeckClick = (event) => {
		const deck = event.target.closest(".sc-presentation-deck");
		if (!deck) return;

		const button = event.target.closest("button, [data-href]");
		if (!button || !deck.contains(button)) return;

		const action = button.dataset.action || "";
		if (action === "next" || button.classList.contains("sc-next") || button.classList.contains("sc-next-footer")) {
			event.preventDefault();
			goScDeck(deck, 1);
			return;
		}
		if (action === "prev" || button.classList.contains("sc-prev")) {
			event.preventDefault();
			goScDeck(deck, -1);
			return;
		}
		if (action === "restart" || button.classList.contains("sc-restart")) {
			event.preventDefault();
			goScDeck(deck, 0, true);
			return;
		}
		if (action === "present" || button.classList.contains("sc-present-mode-button")) {
			event.preventDefault();
			toggleScPresentationMode(button);
			return;
		}
		if (action === "open" || button.classList.contains("sc-open-current")) {
			event.preventDefault();
			openInternalHref(button.dataset.href || getCurrentOpenHref(deck));
			return;
		}
		if (button.dataset.href || button.classList.contains("sc-open-link")) {
			event.preventDefault();
			openInternalHref(button.dataset.href);
		}
	};

	const handleScDeckKeydown = (event) => {
		const deck = document.querySelector(".sc-presentation-deck");
		if (!deck) return;
		const activeElement = document.activeElement;
		if (activeElement && ["INPUT", "TEXTAREA", "SELECT"].includes(activeElement.tagName)) return;
		if (event.key === "ArrowLeft") {
			event.preventDefault();
			goScDeck(deck, 1);
		}
		if (event.key === "ArrowRight") {
			event.preventDefault();
			goScDeck(deck, -1);
		}
		if (event.key === "Enter") {
			event.preventDefault();
			goScDeck(deck, 1);
		}
		if (event.key === "Escape" && document.body.classList.contains("sc-presentation-mode")) {
			event.preventDefault();
			document.body.classList.remove("sc-presentation-mode");
			document.querySelectorAll(".sc-present-toggle, .sc-present-mode-button").forEach((item) => {
				item.textContent = "وضع العرض";
			});
		}
	};

	const bindScPresentationDeck = () => {
		document.querySelectorAll(".sc-presentation-deck").forEach((deck) => renderScDeck(deck));
	};

	const bindScPresentationDeckWhenReady = () => {
		if (!document.__scDeckDelegatedEvents) {
			document.__scDeckDelegatedEvents = true;
			document.addEventListener("click", handleScDeckClick, true);
			document.addEventListener("keydown", handleScDeckKeydown, true);
			const observer = new MutationObserver(() => bindScPresentationDeck());
			observer.observe(document.body, { childList: true, subtree: true });
		}
		bindScPresentationDeck();
		$(document).on("page-change ajaxComplete shown.bs.tab", () => setTimeout(bindScPresentationDeck, 100));
		frappe.router?.on?.("change", () => setTimeout(bindScPresentationDeck, 250));
	};

	const bindScPresentationDeckWhenReadyV2 = () => {
		const isInternalHref = (href) => href && (href === "/pos" || href.startsWith("/app/"));
		const findDecks = () => {
			const decks = Array.from(document.querySelectorAll(".sc-presentation-deck"));
			document.querySelectorAll("*").forEach((node) => {
				if (!node.shadowRoot) return;
				node.shadowRoot.querySelectorAll(".sc-presentation-deck").forEach((deck) => decks.push(deck));
			});
			return Array.from(new Set(decks));
		};
		const getSlides = (deck) => Array.from(deck.querySelectorAll(".sc-slide"));
		const getCurrent = (deck) => {
			const slides = getSlides(deck);
			const active = slides.findIndex((slide) => slide.classList.contains("is-active"));
			const raw = Number(deck.dataset.scCurrent || active || 0);
			return Math.max(0, Math.min(slides.length - 1, Number.isFinite(raw) ? raw : 0));
		};
		const getOpenRoute = (deck) => {
			const slide = getSlides(deck)[getCurrent(deck)];
			return slide?.querySelector("[data-sc-route]")?.dataset.scRoute || slide?.dataset.currentRoute || "";
		};
		const render = (deck, index) => {
			const slides = getSlides(deck);
			if (!slides.length) return;
			const current = Math.max(0, Math.min(slides.length - 1, Number(index ?? deck.dataset.scCurrent ?? 0)));
			deck.dataset.scCurrent = String(current);
			slides.forEach((slide, slideIndex) => slide.classList.toggle("is-active", slideIndex === current));
			deck.querySelectorAll(".sc-slide-tab").forEach((tab, tabIndex) => tab.classList.toggle("is-active", tabIndex === current));
			const counter = deck.querySelector(".sc-counter");
			const progress = deck.querySelector(".sc-progress-bar");
			const prev = deck.querySelector('[data-sc-action="prev"]');
			const next = deck.querySelector('[data-sc-action="next"]');
			const open = deck.querySelector('[data-sc-action="open-current"]');
			if (counter) counter.textContent = `${current + 1} / ${slides.length}`;
			if (progress) progress.style.width = `${((current + 1) / slides.length) * 100}%`;
			if (prev) prev.disabled = current === 0;
			if (next) next.disabled = current === slides.length - 1;
			if (open) {
				const route = getOpenRoute(deck);
				open.disabled = !isInternalHref(route);
				open.dataset.scRoute = route || "";
			}
		};
		const go = (deck, deltaOrIndex, absolute = false) => render(deck, absolute ? deltaOrIndex : getCurrent(deck) + deltaOrIndex);
		const openRoute = (route) => {
			if (isInternalHref(route)) window.location.href = encodeURI(route);
		};
		const setPresentationMode = (deck, active) => {
			document.body.classList.toggle("sc-presentation-mode", active);
			deck.classList.toggle("sc-presentation-mode", active);
			deck.querySelectorAll('[data-sc-action="presentation-mode"]').forEach((button) => {
				button.textContent = active ? "إنهاء وضع العرض" : "وضع العرض";
			});
		};
		const bindDeck = (deck) => {
			if (!deck) return;
			if (deck.dataset.initialized !== "1") {
				deck.dataset.initialized = "1";
				deck.addEventListener("click", (event) => {
					const button = event.target.closest("button");
					if (!button || !deck.contains(button)) return;
					const action = button.dataset.scAction;
					if (!action && button.dataset.scGoto === undefined && !button.dataset.scRoute) return;
					event.preventDefault();
					if (button.dataset.scGoto !== undefined) return go(deck, Number(button.dataset.scGoto), true);
					if (action === "next") return go(deck, 1);
					if (action === "prev") return go(deck, -1);
					if (action === "reset") return go(deck, 0, true);
					if (action === "presentation-mode") return setPresentationMode(deck, !deck.classList.contains("sc-presentation-mode"));
					if (action === "open-current") return openRoute(button.dataset.scRoute || getOpenRoute(deck));
					if (button.dataset.scRoute) return openRoute(button.dataset.scRoute);
				});
			}
			render(deck);
			window.__activeScPresentationDeck = deck;
		};
		const bindAll = () => findDecks().forEach(bindDeck);
		if (!document.__scDeckV2Keyboard) {
			document.__scDeckV2Keyboard = true;
			document.addEventListener("keydown", (event) => {
				const decks = findDecks();
				if (!decks.length) return;
				const tag = document.activeElement?.tagName;
				if (["INPUT", "TEXTAREA", "SELECT"].includes(tag)) return;
				const deck = decks[0];
				if (event.key === "Enter" || event.key === "ArrowLeft") {
					event.preventDefault();
					go(deck, 1);
				} else if (event.key === "ArrowRight") {
					event.preventDefault();
					go(deck, -1);
				} else if (event.key === "Escape") {
					setPresentationMode(deck, false);
				}
			}, true);
			new MutationObserver(bindAll).observe(document.body, { childList: true, subtree: true });
		}
		bindAll();
		setTimeout(bindAll, 250);
		setTimeout(bindAll, 900);
		$(document).on("page-change ajaxComplete shown.bs.tab", () => setTimeout(bindAll, 150));
		frappe.router?.on?.("change", () => setTimeout(bindAll, 300));
	};

	const bindScPresentationDeckFixed = () => {
		const isInternalHref = (href) => Boolean(href && (href === "/pos" || href.startsWith("/app/")));
		const scanDecks = () => {
			const decks = [];
			const scan = (root) => {
				if (!root || typeof root.querySelectorAll !== "function") return;
				root.querySelectorAll(".sc-presentation-deck").forEach((deck) => decks.push(deck));
				root.querySelectorAll("*").forEach((node) => {
					if (node.shadowRoot) scan(node.shadowRoot);
				});
			};
			scan(document);
			return Array.from(new Set(decks));
		};
		const fromPath = (event, selector) => {
			const path = typeof event.composedPath === "function" ? event.composedPath() : [];
			for (const node of path) {
				if (node instanceof Element && node.matches(selector)) return node;
			}
			return event.target instanceof Element ? event.target.closest(selector) : null;
		};
		const slides = (deck) => Array.from(deck.querySelectorAll(".sc-slide"));
		const currentIndex = (deck) => {
			const items = slides(deck);
			if (!items.length) return 0;
			const active = items.findIndex((slide) => slide.classList.contains("is-active"));
			const raw = deck.dataset.scCurrent ?? deck.dataset.current ?? (active >= 0 ? active : 0);
			const index = Number(raw);
			return Math.max(0, Math.min(items.length - 1, Number.isFinite(index) ? index : 0));
		};
		const currentRoute = (deck) => {
			const slide = slides(deck)[currentIndex(deck)];
			const routeButton = slide?.querySelector("[data-sc-route], [data-href]");
			return routeButton?.dataset.scRoute || routeButton?.dataset.href || slide?.dataset.currentRoute || slide?.dataset.open || "";
		};
		const setMode = (deck, active) => {
			document.body.classList.toggle("sc-presentation-mode", Boolean(active));
			deck.classList.toggle("sc-presentation-mode", Boolean(active));
			deck.classList.toggle("is-presenting", Boolean(active));
			deck.querySelectorAll('[data-sc-action="presentation-mode"], .sc-present-mode-button, .sc-present-toggle').forEach((button) => {
				button.textContent = active ? "\u0625\u0646\u0647\u0627\u0621 \u0648\u0636\u0639 \u0627\u0644\u0639\u0631\u0636" : "\u0648\u0636\u0639 \u0627\u0644\u0639\u0631\u0636";
			});
		};
		const render = (deck, nextIndex) => {
			const items = slides(deck);
			if (!items.length) return;
			const raw = Number(nextIndex ?? currentIndex(deck));
			const index = Math.max(0, Math.min(items.length - 1, Number.isFinite(raw) ? raw : 0));
			deck.dataset.scCurrent = String(index);
			deck.dataset.current = String(index);
			items.forEach((slide, slideIndex) => {
				const active = slideIndex === index;
				slide.classList.toggle("is-active", active);
				slide.setAttribute("aria-hidden", active ? "false" : "true");
			});
			deck.querySelectorAll(".sc-slide-tab, .sc-slide-titles span").forEach((tab, tabIndex) => {
				const active = tabIndex === index;
				tab.classList.toggle("is-active", active);
				tab.setAttribute("aria-current", active ? "step" : "false");
			});
			deck.querySelectorAll(".sc-counter").forEach((counter) => {
				counter.textContent = `${index + 1} / ${items.length}`;
			});
			deck.querySelectorAll(".sc-progress-bar, .sc-progress-fill").forEach((bar) => {
				bar.style.width = `${((index + 1) / items.length) * 100}%`;
			});
			deck.querySelectorAll('[data-sc-action="prev"], [data-action="prev"], .sc-prev').forEach((button) => {
				button.disabled = index === 0;
			});
			deck.querySelectorAll('[data-sc-action="next"], [data-action="next"], .sc-next, .sc-next-footer').forEach((button) => {
				button.disabled = index === items.length - 1;
			});
			const route = currentRoute(deck);
			deck.querySelectorAll('[data-sc-action="open-current"], [data-action="open"], .sc-open-current').forEach((button) => {
				button.disabled = !isInternalHref(route);
				button.dataset.scRoute = route || "";
				button.dataset.href = route || "";
			});
			window.__activeScPresentationDeck = deck;
		};
		const go = (deck, value, absolute = false) => render(deck, absolute ? Number(value) : currentIndex(deck) + Number(value || 0));
		const openRoute = (route) => {
			if (!isInternalHref(route)) return;
			if (route.startsWith("/app/query-report/") && window.frappe?.set_route) {
				frappe.set_route("query-report", decodeURIComponent(route.replace("/app/query-report/", "")));
				return;
			}
			window.location.href = encodeURI(route);
		};
		const handleClick = (event) => {
			if (event.__scPresentationFixedHandled) return;
			const button = fromPath(event, "button, [data-sc-route], [data-href]");
			if (!button) return;
			const deck = fromPath(event, ".sc-presentation-deck") || button.closest?.(".sc-presentation-deck");
			if (!deck || !deck.contains(button)) return;
			const action = button.dataset.scAction || button.dataset.action || "";
			const hasGoto = button.dataset.scGoto !== undefined || button.dataset.goto !== undefined;
			const route = button.dataset.scRoute || button.dataset.href || "";
			if (!action && !hasGoto && !route) return;
			event.__scPresentationFixedHandled = true;
			event.preventDefault();
			event.stopPropagation();
			if (hasGoto) return go(deck, button.dataset.scGoto ?? button.dataset.goto, true);
			if (action === "next") return go(deck, 1);
			if (action === "prev") return go(deck, -1);
			if (action === "reset" || action === "restart") return go(deck, 0, true);
			if (action === "presentation-mode" || action === "present") return setMode(deck, !deck.classList.contains("sc-presentation-mode") && !deck.classList.contains("is-presenting"));
			if (action === "open-current" || action === "open") return openRoute(route || currentRoute(deck));
			return openRoute(route);
		};
		const handleKeydown = (event) => {
			const decks = scanDecks();
			if (!decks.length) return;
			const tag = document.activeElement?.tagName;
			if (["INPUT", "TEXTAREA", "SELECT"].includes(tag)) return;
			const deck = window.__activeScPresentationDeck && decks.includes(window.__activeScPresentationDeck) ? window.__activeScPresentationDeck : decks[0];
			if (event.key === "Enter" || event.key === "ArrowLeft") {
				event.preventDefault();
				go(deck, 1);
			} else if (event.key === "ArrowRight") {
				event.preventDefault();
				go(deck, -1);
			} else if (event.key === "Escape") {
				setMode(deck, false);
			}
		};
		const bindAll = () => {
			scanDecks().forEach((deck) => {
				if (deck.dataset.fixedInitialized !== "1") {
					deck.dataset.fixedInitialized = "1";
					deck.addEventListener("click", handleClick, true);
				}
				render(deck);
			});
		};
		if (!document.__scPresentationFixedGlobal) {
			document.__scPresentationFixedGlobal = true;
			document.addEventListener("click", handleClick, true);
			document.addEventListener("keydown", handleKeydown, true);
			new MutationObserver(bindAll).observe(document.body, { childList: true, subtree: true });
		}
		bindAll();
		[100, 300, 750, 1500, 3000, 6000].forEach((delay) => setTimeout(bindAll, delay));
		if (!window.__scPresentationFixedPoller) {
			let attempts = 0;
			window.__scPresentationFixedPoller = setInterval(() => {
				attempts += 1;
				bindAll();
				if (attempts > 40 && scanDecks().length) {
					clearInterval(window.__scPresentationFixedPoller);
					window.__scPresentationFixedPoller = null;
				}
			}, 250);
		}
		$(document)
			.off("page-change.scFixedDeck ajaxComplete.scFixedDeck shown.bs.tab.scFixedDeck")
			.on("page-change.scFixedDeck ajaxComplete.scFixedDeck shown.bs.tab.scFixedDeck", () => setTimeout(bindAll, 150));
		frappe.router?.on?.("change", () => setTimeout(bindAll, 300));
	};

	const runDemoStandardBindings = () => {
		bindLanguageToggle();
		bindSaudiCurrencyFix();
		bindDemoPresentationWhenReady();
		bindScPresentationDeckFixed();
	};

	if (window.frappe && typeof frappe.ready === "function") {
		frappe.ready(runDemoStandardBindings);
	} else if (window.jQuery) {
		jQuery(runDemoStandardBindings);
	}
})();
