# 🚀 Healthcare IoT Security Implementation - Setup Script
# Windows PowerShell Script

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "  Healthcare IoT Monitoring System - Security Setup" -ForegroundColor Cyan
Write-Host "  Phase 1: MQTT + TLS | Phase 2: Ascon Encryption" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "📋 Checking prerequisites..." -ForegroundColor Yellow

# Check Docker
try {
    docker --version | Out-Null
    Write-Host "  ✅ Docker installed" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Docker not found! Please install Docker Desktop" -ForegroundColor Red
    exit 1
}

# Check Docker Compose
try {
    docker-compose --version | Out-Null
    Write-Host "  ✅ Docker Compose installed" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Docker Compose not found!" -ForegroundColor Red
    exit 1
}

# Check OpenSSL
try {
    openssl version | Out-Null
    Write-Host "  ✅ OpenSSL installed" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  OpenSSL not found - attempting to use Git's OpenSSL" -ForegroundColor Yellow
    $gitOpenSSL = "C:\Program Files\Git\usr\bin\openssl.exe"
    if (Test-Path $gitOpenSSL) {
        $env:Path = "C:\Program Files\Git\usr\bin;" + $env:Path
        Write-Host "  ✅ Using Git's OpenSSL" -ForegroundColor Green
    } else {
        Write-Host "  ❌ OpenSSL not available. Install via: choco install openssl" -ForegroundColor Red
        Write-Host "     Or ensure Git is installed" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "🔐 Step 1: Generating TLS Certificates..." -ForegroundColor Yellow
Write-Host "-" * 80 -ForegroundColor DarkGray

Set-Location "config\mosquitto\certs"

if (Test-Path "ca.crt") {
    Write-Host "  ⚠️  Certificates already exist. Regenerate? (y/N): " -ForegroundColor Yellow -NoNewline
    $response = Read-Host
    if ($response -eq 'y' -or $response -eq 'Y') {
        Remove-Item *.crt, *.key, *.srl -ErrorAction SilentlyContinue
        & .\generate_certs.ps1
    } else {
        Write-Host "  ⏩ Skipping certificate generation" -ForegroundColor Gray
    }
} else {
    & .\generate_certs.ps1
}

Set-Location "..\..\.."

Write-Host ""
Write-Host "📦 Step 2: Installing Python Dependencies..." -ForegroundColor Yellow
Write-Host "-" * 80 -ForegroundColor DarkGray

Write-Host "  ℹ️  Dependencies will be installed during Docker build" -ForegroundColor Cyan
Write-Host "  📄 Added to requirements.txt: ascon, paho-mqtt" -ForegroundColor Cyan

Write-Host ""
Write-Host "🔧 Step 3: Configuration Review..." -ForegroundColor Yellow
Write-Host "-" * 80 -ForegroundColor DarkGray

Write-Host "  📁 Environment: config\environment\development.env" -ForegroundColor Cyan
Write-Host "  🔑 Key Storage: data\keys\" -ForegroundColor Cyan
Write-Host "  📜 Certificates: config\mosquitto\certs\" -ForegroundColor Cyan

Write-Host ""
Write-Host "⚙️  Step 4: Deployment Mode Selection..." -ForegroundColor Yellow
Write-Host "-" * 80 -ForegroundColor DarkGray

Write-Host ""
Write-Host "  Choose deployment mode:" -ForegroundColor White
Write-Host "    [1] 🔐 Secure Mode (MQTT + Ascon) - RECOMMENDED" -ForegroundColor Green
Write-Host "    [2] ⚠️  Legacy Mode (HTTP only) - Testing Only" -ForegroundColor Yellow
Write-Host "    [3] 🔄 Hybrid Mode (Both available)" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Selection (1-3): " -ForegroundColor White -NoNewline
$mode = Read-Host

switch ($mode) {
    '1' {
        Write-Host "  ✅ Activating Secure Mode..." -ForegroundColor Green
        
        # Backup originals
        if (Test-Path "services\patient_simulator\send_data.py") {
            Copy-Item "services\patient_simulator\send_data.py" "services\patient_simulator\send_data_legacy.py" -Force
        }
        if (Test-Path "services\main_host\app.py") {
            Copy-Item "services\main_host\app.py" "services\main_host\app_legacy.py" -Force
        }
        
        # Activate encrypted versions
        Copy-Item "services\patient_simulator\send_data_encrypted.py" "services\patient_simulator\send_data.py" -Force
        Copy-Item "services\main_host\app_encrypted.py" "services\main_host\app.py" -Force
        
        Write-Host "  ✅ Secure versions activated" -ForegroundColor Green
    }
    '2' {
        Write-Host "  ⚠️  Legacy mode - no changes made" -ForegroundColor Yellow
        Write-Host "  ⚠️  WARNING: Not production ready!" -ForegroundColor Red
    }
    '3' {
        Write-Host "  🔄 Hybrid mode - both versions available" -ForegroundColor Cyan
        Write-Host "  ℹ️  Use README_DEPLOYMENT.md in each service for switching" -ForegroundColor Cyan
    }
    default {
        Write-Host "  ❌ Invalid selection - keeping current state" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "🐳 Step 5: Docker Deployment..." -ForegroundColor Yellow
Write-Host "-" * 80 -ForegroundColor DarkGray

Write-Host "  Build and start containers? (Y/n): " -ForegroundColor White -NoNewline
$deploy = Read-Host

if ($deploy -ne 'n' -and $deploy -ne 'N') {
    Write-Host ""
    Write-Host "  🔨 Building Docker images..." -ForegroundColor Cyan
    docker-compose build
    
    Write-Host ""
    Write-Host "  🚀 Starting services..." -ForegroundColor Cyan
    docker-compose up -d
    
    Write-Host ""
    Write-Host "  ⏳ Waiting for services to initialize (30s)..." -ForegroundColor Cyan
    Start-Sleep -Seconds 30
    
    Write-Host ""
    Write-Host "  📊 Container Status:" -ForegroundColor Cyan
    docker-compose ps
    
} else {
    Write-Host "  ⏩ Skipping deployment - run manually: docker-compose up --build" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Green
Write-Host "  ✅ Setup Complete!" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Green
Write-Host ""

Write-Host "📚 Next Steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  1️⃣  View logs:" -ForegroundColor White
Write-Host "     docker-compose logs -f patient_simulator" -ForegroundColor Gray
Write-Host "     docker-compose logs -f main_host" -ForegroundColor Gray
Write-Host ""
Write-Host "  2️⃣  Access services:" -ForegroundColor White
Write-Host "     🌐 Web Dashboard: http://localhost:5000" -ForegroundColor Cyan
Write-Host "     📊 Grafana:       http://localhost:3001 (admin/admin)" -ForegroundColor Cyan
Write-Host "     📈 Prometheus:    http://localhost:9090" -ForegroundColor Cyan
Write-Host "     🔔 AlertManager:  http://localhost:9093" -ForegroundColor Cyan
Write-Host ""
Write-Host "  3️⃣  Verify encryption:" -ForegroundColor White
Write-Host "     Look for '🔐 encrypted' in patient_simulator logs" -ForegroundColor Gray
Write-Host "     Look for '🔓 Decrypted' in main_host logs" -ForegroundColor Gray
Write-Host ""
Write-Host "  4️⃣  Check key storage:" -ForegroundColor White
Write-Host "     Get-Content data\keys\device_keys.json" -ForegroundColor Gray
Write-Host ""

Write-Host "🔐 Security Status:" -ForegroundColor Yellow
Write-Host "  ✅ MQTT Broker with TLS" -ForegroundColor Green
Write-Host "  ✅ Ascon-128 Payload Encryption" -ForegroundColor Green
Write-Host "  ✅ Per-Device Key Management" -ForegroundColor Green
Write-Host "  ⏳ Service Authentication (Phase 3)" -ForegroundColor Yellow
Write-Host "  ⏳ Database Encryption (Phase 4)" -ForegroundColor Yellow
Write-Host ""

Write-Host "📖 Documentation:" -ForegroundColor Yellow
Write-Host "  - services/patient_simulator/README_DEPLOYMENT.md" -ForegroundColor Gray
Write-Host "  - services/main_host/README_DEPLOYMENT.md" -ForegroundColor Gray
Write-Host "  - services/common/crypto_utils.py (implementation details)" -ForegroundColor Gray
Write-Host ""

Write-Host "Press any key to exit..." -ForegroundColor DarkGray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
