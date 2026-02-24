// Customer auth context — uses userDatabase for real data
import { createContext, useContext, useState, useCallback } from 'react';
import { CustomerDB } from '../api/userDatabase';

const AuthContext = createContext(null);

const loadUser = () => {
    try { return JSON.parse(localStorage.getItem('portal_user')); } catch { return null; }
};

export function AuthProvider({ children }) {
    const [user, setUser] = useState(loadUser);

    const login = useCallback(async (email, password) => {
        await new Promise(r => setTimeout(r, 800)); // simulate network
        const found = CustomerDB.authenticate(email, password);
        if (!found) throw new Error('Invalid email or password. Please try again.');
        localStorage.setItem('portal_user', JSON.stringify(found));
        setUser(found);
        return found;
    }, []);

    const signup = useCallback(async (formData) => {
        await new Promise(r => setTimeout(r, 1000)); // simulate network
        const newUser = CustomerDB.register(formData); // throws if email exists
        localStorage.setItem('portal_user', JSON.stringify(newUser));
        setUser(newUser);
        return newUser;
    }, []);

    const logout = useCallback(() => {
        localStorage.removeItem('portal_user');
        setUser(null);
    }, []);

    return (
        <AuthContext.Provider value={{ user, login, signup, logout, isAuthenticated: !!user }}>
            {children}
        </AuthContext.Provider>
    );
}

export const useAuth = () => {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error('useAuth must be used within AuthProvider');
    return ctx;
};
