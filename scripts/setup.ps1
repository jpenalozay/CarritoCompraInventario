Write-Host "🚀 Setting up E-commerce Big Data project..." -ForegroundColor Green

# Create data directories
Write-Host "📁 Creating data directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "data\cassandra"

# Start Cassandra with simplified config
Write-Host "🐳 Starting Cassandra cluster..." -ForegroundColor Yellow
docker-compose up -d cassandra

# Wait longer for startup
Write-Host "⏰ Waiting for Cassandra to start (90 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 90

# Test connection with more retries
Write-Host "🔍 Testing Cassandra connection..." -ForegroundColor Yellow
$maxRetries = 8
$retryCount = 0
do {
    try {
        $testResult = docker exec ecommerce-cassandra cqlsh -e "DESCRIBE CLUSTER" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Cassandra is ready!" -ForegroundColor Green
            break
        }
    }
    catch {
        Write-Host "Connection test failed, retrying..." -ForegroundColor Yellow
    }
    $retryCount++
    Write-Host "⏳ Retry $retryCount of $maxRetries..." -ForegroundColor Yellow
    Start-Sleep -Seconds 20
} while ($retryCount -lt $maxRetries)

if ($retryCount -eq $maxRetries) {
    Write-Host "❌ Cassandra failed to start. Check logs with: docker logs ecommerce-cassandra" -ForegroundColor Red
    exit 1
}

# Initialize schemas (NOMBRES CORREGIDOS)
Write-Host "📊 Creating database schemas..." -ForegroundColor Yellow
try {
    # 1. Crear keyspace
    Write-Host "   Creating keyspace..." -ForegroundColor Cyan
    Get-Content "cassandra\schemas\01-keyspace.cql" -Encoding UTF8 | docker exec -i ecommerce-cassandra cqlsh
    
    # 2. Crear tablas (NOMBRE CORREGIDO)
    Write-Host "   Creating tables..." -ForegroundColor Cyan
    Get-Content "cassandra\schemas\02-tables.cql" -Encoding UTF8 | docker exec -i ecommerce-cassandra cqlsh
    
    # 3. Insertar datos de ejemplo
    Write-Host "   Inserting sample data..." -ForegroundColor Cyan
    Get-Content "cassandra\schemas\03-sample-data.cql" -Encoding UTF8 | docker exec -i ecommerce-cassandra cqlsh
    
    Write-Host "✅ Schemas created successfully!" -ForegroundColor Green
}
catch {
    Write-Host "⚠️ Schema creation failed. Error: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "You can create them manually later." -ForegroundColor Yellow
}

# Start web UI
Write-Host "🌐 Starting Cassandra Web UI..." -ForegroundColor Yellow
docker-compose up -d cassandra-web

Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host "📊 Cassandra CQL: docker exec -it ecommerce-cassandra cqlsh" -ForegroundColor Cyan
Write-Host "🌐 Web UI: http://localhost:3000" -ForegroundColor Cyan
Write-Host "🔍 Check status: docker ps" -ForegroundColor Cyan
Write-Host "🔍 Verify data: docker exec -it ecommerce-cassandra cqlsh -e 'USE ecommerce_analytics; SELECT * FROM revenue_by_country_time LIMIT 5;'" -ForegroundColor Cyan