name
parameters
return type
permissions


{
  "name": "run_python",
  "params": {
    "file": "string"
  },
  "returns": "string",
  "permissions": ["execute"]
}

Now this should act as an API


┌──────────────┐
│ AI Client   │
└──────┬───────┘
       ↓
┌──────────────┐
│ Protocol    │  (MCP / JSON RPC)
└──────┬───────┘
       ↓
┌──────────────┐
│ Tool Server │
└──────┬───────┘
       ↓
┌──────────────┐
│ Host Tools  │
└──────────────┘

tools/
  run_python.json
  read_file.json
  write_file.json