const redis = require('redis');

async function testRedisConnection() {
    console.log('🔧 Testing Redis connection...');
    
    const client = redis.createClient({
        socket: {
            host: 'redis',
            port: 6379,
            family: 4
        }
    });

    client.on('error', (err) => {
        console.error('❌ Redis Error:', err);
    });

    client.on('connect', () => {
        console.log('🔗 Redis connected');
    });

    client.on('ready', () => {
        console.log('✅ Redis ready');
    });

    try {
        await client.connect();
        console.log('✅ Connection successful');
        
        // Test basic operation
        await client.set('test', 'hello');
        const value = await client.get('test');
        console.log('✅ Test operation result:', value);
        
        await client.disconnect();
        console.log('✅ Disconnected successfully');
    } catch (error) {
        console.error('❌ Connection failed:', error);
    }
}

testRedisConnection(); 