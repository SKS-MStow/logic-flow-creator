---
name: logic-flow
description: "Generate interactive logic flow diagram JSON for the Logic Flow Editor. Use this skill whenever the user asks to create a flowchart, logic flow, process diagram, decision tree, state machine diagram, workflow chart, or any kind of node-and-arrow diagram. Also trigger when the user says things like 'draw me a flow', 'map out the logic', 'diagram this process', 'show the flow for', 'create a flowchart for', or provides a description of steps/decisions they want visualized. Even casual requests like 'can you sketch the logic for X' or 'what would the flow look like for Y' should trigger this skill."
---

# Logic Flow Diagram Generator

You generate flow diagrams by writing JSON directly to a data file that the Logic Flow Editor auto-loads. This works like an MCP — you write the file, the editor polls it every 2 seconds and live-reloads.

## How It Works — Bidirectional Sync

The editor and Claude share `C:/Users/Mark/Documents/logic-flow-data.json` as a live data file:

- **Claude → Editor**: You write the JSON file, the editor polls every 2s and auto-loads changes
- **Editor → Claude**: User edits in the browser auto-save back to the same JSON file via the server

This means the user never needs to manually save, export, or copy-paste anything. They edit in the browser, then ask you to iterate, and you just read the current file to see their changes.

### Workflow

1. **Ensure the server is running** (see Step 0)
2. User describes what they want diagrammed
3. You generate the JSON and **write it directly** to `C:/Users/Mark/Documents/logic-flow-data.json` using the Write tool
4. The editor auto-loads it within 2 seconds
5. User edits the diagram visually (moves nodes, adds connections, edits text, etc.)
6. Their changes auto-save back to `logic-flow-data.json` (500ms debounce)
7. When the user asks you to iterate, **read `logic-flow-data.json` first** to see their latest changes, then modify and write it back

**Important**: Always use the Write tool to write the JSON file. Never output JSON for the user to copy-paste.

**Critical**: When iterating on an existing diagram, ALWAYS read `C:/Users/Mark/Documents/logic-flow-data.json` first to pick up the user's edits. Never assume the file is the same as what you last wrote — the user may have moved nodes, changed text, added connections, etc.

## Step 0: Start the Local Server

The editor uses a custom Python server (`logic-flow-server.py`) that handles both serving files AND saving edits back. **Before doing anything else**, check if the server is already running, and start it if not:

```bash
# Check if already running
curl -s http://localhost:8000/logic-flow-editor.html > /dev/null 2>&1 && echo "RUNNING" || echo "NOT RUNNING"
```

If NOT RUNNING, start it in the background:

```bash
cd /c/Users/Mark/Documents && python logic-flow-server.py
```

Run this with `run_in_background: true` so it doesn't block. The server auto-opens the editor in the browser.

If the server is already running, skip straight to generating the diagram.

## Flow Sessions

Each diagram is a named "flow" stored in `C:/Users/Mark/Documents/logic-flows/<name>.json`. This means multiple diagrams can coexist without overwriting each other.

### Creating a new flow

When the user asks for a new diagram, pick a short descriptive kebab-case name (e.g., `afp-touchpanel`, `auth-flow`, `order-processing`). Write the JSON to:

```
C:/Users/Mark/Documents/logic-flows/<name>.json
```

Then tell the user to open (or it will auto-open):
```
http://localhost:8000/logic-flow-editor.html?flow=<name>
```

### Iterating on an existing flow

When the user asks to modify a diagram, read the flow file first:
```
C:/Users/Mark/Documents/logic-flows/<name>.json
```
This will include any edits the user made in the browser (they auto-save). Modify and write it back.

### Opening an existing flow

If the user wants to come back to a previous flow, they can click the flow name in the status bar to see all saved flows — or just navigate to `?flow=<name>`.

### After Writing the JSON

Tell the user:
- If the editor is already open on that flow: "Diagram updated — it'll auto-load in a moment."
- First time / new flow: "Flow created. Open http://localhost:8000/logic-flow-editor.html?flow=<name>"
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
| `question` | Rounded rect + ? badge | `#0e7c7b` | Questions from Claude — use when asking the user something |
| `answer` | Rounded rect + A badge + left accent | `#b85c1f` | User answers — drag in to respond to a question |

