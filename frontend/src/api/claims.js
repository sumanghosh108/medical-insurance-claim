// Claims API — all calls with mock-data fallback for standalone use
import client from './client';

// ── Mock Data ──────────────────────────────────────────────────────────────
const now = new Date();
const d = (days) => new Date(now - days * 86400000).toISOString();

const MOCK_CLAIMS = [
    {
        metadata: { claim_id: 'claim_abc001', claim_number: 'CLM-2024001', status: 'approved', priority: 'medium', created_at: d(10), updated_at: d(2), created_by: 'user_1', assigned_to: 'adj_01' },
        claim_data: { claim_type: 'health', amount: { claimed_amount: 12500, currency: 'USD' }, personal_info: { first_name: 'Priya', last_name: 'Sharma', email: 'priya@example.com' }, incident_info: { description: 'Hospitalization for appendectomy surgery' } },
        validation: { is_valid: true, validation_score: 94.5, errors: [], warnings: [] },
        fraud_score: { fraud_probability: 0.08, risk_level: 'low', contributing_factors: [], model_version: '1.0.0' },
        processing: { documents_processed: 3, text_extraction_confidence: 97.2, entities_extracted: 18 },
    },
    {
        metadata: { claim_id: 'claim_abc002', claim_number: 'CLM-2024002', status: 'under_review', priority: 'high', created_at: d(5), updated_at: d(1), created_by: 'user_2', assigned_to: 'adj_02' },
        claim_data: { claim_type: 'auto', amount: { claimed_amount: 35000, currency: 'USD' }, personal_info: { first_name: 'Rahul', last_name: 'Verma', email: 'rahul@example.com' }, incident_info: { description: 'Major vehicle collision causing total loss' } },
        validation: { is_valid: true, validation_score: 78.0, errors: [], warnings: [{ code: 'AMOUNT_HIGH', message: 'Claimed amount is higher than typical for this category' }] },
        fraud_score: { fraud_probability: 0.52, risk_level: 'medium', contributing_factors: ['high_amount', 'recent_policy'], model_version: '1.0.0' },
        processing: { documents_processed: 5, text_extraction_confidence: 89.1, entities_extracted: 22 },
    },
    {
        metadata: { claim_id: 'claim_abc003', claim_number: 'CLM-2024003', status: 'processing', priority: 'urgent', created_at: d(1), updated_at: d(0), created_by: 'user_3', assigned_to: null },
        claim_data: { claim_type: 'property', amount: { claimed_amount: 85000, currency: 'USD' }, personal_info: { first_name: 'Anita', last_name: 'Patel', email: 'anita@example.com' }, incident_info: { description: 'Fire damage to residential property — kitchen and living room' } },
        validation: { is_valid: true, validation_score: 88.0, errors: [], warnings: [] },
        fraud_score: { fraud_probability: 0.18, risk_level: 'low', contributing_factors: [], model_version: '1.0.0' },
        processing: { documents_processed: 2, text_extraction_confidence: 91.5, entities_extracted: 14 },
    },
    {
        metadata: { claim_id: 'claim_abc004', claim_number: 'CLM-2024004', status: 'rejected', priority: 'low', created_at: d(20), updated_at: d(15), created_by: 'user_4', assigned_to: 'adj_01' },
        claim_data: { claim_type: 'health', amount: { claimed_amount: 450, currency: 'USD' }, personal_info: { first_name: 'Kiran', last_name: 'Rao', email: 'kiran@example.com' }, incident_info: { description: 'Prescription refill — policy exclusion applies' } },
        validation: { is_valid: false, validation_score: 42.0, errors: [{ code: 'POLICY_EXCLUSION', message: 'Treatment not covered under policy' }], warnings: [] },
        fraud_score: { fraud_probability: 0.05, risk_level: 'low', contributing_factors: [], model_version: '1.0.0' },
        processing: { documents_processed: 1, text_extraction_confidence: 99.0, entities_extracted: 8 },
    },
    {
        metadata: { claim_id: 'claim_abc005', claim_number: 'CLM-2024005', status: 'submitted', priority: 'medium', created_at: d(0), updated_at: d(0), created_by: 'user_5', assigned_to: null },
        claim_data: { claim_type: 'life', amount: { claimed_amount: 500000, currency: 'USD' }, personal_info: { first_name: 'Meena', last_name: 'Kumar', email: 'meena@example.com' }, incident_info: { description: 'Life insurance claim — policy holder deceased' } },
        validation: null,
        fraud_score: null,
        processing: null,
    },
    {
        metadata: { claim_id: 'claim_abc006', claim_number: 'CLM-2024006', status: 'paid', priority: 'medium', created_at: d(30), updated_at: d(25), created_by: 'user_6', assigned_to: 'adj_03' },
        claim_data: { claim_type: 'auto', amount: { claimed_amount: 8200, currency: 'USD' }, personal_info: { first_name: 'Deepak', last_name: 'Singh', email: 'deepak@example.com' }, incident_info: { description: 'Minor collision — windshield and bumper damage' } },
        validation: { is_valid: true, validation_score: 97.0, errors: [], warnings: [] },
        fraud_score: { fraud_probability: 0.03, risk_level: 'low', contributing_factors: [], model_version: '1.0.0' },
        processing: { documents_processed: 4, text_extraction_confidence: 98.7, entities_extracted: 20 },
    },
    {
        metadata: { claim_id: 'claim_abc007', claim_number: 'CLM-2024007', status: 'pending_documents', priority: 'high', created_at: d(7), updated_at: d(3), created_by: 'user_7', assigned_to: 'adj_02' },
        claim_data: { claim_type: 'health', amount: { claimed_amount: 22000, currency: 'USD' }, personal_info: { first_name: 'Kavya', last_name: 'Reddy', email: 'kavya@example.com' }, incident_info: { description: 'Cardiac procedure — stent placement' } },
        validation: { is_valid: false, validation_score: 60.0, errors: [], warnings: [{ code: 'MISSING_DOCS', message: 'Discharge summary required' }] },
        fraud_score: null,
        processing: { documents_processed: 1, text_extraction_confidence: 85.0, entities_extracted: 9 },
    },
    {
        metadata: { claim_id: 'claim_abc008', claim_number: 'CLM-2024008', status: 'under_review', priority: 'urgent', created_at: d(3), updated_at: d(1), created_by: 'user_8', assigned_to: 'adj_01' },
        claim_data: { claim_type: 'property', amount: { claimed_amount: 145000, currency: 'USD' }, personal_info: { first_name: 'Arjun', last_name: 'Nair', email: 'arjun@example.com' }, incident_info: { description: 'Flood damage — ground floor extensively damaged' } },
        validation: { is_valid: true, validation_score: 82.0, errors: [], warnings: [] },
        fraud_score: { fraud_probability: 0.77, risk_level: 'high', contributing_factors: ['large_amount', 'rapid_claim', 'location_risk'], model_version: '1.0.0' },
        processing: { documents_processed: 6, text_extraction_confidence: 88.3, entities_extracted: 25 },
    },
];

