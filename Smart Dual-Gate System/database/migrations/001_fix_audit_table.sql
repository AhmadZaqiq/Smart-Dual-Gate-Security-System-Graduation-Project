-- Migrate legacy Audit table to the dashboard-compatible schema.
-- Safe to run once on existing databases.

CREATE TABLE IF NOT EXISTS Audit_new
(
    AuditID INTEGER PRIMARY KEY AUTOINCREMENT,
    AdminUserID INTEGER,
    ActionType TEXT NOT NULL,
    TableName TEXT,
    RecordID INTEGER,
    OldValue TEXT,
    NewValue TEXT,
    Description TEXT,
    CreationDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (AdminUserID) REFERENCES AdminUser(AdminUserID)
);

INSERT INTO Audit_new (AuditID, AdminUserID, ActionType, Description, CreationDate)
SELECT
    AuditID,
    AdminUserID,
    COALESCE(Action, 'LEGACY'),
    Details,
    CreationDate
FROM Audit
WHERE EXISTS (
    SELECT 1 FROM pragma_table_info('Audit') WHERE name = 'Action'
);

DROP TABLE IF EXISTS Audit;
ALTER TABLE Audit_new RENAME TO Audit;
