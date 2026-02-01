# 🗄️ Database Setup Guide - Hospital Monitoring Dashboard

## 🚨 **Quick Fix for "no such table: users" Error**

If you're getting the `sqlalchemy.exc.OperationalError: no such table: users` error, follow these steps:

---

## 🛠️ **Method 1: Automatic Setup (Recommended)**

### **Windows:**
```bash
cd services/web_dashboard
start.bat
```

### **Linux/Mac:**
```bash
cd services/web_dashboard
chmod +x start.sh
./start.sh
```

This will automatically:
- ✅ Create virtual environment
- ✅ Install dependencies
- ✅ Initialize database
- ✅ Create sample data
- ✅ Start the application

---

## 🛠️ **Method 2: Manual Setup**

### **Step 1: Navigate to the web dashboard directory**
```bash
cd services/web_dashboard
```

### **Step 2: Create and activate virtual environment**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### **Step 3: Install dependencies**
```bash
pip install -r requirements.txt
```

### **Step 4: Initialize the database**
```bash
python init_database.py
```

### **Step 5: Start the application**
```bash
python app.py
```

---

## 🔧 **Database Management Commands**

### **Initialize Database with Sample Data**
```bash
python init_database.py
```
This creates:
- 👥 4 sample users (admin, doctor, nurse, tech)
- 🏥 15 sample patients
- 📍 Patient locations
- 💓 Vital signs data
- 📋 Medical history

### **Reset Database (Delete All Data)**
```bash
python reset_database.py
```
⚠️ **Warning:** This will delete ALL data!

### **Check Database Status**
```bash
python -c "from app import app; from database import db; from models.user import User; app.app_context().push(); print(f'Users: {User.query.count()}')"
```

---

## 🔑 **Default Login Credentials**

After running `init_database.py`, you can login with:

| Role | Username | Password | Access Level |
|------|----------|----------|--------------|
| **Admin** | `admin` | `admin` | Full access |
| **Doctor** | `doctor` | `doctor` | Patient management |
| **Nurse** | `nurse` | `nurse` | Patient monitoring |
| **Technician** | `tech` | `tech` | System monitoring |

---

## 🗂️ **Database Structure**

The database includes the following tables:

### **Users Table**
- `id` - Primary key
- `username` - Unique username
- `email` - Email address
- `password_hash` - Encrypted password
- `first_name`, `last_name` - User names
- `role` - User role (admin, doctor, nurse, technician)
- `department` - Department assignment
- `created_at`, `last_login` - Timestamps
- `is_active` - Account status

### **Patients Table**
- `patient_id` - Primary key
- `mrn` - Medical Record Number
- `first_name`, `last_name` - Patient names
- `date_of_birth` - Date of birth
- `gender` - Gender
- `blood_type` - Blood type
- `admission_date`, `discharge_date` - Hospital dates
- `status` - Current status
- `notes` - Additional notes

### **Patient Locations Table**
- `location_id` - Primary key
- `patient_id` - Foreign key to patients
- `hospital` - Hospital name
- `department` - Department
- `ward` - Ward number
- `bed` - Bed number
- `assigned_at` - Assignment timestamp
- `active` - Current location status

### **Patient Vital Signs Table**
- `vital_id` - Primary key
- `patient_id` - Foreign key to patients
- `heart_rate` - Heart rate (BPM)
- `spo2` - Oxygen saturation (%)
- `bp_systolic`, `bp_diastolic` - Blood pressure
- `respiratory_rate` - Respiratory rate
- `temperature` - Body temperature
- `etco2` - End-tidal CO2
- `recorded_by` - User who recorded
- `recorded_at` - Recording timestamp

### **Patient Medical History Table**
- `history_id` - Primary key
- `patient_id` - Foreign key to patients
- `condition` - Medical condition
- `diagnosis_date` - Date of diagnosis
- `treatment` - Treatment provided
- `medication` - Medications prescribed
- `notes` - Additional notes
- `recorded_by` - User who recorded
- `recorded_at` - Recording timestamp

---

## 🚨 **Troubleshooting**

### **Error: "no such table: users"**
**Solution:** Run `python init_database.py`

### **Error: "database is locked"**
**Solution:** 
1. Stop the application (Ctrl+C)
2. Delete the database file: `rm instance/healthcare.db`
3. Run `python init_database.py`

### **Error: "Module not found"**
**Solution:**
1. Make sure you're in the `services/web_dashboard` directory
2. Activate virtual environment: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Linux/Mac)
3. Install requirements: `pip install -r requirements.txt`

### **Error: "Permission denied"**
**Solution:**
1. Make sure you have write permissions in the directory
2. Try running as administrator (Windows) or with sudo (Linux/Mac)

### **Database Connection Issues**
**Solution:**
1. Check if the `instance` directory exists
2. Ensure SQLite is properly installed
3. Check file permissions on the database file

---

## 📊 **Sample Data Overview**

After initialization, the database contains:

- **4 Users** with different roles and permissions
- **15 Patients** with realistic medical data
- **15 Locations** mapping patients to hospital departments
- **45 Vital Signs** records (3 per patient)
- **8 Medical History** entries for various conditions

### **Sample Patient Data:**
- **MRN001-MRN015** - Medical Record Numbers
- **Ages 20-70** - Realistic age distribution
- **Multiple Departments** - Cardiology, Neurology, Orthopedics, Emergency, ICU
- **Various Statuses** - Admitted, Stable, Critical
- **Realistic Vital Signs** - Within normal and abnormal ranges

---

## 🔄 **Database Backup and Restore**

### **Backup Database**
```bash
# Copy the database file
cp instance/healthcare.db backup/healthcare_backup_$(date +%Y%m%d_%H%M%S).db
```

### **Restore Database**
```bash
# Stop the application first
# Copy backup file back
cp backup/healthcare_backup_YYYYMMDD_HHMMSS.db instance/healthcare.db
# Restart the application
```

---

## 🎯 **Next Steps**

1. **Access the Dashboard:** http://localhost:5000
2. **Login:** Use the default credentials above
3. **Explore Features:** Navigate through patients, monitoring, and analytics
4. **Add Data:** Create new patients and record vital signs
5. **Customize:** Modify the database schema if needed

---

## 📞 **Support**

If you continue to have issues:

1. **Check the logs** in the terminal for detailed error messages
2. **Verify file permissions** on the database directory
3. **Ensure all dependencies** are installed correctly
4. **Try the reset script** if the database is corrupted: `python reset_database.py`

The database setup is now complete and ready for use! 🎉
