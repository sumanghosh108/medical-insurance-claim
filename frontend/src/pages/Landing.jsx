// InClaim — Public Landing Page
// Responsive, with realistic images, dashboard mockup hero, and full professional footer
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Shield, FileText, UploadCloud, Clock,
    CheckCircle, ArrowRight, Star, Lock, Menu, X,
    Mail, Phone, MapPin, Twitter, Linkedin, Github, Heart,
    Users, Award, TrendingUp, Zap,
} from 'lucide-react';
import '../portal/portal.css';
import './landing.css';

// ── Unsplash images ─────────────────────────────────
const IMG = {
    hero: 'https://images.unsplash.com/photo-1551434678-e076c223a692?w=800&q=80',  // team working on laptops
    step1: 'https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=400&q=80', // person filling form
    step2: 'https://images.unsplash.com/photo-1586953208448-b95a79798f07?w=400&q=80', // phone uploading
    step3: 'https://images.unsplash.com/photo-1518186285589-2f7649de83e0?w=400&q=80', // analytics/tracking
    avatar1: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=80&q=80',  // woman
    avatar2: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=80&q=80',  // man
    avatar3: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=80&q=80',  // woman 2
};

const FEATURES = [
    { icon: FileText, color: '#6366f1', title: 'Submit Claims Online', desc: 'File your insurance claim anytime, from any device — no paperwork needed.' },
    { icon: UploadCloud, color: '#10b981', title: 'Upload Documents', desc: 'Securely attach medical records, invoices, and reports directly from your phone.' },
    { icon: Clock, color: '#f59e0b', title: 'Real-Time Tracking', desc: 'See exactly where your claim is in the pipeline — updated at every step.' },
    { icon: CheckCircle, color: '#818cf8', title: 'Fast Approvals', desc: 'AI-assisted review gets your claim processed in 24–48 hours on average.' },
];

const TESTIMONIALS = [
    { name: 'Priya Sharma', role: 'Software Engineer', avatar: IMG.avatar1, rating: 5, text: 'Got my health claim approved in under 2 days. The status tracker made the whole process completely stress-free.' },
    { name: 'Rahul Verma', role: 'Business Owner', avatar: IMG.avatar2, rating: 5, text: 'Uploading documents from my phone was incredibly easy. No more faxing or mailing anything. Saved me hours.' },
    { name: 'Anita Patel', role: 'School Teacher', avatar: IMG.avatar3, rating: 5, text: 'The real-time updates kept me informed every step of the way. I always knew exactly where my claim stood.' },
];

const STATS = [
    { value: '50K+', label: 'Active Policyholders', icon: Users },
    { value: '₹120Cr', label: 'Claims Processed', icon: TrendingUp },
    { value: '24h', label: 'Avg. Processing Time', icon: Zap },
    { value: '4.9/5', label: 'Customer Rating', icon: Award },
];

