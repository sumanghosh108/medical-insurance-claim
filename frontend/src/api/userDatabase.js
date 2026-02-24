/**
 * User Database — local JSON-based database for the frontend demo.
 * 
 * Mirrors the backend schema (CustomerUser / StaffUser) and uses
 * localStorage for persistence across page reloads.
 * 
 * In production, these would be real API calls to the backend.
 */

// ── Customer Users Table ────────────────────────────────

const DEFAULT_CUSTOMERS = [
    {
        id: 'usr_001',
        email: 'suman@example.com',
        password: 'test@123',
        full_name: 'Suman Ghosh',
        father_name: 'Ramesh Ghosh',
        phone: '+91 98765 43210',
        gender: 'male',
        marital_status: 'married',
        permanent_address: '12, Park Street, Kolkata, WB 700016',
        current_address: '45, MG Road, Bengaluru, KA 560001',
        is_active: true,
        is_verified: true,
        created_at: '2024-01-15T10:00:00Z',
    },
    {
        id: 'usr_002',
        email: 'priya@example.com',
        password: 'priya@123',
        full_name: 'Priya Sharma',
        father_name: 'Anil Sharma',
        phone: '+91 87654 32100',
        gender: 'female',
        marital_status: 'single',
        permanent_address: '78, Gandhi Nagar, Jaipur, RJ 302015',
        current_address: '78, Gandhi Nagar, Jaipur, RJ 302015',
        is_active: true,
        is_verified: true,
        created_at: '2024-02-20T09:30:00Z',
    },
    {
        id: 'usr_003',
        email: 'rahul@example.com',
        password: 'rahul@123',
        full_name: 'Rahul Verma',
        father_name: 'Suresh Verma',
        phone: '+91 76543 21000',
        gender: 'male',
        marital_status: 'single',
        permanent_address: '34, Nehru Place, New Delhi, DL 110019',
        current_address: '22, Indiranagar, Bengaluru, KA 560038',
        is_active: true,
        is_verified: false,
        created_at: '2024-03-10T14:15:00Z',
    },
    {
        id: 'usr_004',
        email: 'anita@example.com',
        password: 'anita@123',
        full_name: 'Anita Patel',
        father_name: 'Mahesh Patel',
        phone: '+91 65432 10000',
        gender: 'female',
        marital_status: 'married',
        permanent_address: '56, SG Highway, Ahmedabad, GJ 380015',
        current_address: '56, SG Highway, Ahmedabad, GJ 380015',
        is_active: true,
        is_verified: true,
        created_at: '2024-04-05T11:45:00Z',
    },
];


// ── Staff Users Table ────────────────────────────────

const DEFAULT_STAFF = [
    {
        id: 'stf_001',
        username: 'admin',
        email: 'admin@claimsportal.com',
        password: 'admin123',
        full_name: 'Admin User',
        phone: '+91 99999 00001',
        employee_id: 'EMP-001',
        department: 'IT',
        designation: 'System Administrator',
        role: 'admin',
        access_level: 3,
        is_active: true,
        failed_login_attempts: 0,
        locked_until: null,
        created_at: '2023-06-01T08:00:00Z',
    },
    {
        id: 'stf_002',
        username: 'adjuster',
        email: 'adjuster@claimsportal.com',
        password: 'staff2024',
        full_name: 'Ajay Adjuster',
        phone: '+91 99999 00101',
        employee_id: 'EMP-101',
        department: 'Claims',
        designation: 'Claims Adjuster',
        role: 'adjuster',
        access_level: 1,
        is_active: true,
        failed_login_attempts: 0,
        locked_until: null,
        created_at: '2023-08-15T09:00:00Z',
    },
    {
        id: 'stf_003',
        username: 'manager',
        email: 'manager@claimsportal.com',
        password: 'manager@1',
        full_name: 'Meera Manager',
        phone: '+91 99999 00201',
        employee_id: 'EMP-201',
        department: 'Management',
        designation: 'Senior Manager',
        role: 'manager',
        access_level: 2,
        is_active: true,
        failed_login_attempts: 0,
        locked_until: null,
        created_at: '2023-07-10T10:30:00Z',
    },
    {
        id: 'stf_004',
        username: 'fraud_analyst',
        email: 'fraud@claimsportal.com',
        password: 'fraud@123',
        full_name: 'Farhan Fraud Analyst',
        phone: '+91 99999 00301',
        employee_id: 'EMP-301',
        department: 'Fraud',
        designation: 'Senior Fraud Analyst',
        role: 'adjuster',
        access_level: 2,
        is_active: true,
        failed_login_attempts: 0,
        locked_until: null,
        created_at: '2023-09-20T11:00:00Z',
    },
    {
        id: 'stf_005',
        username: 'viewer',
        email: 'viewer@claimsportal.com',
        password: 'viewer@123',
        full_name: 'Vijay Viewer',
        phone: null,
        employee_id: 'EMP-401',
        department: 'Claims',
        designation: 'Claims Viewer',
        role: 'viewer',
        access_level: 1,
        is_active: true,
        failed_login_attempts: 0,
        locked_until: null,
        created_at: '2024-01-02T08:30:00Z',
    },
];


