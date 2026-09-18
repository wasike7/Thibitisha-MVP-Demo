const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

const PORT = Number(process.env.PORT || 3000);
const APP_ROOT = path.resolve(__dirname, '..');
const DATA_DIR = path.join(__dirname, 'data');
const DATA_FILE = path.join(DATA_DIR, 'verifications.json');
const HTML_FILE = path.join(APP_ROOT, 'Thibitisha_MVP_Demo.html');
const BANK_HTML_FILE = path.join(APP_ROOT, 'Thibitisha_Bank_Demo.html');

const scenarioResults = {
  safe: {
    decision: 'PROCEED',
    riskScore: 145,
    tier: 'LOW',
    amount: 5000,
    signals: {
      simSwap: { status: 'SAFE', detail: 'Last swap: 59 days ago' },
      device: { status: 'MATCH', detail: 'Known device fingerprint' },
      location: { status: 'NEARBY', detail: '0.3km from home base' },
      velocity: { status: 'NORMAL', detail: '3 transactions today' }
    }
  },
  simswap: {
    decision: 'BLOCK',
    riskScore: 892,
    tier: 'CRITICAL',
    amount: 45000,
    signals: {
      simSwap: { status: 'TODAY', detail: 'Swapped 2 hours ago' },
      device: { status: 'MISMATCH', detail: 'Unknown device detected' },
      location: { status: 'ANOMALY', detail: '450km from home base' },
      velocity: { status: 'HIGH', detail: '12 transactions attempted today' }
    }
  },
  merchant: {
    decision: 'PROCEED',
    riskScore: 67,
    tier: 'LOW',
    amount: 12000,
    signals: {
      simSwap: { status: 'SAFE', detail: 'No swap in 90 days' },
      merchant: { status: 'PLATINUM', detail: 'ABC Electronics Ltd' },
      device: { status: 'MATCH', detail: 'Known device' },
      location: { status: 'NEARBY', detail: 'Near merchant location' }
    }
  }
};

function ensureStore() {
  fs.mkdirSync(DATA_DIR, { recursive: true });
  if (!fs.existsSync(DATA_FILE)) fs.writeFileSync(DATA_FILE, '[]\n');
}

function readVerifications() {
  ensureStore();
  try {
    const records = JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
    return Array.isArray(records) ? records : [];
  } catch {
    return [];
  }
}

function writeVerifications(records) {
  fs.writeFileSync(DATA_FILE, `${JSON.stringify(records.slice(0, 100), null, 2)}\n`);
}

function sendJson(response, status, payload) {
  response.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-store',
    'Access-Control-Allow-Origin': '*'
  });
  response.end(JSON.stringify(payload));
}

function sendFile(response, filePath, contentType) {
  response.writeHead(200, { 'Content-Type': contentType });
  fs.createReadStream(filePath).pipe(response);
}

function readBody(request) {
  return new Promise((resolve, reject) => {
    let body = '';
    request.on('data', chunk => {
      body += chunk;
      if (body.length > 10000) reject(new Error('Request body too large'));
    });
    request.on('end', () => {
      try { resolve(body ? JSON.parse(body) : {}); }
      catch { reject(new Error('Request body must be valid JSON')); }
    });
    request.on('error', reject);
  });
}

function getStats() {
  const records = readVerifications();
  const byTier = records.reduce((counts, record) => {
    counts[record.tier] = (counts[record.tier] || 0) + 1;
    return counts;
  }, { LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0 });
  return {
    total_verifications: records.length,
    total_blocked: records.filter(record => record.decision === 'BLOCK').length,
    by_risk_tier: byTier,
    supported_mnos: ['airtel', 'safaricom', 'telkom', 'faiba']
  };
}

function getMerchant(tillNumber) {
  const merchants = {
    '123456': {
      name: 'ABC Electronics Ltd', till_number: '123456', paybill_number: '987654', badge: 'PLATINUM', verified: true,
      registration_number: 'BN/2023/123456', verified_since: '2024-01-15', kra_status: 'ACTIVE',
      location: { county: 'Nairobi', town: 'Westlands' }, complaints_90d: 3, dispute_rate: 0.001,
      monthly_volume_kes: 4200000, monthly_transactions: 2400
    },
    '789012': {
      name: 'SuperMart Kenya', till_number: '789012', paybill_number: '876543', badge: 'GOLD', verified: true,
      registration_number: 'BN/2022/789012', verified_since: '2023-06-10', kra_status: 'ACTIVE',
      location: { county: 'Nairobi', town: 'Kilimani' }, complaints_90d: 2, dispute_rate: 0.003,
      monthly_volume_kes: 1800000, monthly_transactions: 1200
    }
  };
  return merchants[tillNumber];
}

