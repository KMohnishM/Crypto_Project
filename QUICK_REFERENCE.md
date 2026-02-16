# 🎯 Frontend Quick Reference Card

## 🔑 Default Credentials
```
Username: admin
Password: admin
URL: http://localhost:5000
```

## 📱 Routes Overview

### Public Routes (No Login Required)
| Route | Page | Description |
|-------|------|-------------|
| `/` | Landing | Welcome page with Login/Register buttons |
| `/auth/login` | Login | User authentication |
| `/auth/register` | Register | New user registration (default role: technician) |
| `/monitoring` | Monitoring | Grafana dashboards (public for display screens) |

### Protected Routes (Login Required)
| Route | Page | Min. Role | Description |
|-------|------|-----------|-------------|
| `/dashboard` | Dashboard | Any | Main hub with stats and overview |
| `/patients/` | Patient List | Any | View all patients |
| `/patients/<id>` | Patient Detail | Any | View specific patient vitals |
| `/patients/create` | Create Patient | Doctor+ | Add new patient |
| `/patients/<id>/edit` | Edit Patient | Doctor+ | Modify patient info |
| `/analytics` | Analytics | Any | Charts and statistics |
| `/auth/profile` | Profile | Any | View/edit own profile |
| `/auth/admin/users` | User Management | Admin | Manage all users |

## 👥 User Roles & Permissions

```
┌──────────────┬──────────┬────────────┬──────────┬────────────┬──────────────┐
│ Role         │ View     │ Edit       │ Add      │ Manage     │ Admin        │
│              │ Patients │ Patients   │ Vitals   │ Vitals     │ Panel        │
├──────────────┼──────────┼────────────┼──────────┼────────────┼──────────────┤
│ Admin        │    ✅    │     ✅     │    ✅    │     ✅     │      ✅      │
│ Doctor       │    ✅    │     ✅     │    ✅    │     ✅     │      ❌      │
│ Nurse        │    ✅    │     ❌     │    ✅    │     ✅     │      ❌      │
│ Technician   │    ✅    │     ❌     │    ❌    │     ❌     │      ❌      │
└──────────────┴──────────┴────────────┴──────────┴────────────┴──────────────┘
```

## 🎨 UI Components

### Navigation Bar (When Not Logged In)
```
[🏥 Hospital] | Home | Monitoring |                    [ Login ] [ Register ]
```

### Navigation Bar (When Logged In)
```
[🏥 Hospital] | Dashboard | Patients | Analytics | Monitoring | [👤 John Doe ▼]
                                                                   ├─ Profile
                                                                   └─ Logout
```

### Landing Page Features
- Hero section with hospital icon
- Feature boxes (Security, Monitoring, Analytics)
- Login/Register buttons
- Security badges (HIPAA, Quantum-Resistant)

### Dashboard Cards
- **System Overview**: Total patients, critical alerts, avg vitals
- **Recent Anomalies**: Real-time anomaly detection alerts
- **Hospital Hierarchy**: Organization structure
- **Quick Actions**: Navigate to key features

## 🔄 User Journey

### New User Registration Flow
```
1. Visit http://localhost:5000
2. Click "Register"
3. Fill form (first name, last name, username, email, password)
4. Automatically assigned "technician" role
5. Redirected to login
6. Login with new credentials
7. Access dashboard and view-only features
8. Contact admin for role upgrade if needed
```

### Returning User Flow
```
1. Visit http://localhost:5000
2. If logged in → Auto-redirect to dashboard
3. If not logged in → See landing page
4. Click "Login"
5. Enter credentials
6. Access full system based on role
```

### Admin User Management Flow
```
1. Login as admin
2. Click profile dropdown → Admin Panel (or /auth/admin/users)
3. View all users
4. Click "Create User" to add new user
5. Set username, email, password, role, department
6. User can now login with those credentials
```

## 🔐 Security Features

### Password Storage
- ✅ Hashed with Werkzeug (PBKDF2 + SHA256)
- ✅ Never stored in plaintext
- ✅ Salted automatically