// ── Database helpers ────────────────────────────────

function loadTable(key, defaults) {
    try {
        const stored = localStorage.getItem(key);
        if (stored) return JSON.parse(stored);
    } catch { /* ignore */ }
    localStorage.setItem(key, JSON.stringify(defaults));
    return [...defaults];
}

function saveTable(key, data) {
    localStorage.setItem(key, JSON.stringify(data));
}


// ── Customer DB API ─────────────────────────────────

export const CustomerDB = {
    _table: () => loadTable('db_customer_users', DEFAULT_CUSTOMERS),

    /** Find customer by email */
    findByEmail(email) {
        return this._table().find(u => u.email === email.trim().toLowerCase()) || null;
    },

    /** Authenticate customer — returns user (without password) or null */
    authenticate(email, password) {
        const user = this.findByEmail(email);
        if (!user || !user.is_active) return null;
        if (user.password !== password) return null;
        // Update last_login
        const table = this._table();
        const idx = table.findIndex(u => u.id === user.id);
        table[idx].last_login = new Date().toISOString();
        saveTable('db_customer_users', table);
        const { password: _, ...safeUser } = table[idx];
        return safeUser;
    },

    /** Register new customer — returns user or throws */
    register(data) {
        const table = this._table();
        if (table.find(u => u.email === data.email.trim().toLowerCase())) {
            throw new Error('An account with this email already exists. Please log in.');
        }
        const newUser = {
            id: `usr_${Date.now()}`,
            email: data.email.trim().toLowerCase(),
            password: data.password,
            full_name: data.full_name.trim(),
            father_name: data.father_name.trim(),
            phone: data.phone.trim(),
            gender: data.gender,
            marital_status: data.marital_status,
            permanent_address: data.permanent_address.trim(),
            current_address: data.current_address.trim(),
            is_active: true,
            is_verified: false,
            created_at: new Date().toISOString(),
        };
        table.push(newUser);
        saveTable('db_customer_users', table);
        const { password: _, ...safeUser } = newUser;
        return safeUser;
    },

    /** List all customers (admin view) */
    list() {
        return this._table().map(({ password: _, ...u }) => u);
    },

    /** Count total customers */
    count() {
        return this._table().length;
    },
};


// ── Staff DB API ────────────────────────────────────

const MAX_FAILED_ATTEMPTS = 5;

export const StaffDB = {
    _table: () => loadTable('db_staff_users', DEFAULT_STAFF),

    /** Find staff by username */
    findByUsername(username) {
        return this._table().find(u => u.username === username.trim()) || null;
    },

    /** Authenticate staff — returns user (without password) or null + error message */
    authenticate(username, password) {
        const table = this._table();
        const idx = table.findIndex(u => u.username === username.trim() && u.is_active);
        if (idx === -1) return { user: null, error: 'Invalid username or password.' };

        const staff = table[idx];

        // Check lockout
        if (staff.locked_until && new Date(staff.locked_until) > new Date()) {
            const mins = Math.ceil((new Date(staff.locked_until) - new Date()) / 60000);
            return { user: null, error: `Account locked. Try again in ${mins} minutes.` };
        }

        // Wrong password
        if (staff.password !== password) {
            table[idx].failed_login_attempts += 1;
            if (table[idx].failed_login_attempts >= MAX_FAILED_ATTEMPTS) {
                table[idx].locked_until = new Date(Date.now() + 30 * 60 * 1000).toISOString();
            }
            saveTable('db_staff_users', table);
            const remaining = MAX_FAILED_ATTEMPTS - table[idx].failed_login_attempts;
            if (remaining <= 0) return { user: null, error: 'Account locked due to too many failed attempts.' };
            return { user: null, error: `Invalid password. ${remaining} attempt${remaining !== 1 ? 's' : ''} remaining.` };
        }

        // Success
        table[idx].failed_login_attempts = 0;
        table[idx].locked_until = null;
        table[idx].last_login = new Date().toISOString();
        saveTable('db_staff_users', table);

        const { password: _, ...safeUser } = table[idx];
        return { user: safeUser, error: null };
    },

    /** List all staff (admin view) */
    list(department = null) {
        let data = this._table().map(({ password: _, ...u }) => u);
        if (department) data = data.filter(u => u.department === department);
        return data;
    },

    /** Count total staff */
    count() {
        return this._table().length;
    },

    /** Get departments */
    departments() {
        return [...new Set(this._table().map(u => u.department))].sort();
    },
};
