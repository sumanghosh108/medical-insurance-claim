import React, { createContext, useContext, useState, useCallback } from 'react';

const AppContext = createContext(null);

export function AppProvider({ children }) {
    const [notifications, setNotifications] = useState([]);
    const [user] = useState({ name: 'Suman Ghosh', role: 'admin', email: 'admin@claimsportal.io' });

    const addNotification = useCallback((msg, type = 'info') => {
        const id = Date.now();
        setNotifications(prev => [...prev, { id, msg, type }]);
        setTimeout(() => setNotifications(prev => prev.filter(n => n.id !== id)), 4000);
    }, []);

    return (
        <AppContext.Provider value={{ user, notifications, addNotification }}>
            {children}
            {/* Toast container */}
            <div style={{ position: 'fixed', bottom: '1.5rem', right: '1.5rem', zIndex: 9999, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {notifications.map(n => (
                    <div key={n.id} className="animate-slide" style={{
                        background: n.type === 'success' ? 'rgba(52,211,153,0.2)' : n.type === 'error' ? 'rgba(248,113,113,0.2)' : 'rgba(79,142,247,0.2)',
                        border: `1px solid ${n.type === 'success' ? 'rgba(52,211,153,0.5)' : n.type === 'error' ? 'rgba(248,113,113,0.5)' : 'rgba(79,142,247,0.5)'}`,
                        borderRadius: '10px', padding: '0.75rem 1.25rem', backdropFilter: 'blur(12px)',
                        color: 'var(--text-primary)', fontSize: '0.875rem', fontWeight: 500, maxWidth: '320px',
                    }}>
                        {n.msg}
                    </div>
                ))}
            </div>
        </AppContext.Provider>
    );
}

export function useApp() {
    return useContext(AppContext);
}
