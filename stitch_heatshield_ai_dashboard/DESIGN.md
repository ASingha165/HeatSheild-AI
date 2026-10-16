---
name: Urban Environmental Intelligence
colors:
  surface: '#0e141b'
  surface-dim: '#0e141b'
  surface-bright: '#343a41'
  surface-container-lowest: '#090f15'
  surface-container-low: '#161c23'
  surface-container: '#1a2027'
  surface-container-high: '#242a32'
  surface-container-highest: '#2f353d'
  on-surface: '#dde3ed'
  on-surface-variant: '#bbcabf'
  inverse-surface: '#dde3ed'
  inverse-on-surface: '#2b3139'
  outline: '#86948a'
  outline-variant: '#3c4a42'
  surface-tint: '#4edea3'
  primary: '#4edea3'
  on-primary: '#003824'
  primary-container: '#10b981'
  on-primary-container: '#00422b'
  inverse-primary: '#006c49'
  secondary: '#4cd7f6'
  on-secondary: '#003640'
  secondary-container: '#03b5d3'
  on-secondary-container: '#00424e'
  tertiary: '#ffb95f'
  on-tertiary: '#472a00'
  tertiary-container: '#e29100'
  on-tertiary-container: '#523200'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#6ffbbe'
  primary-fixed-dim: '#4edea3'
  on-primary-fixed: '#002113'
  on-primary-fixed-variant: '#005236'
  secondary-fixed: '#acedff'
  secondary-fixed-dim: '#4cd7f6'
  on-secondary-fixed: '#001f26'
  on-secondary-fixed-variant: '#004e5c'
  tertiary-fixed: '#ffddb8'
  tertiary-fixed-dim: '#ffb95f'
  on-tertiary-fixed: '#2a1700'
  on-tertiary-fixed-variant: '#653e00'
  background: '#0e141b'
  on-background: '#dde3ed'
  surface-variant: '#2f353d'
typography:
  display-lg:
    fontFamily: Space Grotesk
    fontSize: 3rem
    fontWeight: '700'
    lineHeight: 3.5rem
    letterSpacing: -0.03em
  display-lg-mobile:
    fontFamily: Space Grotesk
    fontSize: 2.25rem
    fontWeight: '700'
    lineHeight: 2.75rem
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Space Grotesk
    fontSize: 2rem
    fontWeight: '600'
    lineHeight: 2.5rem
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Space Grotesk
    fontSize: 1.5rem
    fontWeight: '600'
    lineHeight: 2rem
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Space Grotesk
    fontSize: 1.25rem
    fontWeight: '600'
    lineHeight: 1.75rem
    letterSpacing: 0em
  title-md:
    fontFamily: Inter
    fontSize: 1.125rem
    fontWeight: '600'
    lineHeight: 1.5rem
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 1rem
    fontWeight: '400'
    lineHeight: 1.5rem
    letterSpacing: 0em
  body-md:
    fontFamily: Inter
    fontSize: 0.875rem
    fontWeight: '400'
    lineHeight: 1.25rem
    letterSpacing: 0.01em
  body-sm:
    fontFamily: Inter
    fontSize: 0.75rem
    fontWeight: '400'
    lineHeight: 1rem
    letterSpacing: 0.01em
  telemetry-value:
    fontFamily: JetBrains Mono
    fontSize: 1.5rem
    fontWeight: '500'
    lineHeight: 1.75rem
    letterSpacing: -0.02em
  label-mono-md:
    fontFamily: JetBrains Mono
    fontSize: 0.8125rem
    fontWeight: '500'
    lineHeight: 1.125rem
    letterSpacing: 0.04em
  label-mono-sm:
    fontFamily: JetBrains Mono
    fontSize: 0.6875rem
    fontWeight: '500'
    lineHeight: 0.875rem
    letterSpacing: 0.06em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-lg: 1.5rem
  margin: 1rem
  margin-md: 1.5rem
  margin-lg: 2rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