async function handleRequest(request, response) {
  const url = new URL(request.url, `http://${request.headers.host || 'localhost'}`);
  if (request.method === 'OPTIONS') {
    response.writeHead(204, { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET,POST,OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type' });
    return response.end();
  }

  if (request.method === 'GET' && url.pathname === '/api/health') {
    return sendJson(response, 200, { status: 'ok', service: 'thibitisha-api', timestamp: new Date().toISOString() });
  }

  if (request.method === 'GET' && url.pathname === '/health') {
    return sendJson(response, 200, { status: 'healthy', version: '1.0.0', adapters: { airtel: 'AVAILABLE', safaricom: 'AVAILABLE', telkom: 'AVAILABLE', faiba: 'AVAILABLE' } });
  }

  if (request.method === 'GET' && (url.pathname === '/stats' || url.pathname === '/api/stats')) {
    return sendJson(response, 200, getStats());
  }

  if (request.method === 'GET' && url.pathname === '/api/verifications') {
    return sendJson(response, 200, { data: readVerifications() });
  }

  if (request.method === 'POST' && url.pathname === '/api/verifications') {
    try {
      const body = await readBody(request);
      const scenario = body.scenario || 'safe';
      const result = scenarioResults[scenario];
      if (!result) return sendJson(response, 400, { error: 'Unknown verification scenario' });
      const record = {
        id: `VRF-${new Date().toISOString().slice(0, 10).replaceAll('-', '')}-${crypto.randomBytes(3).toString('hex')}`,
        scenario,
        institution: String(body.institution || 'Demo Bank').slice(0, 80),
        amount: Number(body.amount || result.amount),
        createdAt: new Date().toISOString(),
        ...result
      };
      const records = [record, ...readVerifications()];
      writeVerifications(records);
      return sendJson(response, 201, { data: record });
    } catch (error) {
      return sendJson(response, 400, { error: error.message });
    }
  }

  if (request.method === 'GET' && url.pathname === '/api/merchants') {
    const query = (url.searchParams.get('q') || '').trim().toLowerCase();
    const merchant = ['123456', '789012']
      .map(getMerchant)
      .find(candidate => !query || [candidate.name, candidate.till_number, candidate.paybill_number]
        .some(value => value.toLowerCase().includes(query)));
    if (merchant) {
      return sendJson(response, 200, { data: merchant });
    }
    return sendJson(response, 404, { error: 'Merchant not found' });
  }

  if (request.method === 'POST' && url.pathname === '/api/merchant-transactions') {
    try {
      const body = await readBody(request);
      const tillNumber = String(body.till_number || '').trim();
      const merchant = getMerchant(tillNumber);
      const amount = Number(body.amount);
      if (!merchant) return sendJson(response, 404, { error: 'Merchant not found' });
      if (!Number.isFinite(amount) || amount <= 0) return sendJson(response, 400, { error: 'Amount must be greater than zero' });
      return sendJson(response, 201, {
        data: {
          transaction_id: `MTR-${new Date().toISOString().slice(0, 10).replaceAll('-', '')}-${crypto.randomBytes(3).toString('hex')}`,
          status: 'AUTHORIZED',
          merchant: merchant.name,
          till_number: merchant.till_number,
          amount,
          currency: 'KES',
          message: 'Merchant verified. Transaction authorized for the synthetic demo.'
        }
      });
    } catch (error) {
      return sendJson(response, 400, { error: error.message });
    }
  }

  const merchantMatch = url.pathname.match(/^\/v1\/merchants\/([^/]+)$/);
  if (request.method === 'GET' && merchantMatch) {
    const merchant = getMerchant(merchantMatch[1]);
    if (!merchant) return sendJson(response, 404, { detail: 'Merchant not found' });
    return sendJson(response, 200, merchant);
  }

  if (request.method === 'GET' && (url.pathname === '/' || url.pathname === '/Thibitisha_MVP_Demo.html')) {
    return sendFile(response, HTML_FILE, 'text/html; charset=utf-8');
  }

  if (request.method === 'GET' && (url.pathname === '/bank-dashboard' || url.pathname === '/Thibitisha_Bank_Demo.html')) {
    return sendFile(response, BANK_HTML_FILE, 'text/html; charset=utf-8');
  }

  sendJson(response, 404, { error: 'Route not found' });
}

ensureStore();
http.createServer((request, response) => {
  handleRequest(request, response).catch(error => sendJson(response, 500, { error: error.message }));
}).listen(PORT, () => console.log(`Thibitisha API running at http://localhost:${PORT}`));
