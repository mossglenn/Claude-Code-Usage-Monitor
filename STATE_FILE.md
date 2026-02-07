# State File Documentation

## Overview

When the `--write-state` flag is enabled, Claude Monitor writes real-time usage statistics to a JSON file that can be consumed by external applications (VS Code extensions, status bar widgets, etc.).

**File Location**: `~/.claude-monitor/reports/current.json`

**Environment Variable**: `CLAUDE_MONITOR_REPORT_DIR` (set by bootstrap.py)

**Update Frequency**: Updates every `--refresh-rate` seconds (default: 10 seconds) when an active Claude session is detected.

## File Structure

```json
{
  "messages": {
    "used": 140,
    "limit": 250,
    "percent": 56.0
  },
  "tokens": {
    "used": 17582,
    "limit": 38705,
    "percent": 45.43
  },
  "cost": {
    "used": 5.125579,
    "limit": 50.0,
    "percent": 10.25
  },
  "reset": {
    "timestamp": "2026-01-10T00:00:00+00:00",
    "secondsRemaining": 19777,
    "formattedTime": "12:00 AM"
  },
  "burnRate": {
    "tokens": 32859.04,
    "messages": 0
  },
  "lastUpdate": "2026-01-09T13:30:22.976757"
}
```

## Field Descriptions

### `messages`
Message count statistics for the current session window.

- **`used`** (integer): Number of messages sent in the current session window
- **`limit`** (integer): Maximum messages allowed before reset
  - For standard plans (Pro/Max20): Fixed plan limit
  - For custom plans: P90 (90th percentile) calculated from usage history
  - May be `0` if insufficient history for P90 calculation
- **`percent`** (float): Percentage of limit used (0-100+)

### `tokens`
Token usage statistics for the current session window.

- **`used`** (integer): Total tokens consumed (input + output + cache tokens)
- **`limit`** (integer): Maximum tokens allowed before reset
  - For standard plans: Fixed plan limit
  - For custom plans: P90 calculated from usage history
- **`percent`** (float): Percentage of limit used (0-100+)

### `cost`
Cost statistics in USD for the current session window.

- **`used`** (float): Total cost in USD for all API calls
- **`limit`** (float): Maximum cost before reset
  - For standard plans: Fixed plan limit
  - For custom plans: P90 calculated from usage history
- **`percent`** (float): Percentage of limit used (0-100+)

### `reset`
Information about when usage counters reset.

- **`timestamp`** (string): ISO 8601 formatted UTC timestamp of next reset
  - Example: `"2026-01-10T00:00:00+00:00"`
- **`secondsRemaining`** (integer): Seconds until reset occurs
  - Useful for countdown timers
- **`formattedTime`** (string): Human-readable 12-hour time format
  - Example: `"12:00 AM"`
  - Timezone-aware based on `--timezone` setting

### `burnRate`
Current consumption rate based on last hour of activity.

- **`tokens`** (float): Tokens consumed per minute (averaged over last hour)
  - Calculated by `calculate_hourly_burn_rate()` in `core/calculations.py`
  - Returns `0.0` if no activity in last hour
- **`messages`** (integer): Currently always `0` (messages burn rate not yet implemented)

### `lastUpdate`
- **`lastUpdate`** (string): ISO 8601 timestamp when this file was last written
  - Example: `"2026-01-09T13:30:22.976757"`
  - Useful for detecting stale data

## Type Definitions

### TypeScript

```typescript
interface ClaudeMonitorState {
  messages: UsageMetric;
  tokens: UsageMetric;
  cost: UsageMetric;
  reset: ResetInfo;
  burnRate: BurnRate;
  lastUpdate: string; // ISO 8601 timestamp
}

interface UsageMetric {
  used: number;
  limit: number;
  percent: number;
}

interface ResetInfo {
  timestamp: string; // ISO 8601 UTC timestamp
  secondsRemaining: number;
  formattedTime: string; // "HH:MM AM/PM"
}

interface BurnRate {
  tokens: number; // tokens per minute
  messages: number; // currently always 0
}
```

### Python

