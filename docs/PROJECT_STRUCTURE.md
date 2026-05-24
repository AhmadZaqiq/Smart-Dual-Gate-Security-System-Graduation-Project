# Project Structure

Professional runtime layout for the Smart Dual-Gate Security System.

```text
Smart-Dual-Gate-Security-System-Graduation-Project/
├── Smart Dual-Gate System/
│   ├── ai/              # YOLO monitoring, streams, models, dataset
│   ├── auth/            # RFID, fingerprint, face, behavior, enrollment
│   ├── config/          # System settings
│   ├── core/            # FSM and security workflow
│   ├── database/        # SQLite and repositories
│   ├── hardware/        # GPIO and physical devices
│   ├── runtime/         # Generated runtime files
│   ├── utils/           # Shared utilities and alerts
│   ├── web_dashboard/   # Flask dashboard
│   └── main.py          # Main runtime entry point
├── docs/                # Documentation and diagrams
├── development_and_testing/ # Development-only assets
├── README.md
└── .gitignore
```

## Important Notes

- `.env` is local only and must never be committed.
- Runtime files such as PID, lock, JSON, and logs are generated automatically.
- Local backup folders are ignored by Git.
- Critical helper file paths are kept stable to avoid breaking subprocess-based execution.
