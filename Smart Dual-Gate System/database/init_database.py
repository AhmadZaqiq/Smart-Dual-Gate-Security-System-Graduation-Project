import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.database_manager import execute_query


# =========================
# Person Table
# =========================

def create_person_table():
    execute_query("""
        CREATE TABLE IF NOT EXISTS Person
        (
            PersonID INTEGER PRIMARY KEY AUTOINCREMENT,

            NationalID TEXT UNIQUE,

            FirstName TEXT NOT NULL,
            SecondName TEXT NOT NULL,
            ThirdName TEXT NOT NULL,
            LastName TEXT NOT NULL,

            DateOfBirth TEXT,
            Gender TEXT,

            Address TEXT,
            Phone TEXT,
            Email TEXT,

            Picture TEXT,

            IsDeleted INTEGER NOT NULL DEFAULT 0,

            CreationDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            LastUpdatedDate TEXT
        );
    """)


# =========================
# Employee Table
# =========================

def create_employee_table():
    execute_query("""
        CREATE TABLE IF NOT EXISTS Employee
        (
            EmployeeID INTEGER PRIMARY KEY AUTOINCREMENT,

            PersonID INTEGER NOT NULL,

            EmployeeNumber TEXT UNIQUE,

            IsActive INTEGER NOT NULL DEFAULT 1,
            IsDeleted INTEGER NOT NULL DEFAULT 0,

            CreationDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            LastUpdatedDate TEXT,

            FOREIGN KEY (PersonID)
            REFERENCES Person(PersonID)
        );
    """)


# =========================
# Admin User Table
# =========================

def create_admin_user_table():
    execute_query("""
        CREATE TABLE IF NOT EXISTS AdminUser
        (
            AdminUserID INTEGER PRIMARY KEY AUTOINCREMENT,
            AdminCode TEXT UNIQUE,

            PersonID INTEGER NOT NULL,

            UserName TEXT NOT NULL UNIQUE,
            Email TEXT UNIQUE,

            PasswordHash TEXT NOT NULL,

            Role TEXT NOT NULL DEFAULT 'Admin',

            IsActive INTEGER NOT NULL DEFAULT 1,
            IsDeleted INTEGER NOT NULL DEFAULT 0,

            LastLoginDate TEXT,

            CreationDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            LastUpdatedDate TEXT,

            FOREIGN KEY (PersonID)
            REFERENCES Person(PersonID)
        );
    """)


# =========================
# Employee Authentication
# =========================

def create_employee_authentication_table():
    execute_query("""
        CREATE TABLE IF NOT EXISTS EmployeeAuthentication
        (
            EmployeeAuthenticationID INTEGER PRIMARY KEY AUTOINCREMENT,

            EmployeeID INTEGER NOT NULL,

            RFIDUID TEXT UNIQUE,
            FingerprintPosition INTEGER UNIQUE,

            FaceImagePath TEXT,

            BehaviorProfileEnabled INTEGER NOT NULL DEFAULT 1,

            IsActive INTEGER NOT NULL DEFAULT 1,
            IsDeleted INTEGER NOT NULL DEFAULT 0,

            CreationDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            LastUpdatedDate TEXT,

            FOREIGN KEY (EmployeeID)
            REFERENCES Employee(EmployeeID)
        );
    """)


# =========================
# Access Session Table
# =========================

def create_access_session_table():
    execute_query("""
        CREATE TABLE IF NOT EXISTS AccessSession
        (
            AccessSessionID INTEGER PRIMARY KEY AUTOINCREMENT,

            EmployeeID INTEGER,

            EntryTime TEXT,
            ExitTime TEXT,

            SessionDurationSeconds INTEGER,

            EntryMethod TEXT,
            ExitMethod TEXT,

            FinalStatus TEXT,

            Notes TEXT,

            CreationDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            LastUpdatedDate TEXT,

            FOREIGN KEY (EmployeeID)
            REFERENCES Employee(EmployeeID)
        );
    """)


# =========================
# Authentication Attempt
# =========================

def create_authentication_attempt_table():
    execute_query("""
        CREATE TABLE IF NOT EXISTS AuthenticationAttempt
        (
            AuthenticationAttemptID INTEGER PRIMARY KEY AUTOINCREMENT,

            AccessSessionID INTEGER,
            EmployeeID INTEGER,

            RFIDStatus TEXT,
            FingerprintStatus TEXT,
            FaceRecognitionStatus TEXT,
            BehaviorStatus TEXT,

            FinalResult TEXT,

            FailureReason TEXT,

            CreationDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (AccessSessionID)
            REFERENCES AccessSession(AccessSessionID),

            FOREIGN KEY (EmployeeID)
            REFERENCES Employee(EmployeeID)
        );
    """)


# =========================
# Security Event Table
# =========================

def create_security_event_table():
    execute_query("""
        CREATE TABLE IF NOT EXISTS SecurityEvent
        (
            SecurityEventID INTEGER PRIMARY KEY AUTOINCREMENT,

            AccessSessionID INTEGER,
            EmployeeID INTEGER,

            EventType TEXT NOT NULL,
            Severity TEXT NOT NULL,

            DetectedPersonsCount INTEGER,

            Description TEXT,

            IsResolved INTEGER NOT NULL DEFAULT 0,

            ResolvedByAdminUserID INTEGER,
            ResolvedDate TEXT,

            CreationDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            LastUpdatedDate TEXT,

            FOREIGN KEY (AccessSessionID)
            REFERENCES AccessSession(AccessSessionID),

            FOREIGN KEY (EmployeeID)
            REFERENCES Employee(EmployeeID),

            FOREIGN KEY (ResolvedByAdminUserID)
            REFERENCES AdminUser(AdminUserID)
        );
    """)


# =========================
# System Setting Table
# =========================

def create_system_setting_table():
    execute_query("""
        CREATE TABLE IF NOT EXISTS SystemSetting
        (
            SystemSettingID INTEGER PRIMARY KEY AUTOINCREMENT,

            SettingKey TEXT NOT NULL UNIQUE,
            SettingValue TEXT NOT NULL,

            Description TEXT,

            IsDeleted INTEGER NOT NULL DEFAULT 0,

            CreationDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            LastUpdatedDate TEXT
        );
    """)


# =========================
# Audit Table
# =========================

def create_audit_table():
    execute_query("""
        CREATE TABLE IF NOT EXISTS Audit
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

            FOREIGN KEY (AdminUserID)
            REFERENCES AdminUser(AdminUserID)
        );
    """)


# =========================
# Create Full Database
# =========================

def create_database():
    create_person_table()

    create_employee_table()

    create_admin_user_table()

    create_employee_authentication_table()

    create_access_session_table()

    create_authentication_attempt_table()

    create_security_event_table()

    create_system_setting_table()

    create_audit_table()

    print("[DATABASE] Mantrap database created successfully", flush=True)


if __name__ == "__main__":
    create_database()