```python
from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict

class UsageMetric(TypedDict):
    used: int | float
    limit: int | float
    percent: float

class ResetInfo(TypedDict):
    timestamp: str  # ISO 8601 UTC
    secondsRemaining: int
    formattedTime: str

class BurnRate(TypedDict):
    tokens: float
    messages: int

class ClaudeMonitorState(TypedDict):
    messages: UsageMetric
    tokens: UsageMetric
    cost: UsageMetric
    reset: ResetInfo
    burnRate: BurnRate
    lastUpdate: str  # ISO 8601
```

## Usage Examples

### Python Example: File Watching

```python
import json
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

STATE_FILE = Path.home() / ".claude-monitor" / "reports" / "current.json"

class StateFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path == str(STATE_FILE):
            with open(STATE_FILE) as f:
                state = json.load(f)
                print(f"Messages: {state['messages']['used']}/{state['messages']['limit']}")
                print(f"Reset in: {state['reset']['secondsRemaining']}s")

observer = Observer()
observer.schedule(StateFileHandler(), str(STATE_FILE.parent), recursive=False)
observer.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()
```

### TypeScript Example: VS Code Extension

```typescript
import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

const STATE_FILE = path.join(os.homedir(), '.claude-monitor', 'reports', 'current.json');

export function activate(context: vscode.ExtensionContext) {
    const statusBarItem = vscode.window.createStatusBarItem(
        vscode.StatusBarAlignment.Right,
        100
    );

    // Watch for file changes
    const watcher = fs.watch(STATE_FILE, (eventType) => {
        if (eventType === 'change') {
            updateStatusBar(statusBarItem);
        }
    });

    // Initial update
    updateStatusBar(statusBarItem);
    statusBarItem.show();

    context.subscriptions.push(statusBarItem);
    context.subscriptions.push({ dispose: () => watcher.close() });
}

function updateStatusBar(statusBarItem: vscode.StatusBarItem) {
    try {
        const data = fs.readFileSync(STATE_FILE, 'utf8');
        const state: ClaudeMonitorState = JSON.parse(data);

        // Check if data is stale (> 30 seconds old)
        const lastUpdate = new Date(state.lastUpdate);
        const age = Date.now() - lastUpdate.getTime();
        if (age > 30000) {
            statusBarItem.text = "$(circle-slash) Claude: No active session";
            return;
        }

        // Format countdown timer
        const hours = Math.floor(state.reset.secondsRemaining / 3600);
        const minutes = Math.floor((state.reset.secondsRemaining % 3600) / 60);
        const timeLeft = `${hours}h ${minutes}m`;

        // Show messages and reset time
        statusBarItem.text = `$(comment) ${state.messages.used}/${state.messages.limit} | $(clock) ${timeLeft}`;
        statusBarItem.tooltip = `Tokens: ${state.tokens.used}/${state.tokens.limit}\nCost: $${state.cost.used.toFixed(2)}/$${state.cost.limit}\nResets at: ${state.reset.formattedTime}`;
    } catch (error) {
        statusBarItem.text = "$(circle-slash) Claude: Monitor not running";
    }
}
```

### Node.js Example: Simple Reader

```javascript
const fs = require('fs');
const path = require('path');
const os = require('os');

const STATE_FILE = path.join(os.homedir(), '.claude-monitor', 'reports', 'current.json');

function readState() {
    try {
        const data = fs.readFileSync(STATE_FILE, 'utf8');
        return JSON.parse(data);
    } catch (error) {
        console.error('Failed to read state file:', error.message);
        return null;
    }
}

function formatCountdown(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours}h ${minutes}m ${secs}s`;
}