const MOCK_DOCS = [
    { document_id: 'doc_x001', claim_id: 'claim_abc001', document_type: 'medical_record', file_name: 'discharge_summary.pdf', file_size: 245000, content_type: 'application/pdf', uploaded_at: d(9), uploaded_by: 'user_1', processing_status: 'completed' },
    { document_id: 'doc_x002', claim_id: 'claim_abc001', document_type: 'invoice', file_name: 'hospital_bill.pdf', file_size: 98000, content_type: 'application/pdf', uploaded_at: d(9), uploaded_by: 'user_1', processing_status: 'completed' },
    { document_id: 'doc_x003', claim_id: 'claim_abc002', document_type: 'police_report', file_name: 'accident_report.pdf', file_size: 320000, content_type: 'application/pdf', uploaded_at: d(5), uploaded_by: 'user_2', processing_status: 'completed' },
];

const MOCK_STATS = {
    total_claims: 847,
    pending_review: 42,
    avg_processing_hours: 18.5,
    fraud_detected: 23,
    approval_rate: 0.74,
    total_amount_approved: 2_850_000,
};

const MONTHLY = [
    { month: 'Sep', health: 42, auto: 28, property: 15, life: 5 },
    { month: 'Oct', health: 55, auto: 32, property: 18, life: 8 },
    { month: 'Nov', health: 48, auto: 25, property: 22, life: 6 },
    { month: 'Dec', health: 38, auto: 20, property: 12, life: 4 },
    { month: 'Jan', health: 62, auto: 35, property: 20, life: 9 },
    { month: 'Feb', health: 71, auto: 40, property: 25, life: 11 },
];

