# Logic Flow Creator

An interactive logic flow diagram editor with bidirectional AI sync. Built as a zero-dependency, single-file HTML tool that replaces Figma for flowcharting workflows.

## Features

- **5 node types**: Process, Decision, Start/End, I/O, Comment — each with distinct shapes and colors
- **Port-to-port connections** with L-shaped routing and arrowheads
- **Full interactivity**: Drag, resize, inline text edit, pan/zoom, marquee select
- **Bidirectional AI sync**: Claude writes diagrams, you edit them, Claude sees your changes
- **Auto-save**: Every edit saves automatically — no manual save needed
- **Live reload**: Editor polls for changes every 2 seconds
- **JSON import/export** + PNG export
- **Auto-layout** (Sugiyama algorithm)
- **Keyboard shortcuts**: Delete, Ctrl+Z/Y, Ctrl+A/C/V/D, arrow nudge, and more
- **Dark theme** (VS Code-style)

## Quick Start

```bash
python logic-flow-server.py
```

This starts a local server on port 8000 and opens the editor in your browser.

## How It Works

The editor and Claude share `logic-flow-data.json` as a live data file:

1. **Claude writes** a diagram to `logic-flow-data.json`
2. **Editor auto-loads** it within 2 seconds
3. **You edit** the diagram visually (move nodes, add connections, change text)
4. **Changes auto-save** back to the JSON file via the server
5. **Claude reads** the file to see your edits, then iterates

No copy-paste, no manual save, no export steps.

## Files

| File | Description |
|------|-------------|
| `logic-flow-editor.html` | The full editor — single file, zero dependencies, ~3200 lines |
| `logic-flow-server.py` | Local dev server with auto-save support (serves files + accepts POST /save) |
| `skill/SKILL.md` | Claude Code skill definition for AI-powered diagram generation |

## Claude Code Skill

Copy `skill/` to your Claude Code skills directory to enable the `/logic-flow` skill:

```bash
cp -r skill ~/.claude/skills/logic-flow
```

Then just ask Claude: "Draw me a flowchart for user authentication" and it handles everything.

## JSON Schema

```json
{
  "version": 1,
  "nodes": [
    {
      "id": "n1",
      "type": "process|decision|startend|io|comment",
      "x": 100, "y": 100,
      "width": 180, "height": 70,
      "text": "Label",
      "color": "#264f78",
      "textColor": "#ffffff",
      "fontSize": 14
    }
  ],
  "connections": [
    {
      "id": "c1",
      "from": "n1", "fromPort": "bottom",
      "to": "n2", "toPort": "top",
      "label": "Yes",
      "color": "#569cd6",
      "lineStyle": "solid"
    }
  ]
}
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Delete | Delete selected |
| Ctrl+Z | Undo |
| Ctrl+Y | Redo |
| Ctrl+A | Select all |
| Ctrl+C/V | Copy/Paste |
| Ctrl+D | Duplicate |
| G | Toggle grid snap |
| Arrow keys | Nudge selected |
| Mouse wheel | Zoom |
| Middle-click drag | Pan |
| Double-click | Edit node text |
| ? | Help overlay |

## License

MIT
