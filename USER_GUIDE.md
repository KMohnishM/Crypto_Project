# 🏥 Hospital Monitoring System - User Guide

## 🚀 Quick Start

### Default Admin Credentials
```
Username: admin
Password: admin
```

**⚠️ IMPORTANT:** Change the default admin password immediately after first login!

---

## 👤 User Flow

### 1. **Landing Page** (`http://localhost:5000`)
- Beautiful landing page with system features
- Two main actions:
  - **Login** - For existing users
  - **Register** - For new users

### 2. **Registration** (`/auth/register`)
New users can self-register with the following information:
- First Name & Last Name
- Username (must be unique)
- Email (must be unique)
- Password

**Default Role:** New users are automatically assigned the `technician` role (lowest privilege) for security.

### 3. **Login** (`/auth/login`)
- Enter username and password
- Optional "Remember Me" checkbox for persistent sessions
- Redirects to dashboard upon successful authentication

### 4. **Dashboard** (`/dashboard`) 🔒 *Requires Authentication*
Main hub showing:
- System overview and statistics
- Total patients and critical alerts
- Recent anomalies
- Hospital hierarchy
- Quick access to other features

---

## 🔐 Authentication & Security

### Protected Routes (Require Login)
- ✅ Dashboard (`/dashboard`)
- ✅ Patient List (`/patients/`)
- ✅ Patient Details & Management
- ✅ Analytics (`/analytics`)
- ✅ Profile Management (`/auth/profile`)
- ✅ Admin Panel (`/auth/admin/users`) - Admin only

### Public Routes (No Login Required)
- 🌐 Landing Page (`/`)
- 🌐 Monitoring View (`/monitoring`) - For public display screens
- 🌐 Login/Register pages

---

## 👥 User Roles & Permissions

### 1. **Admin** 👑
Full system access including:
- View/Edit all patients
- View all vitals
- Add/Edit vitals
- Manage users (create, edit, deactivate)
- Access admin panel

### 2. **Doctor** 👨‍⚕️
Medical professional access:
- View patients
- Edit patient information
- View vitals
- Add vitals

### 3. **Nurse** 👩‍⚕️
Clinical access:
- View patients
- View vitals
- Add vitals

### 4. **Technician** 🔧
Basic read-only access:
- View patients
- View vitals

---

## 🔄 Complete User Journey

```
┌─────────────────────────────────────────────────────────────┐
│  1. Landing Page                                            │
│     └─► Login or Register                                   │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│  2. Authentication                                          │
│     • Login with credentials                                │
│     • New users register (default: technician role)         │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│  3. Dashboard (Authenticated Users)                         │
│     ├─► Patients: View patient list and details            │
│     ├─► Analytics: Data visualizations and statistics      │
│     ├─► Monitoring: Live Grafana dashboards (public too)   │
│     ├─► Profile: View/edit personal information            │
│     └─► Admin Panel (Admin only): User management          │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│  4. Session Management                                      │
│     • Sessions tracked in database                          │
│     • Logout invalidates session                            │
│     • Returns to landing page after logout                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Key Features

### 🔒 Security
- Password hashing with Werkzeug (PBKDF2 + SHA256)
- Session management with Flask-Login
- CSRF protection
- Role-based access control (RBAC)
- End-to-end encryption for patient data (ASCON AEAD)

### 📊 Real-time Monitoring
- Live patient vitals via MQTT
- ML-powered anomaly detection
- Grafana dashboards for visualization
- Prometheus metrics

### 💼 User Management (Admin Only)
- Create new users with specific roles
- Edit user information and permissions
- Deactivate/activate user accounts
- View all user sessions

---

## 📝 Common Tasks

### Change Your Password
1. Click your name in the top-right corner
2. Select "Profile"
3. Click "Edit Profile"
4. Enter new password
5. Save changes

### View Patient Data
1. Navigate to "Patients" from the navbar
2. Click on any patient to view details
3. View real-time vitals and historical data

### Access Monitoring Dashboard
- Click "Monitoring" in navbar (available to all, including public)
- View live Grafana dashboards with real-time metrics

### Admin: Create New User
1. Click your name → navigate to admin panel
2. Click "Create User"
3. Fill in user details
4. Select appropriate role
5. User receives credentials to login

---

## 🚨 Troubleshooting

### Can't Login
- Verify username and password are correct
- Check if account is active (contact admin)
- Clear browser cache and cookies
- Try "Register" if you don't have an account

### Don't See Expected Menu Items
- Some features are role-restricted
- Contact admin to upgrade your role if needed
- Dashboard and Patients require authentication

### "Permission Denied" Error
- Feature requires higher privileges
- Contact administrator for role upgrade

---

## 🔧 For Administrators

### First-Time Setup
1. Login with default credentials (`admin` / `admin`)
2. **Immediately change the admin password**
3. Create additional admin accounts (backup)
4. Create user accounts for staff
5. Assign appropriate roles

### Security Best Practices
- Change default passwords immediately
- Use strong passwords (min 8 chars, mixed case, numbers, symbols)
- Regularly review user list and deactivate unused accounts
- Monitor user sessions in database
- Keep staff roles at minimum required privilege

### Managing Users
```sql
-- View all users (SQLite database)
SELECT username, email, role, is_active, last_login FROM users;

-- Activate/Deactivate user
UPDATE users SET is_active = 0 WHERE username = 'username';
```

---

## 📱 Access Points

| Service | URL | Authentication |
|---------|-----|----------------|
| Web Dashboard | http://localhost:5000 | Required (except landing/monitoring) |
| Grafana | http://localhost:3000 | Optional (embedded in monitoring) |
| Prometheus | http://localhost:9090 | None |
| Alert Manager | http://localhost:9093 | None |
| Main Host API | http://localhost:8000 | Via MQTT encryption |

---

## 🆘 Support

For issues or questions:
1. Check this guide first
2. Review system logs
3. Contact system administrator
4. Check documentation in project README

---

**System Version:** 1.0.0  
**Last Updated:** February 2026  
**Security Level:** HIPAA Compliant with Quantum-Resistant Encryption
