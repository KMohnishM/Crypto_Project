# PowerShell Script to Generate TLS Certificates for MQTT Broker
# Requires OpenSSL (can be installed via chocolatey: choco install openssl)
# Or use Git Bash's OpenSSL: C:\Program Files\Git\usr\bin\openssl.exe

Write-Host "🔐 Generating TLS Certificates for MQTT Broker..." -ForegroundColor Cyan

# Set OpenSSL path (adjust if needed)
$openssl = "openssl"

# Test if OpenSSL is available
try {
    & $openssl version | Out-Null
} catch {
    Write-Host "❌ OpenSSL not found! Install it via:" -ForegroundColor Red
    Write-Host "   Option 1: choco install openssl" -ForegroundColor Yellow
    Write-Host "   Option 2: Use Git Bash OpenSSL at C:\Program Files\Git\usr\bin\openssl.exe" -ForegroundColor Yellow
    exit 1
}

# Navigate to certs directory
Set-Location $PSScriptRoot

# 1. Generate Certificate Authority (CA)
Write-Host "1️⃣ Generating CA private key..." -ForegroundColor Green
& $openssl genrsa -out ca.key 2048

Write-Host "2️⃣ Generating CA certificate..." -ForegroundColor Green
& $openssl req -new -x509 -days 3650 -key ca.key -out ca.crt -subj "/CN=MQTTBrokerCA/O=Healthcare IoT/C=US"

# 2. Generate Server Certificate
Write-Host "3️⃣ Generating server private key..." -ForegroundColor Green
& $openssl genrsa -out server.key 2048

Write-Host "4️⃣ Generating server certificate signing request..." -ForegroundColor Green
& $openssl req -new -key server.key -out server.csr -subj "/CN=mosquitto/O=Healthcare IoT/C=US"

Write-Host "5️⃣ Signing server certificate with CA..." -ForegroundColor Green
& $openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 3650

# 3. Generate Client Certificate (Optional - for mutual TLS)
Write-Host "6️⃣ Generating client private key..." -ForegroundColor Green
& $openssl genrsa -out client.key 2048

Write-Host "7️⃣ Generating client certificate signing request..." -ForegroundColor Green
& $openssl req -new -key client.key -out client.csr -subj "/CN=esp32-device/O=Healthcare IoT/C=US"

Write-Host "8️⃣ Signing client certificate with CA..." -ForegroundColor Green
& $openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out client.crt -days 3650

# Cleanup CSR files
Remove-Item server.csr -ErrorAction SilentlyContinue
Remove-Item client.csr -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "✅ Certificate generation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Generated files:" -ForegroundColor Cyan
Write-Host "  📄 ca.crt, ca.key       - Certificate Authority"
Write-Host "  📄 server.crt, server.key - MQTT Broker"
Write-Host "  📄 client.crt, client.key - ESP32/IoT Devices"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Keep these files secure (add *.key to .gitignore)"
Write-Host "  2. Copy ca.crt to ESP32 devices"
Write-Host "  3. Start MQTT broker: docker-compose up -d mosquitto"