This design system delivers an operational, command-grade interface built for urban resilience teams, municipal infrastructure directors, and climatological sensor analysts. The design aesthetic balances **tactical precision minimalism** with **restrained glassmorphism**, prioritizing rapid telemetry interpretation, spatial hierarchy, and zero-distraction situational awareness under critical thermal surge conditions.

The visual language draws inspiration from mission control telemetry decks, geospatial monitoring nodes, and aerospace instrumentation:
- **Tone:** Authoritative, vigilant, surgical, and hyper-reliable.
- **Visual Stance:** Dark-graphite base fields punctuated by high-luminance sensor accents and calibrated alert states.
- **Behavioral Intent:** Dense data visualization without cognitive strain; strict demarcation between nominal operations, dynamic cooling interventions, and hazardous surface heat anomalies.

## Colors

The palette leverages deep, low-reflectance carbon substrates paired with high-luminance emissive accents to ensure high-contrast readability across command center displays and mobile field tablets.

### Functional Roles
- **Primary (`#10B981` / Emerald):** Indicates nominal sensor operations, active microclimate stabilization systems, normal cooling grid outputs, and verified urban canopy integrity.
- **Secondary (`#06B6D4` / Cyan):** Real-time spatial telemetry, live hydrological flows, sensor pings, active radar traces, and navigational anchors.
- **Tertiary (`#F59E0B` / Warning Amber):** Thermal accumulation warnings, surface temperature threshold excursions, and advisory sensor diagnostics.
- **Critical / Danger (`#EF4444` / Crimson):** Extreme urban heat island (UHI) events, grid breakdown risks, heatstroke danger thresholds, and sensor hardware failures.
- **Neutral Palette (`#0B0F12`, `#12181F`, `#18222C`):**
  - Surface Void / Base: `#0B0F12`
  - Surface Elevation 1 (Cards, toolbars): `#12181F`
  - Surface Elevation 2 (Elevated modals, flyouts, radar frames): `#18222C`
  - Border and Separator Stroke: `#22313F` at 60% opacity for tactical edge delineation.
  - Text Primary: `#F1F5F9`
  - Text Secondary: `#94A3B8`
  - Text Muted: `#64748B`

## Typography

Typography establishes an unambiguous tripartite hierarchy:
1. **Space Grotesk** anchors critical displays, section titles, and macro-level intelligence readouts, imparting a structured, futuristic, and architectural tone.
2. **Inter** ensures friction-free scanning across analytical narratives, diagnostic logs, and form inputs.
3. **JetBrains Mono** delivers fixed-pitch alignment across tabular datasets, coordinates, thermal readings, sensor latency figures, and technical status pills.

Numbers must always render with tabular lining figures (`tnum`) in dense data views to eliminate horizontal jitter when values update in real time.

## Layout & Spacing

The dashboard operates on a strict **12-column modular grid** optimized for high-density multi-pane monitoring consoles and adaptable telemetry workflows.

- **Breakpoints:**
  - `Mobile` (< 768px): 4-column layout; gutter `1rem`; horizontal outer margin `1rem`. Side navigation collapses into an anchored command bar.
  - `Tablet` (768px - 1199px): 8-column layout; gutter `1rem`; outer margin `1.5rem`. Secondary sensor rails shift to contextual sheets.
  - `Desktop / Command Wall` (≥ 1200px): 12-column dynamic framework; gutter `1.5rem`; outer margin `2rem`. Supports triple-column persistent arrangements (Navigation / Geospatial Canvas / Real-Time Telemetry Inspector).

Spacing scales operate on an 8pt base unit (with a 4pt micro-unit for compact hardware data tables). Components are packed deliberately tight to prioritize screen real estate for spatial mapping and temporal trend curves.

## Elevation & Depth

Visual depth is achieved through **tonal stratification and frosted-glass refraction** rather than high-deflection drop shadows, maintaining an authentic tactical instrument aesthetic.

