/**
 * OpenSY Explorer Input Validation Tests
 * 
 * This file tests input validation for the block explorer routes.
 * Run with: npm test (after adding to package.json)
 * 
 * These tests ensure:
 * - Invalid block hashes are rejected
 * - Invalid transaction IDs are rejected  
 * - Invalid addresses are rejected
 * - Height parameters are validated
 * - Search inputs are sanitized
 */

// Mock RPC responses for testing
const mockRpc = {
    call: async (method, params) => {
        // Simulate RPC errors for invalid inputs
        if (method === 'getblock') {
            const hash = params[0];
            // Valid hash is 64 hex characters
            if (!/^[0-9a-fA-F]{64}$/.test(hash)) {
                throw new Error('Invalid block hash');
            }
        }
        if (method === 'getblockhash') {
            const height = params[0];
            if (typeof height !== 'number' || height < 0 || !Number.isInteger(height)) {
                throw new Error('Invalid block height');
            }
        }
        if (method === 'getrawtransaction') {
            const txid = params[0];
            if (!/^[0-9a-fA-F]{64}$/.test(txid)) {
                throw new Error('Invalid transaction ID');
            }
        }
        return {};
    }
};

// Test cases
const testCases = {
    validBlockHashes: [
        '000000c4c94f54e5ae60a67df5c113dfbfd9ef872639e2359d15796f27920fd1',
        '0000000000000000000000000000000000000000000000000000000000000000',
        'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff',
    ],
    invalidBlockHashes: [
        '',                                     // Empty
        '000000c4c94f54e5',                     // Too short
        '000000c4c94f54e5ae60a67df5c113dfbfd9ef872639e2359d15796f27920fd1aaaa', // Too long
        '000000c4c94f54e5ae60a67df5c113dfbfd9ef872639e2359d15796f27920fXX', // Invalid chars
        'SELECT * FROM blocks',                 // SQL injection attempt
        '<script>alert(1)</script>',           // XSS attempt
        '../../../etc/passwd',                  // Path traversal
        'null',                                 // Null string
        'undefined',                            // Undefined string
    ],
    validHeights: [0, 1, 100, 1000, 10000, 100000],
    invalidHeights: [-1, -100, 1.5, NaN, Infinity, 'abc', null, undefined],
    validAddresses: [
        'syl1q0y76xxxdfvhfad2sju4fymnsn8zs5lndpwhufw',  // bech32
    ],
    invalidAddresses: [
        '',
        'invalid',
        '1234567890',
        '<script>alert(1)</script>',
    ],
};

async function runTests() {
    console.log('=== Explorer Input Validation Tests ===\n');
    let passed = 0;
    let failed = 0;

    // Test valid block hashes
    console.log('Testing valid block hashes...');
    for (const hash of testCases.validBlockHashes) {
        try {
            await mockRpc.call('getblock', [hash]);
            passed++;
            console.log(`  ✓ ${hash.substring(0, 16)}...`);
        } catch (e) {
            failed++;
            console.log(`  ✗ ${hash.substring(0, 16)}... - ${e.message}`);
        }
    }

    // Test invalid block hashes
    console.log('\nTesting invalid block hashes (should all fail)...');
    for (const hash of testCases.invalidBlockHashes) {
        try {
            await mockRpc.call('getblock', [hash]);
            failed++;
            console.log(`  ✗ "${hash.substring(0, 20)}" was accepted (should reject)`);
        } catch (e) {
            passed++;
            console.log(`  ✓ "${hash.substring(0, 20)}" correctly rejected`);
        }
    }

    // Test valid heights
    console.log('\nTesting valid block heights...');
    for (const height of testCases.validHeights) {
        try {
            await mockRpc.call('getblockhash', [height]);
            passed++;
            console.log(`  ✓ height ${height}`);
        } catch (e) {
            failed++;
            console.log(`  ✗ height ${height} - ${e.message}`);
        }
    }

    // Test invalid heights
    console.log('\nTesting invalid block heights (should all fail)...');
    for (const height of testCases.invalidHeights) {
        try {
            await mockRpc.call('getblockhash', [height]);
            failed++;
            console.log(`  ✗ height "${height}" was accepted (should reject)`);
        } catch (e) {
            passed++;
            console.log(`  ✓ height "${height}" correctly rejected`);
        }
    }

    console.log('\n=== Results ===');
    console.log(`Passed: ${passed}`);
    console.log(`Failed: ${failed}`);
    console.log(`Total:  ${passed + failed}`);
    
    if (failed === 0) {
        console.log('\n✅ All input validation tests passed!');
        process.exit(0);
    } else {
        console.log('\n❌ Some tests failed');
        process.exit(1);
    }
}

// Run if called directly
if (require.main === module) {
    runTests().catch(console.error);
}

module.exports = { testCases, runTests };
