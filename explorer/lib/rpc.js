const axios = require('axios');

const rpcConfig = {
    host: process.env.RPC_HOST || '127.0.0.1',
    port: process.env.RPC_PORT || 9632,
    user: process.env.RPC_USER || 'opensy',
    password: process.env.RPC_PASSWORD
};

// CRITICAL: Refuse to start without password in production
if (!rpcConfig.password) {
    console.error('');
    console.error('═══════════════════════════════════════════════════════════════');
    console.error('  FATAL: RPC_PASSWORD environment variable must be set');
    console.error('═══════════════════════════════════════════════════════════════');
    console.error('');
    console.error('  The block explorer requires a secure RPC password to connect');
    console.error('  to the OpenSY node. This prevents unauthorized access.');
    console.error('');
    console.error('  To start the explorer:');
    console.error('');
    console.error('    # Generate a secure password:');
    console.error('    export RPC_PASSWORD=$(openssl rand -hex 32)');
    console.error('');
    console.error('    # Or use the same password from your opensy.conf:');
    console.error('    export RPC_PASSWORD="your_rpcpassword_from_config"');
    console.error('');
    console.error('    # Then start the explorer:');
    console.error('    npm start');
    console.error('');
    console.error('═══════════════════════════════════════════════════════════════');
    console.error('');
    process.exit(1);
}

// Warn about weak passwords
const weakPasswords = ['password', 'admin', 'changeme', 'miner', 'minerpass', '123456', 'opensy'];
for (const weak of weakPasswords) {
    if (rpcConfig.password.toLowerCase().includes(weak)) {
        console.warn('');
        console.warn('⚠️  WARNING: RPC password appears weak!');
        console.warn('   Generate a secure password: openssl rand -hex 32');
        console.warn('');
        break;
    }
}

async function call(method, params = []) {
    // SECURITY: Build URL without credentials to prevent accidental logging
    // Credentials are passed via axios auth config, never in URL
    const url = `http://${rpcConfig.host}:${rpcConfig.port}`;
    
    const response = await axios.post(url, {
        jsonrpc: '1.0',
        id: Date.now(),
        method,
        params
    }, {
        auth: {
            username: rpcConfig.user,
            password: rpcConfig.password
        },
        headers: {
            'Content-Type': 'application/json'
        }
    });
    
    if (response.data.error) {
        throw new Error(response.data.error.message);
    }
    
    return response.data.result;
}

module.exports = { call };
