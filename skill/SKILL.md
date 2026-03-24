---
name: logic-flow
description: "Generate interactive logic flow diagram JSON for the Logic Flow Editor. Use this skill whenever the user asks to create a flowchart, logic flow, process diagram, decision tree, state machine diagram, workflow chart, or any kind of node-and-arrow diagram. Also trigger when the user says things like 'draw me a flow', 'map out the logic', 'diagram this process', 'show the flow for', 'create a flowchart for', or provides a description of steps/decisions they want visualized. Even casual requests like 'can you sketch the logic for X' or 'what would the flow look like for Y' should trigger this skill."
---

# Logic Flow Diagram Generator

You generate flow diagrams by writing JSON directly to a data file that the Logic Flow Editor auto-loads. This works like an MCP — you write the file, the editor polls it every 2 seconds and live-reloads.

## How It Works — Bidirectional Sync

The editor and Claude share `C:/Users/localadmin/logic-flow-data.json` as a live data file:

- **Claude → Editor**: You write the JSON file, the editor polls every 2s and auto-loads changes
- **Editor → Claude**: User edits in the browser auto-save back to the same JSON file via the server

This means the user never needs to manually save, export, or copy-paste anything. They edit in the browser, then ask you to iterate, and you just read the current file to see their changes.

### Workflow

1. **Ensure the server is running** (see Step 0)
2. User describes what they want diagrammed
3. You generate the JSON and **write it directly** to `C:/Users/localadmin/logic-flow-data.json` using the Write tool
4. The editor auto-loads it within 2 seconds
5. User edits the diagram visually (moves nodes, adds connections, edits text, etc.)
6. Their changes auto-save back to `logic-flow-data.json` (500ms debounce)
7. When the user asks you to iterate, **read `logic-flow-data.json` first** to see their latest changes, then modify and write it back

**Important**: Always use the Write tool to write the JSON file. Never output JSON for the user to copy-paste.

**Critical**: When iterating on an existing diagram, ALWAYS read `C:/Users/localadmin/logic-flow-data.json` first to pick up the user's edits. Never assume the file is the same as what you last wrote — the user may have moved nodes, changed text, added connections, etc.

## Step 0: Start the Local Server

The editor uses a custom Python server (`logic-flow-server.py`) that handles both serving files AND saving edits back. **Before doing anything else**, check if the server is already running, and start it if not:

```bash
# Check if already running
curl -s http://localhost:8000/logic-flow-editor.html > /dev/null 2>&1 && echo "RUNNING" || echo "NOT RUNNING"
```

If NOT RUNNING, start it in the background:

```bash
cd /c/Users/localadmin && python logic-flow-server.py
```

Run this with `run_in_background: true` so it doesn't block. The server auto-opens the editor in the browser.

If the server is already running, skip straight to generating the diagram.

## After Writing the JSON

Tell the user:
- If the editor is already open: "Diagram updated — it'll auto-load in a moment."
- First time: "Server started and editor opened at http://localhost:8000/logic-flow-editor.html — diagram is loading now."
- If iterating: "I've read your changes and updated the diagram — check the editor."

## JSON Schema

```json
{
  "version": 1,
  "nodes": [
    {
      "id": "n1",
      "type": "process",
      "x": 100,
      "y": 100,
      "width": 180,
      "height": 70,
      "text": "Node Label",
      "color": "#264f78",
      "textColor": "#ffffff",
      "fontSize": 14
    }
  ],
  "connections": [
    {
      "id": "c1",
      "from": "n1",
      "fromPort": "bottom",
      "to": "n2",
      "toPort": "top",
      "label": "",
      "color": "#569cd6",
      "lineStyle": "solid"
    }
  ]
}
```

## Node Types and Default Colors

| Type | Shape | Default Color | Use For |
|------|-------|--------------|---------|
| `startend` | Stadium (rounded pill) | `#2d7d46` | Start, End, Terminal states |
| `process` | Rectangle | `#264f78` | Actions, steps, operations |
| `decision` | Diamond | `#6a4c93` | Yes/No questions, conditionals, branching |
| `io` | Parallelogram | `#8a5d3b` | Input, output, data, API calls, user interaction |
| `comment` | Dashed rectangle | `#4a4a2a` | Notes, annotations, explanations |

Use custom colors when it helps readability — e.g., `#a03030` for error states, `#c8a820` for SIMPL/control signals, `#c43670` for feedback paths. Always keep `textColor: "#ffffff"` for readability on dark backgrounds (use `"#000000"` on light/yellow backgrounds).

## Ports

Each node has 4 connection ports: `top`, `bottom`, `left`, `right`.

- **Top-to-bottom flows**: Use `bottom` → `top` for the main downward flow
- **Branches from decisions**: Use `right` or `left` for alternate paths, `bottom` for main path
- **Loops back**: Use side ports going back up (e.g., `fromPort: "top"` → `toPort: "right"`)
- **Fan-out from one node**: Use `bottom` port for all — the editor routes them automatically

## Layout Rules

### Spacing
- **Vertical spacing**: 130-150px between node rows
- **Horizontal spacing**: 220-250px between nodes on the same row (branches)
- **Center the main flow** around x=300

### Node Sizing
- **Start/End**: `width: 140, height: 50-60`
- **Process**: `width: 180, height: 70`
- **Decision**: `width: 160, height: 120` (needs room for diamond)
- **IO**: `width: 180, height: 70`
- **Comment**: `width: 200, height: 60`

### Decision Branching
- Main/happy path goes **down** (`bottom` port), labeled `"Yes"` with color `"#4ec970"`
- Alternate/error path goes **right** or **left**, labeled `"No"` with color `"#d64545"`
- Use `lineStyle: "dashed"` for loop-back connections

### ID Convention
- Nodes: `n1`, `n2`, `n3`, ... (use `n10`, `n20` etc. for branch groups)
- Connections: `c1`, `c2`, `c3`, ... (match numbering to node groups)

## Complex Diagrams

For larger flows with multiple branches (like the AFP touchpanel example):
- Keep the main startup/happy path as a straight vertical line down the center
- Fan out branches horizontally at the same y-level, spaced 220-250px apart
- Each branch column flows straight down independently
- Use consistent color coding across branches to show categories (user action, control, feedback, UI)
- Group related nodes by column — one column per interaction type
- Use comment nodes sparingly for annotations

## What NOT to Do

- Don't output JSON in the chat — write it to the file with the Write tool
- Don't use node IDs that could collide
- Don't make nodes overlap — check x/y coordinates and sizes
- Don't forget connections — every node except comments should have at least one
- Don't put all branch nodes at the same x coordinate — spread them out horizontally
