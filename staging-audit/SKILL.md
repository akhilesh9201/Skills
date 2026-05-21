---
name: staging-audit
description: "Use this skill to run a post-handoff design QA audit comparing Figma designs against a staging environment build. Trigger when a designer wants to compare their Figma frames or flows to what developers have built on staging, check if the staging build matches the design specs, produce a design inconsistency report, audit a live or staging URL against Figma, or generate a handoff QA document. Also trigger for phrases like 'staging audit', 'design QA', 'check the staging build', 'compare figma to staging', 'post-handoff review', or 'design review on staging'. Outputs a professional XLSX report with embedded side-by-side screenshots, inconsistency descriptions, and severity rankings ready to share with the development team."
---

# Staging Audit — Design QA Skill

You are running a structured design QA audit. Your job is to compare a Figma annotated flow against the corresponding screens in a staging build, then output a professional XLSX inconsistency report.

## What you need from the user

Ask for these upfront if not provided:

1. **Figma section URL** — a Figma page or section URL containing the annotated flow (frames with arrows and labels showing the user journey)
2. **Staging base URL** — the base URL of the staging environment (e.g., `https://staging.myapp.com`)
3. **Navigation mode** — ask the user:
   - "Do you want me to navigate autonomously? If so, provide the steps and any login credentials needed."
   - "Or would you prefer to navigate yourself while I observe and capture?"
4. **Output path** (optional) — where to save the XLSX; default is the current working directory

## Operating modes

### Autonomous Mode
The user provides navigation steps and credentials. You drive the browser:
- Use the available browser automation tool (Claude in Chrome) to navigate to the staging URL
- Follow the user's navigation instructions step by step
- Capture a full-page screenshot at each meaningful screen/state
- Map each screenshot to the corresponding Figma frame by name

### Observation Mode
The user navigates manually. You observe:
- Ask the user: "Please tell me the names of each screen in order (matching your Figma frame names). For example: Login → Dashboard → Settings → Profile"
- Instruct the user to open the staging build in their browser and navigate through the journey at a natural pace
- Monitor URL changes using browser automation tools — capture a screenshot automatically each time the URL changes
- Map screenshots to Figma frames in the order the user declared upfront
- If a screen requires interaction before the URL changes (e.g., a modal), tell the user: "I'll capture when you say 'mark this'" as a fallback

## Step-by-step workflow

### Step 1: Read the Figma flow

Use the Figma MCP tool to read the Figma section URL:
- Request the design context for the provided URL
- Extract all frame names, their order, any annotations, and arrows that define the journey sequence
- Note any copy, component names, colors, and layout details visible in each frame
- Take a screenshot of each frame using the Figma MCP screenshot tool

Store an ordered list: `[{ frame_name, figma_screenshot, annotations }]`

### Step 2: Capture staging screens

**In Autonomous Mode:**
- Navigate to the staging URL using browser automation
- Follow each navigation step provided by the user
- After each step lands on a new screen, take a full-page screenshot
- Label each screenshot with the frame name it corresponds to

**In Observation Mode:**
- Monitor for URL changes as the user navigates
- Capture a screenshot on each URL change
- Map screenshots to the pre-declared frame names in order

Store a parallel list: `[{ frame_name, staging_screenshot, url }]`

### Step 3: Compare and identify inconsistencies

For each frame/screen pair, analyze side by side. Flag inconsistencies in these categories:

**Visual**
- Colors (background, text, borders, icons — compare hex values where possible)
- Typography (font family, size, weight, line height, letter spacing)
- Spacing (padding, margin, gap between elements)
- Shadows, border radius, opacity

**Copy**
- Wrong or missing text
- Incorrect labels or button text
- Placeholder copy that should be replaced
- Missing microcopy or error messages

**Layout**
- Missing components or sections
- Extra components not in the design
- Sections that appear/disappear incorrectly
- Do NOT flag wrong element order — this is expected to vary and is too noisy

**Severity guide:**
- **Critical** — feature is broken or completely wrong (missing entire section, wrong page loaded, broken interaction)
- **Major** — clearly visible and would be noticed by a user (wrong color, missing component, wrong copy)
- **Minor** — subtle polish issues (1-2px spacing off, slightly wrong font weight, shadow missing)