Use custom colors when it helps readability — e.g., `#a03030` for error states, `#c8a820` for SIMPL/control signals, `#c43670` for feedback paths. Always keep `textColor: "#ffffff"` for readability on dark backgrounds (use `"#000000"` on light/yellow backgrounds).

## Ports

Each node has 4 connection ports: `top`, `bottom`, `left`, `right`.

- **Top-to-bottom flows**: Use `bottom` → `top` for the main downward flow
- **Branches from decisions**: Use `right` or `left` for alternate paths, `bottom` for main path
- **Loops back**: Use side ports going back up (e.g., `fromPort: "top"` → `toPort: "right"`)
- **Fan-out from one node**: Use `bottom` port for all — the editor routes them automatically

## Layout Rules

### NO OVERLAPPING NODES — Critical Rule

Nodes and branches must NEVER overlap. This is the most important layout rule. Connection lines can cross, but node rectangles must never sit on top of each other.

Before finalizing the JSON, mentally check every node's bounding box (`x` to `x+width`, `y` to `y+height`) against every other node. If any two overlap, adjust positions. Common mistakes:
- A side branch column sits underneath the main flow column because the x-offset wasn't enough
- Decision "No" branches overlap with the next node in the main "Yes" path below
- Multiple fan-out branches at the same y-level are too close together — each branch column needs its own clear x-lane

**How to prevent overlaps with branches:**
1. First, lay out the main vertical flow down the center
2. For each branch point, calculate how wide the branch column will be (widest node + padding)
3. Space branch columns so that `column_x + max_node_width + 40px < next_column_x`
4. If a branch is tall (many nodes), make sure it doesn't extend into the y-range of the next section of the main flow

### Spacing
- **Vertical spacing**: 130-150px between node rows
- **Horizontal spacing**: 220-250px between branch columns (measured from left edge to left edge)
- **Center the main flow** around x=300
- **Minimum gap**: Always keep at least 40px between the right edge of one node and the left edge of another

### Node Sizing
- **Start/End**: `width: 140, height: 50-60`
- **Process**: `width: 180, height: 70`
- **Decision**: `width: 160, height: 120` (needs room for diamond)
- **IO**: `width: 180, height: 70`
- **Comment**: `width: 200, height: 60`
- **Question**: `width: 200, height: 90`
- **Answer**: `width: 200, height: 90`

### Decision Branching
- Main/happy path goes **down** (`bottom` port), labeled `"Yes"` with color `"#4ec970"`
- Alternate/error path goes **right** or **left**, labeled `"No"` with color `"#d64545"`
- Use `lineStyle: "dashed"` for loop-back connections

### ID Convention
- Nodes: `n1`, `n2`, `n3`, ... (use `n10`, `n20` etc. for branch groups)
- Connections: `c1`, `c2`, `c3`, ... (match numbering to node groups)

## Complex Diagrams

For larger flows with multiple branches:
- Keep the main startup/happy path as a straight vertical line down the center
- Fan out branches horizontally at the same y-level
- **Each branch gets its own x-lane** — calculate lane widths based on the widest node in each branch, plus 40px padding on each side
- Each branch column flows straight down independently within its lane
- Use consistent color coding across branches to show categories
- Group related nodes by column — one column per interaction type
- Use comment nodes sparingly for annotations

## Question & Answer Blocks

Use `question` and `answer` blocks for interactive back-and-forth within a diagram:

- **Question** (`#0e7c7b` teal, ? badge): Use whenever you need to ask the user something in the flow — e.g., a design decision, a clarification, or a choice point. Default text: `"Question?"`
- **Answer** (`#b85c1f` orange, A badge, left accent bar): The user drags this in from the toolbar to respond to a question. Default text: `"Answer"`

Typical pattern: place a question block where the flow needs user input, connect it to the next step. The user can then add an answer block, type their response, and connect it.

## What NOT to Do

- Don't output JSON in the chat — write it to the file with the Write tool
- Don't use node IDs that could collide
- Don't let nodes overlap — this is the #1 layout failure; always verify bounding boxes
- Don't forget connections — every node except comments should have at least one
- Don't put branch columns too close together — account for the full width of every node in each column