### Session Management
- ✅ Flask-Login for session handling
- ✅ Sessions tracked in database
- ✅ "Remember Me" option (30 days)
- ✅ Session invalidation on logout

### Route Protection
- ✅ `@login_required` decorator on sensitive routes
- ✅ Automatic redirect to login if not authenticated
- ✅ Smart "next" parameter to return to original page
- ✅ Role-based permission checks

### Data Protection
- ✅ ASCON AEAD encryption for patient data in transit
- ✅ SQLCipher encryption for database at rest
- ✅ TLS 1.2 for MQTT communication
- ✅ CSRF protection built-in

## 🧪 Testing Checklist

### Manual Testing
- [ ] Access landing page → Should see welcome screen
- [ ] Click Register → Create new account
- [ ] Login with new account → See dashboard
- [ ] Try to access `/dashboard` while logged out → Redirect to login
- [ ] Login as admin → All features available
- [ ] Create user with "doctor" role → Test permissions
- [ ] Logout → Returns to landing page
- [ ] Try protected routes after logout → Redirected to login

### Automated Testing
```bash
# Run the test suite
python test_authentication.py
```

## 📊 Database Queries

### View All Users
```sql
SELECT id, username, email, role, is_active, last_login 
FROM users 
ORDER BY created_at DESC;
```

### View Active Sessions
```sql
SELECT us.session_id, u.username, us.ip_address, us.created_at, us.expires_at
FROM user_sessions us
JOIN users u ON us.user_id = u.id
ORDER BY us.created_at DESC;
```

### Deactivate User
```sql
UPDATE users 
SET is_active = 0 
WHERE username = 'username_here';
```

### Change User Role
```sql
UPDATE users 
SET role = 'doctor' 
WHERE username = 'username_here';
```

## 🚨 Troubleshooting

### "Page Not Found" Error
- Check Docker containers are running: `docker compose ps`
- Web dashboard should be on port 5000
- Try: `http://localhost:5000` (not https)

### Can't Login
- Verify username/password are correct
- Check user is active: `SELECT is_active FROM users WHERE username='...'`
- Try default admin: `admin` / `admin`
- Clear browser cookies and try again

### "Permission Denied"
- Check user role: `SELECT role FROM users WHERE username='...'`
- Contact admin for role upgrade
- Some features require doctor or admin role

### Session Issues
- Clear browser cookies
- Logout and login again
- Check session expiry in database

## 📝 Common Admin Tasks

### Change Admin Password (First Thing!)
```
1. Login as admin
2. Click profile dropdown → Profile
3. Click "Edit Profile"
4. Enter new password
5. Save changes
```

### Create Staff Accounts
```
1. Login as admin
2. Go to /auth/admin/users
3. Click "Create User"
4. Fill in details, select role
5. Provide credentials to staff member
```

### Upgrade User Role
```
1. Login as admin
2. Go to /auth/admin/users
3. Click on user to edit
4. Change role dropdown
5. Save changes
```

### Deactivate User Account
```
1. Login as admin
2. Go to /auth/admin/users
3. Click on user to edit
4. Uncheck "Is Active"
5. Save changes
```

## 🎯 Best Practices

### For Users
- ✅ Use strong passwords (8+ chars, mixed case, numbers, symbols)
- ✅ Logout when done, especially on shared computers
- ✅ Don't share credentials
- ✅ Report suspicious activity to admin

### For Admins
- ✅ Change default admin password immediately
- ✅ Create separate admin accounts (don't share one)
- ✅ Assign minimum required role to users
- ✅ Regularly review user list and deactivate unused accounts
- ✅ Monitor login activity in user_sessions table
- ✅ Keep system and dependencies updated

---

**Quick Links:**
- [USER_GUIDE.md](USER_GUIDE.md) - Detailed user guide
- [AUTH_FLOW_DIAGRAM.md](AUTH_FLOW_DIAGRAM.md) - Visual flow diagrams
- [FRONTEND_AUTHENTICATION_REPORT.md](FRONTEND_AUTHENTICATION_REPORT.md) - Implementation details

**Version:** 1.0.0  
**Last Updated:** February 16, 2026
