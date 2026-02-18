{
  "app_context": {
    "product_name_working": "KsięgowySEO Writer",
    "type": "saas_app",
    "language": "pl-PL",
    "primary_users": ["biura rachunkowe", "księgowi", "doradcy podatkowi"],
    "primary_success_actions": [
      "Wygeneruj artykuł SEO w języku polskim",
      "Edytuj artykuł w trybie Wizualnym i HTML",
      "Popraw wynik SEO na panelu (checklista + metryki)",
      "Wyeksportuj treść do Facebook/Google Business + pobierz HTML/PDF",
      "Zastosuj sugestie linków wewnętrznych oraz FAQ"
    ]
  },
  "brand_personality": {
    "attributes": ["wiarygodny", "precyzyjny", "profesjonalny", "nowoczesny", "spokojny"],
    "visual_metaphor": "‘redakcyjny pulpit’ + ‘audyt SEO’ (księgowość = porządek, SEO = kontrola jakości)",
    "style_fusion": [
      "Layout gęsty jak Notion/Linear (power-user)",
      "Jasne tło i ostre typograficzne nagłówki jak nowoczesne fintech dashboards",
      "Delikatne akcenty ocean-blue + miękka faktura/noise (żeby nie było ‘płasko’)"
    ]
  },
  "design_tokens": {
    "notes": [
      "Nie używać intensywnych gradientów. Gradient tylko jako delikatny akcent w tle hero/toolbar (<=20% viewport).",
      "Domyślnie jasny UI (desktop-first), z trybem dark opcjonalnie później."
    ],
    "css_custom_properties": {
      ":root": {
        "--background": "210 33% 99%",
        "--foreground": "222 47% 11%",
        "--card": "0 0% 100%",
        "--card-foreground": "222 47% 11%",
        "--popover": "0 0% 100%",
        "--popover-foreground": "222 47% 11%",

        "--primary": "209 88% 36%",
        "--primary-foreground": "210 40% 98%",

        "--secondary": "210 20% 96%",
        "--secondary-foreground": "222 47% 15%",

        "--muted": "210 22% 96%",
        "--muted-foreground": "215 16% 45%",

        "--accent": "191 63% 92%",
        "--accent-foreground": "222 47% 12%",

        "--destructive": "0 72% 51%",
        "--destructive-foreground": "210 40% 98%",

        "--border": "214 18% 88%",
        "--input": "214 18% 88%",
        "--ring": "209 88% 36%",

        "--success": "158 55% 34%",
        "--success-foreground": "210 40% 98%",
        "--warning": "38 92% 45%",
        "--warning-foreground": "222 47% 12%",
        "--info": "209 88% 36%",
        "--info-foreground": "210 40% 98%",

        "--radius": "0.75rem",

        "--shadow-sm": "0 1px 2px rgba(15, 23, 42, 0.06)",
        "--shadow-md": "0 8px 24px rgba(15, 23, 42, 0.10)",
        "--shadow-focus": "0 0 0 4px rgba(14, 116, 144, 0.18)",

        "--editor-bg": "0 0% 100%",
        "--editor-gutter": "210 22% 96%",
        "--code-bg": "222 47% 11%",
        "--code-fg": "210 40% 98%"
      },
      "texture_and_gradients": {
        "allowed_gradients": [
          {
            "name": "toolbar-wash",
            "css": "radial-gradient(1200px 300px at 20% 0%, rgba(14,116,144,0.10), transparent 55%), radial-gradient(900px 260px at 80% 0%, rgba(2,132,199,0.10), transparent 60%)",
            "usage": "Top header/toolbar background only (thin band)."
          }
        ],
        "noise_overlay": {
          "css": "background-image: url('data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22120%22 height=%22120%22%3E%3Cfilter id=%22n%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.9%22 numOctaves=%223%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22120%22 height=%22120%22 filter=%22url(%23n)%22 opacity=%220.05%22/%3E%3C/svg%3E')",
          "usage": "Apply as overlay on app background or header only (opacity <= 0.06)."
        }
      }
    }
  },
  "typography": {
    "font_pairing": {
      "display": {
        "name": "Space Grotesk",
        "google_fonts_import": "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap",
        "usage": "Nagłówki, KPI, tytuły paneli, ‘score’"
      },
      "body": {
        "name": "IBM Plex Sans",
        "google_fonts_import": "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&display=swap",
        "usage": "Tekst UI, formularze, długie treści meta/FAQ"
      },
      "mono": {
        "name": "IBM Plex Mono",
        "google_fonts_import": "https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&display=swap",
        "usage": "Podgląd HTML, fragmenty kodu, slug/anchors"
      }
    },
    "tailwind_recommendation": {
      "add_to_index_css": "body { font-family: 'IBM Plex Sans', ui-sans-serif, system-ui; } h1,h2,h3,[data-role='display'] { font-family: 'Space Grotesk', ui-sans-serif, system-ui; } code, pre, [data-role='mono'] { font-family: 'IBM Plex Mono', ui-monospace, SFMono-Regular; }",
      "text_size_hierarchy": {
        "h1": "text-4xl sm:text-5xl lg:text-6xl",
        "h2": "text-base md:text-lg",
        "body": "text-sm md:text-base",
        "small": "text-xs md:text-sm"
      }
    }
  },
  "layout_and_grid": {
    "app_shell": {
      "pattern": "Left sidebar (collapsed optional) + top toolbar + content area",
      "max_width": "No hard max width for editor pages; use fluid width with comfortable paddings",
      "grid": {
        "desktop": "Sidebar 260px + content (auto). Editor page: 3-column: left ‘outline/TOC’ (280px) | editor (fluid) | right ‘SEO/Export’ (360px) using resizable panels.",
        "tablet": "2-column: sidebar + content; editor right panel becomes drawer/sheet.",
        "mobile": "Stacked: tabs for Visual/HTML/SEO/Export; TOC and suggestions inside sheets."
      },
      "spacing": {
        "page_padding": "px-4 sm:px-6 lg:px-8",
        "section_gap": "gap-4 sm:gap-6",
        "card_padding": "p-4 sm:p-5",
        "editor_padding": "p-4 sm:p-6"
      }
    },
    "reading_comfort": {
      "wysiwyg_typography": "Prose styling: max-w-none, leading-7, paragraph spacing; keep editor canvas width ~760-880px inside fluid container with centered ‘paper’ feel only in the canvas, not the whole app.",
      "long_content": "Use ScrollArea for editor panes and side panels; sticky headers for tabs and action bars."
    }
  },
  "components": {
    "component_path": {
      "shadcn_primary": [
        "/app/frontend/src/components/ui/button.jsx",
        "/app/frontend/src/components/ui/card.jsx",
        "/app/frontend/src/components/ui/tabs.jsx",
        "/app/frontend/src/components/ui/scroll-area.jsx",
        "/app/frontend/src/components/ui/resizable.jsx",
        "/app/frontend/src/components/ui/separator.jsx",
        "/app/frontend/src/components/ui/badge.jsx",
        "/app/frontend/src/components/ui/progress.jsx",
        "/app/frontend/src/components/ui/dialog.jsx",
        "/app/frontend/src/components/ui/sheet.jsx",
        "/app/frontend/src/components/ui/tooltip.jsx",
        "/app/frontend/src/components/ui/accordion.jsx",
        "/app/frontend/src/components/ui/table.jsx",
        "/app/frontend/src/components/ui/select.jsx",
        "/app/frontend/src/components/ui/textarea.jsx",
        "/app/frontend/src/components/ui/input.jsx",
        "/app/frontend/src/components/ui/skeleton.jsx",
        "/app/frontend/src/components/ui/sonner.jsx",
        "/app/frontend/src/components/ui/calendar.jsx"
      ],
      "icon_library": "lucide-react"
    },
    "page_blueprints": {
      "dashboard_home": {
        "layout": "Top toolbar with search + ‘Nowy artykuł’ CTA; grid of KPI cards + table of recent articles.",
        "key_components": ["Card", "Table", "Badge", "Button", "Input", "Skeleton"],
        "kpis": ["Wygenerowane artykuły", "Śr. wynik SEO", "Artykuły do poprawy", "Eksporty w tym tygodniu"],
        "data_testids": {
          "new_article_button": "dashboard-new-article-button",
          "search_input": "dashboard-search-input",
          "articles_table": "dashboard-articles-table"
        }
      },
      "new_article_generator": {
        "layout": "Wizard w Card: lewa kolumna ‘Ustawienia’ + prawa ‘Podgląd briefu’. Na mobile: Tabs.",
        "form_sections": [
          "Temat i cel (branża/nisza)",
          "Słowa kluczowe (główne + pomocnicze)",
          "Ton (formalny, ekspercki, przystępny)",
          "Długość (liczba słów) + struktura nagłówków",
          "Źródła (tylko wiarygodne)"
        ],
        "key_components": ["Form", "Input", "Textarea", "Select", "Slider", "Tabs", "Badge"],
        "loading_state": "After submit, show full-page generation state with progress + tips + skeleton preview.",
        "data_testids": {
          "generate_submit": "generator-generate-article-button",
          "topic_input": "generator-topic-input",
          "keywords_input": "generator-keywords-input",
          "tone_select": "generator-tone-select",
          "length_slider": "generator-length-slider"
        }
      },
      "article_editor": {
        "layout": "Three-panel using Resizable: left TOC/anchors; center editor; right SEO/Export panel. Top sticky action bar (Zapisz, Generuj ponownie, Cofnij/Ponów, Podgląd).",
        "tabs": ["Wizualny", "HTML", "SEO", "Eksport"],
        "key_components": ["Resizable", "Tabs", "ScrollArea", "Card", "Separator", "Tooltip", "Dialog", "Sheet"],
        "editor_canvas": {
          "visual": "WYSIWYG area with ‘paper’ card (white) inside light background. Floating mini-toolbar on text selection (optional).",
          "html": "Monospace editor with dark code surface inside card, line numbers optional.",
          "accessibility": "Ensure keyboard navigation between panes and focus outlines (ring)."
        },
        "data_testids": {
          "editor-tabs": "article-editor-tabs",
          "visual-editor": "article-visual-editor",
          "html-editor": "article-html-editor",
          "save-button": "article-save-button",
          "export-panel": "article-export-panel",
          "seo-panel": "article-seo-panel",
          "toc-panel": "article-toc-panel"
        }
      },
      "topic_suggestions": {
        "layout": "Split: left filters (branża, miesiąc/okres, typ podatku) + right list/grid of topic cards with ‘Użyj w generatorze’.",
        "key_components": ["Command", "Card", "Badge", "Button", "Tabs", "Pagination"],
        "data_testids": {
          "topic-search": "topics-search-input",
          "topic-card": "topics-topic-card",
          "use-topic": "topics-use-topic-button"
        }
      },
      "meta_settings": {
        "layout": "Card: Meta tytuł + opis + slug + OpenGraph preview style (simple).",
        "key_components": ["Input", "Textarea", "Badge", "Card"],
        "data_testids": {
          "meta-title": "meta-title-input",
          "meta-description": "meta-description-textarea",
          "meta-slug": "meta-slug-input"
        }
      }
    },
    "seo_score_panel": {
      "visual_priority": "Always visible on desktop (right panel). On smaller screens: sticky summary bar + details in Sheet.",
      "widgets": [
        {
          "name": "Score gauge",
          "implementation": "Use Progress + numeric score + colored badge (Słaby/OK/Dobry). For nicer arc gauge, use Recharts RadialBarChart.",
          "states": {
            "0-49": "destructive",
            "50-79": "warning",
            "80-100": "success"
          },
          "data_testid": "seo-score-gauge"
        },
        {
          "name": "Checklist",
          "implementation": "Accordion sections: Czytelność, Struktura nagłówków, Gęstość słów kluczowych, Długość, Linkowanie.",
          "data_testid": "seo-checklist"
        },
        {
          "name": "Keyword density",
          "implementation": "Mini bar chart / list with % + recommended range using Progress.",
          "data_testid": "seo-keyword-density"
        }
      ],
      "microcopy_pl": {
        "score_title": "Wynik SEO",
        "next_actions": "Najważniejsze poprawki",
        "explain": "Każda zmiana w treści aktualizuje ocenę w czasie rzeczywistym."
      }
    },
    "export_panel": {
      "platform_cards": [
        {
          "platform": "Facebook",
          "content": "Copy-ready (krótsze akapity, 1–2 CTA, bez przesadnych hashtagów)",
          "actions": ["Kopiuj", "Pobierz HTML"],
          "data_testid": "export-facebook-card"
        },
        {
          "platform": "Google Business Profile",
          "content": "Copy-ready (lokalny ton, konkret, 1 CTA, limit znaków indicator)",
          "actions": ["Kopiuj"],
          "data_testid": "export-google-business-card"
        },
        {
          "platform": "HTML",
          "content": "Pobierz pełny artykuł jako HTML",
          "actions": ["Pobierz"],
          "data_testid": "export-html-download"
        },
        {
          "platform": "PDF",
          "content": "Pobierz jako PDF (format A4)",
          "actions": ["Pobierz"],
          "data_testid": "export-pdf-download"
        }
      ],
      "ux_rules": [
        "Każda karta eksportu ma preview textarea (read-only) + przycisk Kopiuj.",
        "Wyświetl komunikat Sonner po skopiowaniu/pobraniu.",
        "Pokaż licznik znaków + ostrzeżenie, jeśli przekroczono limity platformy."
      ]
    },
    "toc_and_anchors": {
      "toc_panel": "Left panel: lista nagłówków H2/H3 z drag reorder (optional later).",
      "anchor_management": "Każdy heading ma slug/anchor input w monospace; przycisk ‘Skopiuj link’.",
      "components": ["ScrollArea", "Input", "Button", "Tooltip", "Badge"],
      "data_testids": {
        "toc-list": "toc-list",
        "toc-anchor-input": "toc-anchor-input",
        "toc-copy-anchor": "toc-copy-anchor-button"
      }
    },
    "internal_link_suggestions": {
      "layout": "Right panel section: table/list suggestions with confidence badge + ‘Wstaw link’.",
      "components": ["Table", "Badge", "Button"],
      "data_testids": {
        "internal-links-table": "internal-links-table",
        "insert-internal-link": "insert-internal-link-button"
      }
    },
    "faq_editor": {
      "pattern": "Accordion of Q/A with inline add/remove; keep controls compact.",
      "components": ["Accordion", "Input", "Textarea", "Button", "Dialog"],
      "data_testids": {
        "faq-accordion": "faq-accordion",
        "faq-add": "faq-add-button",
        "faq-remove": "faq-remove-button"
      }
    }
  },
  "motion_and_microinteractions": {
    "principles": [
      "Interakcje szybkie i ‘pewne’: 120–180ms dla hover/focus, 180–240ms dla otwierania paneli.",
      "Preferuj subtle scale (1.00 -> 1.02) i cień na hover dla primary CTA.",
      "W panelu SEO: animuj zmianę wyniku (count-up) + delikatny flash tła sekcji, która się poprawiła (accent/5%)."
    ],
    "do_not": ["Nie używać transition: all"],
    "tailwind_snippets": {
      "button_hover": "transition-colors duration-150 hover:bg-primary/90 active:scale-[0.98]",
      "card_hover": "transition-shadow duration-200 hover:shadow-[var(--shadow-md)]",
      "focus": "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
    },
    "recommended_library": {
      "name": "framer-motion",
      "why": "Animacje paneli (Sheet/Drawer), skeleton-to-content, count-up score, subtle entrance for suggestions.",
      "install": "npm i framer-motion",
      "usage_note": "Use motion.div for panel transitions only; keep it subtle (opacity + y 4px)."
    }
  },
  "data_viz_and_scoring": {
    "recommended_library": {
      "name": "recharts",
      "install": "npm i recharts",
      "use_cases": [
        "SEO gauge (RadialBarChart)",
        "Keyword density histogram",
        "Readability breakdown (bar)"
      ]
    },
    "empty_states": {
      "pattern": "Icon + concise PL copy + 1 CTA.",
      "examples": [
        "‘Brak artykułów. Wygeneruj pierwszy wpis.’",
        "‘Brak sugestii dla tego słowa kluczowego — spróbuj innej frazy.’"
      ]
    }
  },
  "loading_states": {
    "generation": {
      "duration": "10–30s",
      "ui": [
        "Full-screen card with Progress + stepper: Analiza tematu → Szkic struktury → Pisanie → SEO korekty → Finalizacja",
        "Skeleton preview of article sections",
        "Tips carousel: ‘Jak poprawić czytelność’, ‘Jak dobierać H2/H3’"
      ],
      "components": ["Progress", "Skeleton", "Card", "Carousel"],
      "data_testids": {
        "generation-progress": "generation-progress",
        "generation-stage": "generation-stage-label"
      }
    }
  },
  "accessibility": {
    "requirements": [
      "WCAG AA kontrast (szczególnie teksty w kartach i badge).",
      "Widoczny focus ring na wszystkich kontrolkach.",
      "Klawiatura: Tab order logiczny, skróty w edytorze nie mogą kolidować z przeglądarką.",
      "Prefer-reduced-motion: ogranicz animacje do opacity bez przesunięć."
    ]
  },
  "testing_requirements": {
    "data_testid_rule": "All interactive and key informational elements MUST include data-testid (kebab-case, role-based).",
    "examples": [
      "data-testid=\"sidebar-nav-dashboard\"",
      "data-testid=\"article-export-pdf-button\"",
      "data-testid=\"seo-readability-score\""
    ]
  },
  "image_urls": {
    "branding_usage": [
      {
        "category": "dashboard_header_illustration_optional",
        "description": "Subtelny obraz w pustym stanie dashboardu (biuro/praca). Używać oszczędnie.",
        "urls": [
          "https://images.unsplash.com/photo-1579362243176-b746a02bc030?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA0MTJ8MHwxfHNlYXJjaHwzfHxtb2Rlcm4lMjBvZmZpY2UlMjBkZXNrJTIwbGFwdG9wJTIwd3JpdGluZyUyMGVkaXRvcmlhbCUyMGNsZWFuJTIwYmx1ZXxlbnwwfHx8Ymx1ZXwxNzcxNDU3NDk4fDA&ixlib=rb-4.1.0&q=85",
          "https://images.pexels.com/photos/6931346/pexels-photo-6931346.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940"
        ]
      },
      {
        "category": "editor_empty_state",
        "description": "Minimalny, dokumentowy klimat dla pustych stanów (bez rozpraszania).",
        "urls": [
          "https://images.unsplash.com/photo-1611420111738-7deb3150ecbc?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1ODh8MHwxfHNlYXJjaHw0fHxtaW5pbWFsJTIwZG9jdW1lbnQlMjB0eXBvZ3JhcGh5JTIwY2xvc2UlMjB1cCUyMGVkaXRvcmlhbHxlbnwwfHx8YmxhY2tfYW5kX3doaXRlfDE3NzE0NTc1MDF8MA&ixlib=rb-4.1.0&q=85",
          "https://images.unsplash.com/photo-1609605348232-a501212c5084?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1ODh8MHwxfHNlYXJjaHwyfHxtaW5pbWFsJTIwZG9jdW1lbnQlMjB0eXBvZ3JhcGh5JTIwY2xvc2UlMjB1cCUyMGVkaXRvcmlhbHxlbnwwfHx8YmxhY2tfYW5kX3doaXRlfDE3NzE0NTc1MDF8MA&ixlib=rb-4.1.0&q=85"
        ]
      }
    ]
  },
  "implementation_notes_for_js": {
    "react_files": "Project uses .js components (not .tsx). Keep shadcn imports as existing (./components/ui/...).",
    "wysiwyg": {
      "recommendation": "Use a battle-tested WYSIWYG with good HTML output. Prefer TipTap (React) or Lexical.",
      "tiptap_install": "npm i @tiptap/react @tiptap/starter-kit @tiptap/extension-link @tiptap/extension-heading",
      "fallback": "If WYSIWYG is out of scope, use a simplified editor with contentEditable + toolbar, but keep HTML source view authoritative."
    }
  },
  "instructions_to_main_agent": [
    "Replace CRA default App.css header styles; do NOT center app container globally.",
    "Update /app/frontend/src/index.css :root tokens to the HSL values above (professional blue + teal accent).",
    "Add Google Fonts imports in index.html or via CSS import at top of index.css (Space Grotesk, IBM Plex Sans, IBM Plex Mono).",
    "Build app shell: Sidebar navigation + top toolbar; use shadcn Button, Tooltip, Sheet for mobile nav.",
    "Editor page: implement Resizable panels; ensure center editor uses ScrollArea and comfortable line-height.",
    "SEO panel: implement score badge + Progress, and optionally Recharts gauge.",
    "Every interactive element and key metric must have data-testid in kebab-case.",
    "Use Sonner for copy/download success toasts.",
    "No purple gradients; keep gradient usage limited to thin header wash only (<=20% viewport)."
  ],
  "general_ui_ux_design_guidelines_appendix": "<General UI UX Design Guidelines>  \n    - You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms\n    - You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text\n   - NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json\n\n **GRADIENT RESTRICTION RULE**\nNEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc\nNEVER use dark gradients for logo, testimonial, footer etc\nNEVER let gradients cover more than 20% of the viewport.\nNEVER apply gradients to text-heavy content or reading areas.\nNEVER use gradients on small UI elements (<100px width).\nNEVER stack multiple gradient layers in the same viewport.\n\n**ENFORCEMENT RULE:**\n    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors\n\n**How and where to use:**\n   • Section backgrounds (not content backgrounds)\n   • Hero section header content. Eg: dark to light to dark color\n   • Decorative overlays and accent elements only\n   • Hero section with 2-3 mild color\n   • Gradients creation can be done for any angle say horizontal, vertical or diagonal\n\n- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**\n\n</Font Guidelines>\n\n- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead. \n   \n- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.\n\n- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.\n   \n- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly\n    Eg: - if it implies playful/energetic, choose a colorful scheme\n           - if it implies monochrome/minimal, choose a black–white/neutral scheme\n\n**Component Reuse:**\n\t- Prioritize using pre-existing components from src/components/ui when applicable\n\t- Create new components that match the style and conventions of existing components when needed\n\t- Examine existing components to understand the project's component patterns before creating new ones\n\n**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component\n\n**Best Practices:**\n\t- Use Shadcn/UI as the primary component library for consistency and accessibility\n\t- Import path: ./components/[component-name]\n\n**Export Conventions:**\n\t- Components MUST use named exports (export const ComponentName = ...)\n\t- Pages MUST use default exports (export default function PageName() {...})\n\n**Toasts:**\n  - Use `sonner` for toasts\"\n  - Sonner component are located in `/app/src/components/ui/sonner.tsx`\n\nUse 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals.\n</General UI UX Design Guidelines>"
}