export default function Landing() {
    const nav = useNavigate();
    const [menuOpen, setMenuOpen] = useState(false);

    return (
        <div style={{ minHeight: '100vh', background: 'var(--bg-base)' }}>

            {/* ══ HEADER ══════════════════════════════════════════ */}
            <header style={{ position: 'sticky', top: 0, zIndex: 100, borderBottom: '1px solid rgba(99,102,241,0.12)', background: 'rgba(6,11,24,0.88)', backdropFilter: 'blur(20px)' }}>
                <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 1.25rem', height: 64, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    {/* Logo */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', cursor: 'pointer' }} onClick={() => nav('/')}>
                        <div style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', borderRadius: 10, padding: '6px', display: 'flex' }}>
                            <Shield size={20} color="#fff" />
                        </div>
                        <span style={{ fontWeight: 800, fontSize: '1.125rem', color: 'var(--text-primary)' }}>InClaim</span>
                    </div>

                    {/* Desktop nav */}
                    <nav className="landing-nav-links">
                        {['Features', 'How it works', 'Contact'].map(l => (
                            <a key={l} href={`#${l.toLowerCase().replace(/ /g, '-')}`}
                                style={{ padding: '0.4rem 0.875rem', color: 'var(--text-secondary)', textDecoration: 'none', fontSize: '0.875rem', borderRadius: 8, transition: 'color 0.15s' }}
                                onMouseEnter={e => e.target.style.color = 'var(--text-primary)'}
                                onMouseLeave={e => e.target.style.color = 'var(--text-secondary)'}
                            >{l}</a>
                        ))}
                    </nav>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <div className="landing-auth-btns">
                            <button className="btn btn-secondary" onClick={() => nav('/portal/login')} style={{ fontSize: '0.8125rem', padding: '0.4rem 0.875rem' }}>Sign In</button>
                            <button className="btn btn-primary" onClick={() => nav('/portal/signup')}
                                style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', fontSize: '0.8125rem', padding: '0.4rem 0.875rem' }}>
                                Get Started <ArrowRight size={13} />
                            </button>
                        </div>
                        {/* Mobile hamburger */}
                        <button className="landing-mobile-menu-btn" onClick={() => setMenuOpen(!menuOpen)}>
                            {menuOpen ? <X size={22} /> : <Menu size={22} />}
                        </button>
                    </div>
                </div>
            </header>

            {/* Mobile menu overlay */}
            {menuOpen && (
                <div className="mobile-menu">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <div style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', borderRadius: 8, padding: 5, display: 'flex' }}><Shield size={16} color="#fff" /></div>
                            <span style={{ fontWeight: 800, color: 'var(--text-primary)' }}>InClaim</span>
                        </div>
                        <button onClick={() => setMenuOpen(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)' }}><X size={22} /></button>
                    </div>
                    {['Features', 'How it works', 'Contact'].map(l => (
                        <a key={l} href={`#${l.toLowerCase().replace(/ /g, '-')}`} onClick={() => setMenuOpen(false)}>{l}</a>
                    ))}
                    <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem', padding: '1rem 0' }}>
                        <button className="btn btn-secondary" onClick={() => { setMenuOpen(false); nav('/portal/login'); }} style={{ flex: 1 }}>Sign In</button>
                        <button className="btn btn-primary" onClick={() => { setMenuOpen(false); nav('/portal/signup'); }}
                            style={{ flex: 1, background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}>Get Started</button>
                    </div>
                </div>
            )}


            {/* ══ HERO ════════════════════════════════════════════ */}
            <section className="landing-hero section-bg bg-hero">
                <div className="landing-hero-content">
                    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.25)', borderRadius: 100, padding: '0.3rem 0.875rem', marginBottom: '1.5rem' }}>
                        <Star size={12} color="#818cf8" fill="#818cf8" />
                        <span style={{ fontSize: '0.8125rem', color: '#818cf8', fontWeight: 600 }}>Trusted by 50,000+ policyholders</span>
                    </div>

                    <h1>
                        Insurance claims.<br />
                        <span style={{ background: 'linear-gradient(135deg, #6366f1, #a78bfa)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                            Done in days, not weeks.
                        </span>
                    </h1>

                    <p className="hero-sub">
                        Submit your claim online, upload documents securely, and track your approval status in real time — all from one place.
                    </p>

                    <div className="landing-hero-btns">
                        <button className="btn btn-primary btn-lg" onClick={() => nav('/portal/signup')}
                            style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', boxShadow: '0 6px 24px rgba(99,102,241,0.45)', fontSize: '1rem' }}>
                            Get Started Free <ArrowRight size={16} />
                        </button>
                        <button className="btn btn-secondary btn-lg" onClick={() => nav('/portal/login')} style={{ fontSize: '1rem' }}>
                            Sign In
                        </button>
                    </div>

                    {/* Trust items */}
                    <div className="landing-trust-bar">
                        <div className="trust-item">
                            <div className="trust-item-icon" style={{ background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.2)' }}><Lock size={14} color="#10b981" /></div>
                            256-bit Encrypted
                        </div>
                        <div className="trust-item">
                            <div className="trust-item-icon" style={{ background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.2)' }}><Shield size={14} color="#818cf8" /></div>
                            HIPAA Compliant
                        </div>
                        <div className="trust-item">
                            <div className="trust-item-icon" style={{ background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.2)' }}><Zap size={14} color="#f59e0b" /></div>
                            24h Processing
                        </div>
                    </div>
                </div>

                {/* Hero visual — dashboard mockup with real image */}
                <div className="landing-hero-visual">
                    <div className="hero-dashboard">
                        <div className="hero-dashboard-bar">
                            <span className="hero-dashboard-dot" style={{ background: '#ff5f57' }} />
                            <span className="hero-dashboard-dot" style={{ background: '#ffbd2e' }} />
                            <span className="hero-dashboard-dot" style={{ background: '#28c840' }} />
                            <span style={{ flex: 1 }} />
                            <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>inclaim.io/dashboard</span>
                        </div>
                        <img src={IMG.hero} alt="InClaim Dashboard — team working on insurance claims" className="hero-dashboard-img" loading="eager" />
                    </div>
                </div>
            </section>


            <div className="section-divider" />

            {/* ══ STATS ═══════════════════════════════════════════ */}
            <section className="landing-stats section-bg bg-stats">
                <div className="landing-stats-inner">
                    {STATS.map(s => (
                        <div key={s.label} className="stat-item">
                            <div className="stat-value">{s.value}</div>
                            <div className="stat-label">{s.label}</div>
                        </div>
                    ))}
                </div>
            </section>


            <div className="section-divider" />

            {/* ══ FEATURES ════════════════════════════════════════ */}
            <section id="features" className="landing-section section-bg bg-features">
                <h2>Everything you need</h2>
                <p className="section-sub">Built to make insurance claims as simple as possible</p>

                <div className="features-grid">
                    {FEATURES.map(f => (
                        <div key={f.title} className="portal-glass portal-card feature-card">
                            <div className="feature-icon" style={{ background: `${f.color}18`, border: `1px solid ${f.color}30` }}>
                                <f.icon size={22} color={f.color} />
                            </div>
                            <h3 style={{ marginBottom: '0.5rem', fontSize: '1rem' }}>{f.title}</h3>
                            <p style={{ fontSize: '0.875rem', lineHeight: 1.7, color: 'var(--text-secondary)' }}>{f.desc}</p>
                        </div>
                    ))}
                </div>
            </section>


            <div className="section-divider" />

            {/* ══ HOW IT WORKS ════════════════════════════════════ */}
            <section id="how-it-works" className="landing-section section-bg bg-hiw">
                <h2>How it works</h2>
                <p className="section-sub">Three simple steps to get your claim resolved</p>

                <div className="hiw-grid">
                    {[
                        { n: '01', img: IMG.step1, title: 'Submit Your Claim', desc: 'Fill out our guided form in under 5 minutes. Tell us what happened and how much you\'re claiming.' },
                        { n: '02', img: IMG.step2, title: 'Upload Documents', desc: 'Attach receipts, medical records, or police reports directly from your device. PDF, JPG, PNG supported.' },
                        { n: '03', img: IMG.step3, title: 'Track & Get Paid', desc: 'Watch your claim move through review in real time. Approved claims are paid within 3–5 business days.' },
                    ].map(s => (
                        <div key={s.n} className="portal-glass hiw-card">
                            <img src={s.img} alt={s.title} className="hiw-img" loading="lazy" />
                            <div className="hiw-number">{s.n}</div>
                            <h3 style={{ marginBottom: '0.5rem', fontSize: '1.0625rem' }}>{s.title}</h3>
                            <p style={{ fontSize: '0.875rem', lineHeight: 1.7, color: 'var(--text-secondary)' }}>{s.desc}</p>
                        </div>
                    ))}
                </div>
            </section>


            <div className="section-divider" />

            {/* ══ TESTIMONIALS ════════════════════════════════════ */}
            <section className="landing-section section-bg bg-testimonials">
                <h2>What our customers say</h2>
                <p className="section-sub">Join thousands of happy policyholders</p>

                <div className="testimonials-grid">
                    {TESTIMONIALS.map(t => (
                        <div key={t.name} className="portal-glass testimonial-card">
                            <div style={{ display: 'flex', gap: '0.25rem', marginBottom: '1rem' }}>
                                {[...Array(t.rating)].map((_, i) => <Star key={i} size={14} color="#f59e0b" fill="#f59e0b" />)}
                            </div>
                            <p style={{ fontSize: '0.9375rem', lineHeight: 1.7, color: 'var(--text-primary)', marginBottom: '1.25rem', fontStyle: 'italic' }}>"{t.text}"</p>
                            <div style={{ display: 'flex', alignItems: 'center' }}>
                                <img src={t.avatar} alt={t.name} className="testimonial-avatar" loading="lazy" />
                                <div>
                                    <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)' }}>{t.name}</div>
                                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{t.role}</div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </section>


            <div className="section-divider" />

            {/* ══ CTA BANNER ══════════════════════════════════════ */}
            <section className="landing-cta section-bg bg-cta">
                <div className="landing-cta-inner">
                    <div className="cta-bg-glow" />
                    <h2 style={{ marginBottom: '0.625rem', fontSize: 'clamp(1.5rem, 3vw, 1.875rem)', position: 'relative' }}>Ready to file your claim?</h2>
                    <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem', fontSize: '1rem', position: 'relative' }}>Create a free account and file your claim in under 5 minutes.</p>
                    <button className="btn btn-primary btn-lg" onClick={() => nav('/portal/signup')}
                        style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', boxShadow: '0 6px 24px rgba(99,102,241,0.4)', fontSize: '1rem', position: 'relative' }}>
                        Create Free Account <ArrowRight size={16} />
                    </button>
                </div>
            </section>


            {/* ══ FOOTER ══════════════════════════════════════════ */}
            <footer id="contact" className="landing-footer">
                <div className="footer-inner">
                    <div className="footer-grid">
                        {/* Brand */}
                        <div className="footer-brand">
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                                <div style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', borderRadius: 8, padding: 5, display: 'flex' }}>
                                    <Shield size={16} color="#fff" />
                                </div>
                                <span style={{ fontWeight: 800, fontSize: '1rem', color: 'var(--text-primary)' }}>InClaim</span>
                            </div>
                            <p>Making insurance claims simple, fast, and transparent. Built with ❤️ for policyholders across India.</p>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '1rem' }}>
                                <Mail size={13} color="var(--text-muted)" />
                                <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>support@inclaim.io</span>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.375rem' }}>
                                <Phone size={13} color="var(--text-muted)" />
                                <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>1800-123-4567 (Toll Free)</span>
                            </div>
                        </div>

                        {/* Product */}
                        <div className="footer-col">
                            <h4>Product</h4>
                            <a href="#features">Features</a>
                            <a href="#how-it-works">How it Works</a>
                            <a href="#" onClick={e => { e.preventDefault(); nav('/portal/signup'); }}>Get Started</a>
                            <a href="#" onClick={e => { e.preventDefault(); nav('/portal/login'); }}>Sign In</a>
                        </div>

                        {/* Company */}
                        <div className="footer-col">
                            <h4>Company</h4>
                            <a href="#">About Us</a>
                            <a href="#">Careers</a>
                            <a href="#">Press & Media</a>
                            <a href="#">Blog</a>
                        </div>

                        {/* Legal */}
                        <div className="footer-col">
                            <h4>Legal</h4>
                            <a href="#">Privacy Policy</a>
                            <a href="#">Terms of Service</a>
                            <a href="#">Cookie Policy</a>
                            <a href="#">IRDAI Compliance</a>
                        </div>
                    </div>

                    {/* Bottom bar */}
                    <div className="footer-bottom">
                        <p>© 2026 InClaim Insurance Technologies Pvt. Ltd. · All rights reserved · CIN: U72200KA2024PTC123456</p>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                            <div className="footer-social">
                                <a href="#" title="Twitter"><Twitter size={14} /></a>
                                <a href="#" title="LinkedIn"><Linkedin size={14} /></a>
                                <a href="#" title="GitHub"><Github size={14} /></a>
                            </div>
                            {/* Hidden admin access */}
                            <a href="/admin/login" style={{ fontSize: '0.65rem', color: 'rgba(255,255,255,0.05)', textDecoration: 'none' }}
                                onMouseEnter={e => e.target.style.color = 'var(--text-muted)'}
                                onMouseLeave={e => e.target.style.color = 'rgba(255,255,255,0.05)'}
                            >Staff</a>
                        </div>
                    </div>
                </div>
            </footer>
        </div>
    );
}
