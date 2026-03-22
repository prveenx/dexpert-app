/**
 * PCAGENT PROCESSOR
 * DO NOT CHANGE ANYTHING IN THIS FILE (specificaly adding shadow dom elements which make efficiency drop and other, but can be added new features or dom awareness)
 * Core Logic: Efficient Viewport Scanning, Ghost Element Detection, and Semantic Grouping.
 * Optimization: Limits scanning to the current viewport (+ buffer) to reduce token usage and hallucinations.
 * Features: Hover Awareness, Tooltip detection, and Smart Pruning.
 */

(function () {
    // Prevent multiple injections
    if (window.PCAgentProcessor) return;

    const CONFIG = {
        INTERACTIVE: [
            'a[href]', 'button', 'input', 'textarea', 'select', 'details', 'summary',
            '[tabindex]:not([tabindex="-1"])',
            '[onclick]', '[role="button"]', '[role="link"]',
            '[role="checkbox"]', '[role="switch"]', '[role="menuitem"]', '[role="menuitemcheckbox"]',
            '[role="tab"]', '[contenteditable="true"]', 'video', 'iframe'
        ].join(','),

        CONTAINERS: [
            'article', 'form', 'nav', 'ul', 'ol', 'li', 'tr', 'table', 'section', 'main', 'aside', 'header', 'footer',
            '[role="list"]', '[role="grid"]', '[role="dialog"]', '[role="alertdialog"]', '[role="group"]',
            '[role="region"]', '[role="main"]', '[role="feed"]', '[role="complementary"]', '[role="navigation"]',
            '[data-component-type="s-search-result"]',
            '.card', '.product-card', '.list-item', '.row', '.container'
        ].join(','),

        IGNORE_TAGS: new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'SVG', 'PATH', 'CIRCLE', 'RECT', 'POLYGON', 'LINK', 'META', 'HEAD', 'TITLE']),
        SPACING_REGEX: /[\s\u00A0\u200B\u200C\u200D\u2060\uFEFF]+/g,
        COLORS: ['#FF0000', '#00FF00', '#0000FF', '#FF00FF', '#00FFFF', '#FFA500', '#800080', '#FFFF00'],
        MIN_SIZE: 5
    };

    let axIdCounter = 0;
    const registry = {};

    // --- UTILITIES ---

    function cleanText(text) {
        if (!text) return '';
        return text.replace(CONFIG.SPACING_REGEX, ' ').trim().substring(0, 300);
    }

    // Viewport-Centric Visibility Check
    // This reduces node count by ignoring elements far off-screen
    function isVisible(el, style) {
        // ALWAYS include file inputs, even if they are hidden via CSS (WhatsApp/Instagram do this)
        if (el.tagName === 'INPUT' && el.type === 'file') return true;

        const rect = el.getBoundingClientRect();
        if (rect.width < CONFIG.MIN_SIZE || rect.height < CONFIG.MIN_SIZE) return false;
        if (style.display === 'none' || style.visibility === 'hidden' || parseFloat(style.opacity) === 0) return false;

        // Viewport Buffer: Only scan what is effectively "on screen" or close to it
        if (rect.bottom < -500 || rect.top > window.innerHeight + 500) return false;
        return true;
    }

    // --- GHOST DETECTOR ---
    // Checks if a container holds interactive elements that are currently hidden via CSS
    // Essential for "Hover to Reveal" menus (e.g., Gmail actions on rows)
    function hasHiddenInteractiveChild(el) {
        const walker = document.createTreeWalker(el, NodeFilter.SHOW_ELEMENT, {
            acceptNode: (node) => {
                if (CONFIG.IGNORE_TAGS.has(node.tagName)) return NodeFilter.FILTER_REJECT;
                return NodeFilter.FILTER_ACCEPT;
            }
        });

        while (walker.nextNode()) {
            const child = walker.currentNode;
            if (child === el) continue;

            // Stop digging if we hit another container (that container handles itself)
            if (child.matches && child.matches(CONFIG.CONTAINERS)) return false;

            if (child.matches && child.matches(CONFIG.INTERACTIVE)) {
                const style = window.getComputedStyle(child);
                if (style.display !== 'none' && (style.visibility === 'hidden' || parseFloat(style.opacity) < 0.1)) {
                    return true;
                }
            }
        }
        return false;
    }

    // --- STATE ENGINE ---

    function getDetailedState(el, style, isContainer) {
        let tags =[];

        // Interaction States
        const isChecked = el.checked || el.getAttribute('aria-checked') === 'true' || el.classList.contains('checked');
        if (isChecked) tags.push('[CHECKED]');
        if (el.indeterminate || el.getAttribute('aria-checked') === 'mixed') tags.push('[HALF_CHECKED]');
        if (el.selected || el.getAttribute('aria-selected') === 'true') tags.push('[SELECTED]');
        if (el.disabled || el.getAttribute('aria-disabled') === 'true') tags.push('[DISABLED]');
        if (el.readOnly || el.getAttribute('readonly')) tags.push('[READONLY]');
        if (el.getAttribute('aria-expanded') === 'true' || el.open) tags.push('[OPEN]');

        // Menu & Popup Awareness
        if (el.getAttribute('aria-haspopup')) tags.push('[HAS_MENU]');
        if (el.title && el.title.trim().length > 0) tags.push('[TOOLTIP]');

        // Ghost Detection
        if (isContainer && !tags.includes('[HAS_MENU]')) {
            if (hasHiddenInteractiveChild(el)) tags.push('[HOVER_REVEALS]');
        }

        // Standard Attributes
        if (el.tagName === 'A' && el.target === '_blank') tags.push('[NEW_TAB]');
        if (el.tagName === 'INPUT' && el.type === 'file') tags.push('[UPLOAD]');
        if (el.required || el.getAttribute('aria-required') === 'true') tags.push('[REQUIRED]');
        if (el.getAttribute('aria-invalid') === 'true') tags.push('[INVALID]');
        
        // 🚀 ARCHITECTURE UPGRADE: Semantic Download Detection
        let isDownload = false;
        const dlExts = /\.(exe|msi|zip|tar|gz|rar|pdf|dmg|pkg|iso|apk|csv|xlsx|docx)$/i;
        if (el.hasAttribute('download')) isDownload = true;
        if (el.tagName === 'A' && el.href && dlExts.test(el.href.split('?')[0])) isDownload = true;
        if ((el.tagName === 'BUTTON' || el.tagName === 'A') && el.innerText && /download/i.test(el.innerText)) isDownload = true;
        if (isDownload) tags.push('[DOWNLOAD]');

        if (el.getAttribute('role') === 'dialog' || el.getAttribute('role') === 'alertdialog') tags.push('[MODAL]');
        if (style.position === 'fixed' || style.position === 'sticky') tags.push('[STICKY]');

        // Scroll Detection
        const hasScrollableContentY = el.scrollHeight > el.clientHeight + 2;
        const hasScrollableContentX = el.scrollWidth > el.clientWidth + 2;
        const isOverflowScrollY = style.overflowY === 'scroll' || style.overflowY === 'auto' || style.overflowY === 'hidden';
        const isOverflowScrollX = style.overflowX === 'scroll' || style.overflowX === 'auto' || style.overflowX === 'hidden';

        if (hasScrollableContentY && isOverflowScrollY) tags.push('[SCROLLABLE_Y]');
        if (hasScrollableContentX && isOverflowScrollX) tags.push('[SCROLLABLE_X]');
        if (tags.includes('[SCROLLABLE_Y]') || tags.includes('[SCROLLABLE_X]')) tags.push('[SCROLLABLE]');

        return tags.length ? " " + tags.join(' ') : "";
    }

    // --- ATOMIC NAME GENERATOR ---

    function getAtomicName(el) {
        if (['INPUT', 'TEXTAREA', 'SELECT'].includes(el.tagName)) {
            if (el.type === 'checkbox' || el.type === 'radio') {
                if (el.id) {
                    const l = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
                    if (l) return cleanText(l.innerText);
                }
                if (el.parentElement.tagName === 'LABEL') return cleanText(el.parentElement.innerText);
                return '';
            }
            return cleanText(el.value || el.placeholder || el.getAttribute('aria-label') || '');
        }

        const parts = [];
        const aria = el.getAttribute('aria-label');
        if (aria) parts.push(cleanText(aria));

        const walker = document.createTreeWalker(el, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT, null, false);
        let node;
        while (node = walker.nextNode()) {
            if (node.nodeType === 3) {
                const txt = cleanText(node.textContent);
                if (txt) parts.push(txt);
            } else if (node.nodeType === 1) {
                if (node.tagName === 'IMG' || node.tagName === 'SVG') {
                    const rect = node.getBoundingClientRect();
                    if (rect.width > 0 && rect.width < 50) {
                        const alt = node.getAttribute('alt') || node.getAttribute('aria-label');
                        parts.push(alt ? `[ICON: ${cleanText(alt)}]` : '[ICON]');
                    }
                }
            }
        }
        return [...new Set(parts)].join(' ');
    }

    function findBestImage(containerElement) {
        if (!containerElement) return null;
        let bestImage = { src: null, area: -1 };

        // 1. Check direct <img> tags
        const images = Array.from(containerElement.querySelectorAll('img'));
        images.forEach(img => {
            const rect = img.getBoundingClientRect();
            const area = rect.width * rect.height;
            // Filter: Must be > 50x50px to avoid icons/tracking pixels
            if (area > bestImage.area && rect.width > 50 && rect.height > 50) {
                bestImage = { src: img.src || img.getAttribute('data-src'), area };
            }
        });

        // 2. Check CSS background-images (common in cards)
        if (!bestImage.src) {
            const allChildren = [containerElement, ...Array.from(containerElement.querySelectorAll('*'))];
            allChildren.forEach(el => {
                const style = window.getComputedStyle(el);
                if (style.backgroundImage && style.backgroundImage !== 'none') {
                    const match = style.backgroundImage.match(/url\(['"]?(.*?)['"]?\)/);
                    if (match && match[1]) {
                        const rect = el.getBoundingClientRect();
                        const area = rect.width * rect.height;
                        if (area > bestImage.area && rect.width > 50 && rect.height > 50) {
                            bestImage = { src: match[1], area };
                        }
                    }
                }
            });
        }
        
        // Resolve relative URLs
        if (bestImage.src) {
            try { return new URL(bestImage.src, window.location.href).href; } catch (e) { return null; }
        }
        return null;
    }

    // --- MAIN PROCESSOR ---

    class PCAgentProcessor {
        run() {
            const startTime = performance.now();
            axIdCounter = 0;
            for (let k in registry) delete registry[k];

            const allElements = document.querySelectorAll('*');
            const nodes = [];
            const elementToNode = new Map();

            allElements.forEach(el => {
                if (CONFIG.IGNORE_TAGS.has(el.tagName) || el.id === 'pcagent-overlay' || el.closest('#pcagent-overlay')) return;
                const style = window.getComputedStyle(el);
                if (!isVisible(el, style)) return;

                const isInteractive = el.matches(CONFIG.INTERACTIVE);
                let isContainer = el.matches(CONFIG.CONTAINERS);

                // Check for scrollable overflow early to ensure we don't skip it
                const isScrollableX = el.scrollWidth > el.clientWidth + 2 && (style.overflowX === 'scroll' || style.overflowX === 'auto' || style.overflowX === 'hidden');
                const isScrollableY = el.scrollHeight > el.clientHeight + 2 && (style.overflowY === 'scroll' || style.overflowY === 'auto' || style.overflowY === 'hidden');
                const isScrollable = isScrollableX || isScrollableY;

                if (isScrollable) isContainer = true;

                // ATOMICITY: No nodes allowed inside Buttons/Links
                if (!isInteractive) {
                    const parentInteractive = el.closest(CONFIG.INTERACTIVE);
                    if (parentInteractive) return;
                }

                // DIRECT TEXT CHECK
                let isText = false;
                if (!isInteractive && !isContainer) {
                    for (let i = 0; i < el.childNodes.length; i++) {
                        if (el.childNodes[i].nodeType === 3 && el.childNodes[i].textContent.trim().length > 0) {
                            isText = true;
                            break;
                        }
                    }
                }

                if (!isInteractive && !isText && el.tagName !== 'IMG' && !isContainer) return;

                let type = 'TXT';
                let name = '';

                if (isInteractive) {
                    type = this.getInteractiveType(el);
                    name = getAtomicName(el);
                    // Ensure hidden file inputs get a recognizable name
                    if (el.tagName === 'INPUT' && el.type === 'file' && !name) {
                        name = "Hidden File Upload Input";
                    }
                } else if (el.tagName === 'IMG') {
                    name = cleanText(el.alt) || (el.src ? el.src.split('/').pop().substring(0, 20) : '');
                    if (!name) return;
                } else if (isText) {
                    type = 'TXT';
                    name = getAtomicName(el);
                } else if (isContainer) {
                    type = this.getContainerType(el);
                    name = cleanText(el.getAttribute('aria-label') || el.title);
                }

                // Pruning empty non-inputs
                if (isInteractive && !name && !['INP', 'CHK', 'SEL'].includes(type)) return;
                if (type === 'TXT' && !name) return;

                const awarenessTags = getDetailedState(el, style, isContainer);
                const tagString = awarenessTags.trim();
                const isActualScrollable = tagString.includes('[SCROLLABLE]');

                const node = {
                    id: (isContainer && !isInteractive && !isActualScrollable) ? null : ++axIdCounter,
                    el, type, name, tags: awarenessTags,
                    isContainer: isContainer && !isInteractive,
                    rect: el.getBoundingClientRect(),
                    children: [], parent: null
                };

                nodes.push(node);
                elementToNode.set(el, node);

                if (node.id) {
                    el.setAttribute('data-pcagent-id', 'ax-' + node.id);
                    
                    const attributes = {};
                    if (el.tagName === 'IMG') attributes.src = el.src;
                    if (el.tagName === 'A') attributes.href = el.href;
                    
                    // AUTO-IMAGE EXTRACTION LOGIC
                    if (node.isContainer || type === 'CARD' || type === 'ITEM') {
                        const imgUrl = findBestImage(el);
                        if (imgUrl) attributes._implicit_image_url = imgUrl;
                    }

                    registry[node.id] = {
                        type, text: name, tags: awarenessTags,
                        box: { x: node.rect.left, y: node.rect.top, width: node.rect.width, height: node.rect.height },
                        xpath: this.getXPath(el),
                        attributes: attributes
                    };
                }
            });

            // RECONSTRUCT TREE
            const roots = [];
            nodes.forEach(node => {
                let parent = node.el.parentElement;
                let foundParent = false;
                while (parent && parent !== document.body) {
                    if (elementToNode.has(parent)) {
                        const parentNode = elementToNode.get(parent);
                        parentNode.children.push(node);
                        node.parent = parentNode;
                        foundParent = true;
                        break;
                    }
                    parent = parent.parentElement;
                }
                if (!foundParent) roots.push(node);
            });

            const validRoots = this.pruneTree(roots);
            const script = this.generateScript(validRoots);

            if (window.PCAGENT_CONFIG && window.PCAGENT_CONFIG.show_highlights) {
                this.draw(registry);
            } else {
                this.clearDraw();
            }

            return {
                script: script,
                registry: registry,
                meta: { nodes: Object.keys(registry).length, time: performance.now() - startTime }
            };
        }

        getInteractiveType(el) {
            const role = el.getAttribute('role');
            if (role === 'checkbox' || role === 'switch' || role === 'menuitemcheckbox' || role === 'radio') return 'CHK';
            const t = el.tagName;
            if (t === 'INPUT') {
                if (el.type === 'checkbox' || el.type === 'radio') return 'CHK';
                return (el.type === 'submit' || el.type === 'button') ? 'BTN' : 'INP';
            }
            if (t === 'TEXTAREA') return 'INP';
            if (t === 'SELECT') return 'SEL';
            if (t === 'BUTTON') return 'BTN';
            if (t === 'A') return 'LNK';
            return 'BTN';
        }

        getContainerType(el) {
            const t = el.tagName;
            if (t === 'ARTICLE' || el.classList.contains('card')) return 'CARD';
            if (t === 'FORM') return 'FORM';
            if (t === 'NAV') return 'NAV';
            if (t === 'UL' || t === 'OL' || el.getAttribute('role') === 'list') return 'LIST';
            if (t === 'LI') return 'ITEM';
            if (t === 'TR') return 'ROW';
            if (el.getAttribute('role') === 'dialog') return 'MODAL';
            return 'GROUP';
        }

        getXPath(el) {
            if (el.id) return `//*[@id="${el.id}"]`;
            if (el === document.body) return '/html/body';
            let ix = 0;
            const siblings = el.parentNode ? el.parentNode.childNodes : [];
            for (let i = 0; i < siblings.length; i++) {
                const sibling = siblings[i];
                if (sibling === el) {
                    const parentPath = this.getXPath(el.parentNode);
                    if (!parentPath) return '';
                    return `${parentPath}/${el.tagName.toLowerCase()}[${ix + 1}]`;
                }
                if (sibling.nodeType === 1 && sibling.tagName === el.tagName) ix++;
            }
            return '';
        }

        pruneTree(nodes) {
            const valid = [];
            for (const node of nodes) {
                node.children = this.pruneTree(node.children);

                // CRITICAL: Never prune or bypass a scrollable container.
                // If we bypass it, the Agent loses the ability to target the scrollable area.
                const isScrollable = node.tags && node.tags.includes('[SCROLLABLE]');

                if (node.isContainer && !isScrollable && node.children.length === 0) continue;
                if (node.isContainer && !isScrollable && node.children.length === 1 && !node.name) {
                    const child = node.children[0];
                    valid.push(child);
                    continue;
                }
                valid.push(node);
            }
            return valid;
        }

        generateScript(nodes, depth = 0) {
            let output = "";
            const indent = "  ".repeat(depth);
            nodes.sort((a, b) => (a.rect.top - b.rect.top) || (a.rect.left - b.rect.left));

            nodes.forEach(node => {
                if (node.parent && node.type === 'TXT' && node.parent.name && node.parent.name.includes(node.name)) return;

                let tag = node.type;
                if (tag === 'TXT') {
                    if (['H1', 'H2', 'H3'].includes(node.el.tagName)) tag = 'HEADER';
                    else if (node.name.match(/[\$€£¥₹]/)) tag = 'PRICE';
                }

                // Logic: If a container has Hover Reveals or is Scrollable, force an ID so the Agent can target it
                const isScrollable = node.tags && (node.tags.includes('[SCROLLABLE]') || node.tags.includes('[SCROLLABLE_Y]') || node.tags.includes('[SCROLLABLE_X]'));
                const isHoverReveal = node.tags && node.tags.includes('[HOVER_REVEALS]');

                if (node.isContainer && (isHoverReveal || isScrollable)) {
                    if (!node.id) {
                        node.id = ++axIdCounter;
                        registry[node.id] = {
                            type: tag, text: node.name, tags: node.tags,
                            box: { x: node.rect.left, y: node.rect.top, width: node.rect.width, height: node.rect.height },
                            xpath: this.getXPath(node.el),
                            attributes: {}
                        };
                        node.el.setAttribute('data-pcagent-id', 'ax-' + node.id);
                    }
                }

                const idStr = node.id ? `[${node.id}] ` : '';
                const nameStr = node.name ? ` "${node.name}"` : '';

                output += `${indent}${idStr}${tag}${nameStr}${node.tags}\n`;

                if (node.children.length > 0) {
                    output += this.generateScript(node.children, depth + 1);
                }
            });
            return output;
        }

        draw(reg) {
            this.clearDraw();
            const div = document.createElement('div');
            div.id = 'pcagent-overlay';
            Object.assign(div.style, { position: 'fixed', top: 0, left: 0, zIndex: 2147483647, pointerEvents: 'none' });

            for (let id in reg) {
                const node = reg[id];
                const color = CONFIG.COLORS[parseInt(id) % CONFIG.COLORS.length];
                const el = document.createElement('div');
                Object.assign(el.style, {
                    position: 'absolute', left: node.box.x + 'px', top: node.box.y + 'px',
                    width: node.box.width + 'px', height: node.box.height + 'px',
                    border: `1px solid ${color}`, backgroundColor: `${color}0D`
                });

                // Visual Indicator for Hover Reveals (Dashed Line)
                if (node.tags && node.tags.includes('[HOVER_REVEALS]')) {
                    el.style.borderStyle = 'dashed';
                    el.style.borderWidth = '2px';
                    el.style.backgroundColor = 'rgba(255, 165, 0, 0.05)';
                }

                if (node.type !== 'TXT' || node.box.height > 15) {
                    const l = document.createElement('span');
                    l.textContent = id;
                    Object.assign(l.style, {
                        position: 'absolute', top: '-11px', left: '0',
                        backgroundColor: color, color: 'white',
                        fontSize: '9px', padding: '0 2px', borderRadius: '2px'
                    });
                    el.appendChild(l);
                }
                div.appendChild(el);
            }
            document.body.appendChild(div);

            // Auto-clear after 2 seconds to prevent interference with next turns
            setTimeout(() => {
                this.clearDraw();
            }, 2000);
        }

        clearDraw() {
            const old = document.getElementById('pcagent-overlay');
            if (old) old.remove();
        }
    }

    window.PCAgentProcessor = new PCAgentProcessor();
    console.log("[PCAgent] Processor Loaded.");

})();