const STATUS_DIST = [
    { name: 'Approved', value: 340, color: '#34d399' },
    { name: 'Processing', value: 120, color: '#38bdf8' },
    { name: 'Under Review', value: 95, color: '#fbbf24' },
    { name: 'Submitted', value: 85, color: '#94a3b8' },
    { name: 'Rejected', value: 78, color: '#f87171' },
    { name: 'Paid', value: 65, color: '#6ee7b7' },
    { name: 'Pending Docs', value: 64, color: '#a78bfa' },
];

const FRAUD_TREND = [
    { month: 'Sep', score: 12 }, { month: 'Oct', score: 18 }, { month: 'Nov', score: 15 },
    { month: 'Dec', score: 9 }, { month: 'Jan', score: 21 }, { month: 'Feb', score: 23 },
];

// ── API Functions ───────────────────────────────────────────────────────────
const USE_MOCK = !import.meta.env.VITE_API_URL;

function delay(ms = 400) { return new Promise(r => setTimeout(r, ms)); }

export async function fetchStats() {
    if (USE_MOCK) { await delay(300); return MOCK_STATS; }
    const res = await client.get('/health');
    return res.data;
}

export async function fetchMonthlyData() {
    await delay(200);
    return MONTHLY;
}

export async function fetchStatusDistribution() {
    await delay(200);
    return STATUS_DIST;
}

export async function fetchFraudTrend() {
    await delay(200);
    return FRAUD_TREND;
}

export async function fetchClaims(filters = {}) {
    if (USE_MOCK) {
        await delay(500);
        let claims = [...MOCK_CLAIMS];
        if (filters.status) claims = claims.filter(c => c.metadata.status === filters.status);
        if (filters.claim_type) claims = claims.filter(c => c.claim_data?.claim_type === filters.claim_type);
        if (filters.search) {
            const q = filters.search.toLowerCase();
            claims = claims.filter(c =>
                c.metadata.claim_number.toLowerCase().includes(q) ||
                c.claim_data?.personal_info?.first_name?.toLowerCase().includes(q) ||
                c.claim_data?.personal_info?.last_name?.toLowerCase().includes(q)
            );
        }
        return { claims, total_count: claims.length, has_more: false };
    }
    const res = await client.get('/claims', { params: filters });
    return res.data;
}

export async function fetchClaim(claimId) {
    if (USE_MOCK) {
        await delay(400);
        const claim = MOCK_CLAIMS.find(c => c.metadata.claim_id === claimId);
        if (!claim) throw new Error('Claim not found');
        return claim;
    }
    const res = await client.get(`/claims/${claimId}`);
    return res.data;
}

export async function submitClaim(data) {
    if (USE_MOCK) {
        await delay(1200);
        const id = `claim_${Math.random().toString(36).substr(2, 8)}`;
        return {
            metadata: {
                claim_id: id,
                claim_number: `CLM-${Date.now()}`,
                status: 'submitted',
                priority: data.priority || 'medium',
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
                created_by: 'current_user',
            },
            next_steps: [
                'Claim submitted successfully',
                'Documents are being processed',
                'You will receive updates via email',
                'Expected processing time: 24-48 hours',
            ],
        };
    }
    const res = await client.post('/claims', data);
    return res.data;
}

export async function updateClaim(claimId, updates) {
    if (USE_MOCK) { await delay(600); return { message: 'Claim updated successfully', claim_id: claimId }; }
    const res = await client.patch(`/claims/${claimId}`, updates);
    return res.data;
}

export async function fetchDocuments(claimId) {
    if (USE_MOCK) {
        await delay(300);
        return claimId ? MOCK_DOCS.filter(d => d.claim_id === claimId) : MOCK_DOCS;
    }
    const res = await client.get('/documents', { params: { claim_id: claimId } });
    return res.data;
}

export async function uploadDocument(data) {
    if (USE_MOCK) {
        await delay(800);
        return {
            metadata: { document_id: `doc_${Math.random().toString(36).substr(2, 6)}`, ...data, processing_status: 'pending', uploaded_at: new Date().toISOString() },
            presigned_url: 'https://mock-s3.example.com/upload',
        };
    }
    const res = await client.post('/documents/upload', data);
    return res.data;
}
