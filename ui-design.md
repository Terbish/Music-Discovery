# Daily Discovery Album Tools — Design System

## Overview
A modern, minimalist desktop application UI that bridges a powerful Python backend with an intuitive cross-platform experience. The design language now centers on a Swiss-inspired ruled grid: precise enough for library management, but with a light scratch book quality that fits music discovery and ongoing curation.

---

## Philosophy

- **Clarity First**: Every action has a clear purpose. No decorative noise.
- **Respect the Content**: Music metadata, genres, and artwork are the heroes. UI recedes.
- **Ruled Workspace**: Every major page uses the same visible grid background, like a clean working notebook for music data.
- **Cross-Platform Native Feel**: Uses a restrained desktop shell and predictable controls without mimicking a single OS.
- **Progressive Disclosure**: Simple by default, powerful when needed.

---

## Color Palette

### Primary Colors
| Token | Hex | Usage |
|-------|-----|-------|
| `primary` | `#0A0A0A` | Primary text, active states, key buttons |
| `primary-muted` | `#6B6B6B` | Secondary text, icons, inactive tabs |
| `accent` | `#FF6B35` | Accent actions, progress indicators, genre highlights |
| `accent-hover` | `#E55A2B` | Accent hover state |

### Background Colors
| Token | Hex | Usage |
|-------|-----|-------|
| `bg-base` | `#FFFFFF` | Main window background |
| `bg-elevated` | `#F5F5F7` | Cards, panels, sidebar (macOS vibe) |
| `bg-pressed` | `#E8E8ED` | Pressed states, selected rows |
| `bg-overlay` | `rgba(255,255,255,0.85)` | Modals, popovers with backdrop blur |
| `grid-line` | `#D9D9DE` | 48px ruled page grid on content surfaces |

### Semantic Colors
| Token | Hex | Usage |
|-------|-----|-------|
| `success` | `#34C759` | Completed tasks, success states |
| `warning` | `#FF9500` | Warnings, pending actions |
| `error` | `#FF3B30` | Errors, failed downloads |
| `info` | `#007AFF` | Informational badges |

### Genre Color Mapping (Data Visualization)
A restrained categorical palette for genre tags and charts:
- Rock: `#FF6B35` (accent)
- Electronic: `#5856D6`
- Jazz: `#FFCC00`
- Classical: `#8E8E93`
- Hip-Hop: `#AF52DE`
- Pop: `#FF2D55`
- Folk: `#34C759`
- Metal: `#5AC8FA`
- Default: `#C7C7CC`

---

## Typography

### Font Stack
```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
```
Uses system fonts for native rendering on both macOS (San Francisco) and Windows (Segoe UI).

### Type Scale
| Token | Size | Weight | Line Height | Usage |
|-------|------|--------|-------------|-------|
| `display` | 28px | 700 | 1.2 | Empty states, welcome headers |
| `title-1` | 22px | 600 | 1.3 | Page titles, major sections |
| `title-2` | 17px | 600 | 1.3 | Card titles, panel headers |
| `title-3` | 15px | 600 | 1.4 | List headers, subsections |
| `body` | 13px | 400 | 1.5 | Primary body text |
| `body-small` | 12px | 400 | 1.5 | Secondary descriptions |
| `caption` | 11px | 500 | 1.4 | Tags, badges, metadata labels |
| `mono` | 12px | 400 | 1.4 | File paths, technical data |

---

## Spacing System

Base unit: **4px**

| Token | Value | Usage |
|-------|-------|-------|
| `space-1` | 4px | Tight internal padding, icon gaps |
| `space-2` | 8px | Button padding, inline spacing |
| `space-3` | 12px | Card internal padding |
| `space-4` | 16px | Standard section padding |
| `space-5` | 20px | Dialog padding |
| `space-6` | 24px | Major section separation |
| `space-8` | 32px | Page-level margins |
| `space-10` | 40px | Hero spacing |

---

## Layout Grid

- **Window Min Width**: 900px
- **Window Min Height**: 600px
- **App Shell**: Fixed to the viewport height; the window itself should not page-scroll.
- **Sidebar Width**: 220px (collapsible to 64px)
- **Sidebar Behavior**: Non-scrollable, full-height left rail. Only the right-side content area scrolls.
- **Content Surface**: All pages use the same 48px ruled grid background: two 1px linear gradients over `bg-base`.
- **Content Max Width**: 1200px (centered with auto margins in wide windows)
- **Card Grid**: Responsive CSS Grid, minmax(280px, 1fr)

---

## Components

### Buttons