For each inconsistency, record:
- Which frame it occurred on
- A clear one-sentence description of what is different
- The severity (Critical / Major / Minor)
- The cropped region showing the inconsistency (you'll use this for the image callout in Step 4)

### Step 4: Compose the image references

For each inconsistency row, create a side-by-side image:
- **Left half:** the relevant Figma frame screenshot (full frame)
- **Right half:** the corresponding staging screenshot (full page)
- **Callout inset:** a cropped, zoomed-in section highlighting exactly where the issue is (drawn from the staging screenshot, with a red rectangle border)

Use the `scripts/compose_images.py` script to generate these composite images. Pass it the two screenshot paths and the crop coordinates of the inconsistency region.

```bash
python scripts/compose_images.py \
  --figma figma_frame.png \
  --staging staging_screen.png \
  --crop x1,y1,x2,y2 \
  --output row_N_image.png
```

Save all composed images to a temporary working directory.

### Step 5: Build the XLSX report

Use openpyxl to create the XLSX file. Use `scripts/create_audit.py` to build it.

**Column headers (row 1):**
`Sr No | Occurred on | Image reference | Issue identified | Priority | Dev comments | Designer sign-off`

**Column widths:**
- Sr No: 8
- Occurred on: 25
- Image reference: 60 (wide to fit the embedded images)
- Issue identified: 50
- Priority: 15
- Dev comments: 35
- Designer sign-off: 25

**Row height:** Set each data row to 120pt height to accommodate the embedded images.

**For each inconsistency row:**
- Sr No: sequential integer
- Occurred on: frame name (e.g., "Login Screen", "Dashboard")
- Image reference: embed the composed side-by-side PNG using openpyxl's `add_image`
- Issue identified: clear description
- Priority: Critical / Major / Minor (use conditional color: red for Critical, orange for Major, yellow for Minor)
- Dev comments: empty, light grey background
- Designer sign-off: empty, light grey background

**Header row styling:**
- Bold, dark background (#1A1A2E), white text, centered

**Alternating row colors:** light grey (#F5F5F5) and white for readability.

```bash
python scripts/create_audit.py \
  --data audit_data.json \
  --images-dir ./audit_images/ \
  --output staging-audit-YYYY-MM-DD.xlsx
```

### Step 6: Save and notify

1. Save the XLSX to the **current working directory** with a timestamped filename:
   `staging-audit-{YYYY-MM-DD}.xlsx`

2. Also save a backup copy to `~/.claude/staging-audits/` (create this directory if it doesn't exist):
   ```bash
   mkdir -p ~/.claude/staging-audits
   cp staging-audit-*.xlsx ~/.claude/staging-audits/
   ```

3. Tell the user:
   ```
   Audit complete. Found X inconsistencies across Y screens.
   
   Saved to:
   - ./staging-audit-YYYY-MM-DD.xlsx  (working directory)
   - ~/.claude/staging-audits/staging-audit-YYYY-MM-DD.xlsx  (backup)
   
   Summary:
   - Critical: N
   - Major: N
   - Minor: N
   ```

## Edge cases

- **Can't reach the staging URL:** Inform the user and suggest switching to Observation Mode or checking VPN/credentials.
- **Figma frame has no direct staging equivalent:** Note it in the audit as "No staging counterpart found" with Critical severity.
- **Staging screen has no Figma frame:** Note it as "Undocumented screen — no design reference" and include it at the end of the report.
- **Authentication required and not provided:** Prompt the user for credentials or switch to Observation Mode.
- **Screenshot fails:** Retry once; if it fails again, insert a placeholder row with "Screenshot capture failed" and continue.

## Important notes

- Focus on real, observable differences — not theoretical or pixel-perfect pedantry. If something would be noticed by a real user, flag it.
- When in doubt about severity, lean toward Major rather than Minor — it's better for developers to see a flagged item than miss a real issue.
- Be concise in the "Issue identified" column: "Button background is #E63946 in Figma, #FF0000 on staging" is better than a paragraph.
- Empty "Dev comments" and "Designer sign-off" columns are intentional — they are for the team to fill in asynchronously.
