# Mantrap Admin Dashboard Setup

## Prerequisites

- Python 3.10+
- SQLite database initialized
- Raspberry Pi recommended for GPIO mantrap runtime
- Dashboard and mantrap run as separate processes

## 1. Install dashboard dependencies

```bash
cd "Smart Dual-Gate System"
python -m venv venv-dashboard
```

Windows:

```powershell
.\venv-dashboard\Scripts\activate
pip install -r requirements-dashboard.txt
```

Linux / Raspberry Pi:

```bash
source venv-dashboard/bin/activate
pip install -r requirements-dashboard.txt
```

## 2. Environment file

```bash
copy .env.example .env
```

Edit `.env` and set:

- `FLASK_SECRET_KEY`
- `AHMAD_ADMIN_PASSWORD`
- `DIAA_ADMIN_PASSWORD`
- `MANTRAP_PYTHON=python3` on Raspberry Pi

Do not commit `.env`.

## 3. Database setup

```bash
python database/init_database.py
python database/seed_auth_settings.py
python database/seed_admin_user.py
python database/run_migrations.py
```

Admin accounts created:

| Username | Display Name |
|----------|--------------|
| `ahmad` | Ahmad |
| `diaa` | Diaa |

Passwords come only from environment variables. They are never printed by the seed script.

## 4. Run the dashboard

```bash
python -m web_dashboard.app
```

Open: `http://localhost:8000`

## 5. Safe system control (Start / Stop / Restart)

The dashboard controls only the `main.py` process lifecycle.

| Action | API | Behavior |
|--------|-----|----------|
| Start | `POST /api/system/start` | Launches `python3 main.py` if not running |
| Stop | `POST /api/system/stop` | Terminates the tracked PID |
| Restart | `POST /api/system/restart` | Stop, then start |
| Status | `GET /api/system/process-status` | Returns RUNNING / STOPPED / STARTING / STOPPING |

Runtime files:

- `runtime/mantrap.pid` — written by `main.py`
- `runtime/mantrap.lock` — control-operation lock
- `runtime/process_state.json` — dashboard lifecycle state
- `runtime/mantrap_status.json` — workflow status bridge

The dashboard never imports GPIO, cameras, or hardware modules.

## 5b. Premium control center features

| Feature | API / Route |
|---------|-------------|
| Dual camera streams | `GET /api/streams/status`, `POST /api/streams/face/start`, `POST /api/streams/inner/start` |
| Workflow path view | `GET /api/system/status` (includes `workflow`) |
| Reset to idle | `POST /api/system/reset-idle` |
| Employee enrollment | `GET /employees/new` (wizard), `POST /api/employees/` |
| RFID / fingerprint enrollment | `POST /api/enrollment/rfid/start`, `POST /api/enrollment/fingerprint/start` |
| Employee active toggle | `PATCH /api/employees/<id>/active` |
| Admin management | `GET /admins/` (Super Admin only) |

Stream ports:

| Camera | Port |
|--------|------|
| YOLO inner (FSM) | 5000 |
| Face preview subprocess | 5001 |
| Inner preview subprocess | 5002 |

## 6. Recommended operating procedure

Terminal 1 (optional if using dashboard controls):

```bash
python main.py
```

Terminal 2:

```bash
python -m web_dashboard.app
```

Or start the mantrap from the dashboard **Overview** or **Live Monitor** page.

## 7. Testing system control

### Verify only one mantrap process

Linux / Pi:

```bash
pgrep -af "main.py"
```

Windows PowerShell:

```powershell
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*main.py*' }
```

Expected: one `main.py` process when RUNNING.

### Test dashboard controls

1. Login as `ahmad` or `diaa`
2. Open Overview
3. Click **Start System** and confirm
4. Confirm badge changes to `RUNNING`
5. Confirm `runtime/mantrap.pid` exists
6. Click **Stop System** and confirm badge changes to `STOPPED`
7. Click **Restart System** and confirm process returns to `RUNNING`

### Verify audit records

Open **Audit Trail** and confirm entries such as:

- `SYSTEM_START`
- `SYSTEM_STOP`
- `SYSTEM_RESTART` (via restart start action)
- `UPDATE_SETTING`
- `RESOLVE_SECURITY_EVENT`

## 8. Ports

| Service | Port |
|---------|------|
| YOLO MJPEG stream | 5000 |
| Admin dashboard | 8000 |

## 9. Troubleshooting

| Issue | Fix |
|-------|-----|
| Cannot login | Re-run `seed_admin_user.py` after setting env passwords |
| Status cards empty | Start mantrap process and wait 2-3 seconds |
| Stream offline | Normal outside person-counting phase; use Live Monitor stream controls |
| Start fails | Check `MANTRAP_PYTHON`, GPIO permissions, and logs |

## 10. Testing premium features

### Dual camera streams (Live Monitor)

1. Login and open **Live Monitor**
2. Click **Open Stream** on Face Camera — health should move to `ONLINE`
3. Start mantrap (`main.py`) if needed for YOLO inner stream during person counting
4. When YOLO is inactive, click **Open Stream** on Inner Camera for preview mode (`:5002`)
5. Click **Close Stream** on each camera independently

### Employee enrollment wizard

1. Open **Employees** → **Add Employee**
2. Complete step 1 (employee information) → **Next**
3. Step 2: **Start Registration** for RFID — place card on reader
4. Step 3: **Start Enrollment** for fingerprint — follow on-screen prompts
5. Step 4: enter face image path → **Next**
6. Step 5: review → **Save Employee**

### Active / inactive toggle

1. On **Employees** list, flip the status switch
2. Confirm no page reload; check **Audit Trail** for `UPDATE_EMPLOYEE_STATUS`

### Admin management (Super Admin: `ahmad`)

1. Open **Admin Management**
2. Add admin, edit role/status, reset password
3. Login as Operator (`diaa`) — Admin Management link should be hidden

### Reset system to idle

1. Ensure mantrap process is **RUNNING**
2. On Overview, click **Reset to Idle** and confirm
3. Workflow returns to standby without rebooting Pi or dashboard
4. Confirm audit entry `RESET_TO_IDLE`

## 11. Security notes

- Change Ahmad/Diaa passwords immediately in production
- Use HTTPS reverse proxy for remote access
- Keep dashboard and mantrap on trusted network only
- Do not expose port 8000 publicly without authentication hardening