**Primary Button**
- Background: `primary` (#0A0A0A)
- Text: `#FFFFFF`, `body` size, weight 500
- Padding: `space-2` vertical, `space-3` horizontal
- Border Radius: 8px
- Hover: Scale 1.02, background lightens to `#1A1A1A`
- Active: Scale 0.98, background `#333333`
- Transition: all 150ms cubic-bezier(0.25, 0.1, 0.25, 1)

**Secondary Button**
- Background: `bg-elevated`
- Text: `primary`
- Border: 1px solid `#E5E5EA`
- Same radius and padding as Primary

**Ghost Button**
- Background: transparent
- Text: `primary-muted`
- Hover: background `bg-elevated`, text `primary`

**Icon Button**
- Size: 32px × 32px
- Border Radius: 8px
- Contains 16px icon

### Inputs

**Text Field**
- Background: `bg-elevated`
- Border: 1px solid `#E5E5EA`
- Border Radius: 8px
- Padding: `space-2` `space-3`
- Font: `body`
- Focus: border `accent`, subtle inner glow
- Placeholder: `primary-muted` at 60% opacity

**File Drop Zone**
- Border: 2px dashed `#D1D1D6`
- Border Radius: 12px
- Background: `bg-elevated`
- Padding: `space-8`
- Hover: border `accent`, background `rgba(255,107,53,0.04)`
- Active/Dragover: border `accent`, background `rgba(255,107,53,0.08)`

### Cards

**Standard Card**
- Background: `bg-base`
- Border: 1px solid `primary`
- Border Radius: 0px
- Padding: `space-4`
- Shadow: none
- Hover: border color may shift to `accent`; avoid floating card effects

**Track Card**
- Horizontal layout: 48px artwork + text column + action buttons
- Artwork: 48px, border-radius 6px, object-fit cover
- Title: `title-3`
- Artist/Album: `body-small` in `primary-muted`
- Genre tags: `caption` pills

### Lists

**Table / List View**
- Row height: 44px
- Hover background: `bg-elevated`
- Selected background: `bg-pressed`
- Selected left border: 3px `accent`
- Divider: 1px solid `#F2F2F7` (subtle)

### Badges & Tags

**Genre Tag**
- Background: tinted version of genre color at 12% opacity
- Text: genre color at full opacity
- Padding: 2px 8px
- Border Radius: 4px
- Font: `caption`, weight 600

**Status Badge**
- Size: fits content
- Pill shape (border-radius 999px)
- Uses semantic colors for background (10% opacity) and text

### Progress Indicators

**Linear Progress**
- Height: 4px
- Background track: `#E5E5EA`
- Fill: `accent`
- Border Radius: 2px
- Animated with indeterminate state for unknown duration

**Circular Progress**
- Size: 24px
- Stroke: 3px
- Color: `accent`
- Used in buttons and inline status

### Modals & Overlays

**Modal**
- Background: `bg-overlay`
- Backdrop: `rgba(0,0,0,0.3)` with `backdrop-filter: blur(12px)`
- Border Radius: 16px
- Shadow: `0 20px 60px rgba(0,0,0,0.15)`
- Padding: `space-6`
- Max Width: 520px

**Toast / Notification**
- Position: bottom-right, stacked
- Background: `primary` with 90% opacity
- Text: white
- Border Radius: 10px
- Padding: `space-3` `space-4`
- Auto-dismiss: 4 seconds

---

## Icons

- **Style**: Outlined, 1.5px stroke, 24×24 viewBox
- **Library**: Custom SVG set + Lucide-style semantics
- **Sizes**: 16px (inline), 20px (navigation), 24px (empty states)

### Key Icons
- Home / Dashboard
- Library (vinyl/disc metaphor)
- Chart / Analytics (waveform)
- Download / Cloud
- Settings / Gear
- Play, Pause, Refresh, Check, X, Chevron, Search, Filter

---

## Motion & Animation

### Easing
| Name | Value | Usage |
|------|-------|-------|
| `ease-standard` | `cubic-bezier(0.25, 0.1, 0.25, 1)` | General transitions |
| `ease-enter` | `cubic-bezier(0, 0, 0.2, 1)` | Elements entering |
| `ease-exit` | `cubic-bezier(0.4, 0, 1, 1)` | Elements exiting |
| `ease-spring` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | Playful bounces |

### Durations
- Micro (hover, focus): 150ms
- Standard (layout changes): 250ms
- Emphasis (page transitions, modals): 350ms

### Patterns
- **Page Transition**: Fade + slight translateY(8px → 0)
- **List Item Enter**: Staggered fade-in, 50ms delay between items
- **Modal**: Scale(0.95 → 1) + fade, backdrop fade
- **Progress**: Smooth width transition, 300ms
- **Skeleton**: Shimmer animation, 1.5s cycle

---

## Specific Screen Guidelines

### Dashboard
- Hero stat cards: 4-column grid showing Library Size, Top Genre, Discovery Streak, Pending Downloads
- Recent Activity feed: chronological list with icons
- Quick Action buttons: prominent row for "Import Library", "Run Discovery", "View Taste Profile"

### Library View
- Dual-pane: Filter sidebar (left) + Scrollable track list (right)
- Filter sidebar: Search, Genre multi-select, Artist autocomplete
- Track list: Sortable columns (Title, Artist, Album, Genre, Date Added)
- Bulk actions: Select all, Export, Enrich Genres

### Taste Profile
- Visual summary: Donut chart for genre distribution, horizontal bar chart for top artists
- Key insight cards: "Your #1 Genre", "Discovery Diversity Score", "Era Preference"
- Genre explorer: Clickable grid of genre cards showing percentage and sample tracks

### Discovery
- Batch header: Date, track count, batch status
- Track cards with preview capability (simulated)
- Download queue: Inline progress per track
- "Refresh Batch" action with confirmation modal

### Settings
- Grouped sections: General, Paths, Audio Quality, API Preferences, About
- Toggle switches: 44px wide, 24px tall, `accent` when on
- Path inputs: Text field with "Browse" button, monospace font for paths

---

## Accessibility

- Minimum contrast ratio: 4.5:1 for all text
- Focus rings: 2px solid `accent` with 2px offset
- Reduced motion: Respect `prefers-reduced-motion`, disable transforms
- Keyboard navigation: Full tab order, arrow keys for lists, Enter/Space for activation
