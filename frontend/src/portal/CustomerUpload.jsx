// Customer Upload Documents page
import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, CheckCircle, AlertCircle, FileText, Trash2, Loader, ArrowLeft, Info } from 'lucide-react';
import { fetchClaims, uploadDocument } from '../api/claims';
import { useApp } from '../contexts/AppContext';

const DOC_TYPES = [
    { value: 'medical_record', label: 'Medical Record / Discharge Summary' },
    { value: 'invoice', label: 'Hospital/Provider Invoice' },
    { value: 'police_report', label: 'Police Report' },
    { value: 'proof_of_loss', label: 'Proof of Loss' },
    { value: 'id_verification', label: 'ID / Identity Document' },
    { value: 'claim_form', label: 'Completed Claim Form' },
    { value: 'other', label: 'Other Document' },
];

function fmtSize(b) {
    if (b < 1024) return `${b} B`;
    if (b < 1024 * 1024) return `${(b / 1024).toFixed(0)} KB`;
    return `${(b / 1024 / 1024).toFixed(1)} MB`;
}

export default function CustomerUpload() {
    const nav = useNavigate();
    const { addNotification } = useApp();
    const inputRef = useRef();

    const [claims, setClaims] = useState([]);
    const [claimId, setClaimId] = useState('');
    const [docType, setDocType] = useState('medical_record');
    const [dragging, setDragging] = useState(false);
    const [queue, setQueue] = useState([]);      // { file, status, id }
    const [uploading, setUploading] = useState(false);

    useEffect(() => {
        fetchClaims().then(r => {
            const activeClaims = r.claims.filter(c => !['paid', 'closed'].includes(c.metadata.status));
            setClaims(activeClaims);
            if (activeClaims.length) setClaimId(activeClaims[0].metadata.claim_id);
        });
    }, []);

    const addFiles = (files) => {
        const newItems = Array.from(files).map(f => ({ file: f, status: 'pending', id: Math.random().toString(36).substr(2, 8) }));
        setQueue(prev => [...prev, ...newItems]);
    };

    const removeItem = (id) => setQueue(prev => prev.filter(i => i.id !== id));

    const uploadAll = async () => {
        if (!claimId) { addNotification('Please select a claim first', 'error'); return; }
        if (!queue.filter(i => i.status === 'pending').length) { addNotification('No files to upload', 'error'); return; }

        setUploading(true);
        let successCount = 0;

        for (const item of queue.filter(i => i.status === 'pending')) {
            setQueue(prev => prev.map(i => i.id === item.id ? { ...i, status: 'uploading' } : i));
            try {
                await uploadDocument({ claim_id: claimId, document_type: docType, file_name: item.file.name, file_size: item.file.size, content_type: item.file.type || 'application/octet-stream' });
                setQueue(prev => prev.map(i => i.id === item.id ? { ...i, status: 'done' } : i));
                successCount++;
            } catch {
                setQueue(prev => prev.map(i => i.id === item.id ? { ...i, status: 'error' } : i));
            }
        }

        setUploading(false);
        if (successCount > 0) addNotification(`${successCount} document${successCount > 1 ? 's' : ''} uploaded successfully!`, 'success');
    };

    const allDone = queue.length > 0 && queue.every(i => i.status === 'done');
    const hasPending = queue.some(i => i.status === 'pending');

    return (
        <div className="animate-fade" style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem', maxWidth: 720, margin: '0 auto' }}>
            <div>
                <button className="btn btn-ghost btn-sm" onClick={() => nav('/portal')} style={{ marginBottom: '0.875rem', color: 'var(--text-muted)' }}>
                    <ArrowLeft size={14} /> My Claims
                </button>
                <h1 style={{ marginBottom: '0.25rem' }}>Upload Documents</h1>
                <p>Attach supporting documents to your claim for faster processing</p>
            </div>

            {/* Info banner */}
            <div className="portal-alert portal-alert-info">
                <Info size={18} color="#818cf8" style={{ flexShrink: 0, marginTop: 2 }} />
                <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                    Accepted formats: <strong style={{ color: 'var(--text-primary)' }}>PDF, JPG, PNG, DOCX</strong> — Maximum file size: <strong style={{ color: 'var(--text-primary)' }}>50 MB</strong> per file. Documents are encrypted over HTTPS.
                </p>
            </div>

            <div className="portal-glass" style={{ padding: '1.75rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                {/* Claim + type selectors */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <div className="form-group">
                        <label className="form-label">Select Your Claim *</label>
                        <select value={claimId} onChange={e => setClaimId(e.target.value)} className="form-select">
                            {claims.length === 0
                                ? <option>No active claims</option>
                                : claims.map(c => (
                                    <option key={c.metadata.claim_id} value={c.metadata.claim_id}>
                                        {c.metadata.claim_number} — {c.claim_data?.claim_type}
                                    </option>
                                ))
                            }
                        </select>
                    </div>
                    <div className="form-group">
                        <label className="form-label">Document Type *</label>
                        <select value={docType} onChange={e => setDocType(e.target.value)} className="form-select">
                            {DOC_TYPES.map(d => <option key={d.value} value={d.value}>{d.label}</option>)}
                        </select>
                    </div>
                </div>

                {/* Drop zone */}
                <div
                    className={`upload-zone ${dragging ? 'drag-over' : ''}`}
                    onDragOver={e => { e.preventDefault(); setDragging(true); }}
                    onDragLeave={() => setDragging(false)}
                    onDrop={e => { e.preventDefault(); setDragging(false); addFiles(e.dataTransfer.files); }}
                    onClick={() => inputRef.current?.click()}
                >
                    <input ref={inputRef} type="file" multiple style={{ display: 'none' }} onChange={e => addFiles(e.target.files)} />
                    <UploadCloud size={44} color={dragging ? '#818cf8' : 'var(--text-muted)'} style={{ margin: '0 auto 1rem', display: 'block' }} />
                    <p style={{ fontWeight: 700, color: dragging ? '#818cf8' : 'var(--text-primary)', marginBottom: '0.375rem' }}>
                        {dragging ? 'Release to add files' : 'Drag files here or click to browse'}
                    </p>
                    <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>You can add multiple files at once</p>
                </div>

                {/* File queue */}
                {queue.length > 0 && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                        <p style={{ fontWeight: 700, fontSize: '0.8125rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                            Files to Upload ({queue.length})
                        </p>
                        {queue.map(item => (
                            <div key={item.id} style={{
                                display: 'flex', alignItems: 'center', gap: '0.875rem',
                                padding: '0.75rem 1rem', borderRadius: 10,
                                background: item.status === 'done' ? 'rgba(16,185,129,0.06)' : item.status === 'error' ? 'rgba(239,68,68,0.06)' : 'rgba(255,255,255,0.03)',
                                border: `1px solid ${item.status === 'done' ? 'rgba(16,185,129,0.2)' : item.status === 'error' ? 'rgba(239,68,68,0.2)' : 'var(--border)'}`,
                            }}>
                                <FileText size={18} color={item.status === 'done' ? '#10b981' : item.status === 'error' ? '#ef4444' : 'var(--text-muted)'} />
                                <div style={{ flex: 1, minWidth: 0 }}>
                                    <p className="truncate" style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>{item.file.name}</p>
                                    <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: 0 }}>{fmtSize(item.file.size)}</p>
                                </div>
                                {item.status === 'pending' && <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Ready</span>}
                                {item.status === 'uploading' && <Loader size={15} color="#818cf8" style={{ animation: 'spin 1s linear infinite', flexShrink: 0 }} />}
                                {item.status === 'done' && <CheckCircle size={15} color="#10b981" />}
                                {item.status === 'error' && <AlertCircle size={15} color="#ef4444" />}
                                {item.status === 'pending' && (
                                    <button className="btn btn-ghost btn-icon btn-sm" onClick={() => removeItem(item.id)}>
                                        <Trash2 size={13} color="var(--text-muted)" />
                                    </button>
                                )}
                            </div>
                        ))}
                    </div>
                )}

                {/* ── Success banner (shows after all uploads complete) ── */}
                {allDone && (
                    <div style={{
                        display: 'flex', gap: '0.875rem', alignItems: 'flex-start',
                        padding: '1rem 1.25rem', borderRadius: 12,
                        background: 'rgba(16,185,129,0.09)', border: '1px solid rgba(16,185,129,0.3)',
                    }}>
                        <CheckCircle size={20} color="#10b981" style={{ flexShrink: 0, marginTop: 2 }} />
                        <div>
                            <p style={{ fontWeight: 700, color: '#10b981', marginBottom: '0.2rem' }}>
                                Documents uploaded successfully!
                            </p>
                            <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', margin: 0 }}>
                                {queue.length} file{queue.length !== 1 ? 's' : ''} received. Your adjuster will review them within 24–48 hours. Check your claim status below.
                            </p>
                        </div>
                    </div>
                )}

                {/* Actions */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '0.5rem', borderTop: '1px solid var(--border)' }}>
                    <button className="btn btn-secondary" onClick={() => setQueue([])} disabled={!queue.length || uploading}>
                        Clear All
                    </button>
                    {allDone ? (
                        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
                            <button
                                className="btn btn-ghost btn-sm"
                                onClick={() => { setQueue([]); }}
                                style={{ color: 'var(--text-muted)' }}
                            >
                                Upload More Files
                            </button>
                            <button
                                className="btn btn-primary btn-lg"
                                onClick={() => nav(`/portal/status/${claimId}`)}
                                style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', boxShadow: '0 4px 18px rgba(99,102,241,0.45)', gap: '0.5rem' }}
                            >
                                <CheckCircle size={16} />
                                View Claim Status →
                            </button>
                        </div>
                    ) : (
                        <button className="btn btn-primary btn-lg" onClick={uploadAll} disabled={!hasPending || uploading || !claimId}>
                            {uploading ? <><Loader size={15} style={{ animation: 'spin 1s linear infinite' }} /> Uploading…</> : <><UploadCloud size={15} /> Upload {queue.filter(i => i.status === 'pending').length || ''} File{queue.filter(i => i.status === 'pending').length !== 1 ? 's' : ''}</>}
                        </button>
                    )}
                </div>
            </div>

            {/* What happens next */}
            <div className="portal-glass" style={{ padding: '1.5rem' }}>
                <h4 style={{ marginBottom: '1rem' }}>What happens after upload?</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {[
                        { step: '1', text: 'Our system scans & extracts data from your documents automatically', color: '#818cf8' },
                        { step: '2', text: 'A claims adjuster reviews the information within 24–48 hours', color: '#10b981' },
                        { step: '3', text: 'You\'ll receive an email update once your claim status changes', color: '#f59e0b' },
                    ].map(s => (
                        <div key={s.step} style={{ display: 'flex', gap: '0.875rem', alignItems: 'flex-start' }}>
                            <div style={{ width: 24, height: 24, borderRadius: '50%', background: `${s.color}20`, border: `1px solid ${s.color}40`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, fontSize: '0.6875rem', fontWeight: 800, color: s.color }}>
                                {s.step}
                            </div>
                            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>{s.text}</p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