// Read and display current state
const state = readState();
if (state) {
    console.log(`Messages: ${state.messages.used}/${state.messages.limit} (${state.messages.percent.toFixed(1)}%)`);
    console.log(`Tokens: ${state.tokens.used}/${state.tokens.limit} (${state.tokens.percent.toFixed(1)}%)`);
    console.log(`Cost: $${state.cost.used.toFixed(2)}/$${state.cost.limit} (${state.cost.percent.toFixed(1)}%)`);
    console.log(`Reset in: ${formatCountdown(state.reset.secondsRemaining)}`);
    console.log(`Burn rate: ${state.burnRate.tokens.toFixed(1)} tokens/min`);
}
```

## Best Practices

### File Watching

1. **Use native file watchers** instead of polling for better performance
   - Python: `watchdog` library
   - Node.js: `fs.watch()` or `chokidar`
   - Go: `fsnotify`

2. **Debounce updates** to avoid excessive redraws (100-500ms recommended)

3. **Check `lastUpdate` timestamp** to detect stale data
   - If `lastUpdate` is > 30 seconds old, assume monitor is not running
   - If `lastUpdate` is > 2 × `refresh_rate`, assume monitor crashed

### Error Handling

1. **File may not exist** if:
   - Monitor has never been run with `--write-state`
   - No active Claude session has occurred yet
   - User cleared the reports directory

2. **File may be empty or invalid JSON** during write operations
   - Catch JSON parse errors gracefully
   - Consider using file locking or atomic reads if critical

3. **Permissions** - File is created with user permissions (0644)

### Data Interpretation

1. **Limits may be 0** for custom plans with insufficient history
   - Check if `limit === 0` before calculating percentages
   - Show "Calculating..." or "N/A" in UI

2. **Percentages can exceed 100%** if user goes over their limit
   - Handle gracefully in UI (show warning color, etc.)

3. **Reset time is timezone-aware**
   - `timestamp` is always UTC
   - `formattedTime` uses user's `--timezone` setting (default: Europe/Warsaw)

4. **Burn rate reflects last hour**
   - May be 0 if no activity in last 60 minutes
   - Not predictive, purely historical

## Configuration

### Enable State File Writing

```bash
# Enable state file writing
claude-monitor --write-state

# With custom refresh rate (updates every 5 seconds)
claude-monitor --write-state --refresh-rate 5

# Settings persist across sessions
claude-monitor --write-state  # Run once
claude-monitor                # Will remember --write-state flag
```

### Disable State File Writing

```bash
# Disable by not passing the flag
claude-monitor

# Or explicitly clear saved settings
claude-monitor --clear
```

### Environment Variables

The state file location can be customized via environment variable:

```bash
export CLAUDE_MONITOR_REPORT_DIR="/custom/path/to/reports"
claude-monitor --write-state
```

Default: `~/.claude-monitor/reports/`

## Technical Details

### Update Mechanism

1. **Data Flow**:
   ```
   MonitoringOrchestrator (every --refresh-rate seconds)
   → on_data_update callback
   → DisplayController.create_data_display()
   → _write_state_file() [if write_state_enabled]
   ```

2. **Only updates when there's an active session**
   - File is NOT updated if no Claude activity detected
   - Check `lastUpdate` to determine if session is active

3. **Atomic writes**: File is written atomically using `Path.write_text()`
   - No partial writes under normal conditions
   - No file locking required for readers

### Data Sources

- **Messages/Tokens/Cost**: Calculated from session blocks in `~/.claude/projects/`
- **Limits**:
  - Standard plans: Fixed values from `core/plans.py`
  - Custom plans: P90 calculated from historical usage via `P90Calculator`
- **Reset time**: Extracted from session `end_time_str` in processed_data (not from `--reset-hour` setting)
- **Burn rate**: Calculated by `calculate_hourly_burn_rate()` from last hour of activity

### File Format

- **Encoding**: UTF-8
- **Indentation**: 2 spaces
- **Line endings**: Platform-specific (LF on Unix, CRLF on Windows)
- **File size**: Typically < 500 bytes

## Troubleshooting

### File Not Created

- Ensure `--write-state` flag is enabled
- Check that monitor is running with an active Claude session
- Verify permissions on `~/.claude-monitor/reports/` directory

### Stale Data

- Check monitor is still running: `ps aux | grep claude-monitor`
- Verify `lastUpdate` timestamp is recent
- Check logs: `~/.claude-monitor/logs/debug.log`

### Invalid JSON

- File may be mid-write when read (very rare with atomic writes)
- Retry read after brief delay (10-50ms)
- Check disk space and permissions

### Wrong Limits

- For custom plans, P90 requires sufficient history (typically 10+ sessions)
- Limits show `0` if insufficient data - this is expected behavior
- Standard plans (pro/max20) always have fixed non-zero limits

## Related Documentation

- [Main README](README.md) - Installation and basic usage
- [DEVELOPMENT.md](DEVELOPMENT.md) - Development setup
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues

## Version History

- **v3.1.0** (2026-01-09): Initial state file feature with `--write-state` flag