- **Surface Tier 0 (Base Canvas):** `#0B0F12` solid fill. Host layer for geospatial GIS maps and vector radar sweeps.
- **Surface Tier 1 (Docked Containers & Grid Cards):** `#12181F` with a backdrop blur of `12px` and an alpha transparency of 85% (`rgba(18, 24, 31, 0.85)`). Surrounded by a sub-pixel border of `1px solid rgba(148, 163, 184, 0.12)`.
- **Surface Tier 2 (Floating Inspect Panels, Flyouts):** `#18222C` with `16px` blur (`rgba(24, 34, 44, 0.9)`), edged with `1px solid rgba(6, 182, 212, 0.25)`.
- **Telemetry Glows:** Elevation under critical or warning events is accentuated via localized ambient backlighting:
  - Nominal: `0 0 16px rgba(16, 185, 129, 0.15)`
  - Alert / Surge: `0 0 20px rgba(239, 68, 68, 0.25)`
  - Active Scanning: `0 0 16px rgba(6, 182, 212, 0.2)`

## Shapes

The design system employs a **Soft (0.25rem / 4px base)** corner language across micro-components, escalating to `0.5rem` (8px) for containers and data panels.

- Structural cards, buttons, and telemetry cells feature subtle, technical rounding that reflects modern avionics hardware.
- Circular radii (`rounded-full`) are reserved strictly for circular status beacons, radar reticles, and pulse transmitters.
- Sharp diagonal corner cuts (chamfers at 45 degrees) are permitted solely on primary map coordinate readouts and alert badges to evoke precision instrumentation.

## Components

### Buttons
- **Primary Action (Active Intervention / Scan):** Solid `#10B981` background, `#0B0F12` text, `JetBrains Mono` medium 12px uppercase typography. Hover introduces a high-luminance border halo (`rgba(16, 185, 129, 0.4)`).
- **Secondary (Telemetry Toggles):** Transparent background, `1px solid rgba(6, 182, 212, 0.4)` stroke, `#06B6D4` text. Hover shifts background to `rgba(6, 182, 212, 0.1)`.
- **Destructive / Emergency Override:** Deep crimson border with `#EF4444` label; on click, initiates confirmation modal with animated warning stripe borders.

### Chips & Sensor Badges
- Constructed with `label-mono-sm` font, `4px` padding inline, `2px` padding block.
- Feature a leading 6px pulsing dot denoting node freshness:
  - Online / Nominal: Solid Emerald dot with `ping` keyframe animation.
  - Heat Warning: Amber dot, steady glow.
  - Thermal Excursion: Crimson dot, high-frequency pulse.

### Cards & Data Panels
- Background: Translucent graphite (`#12181F` at 85%), `backdrop-filter: blur(12px)`.
- Top header section features a technical separator: `1px solid rgba(148, 163, 184, 0.08)`.
- Headers host title in `Space Grotesk` alongside coordinates or sensor IDs in `JetBrains Mono` muted gray.

### Inputs & Selectors
- Background: `#0B0F12`, border: `1px solid #22313F`.
- Typography: `Inter` 14px for user input, labels rendered in `JetBrains Mono` 11px uppercase (`#94A3B8`).
- Focus state: Border transitions to `#06B6D4` with an inner glow of `0 0 0 1px rgba(6, 182, 212, 0.3)`.

### Checkboxes & Segmented Controls
- Binary toggles feature technical geometric indicators: square checkboxes with a glowing crosshair or checkmark in `#10B981`.
- Layer control switches use segmented horizontal bars with crisp divider ticks.

### Domain-Specific Components
- **Radar Sweeper:** Circular radar component with concentric degree rings (`#22313F`), a rotational 360-degree sweep gradient fading from `#06B6D4` (25% opacity) to 0%, and plotted heat coordinate pings.
- **Thermal Heat Strip:** Continuous or segmented gradient track (`#10B981` -> `#06B6D4` -> `#F59E0B` -> `#EF4444`) with fixed-width indicator pins displaying microclimate surface temperatures in Celsius/Fahrenheit.
- **Sensor Telemetry Tile:** Compact card showcasing metric label, live value in `telemetry-value`, mini sparkline rendered in primary green or alert amber, and variance delta percentage.