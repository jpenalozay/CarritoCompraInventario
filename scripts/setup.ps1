Write-Host "🚀 Setting up E-commerce Big Data project..." -ForegroundColor Green

# Create data directories
Write-Host "📁 Creating data directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "data\cassandra"
New-Item -ItemType Directory -Force -Path "data\redis"
New-Item -ItemType Directory -Force -Path "redis\config"

# Start infrastructure services
Write-Host "🐳 Starting infrastructure services..." -ForegroundColor Yellow
docker-compose up -d cassandra redis

# Wait for services to start
Write-Host "⏰ Waiting for services to start (90 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 90

# Test Cassandra connection
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
    Write-Host "⏳ Cassandra retry $retryCount of $maxRetries..." -ForegroundColor Yellow
    Start-Sleep -Seconds 20
} while ($retryCount -lt $maxRetries)

# Test Redis connection
Write-Host "🔍 Testing Redis connection..." -ForegroundColor Yellow
$redisRetries = 5
$redisRetryCount = 0
do {
    try {
        $redisTest = docker exec ecommerce-redis redis-cli ping 2>$null
        if ($redisTest -eq "PONG") {
            Write-Host "✅ Redis is ready!" -ForegroundColor Green
            break
        }
    }
    catch {
        Write-Host "Redis connection test failed, retrying..." -ForegroundColor Yellow
    }
    $redisRetryCount++
    Write-Host "⏳ Redis retry $redisRetryCount of $redisRetries..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
} while ($redisRetryCount -lt $redisRetries)

# Initialize Cassandra schemas
if ($retryCount -lt $maxRetries) {
    Write-Host "📊 Creating Cassandra schemas..." -ForegroundColor Yellow
    try {
        Write-Host "   Creating keyspace..." -ForegroundColor Cyan
        Get-Content "cassandra\schemas\01-keyspace.cql" -Encoding UTF8 | docker exec -i ecommerce-cassandra cqlsh
        
        Write-Host "   Creating tables..." -ForegroundColor Cyan
        Get-Content "cassandra\schemas\02-tables.cql" -Encoding UTF8 | docker exec -i ecommerce-cassandra cqlsh
        
        Write-Host "   Inserting sample data..." -ForegroundColor Cyan
        Get-Content "cassandra\schemas\03-sample-data.cql" -Encoding UTF8 | docker exec -i ecommerce-cassandra cqlsh
        
        Write-Host "✅ Cassandra schemas created successfully!" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️ Cassandra schema creation failed. Error: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Initialize Redis with sample data
if ($redisRetryCount -lt $redisRetries) {
    Write-Host "📊 Setting up Redis cache..." -ForegroundColor Yellow
    try {
        # Test Redis databases
        docker exec ecommerce-redis redis-cli SELECT 0
        docker exec ecommerce-redis redis-cli SET "test:connection" "success" EX 60
        
        # Create sample cache entries
        Write-Host "   Creating sample cache entries..." -ForegroundColor Cyan
        
        # API Cache samples (DB 0)
        docker exec ecommerce-redis redis-cli SELECT 0
        docker exec ecommerce-redis redis-cli SET "api:revenue:uk:latest" '{"value": 125.50, "currency": "GBP", "timestamp": "2025-07-04T10:30:00Z"}' EX 300
        docker exec ecommerce-redis redis-cli SET "api:customers:uk:count" "1247" EX 300
        
        # Session samples (DB 1)  
        docker exec ecommerce-redis redis-cli SELECT 1
        docker exec ecommerce-redis redis-cli HSET "session:ses001:cart" "item_count" "3" "total_value" "125.50" "currency" "GBP"
        docker exec ecommerce-redis redis-cli EXPIRE "session:ses001:cart" 1800
        
        # Metrics samples (DB 2)
        docker exec ecommerce-redis redis-cli SELECT 2
        docker exec ecommerce-redis redis-cli SET "metrics:revenue:uk:current" "125.50" EX 300
        docker exec ecommerce-redis redis-cli SET "metrics:orders:uk:current" "15" EX 300
        
        Write-Host "✅ Redis cache setup completed!" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️ Redis setup failed. Error: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Start web UIs
Write-Host "🌐 Starting web interfaces..." -ForegroundColor Yellow
docker-compose up -d cassandra-web redis-commander

Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host "" -ForegroundColor White
Write-Host "🔗 Available Services:" -ForegroundColor White
Write-Host "📊 Cassandra CQL: docker exec -it ecommerce-cassandra cqlsh" -ForegroundColor Cyan
Write-Host "🌐 Cassandra Web UI: http://localhost:3000" -ForegroundColor Cyan
Write-Host "🚀 Redis CLI: docker exec -it ecommerce-redis redis-cli" -ForegroundColor Cyan  
Write-Host "🌐 Redis Web UI: http://localhost:8081 (admin/admin123)" -ForegroundColor Cyan
Write-Host "🔍 Check status: docker ps" -ForegroundColor Cyan
Write-Host "" -ForegroundColor White
Write-Host "🧪 Test Commands:" -ForegroundColor White
Write-Host "Redis: docker exec ecommerce-redis redis-cli ping" -ForegroundColor Gray
Write-Host "Cassandra: docker exec ecommerce-cassandra cqlsh -e 'USE ecommerce_analytics; SELECT * FROM revenue_by_country_time LIMIT 3;'" -ForegroundColor Gray