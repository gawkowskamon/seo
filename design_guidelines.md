{
  "brand": {
    "name": "Kurdynowski Accounting & Tax Solutions",
    "visual_personality": [
      "professional",
      "trustworthy",
      "premium",
      "modern-classic (editorial headings + contemporary UI)",
      "calm data-first (accounting SaaS)"
    ],
    "locale": "pl-PL",
    "tone_of_voice_pl": {
      "principles": [
        "Krótkie, rzeczowe etykiety",
        "Bez żargonu marketingowego",
        "Jasne CTA: 'Generuj artykuł', 'Zapisz', 'Eksportuj'",
        "Komunikaty błędów: co się stało + co zrobić dalej"
      ],
      "microcopy_examples": {
        "empty_state_title": "Brak artykułów",
        "empty_state_desc": "Wygeneruj pierwszy artykuł SEO dla bloga podatkowego.",
        "search_placeholder": "Szukaj po tytule, słowach kluczowych, dacie…",
        "save": "Zapisz zmiany",
        "export": "Eksportuj",
        "ai_assist": "Zapytaj asystenta SEO"
      }
    }
  },

  "design_direction": {
    "inspiration_notes": [
      "High-performance SaaS dashboard patterns (modular widgets, clear hierarchy, F-pattern).",
      "Modern editorial systems: serif display for headings, restrained palette, generous whitespace.",
      "Avoid flashy gradients; use solid surfaces with subtle noise + warm amber accents for premium feel."
    ],
    "layout_principles": [
      "Data-first dashboard with calm surfaces; accent color only for actions and key status.",
      "Modern-classic hybrid: serif headings for brand authority; sans body for speed and readability.",
      "Editor = 'command center': three-panel with resizable rails and sticky toolbars.",
      "Mobile-first: collapse side panels into Drawer/Sheet with persistent primary actions."
    ]
  },

  "color_system": {
    "notes": [
      "Primary brand blue must replace existing hsl(209, 88%, 36%).",
      "Orange used as accent for primary CTAs and highlights; never for body text blocks.",
      "Keep UI light mode; use warm neutrals instead of cold grays."
    ],
    "base_hex": {
      "brand_blue": "#04389E",
      "brand_orange": "#F28C28",
      "white": "#FFFFFF",
      "ink": "#0B1220",
      "slate": "#334155"
    },
    "tokens_css_variables": {
      "where": "/app/frontend/src/index.css :root (HSL tokens used by shadcn)",
      "recommendation": {
        "--background": "210 33% 99%",
        "--foreground": "222 47% 11%",
        "--card": "0 0% 100%",
        "--card-foreground": "222 47% 11%",
        "--popover": "0 0% 100%",
        "--popover-foreground": "222 47% 11%",

        "--primary": "220 95% 32%",
        "--primary-foreground": "210 40% 98%",

        "--secondary": "35 35% 96%",
        "--secondary-foreground": "222 47% 15%",

        "--muted": "210 22% 96%",
        "--muted-foreground": "215 16% 45%",

        "--accent": "34 90% 94%",
        "--accent-foreground": "222 47% 12%",

        "--border": "214 18% 88%",
        "--input": "214 18% 88%",
        "--ring": "220 95% 32%",

        "--destructive": "0 72% 51%",
        "--destructive-foreground": "210 40% 98%",

        "--success": "158 55% 34%",
        "--success-foreground": "210 40% 98%",

        "--warning": "34 92% 45%",
        "--warning-foreground": "222 47% 12%",

        "--radius": "0.75rem"
      },
      "mapping_to_brand": {
        "primary": "brand blue (#04389E)",
        "accent": "warm orange/amber family (#F28C28) as soft background + CTA borders",
        "secondary": "warm off-white (paper tint)"
      }
    },
    "semantic_usage": {
      "backgrounds": {
        "app": "bg-[hsl(var(--background))]",
        "subtle_section": "bg-[hsl(var(--secondary))]",
        "editor_canvas": "bg-[hsl(var(--card))]"
      },
      "text": {
        "primary": "text-[hsl(var(--foreground))]",
        "muted": "text-[hsl(var(--muted-foreground))]",
        "link": "text-[hsl(var(--primary))] hover:text-[hsl(var(--primary))]/90"
      },
      "borders": {
        "default": "border-[hsl(var(--border))]",
        "focus_ring": "focus-visible:ring-2 focus-visible:ring-[hsl(var(--ring))]"
      },
      "status": {
        "success": "text-[hsl(var(--success))] bg-[hsl(var(--success))]/10",
        "warning": "text-[hsl(var(--warning))] bg-[hsl(var(--warning))]/12",
        "danger": "text-[hsl(var(--destructive))] bg-[hsl(var(--destructive))]/10"
      }
    },
    "allowed_gradients": {
      "restriction": "Use only as decorative section background overlays and keep under 20% viewport.",
      "safe_examples_tailwind": [
        "bg-gradient-to-br from-[#04389E]/8 via-white to-[#F28C28]/10",
        "bg-gradient-to-r from-[#F28C28]/10 via-white to-[#04389E]/8"
      ]
    }
  },

  "typography": {
    "font_pairing": {
      "display_headings": {
        "google_font": "Instrument Serif",
        "fallback": "Playfair Display",
        "usage": "App headings, page titles, sidebar brand wordmark 'Kurdynowski'",
        "css": "font-family: 'Instrument Serif', ui-serif, Georgia, serif;"
      },
      "body_ui": {
        "google_font": "IBM Plex Sans (already imported)",
        "usage": "All UI, forms, table labels",
        "css": "font-family: 'IBM Plex Sans', ui-sans-serif, system-ui, sans-serif;"
      },
      "mono": {
        "google_font": "IBM Plex Mono (already imported)",
        "usage": "HTML editor, code blocks"
      }
    },
    "text_size_hierarchy_tailwind": {
      "h1": "text-4xl sm:text-5xl lg:text-6xl tracking-tight",
      "h2": "text-base md:text-lg",
      "body": "text-sm md:text-base leading-6",
      "small": "text-xs md:text-sm",
      "kpi_number": "text-3xl md:text-4xl font-semibold"
    },
    "type_styles": {
      "page_title": "font-[display] (Instrument Serif) text-3xl md:text-4xl text-foreground",
      "section_label": "text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground",
      "table_header": "text-xs font-semibold uppercase tracking-[0.10em]"
    }
  },

  "spacing_grid": {
    "container": {
      "max_width": "max-w-[1400px]",
      "page_padding": "px-4 sm:px-6 lg:px-8 py-6",
      "editor_padding": "p-4 sm:p-6"
    },
    "grid_rules": [
      "Dashboard stats: 1 col mobile, 2 cols sm, 4 cols lg.",
      "Tables: sticky header on desktop; on mobile switch to card-list rows.",
      "Editor 3-panel: left 260px, right 360px, center fluid; allow Resizable rails for desktop."
    ]
  },

  "components": {
    "component_path": {
      "shadcn_ui_base": "/app/frontend/src/components/ui",
      "use_these": [
        { "name": "button", "path": "components/ui/button.jsx" },
        { "name": "card", "path": "components/ui/card.jsx" },
        { "name": "tabs", "path": "components/ui/tabs.jsx" },
        { "name": "table", "path": "components/ui/table.jsx" },
        { "name": "badge", "path": "components/ui/badge.jsx" },
        { "name": "input", "path": "components/ui/input.jsx" },
        { "name": "textarea", "path": "components/ui/textarea.jsx" },
        { "name": "select", "path": "components/ui/select.jsx" },
        { "name": "progress", "path": "components/ui/progress.jsx" },
        { "name": "separator", "path": "components/ui/separator.jsx" },
        { "name": "scroll-area", "path": "components/ui/scroll-area.jsx" },
        { "name": "resizable", "path": "components/ui/resizable.jsx" },
        { "name": "sheet", "path": "components/ui/sheet.jsx" },
        { "name": "drawer", "path": "components/ui/drawer.jsx" },
        { "name": "dialog", "path": "components/ui/dialog.jsx" },
        { "name": "alert", "path": "components/ui/alert.jsx" },
        { "name": "sonner", "path": "components/ui/sonner.jsx" },
        { "name": "calendar", "path": "components/ui/calendar.jsx" }
      ]
    },

    "sidebar_wordmark": {
      "goal": "Stylize text-only logo: 'Kurdynowski' in brand colors (no image).",
      "layout": "Kurdynowski (serif) + smaller descriptor line in sans.",
      "tailwind_example": {
        "container": "flex items-center gap-3",
        "mark": "h-9 w-9 rounded-xl bg-[hsl(var(--primary))] text-white flex items-center justify-center shadow-sm",
        "name": "font-[display] text-lg tracking-tight",
        "name_highlight": "text-[hsl(var(--primary))]",
        "accent_dot": "text-[#F28C28]",
        "descriptor": "text-[11px] text-muted-foreground leading-tight"
      },
      "copy": {
        "name": "Kurdynowski",
        "descriptor": "Accounting & Tax Solutions"
      }
    },

    "buttons": {
      "style": "Luxury / Elegant (slim, tall, rounded 10–12px)",
      "variants": {
        "primary": {
          "use_for": ["Generuj", "Zapisz", "Eksportuj"],
          "classes": "bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] hover:bg-[hsl(var(--primary))]/95 focus-visible:ring-[hsl(var(--ring))]",
          "press": "active:translate-y-[0.5px]"
        },
        "secondary": {
          "use_for": ["Podgląd", "Wstaw", "Dodaj"],
          "classes": "bg-white border border-[hsl(var(--border))] hover:bg-[hsl(var(--secondary))]"
        },
        "accent": {
          "use_for": ["Szybka akcja", "Polecane"],
          "classes": "bg-[#F28C28] text-[#1b1206] hover:bg-[#F28C28]/90 focus-visible:ring-[#F28C28]/40"
        },
        "ghost": {
          "use_for": ["Anuluj", "Zamknij"],
          "classes": "hover:bg-[hsl(var(--secondary))]"
        }
      },
      "sizes": {
        "sm": "h-9 px-3 text-sm",
        "md": "h-10 px-4 text-sm",
        "lg": "h-11 px-5 text-base"
      },
      "data_testid_rule": "Every Button must have data-testid e.g. data-testid=\"article-generator-submit-button\""
    },

    "cards_kpis": {
      "dashboard_kpi_card": {
        "structure": "Card -> header with label + icon, body with KPI number, footer with delta",
        "classes": "rounded-xl border bg-white shadow-[0_1px_0_rgba(15,23,42,0.04)] hover:shadow-[0_12px_30px_rgba(15,23,42,0.10)] transition-shadow",
        "kpi_number_style": "font-[display] text-3xl md:text-4xl text-foreground",
        "accent_rule": "Only one accent element per card (icon background OR small badge)."
      }
    },

    "editor_3_panel": {
      "desktop": {
        "use": "Resizable panels for TOC / Editor / Right Sidebar.",
        "components": ["resizable", "scroll-area", "tabs", "separator"],
        "behavior": [
          "Sticky toolbar at top of center editor.",
          "TOC panel: ScrollArea with active section highlight.",
          "Right panel: Tabs (SEO / AI / FAQ / Obrazy / Eksport).",
          "Use subtle paper background behind editor canvas (secondary)."
        ]
      },
      "mobile": {
        "pattern": "Center editor full width; TOC + Right panels in Drawer/Sheet with bottom bar actions.",
        "components": ["drawer", "sheet"],
        "cta": "Bottom sticky bar: primary Save + secondary Panels"
      }
    },

    "forms_wizard": {
      "article_generator": {
        "pattern": "Wizard: Tabs or Steps + Progress",
        "components": ["form", "input", "textarea", "select", "progress", "card"],
        "field_spacing": "space-y-4 sm:space-y-5",
        "hint_style": "text-xs text-muted-foreground",
        "validation": "Use Alert component for form-level errors; inline for field errors."
      }
    },

    "badges_status": {
      "seo_score_badge": {
        "use": "Badge component with semantic colors",
        "classes": {
          "high": "bg-emerald-50 text-emerald-700 border border-emerald-100",
          "medium": "bg-amber-50 text-amber-800 border border-amber-100",
          "low": "bg-rose-50 text-rose-700 border border-rose-100"
        },
        "note": "Keep orange brand for actions; status colors remain semantic for clarity."
      }
    },

    "tables": {
      "articles_table": {
        "components": ["table", "input", "dropdown-menu", "pagination"],
        "desktop": "Use Table with sticky header, zebra hover only (no zebra rows).",
        "mobile": "Convert each row into Card with key-value pairs + quick actions menu."
      }
    },

    "toasts": {
      "library": "sonner",
      "component": "/app/frontend/src/components/ui/sonner.jsx",
      "usage": "Success: Zapisano. Error: Nie udało się zapisać — spróbuj ponownie."
    }
  },

  "motion_microinteractions": {
    "principles": [
      "Use motion to confirm actions (save/export), not to decorate.",
      "Prefer opacity/translate/blur transitions; avoid large scaling.",
      "No 'transition: all'."
    ],
    "recommended_library": {
      "name": "framer-motion",
      "install": "npm i framer-motion",
      "use_cases": [
        "Dashboard KPI cards entrance",
        "Wizard step transitions",
        "Right-panel tab content crossfade"
      ],
      "simple_scaffold_js": "import { motion } from 'framer-motion';\n\nexport default function FadeInSection({ children }) {\n  return (\n    <motion.div\n      initial={{ opacity: 0, y: 6 }}\n      animate={{ opacity: 1, y: 0 }}\n      transition={{ duration: 0.22, ease: 'easeOut' }}\n    >\n      {children}\n    </motion.div>\n  );\n}\n"
    },
    "hover_states": {
      "cards": "hover:shadow-[0_12px_30px_rgba(15,23,42,0.10)]",
      "buttons": "active:translate-y-[0.5px]",
      "links": "hover:underline underline-offset-4"
    }
  },

  "texture_and_surface": {
    "goal": "Premium paper-like UI without gradients.",
    "approach": [
      "Add subtle noise overlay at app background level (very low opacity).",
      "Use warm-tinted secondary background for sections and panels.",
      "Shadows: soft, realistic, minimal blur."
    ],
    "css_snippet": {
      "where": "/app/frontend/src/index.css (global)",
      "snippet": "body::before {\n  content: '';\n  position: fixed;\n  inset: 0;\n  pointer-events: none;\n  background-image: url('https://images.unsplash.com/photo-1581021833436-5ddc202fd333?auto=format&fit=crop&w=1200&q=60');\n  opacity: 0.04;\n  mix-blend-mode: multiply;\n}\n"
    }
  },

  "accessibility": {
    "requirements": [
      "WCAG AA contrast for text and interactive elements.",
      "Visible focus rings: use ring token (brand blue).",
      "Touch targets >= 44px on mobile for primary controls.",
      "Tables must be navigable; buttons and inputs need aria-label when icon-only."
    ]
  },

  "data_testid_conventions": {
    "rules": [
      "Preserve existing data-testid attributes (do not rename).",
      "Any new interactive element must include data-testid in kebab-case describing role.",
      "Examples: sidebar-nav-dashboard-link, article-editor-save-button, seo-panel-run-audit-button, topic-suggestions-generate-button"
    ]
  },

  "image_urls": {
    "hero_or_dashboard_header_optional": [
      {
        "category": "dashboard_header",
        "description": "Subtle professional office image used as blurred decorative header background (max 20% viewport).",
        "url": "https://images.unsplash.com/photo-1606223226391-c267641c318c?crop=entropy&cs=srgb&fm=jpg&ixlib=rb-4.1.0&q=85"
      }
    ],
    "texture_overlays": [
      {
        "category": "noise_texture",
        "description": "Warm paper/concrete texture used at very low opacity for premium grain.",
        "url": "https://images.unsplash.com/photo-1581021833436-5ddc202fd333?auto=format&fit=crop&w=1200&q=60"
      },
      {
        "category": "amber_abstract",
        "description": "Optional decorative amber abstract texture for onboarding/login side panel (keep subtle).",
        "url": "https://images.unsplash.com/photo-1613216514014-edb92d8e3e8d?crop=entropy&cs=srgb&fm=jpg&ixlib=rb-4.1.0&q=85"
      }
    ]
  },

  "instructions_to_main_agent": [
    "Update /app/frontend/src/index.css tokens: swap --primary and --ring to match brand blue (#04389E). Keep light mode; adjust --secondary and --accent to warm neutrals.",
    "Replace current Space Grotesk heading font with Instrument Serif for headings/wordmark only; keep IBM Plex Sans for body. Keep IBM Plex Mono for HTML editor.",
    "Do NOT remove or rename any existing data-testid. Add data-testid to any newly introduced interactive element.",
    "Sidebar wordmark: text-only 'Kurdynowski' with serif + small descriptor; incorporate orange as a tiny dot/accent, not a big block.",
    "Editor layout: use shadcn Resizable for desktop; collapse to Drawer/Sheet on <=1024px. Keep center editor primary.",
    "Buttons: primary brand blue; accent orange only for 1–2 emphasized actions (e.g., 'Eksportuj' or 'Generuj').",
    "Avoid gradients except very subtle section overlays under 20% viewport. Prefer solid surfaces + subtle noise.",
    "No transition: all; apply transition only to background-color, color, box-shadow, border-color as needed."
  ],

  "General UI UX Design Guidelines": [
    "- You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms",
    "- You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text",
    "- NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json",
    " **GRADIENT RESTRICTION RULE**",
    "NEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc",
    "NEVER use dark gradients for logo, testimonial, footer etc",
    "NEVER let gradients cover more than 20% of the viewport.",
    "NEVER apply gradients to text-heavy content or reading areas.",
    "NEVER use gradients on small UI elements (<100px width).",
    "NEVER stack multiple gradient layers in the same viewport.",
    "\n**ENFORCEMENT RULE:**",
    "    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors",
    "\n**How and where to use:**",
    "   • Section backgrounds (not content backgrounds)",
    "   • Hero section header content. Eg: dark to light to dark color",
    "   • Decorative overlays and accent elements only",
    "   • Hero section with 2-3 mild color",
    "   • Gradients creation can be done for any angle say horizontal, vertical or diagonal",
    "\n- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**",
    "\n- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead.",
    "   ",
    "- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.",
    "\n- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.",
    "   ",
    "- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly\n    Eg: - if it implies playful/energetic, choose a colorful scheme\n           - if it implies monochrome/minimal, choose a black–white/neutral scheme",
    "\n**Component Reuse:**\n\t- Prioritize using pre-existing components from src/components/ui when applicable\n\t- Create new components that match the style and conventions of existing components when needed\n\t- Examine existing components to understand the project's component patterns before creating new ones",
    "\n**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component",
    "\n**Best Practices:**\n\t- Use Shadcn/UI as the primary component library for consistency and accessibility\n\t- Import path: ./components/[component-name]",
    "\n**Export Conventions:**\n\t- Components MUST use named exports (export const ComponentName = ...)\n\t- Pages MUST use default exports (export default function PageName() {...})",
    "\n**Toasts:**\n  - Use `sonner` for toasts\n  - Sonner component are located in `/app/src/components/ui/sonner.tsx`",
    "\nUse 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals."
  ]
}
