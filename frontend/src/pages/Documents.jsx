// Documents page — drag-and-drop upload + document grid
import { useState, useRef } from 'react';
import { UploadCloud, FileText, File, Image, Download, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import { fetchDocuments, uploadDocument } from '../api/claims';
import { useEffect } from 'react';
import { useApp } from '../contexts/AppContext';

const DOC_TYPES = ['claim_form', 'medical_record', 'invoice', 'police_report', 'proof_of_loss', 'id_verification', 'other'];

function fmtSize(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
function fmtDate(s) { return s ? new Date(s).toLocaleDateString('en-IN', { dateStyle: 'medium' }) : '—'; }

function FileIcon({ type }) {
    if (type?.includes('image')) return <Image size={20} color="var(--primary)" />;
    if (type?.includes('pdf')) return <FileText size={20} color="var(--danger)" />;
    return <File size={20} color="var(--text-muted)" />;
}

function ProcBadge({ status }) {
    if (status === 'completed') return <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.75rem', color: 'var(--success)', fontWeight: 600 }}><CheckCircle size={12} />Done</span>;
    if (status === 'pending') return <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.75rem', color: 'var(--warning)', fontWeight: 600 }}><Clock size={12} />Pending</span>;
    return <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.75rem', color: 'var(--danger)', fontWeight: 600 }}><AlertCircle size={12} />{status}</span>;
}

export default function Documents() {
    const { addNotification } = useApp();
    const [docs, setDocs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [dragging, setDragging] = useState(false);
    const [docType, setDocType] = useState('medical_record');
    const [uploading, setUploading] = useState(false);
    const inputRef = useRef();

    useEffect(() => { fetchDocuments().then(setDocs).finally(() => setLoading(false)); }, []);

    const handleFiles = async (files) => {
        if (!files?.length) return;
        setUploading(true);
        try {
            const f = files[0];
            const result = await uploadDocument({ claim_id: 'claim_abc001', document_type: docType, file_name: f.name, file_size: f.size, content_type: f.type || 'application/octet-stream' });
            setDocs(prev => [result.metadata, ...prev]);
            addNotification(`"${f.name}" uploaded successfully`, 'success');
        } catch (e) {
            addNotification('Upload failed: ' + e.message, 'error');
        } finally { setUploading(false); }
    };

    return (
        <div className="animate-fade" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div>
                <h1>Documents</h1>
                <p>Upload and manage claim documents</p>
            </div>

            {/* Upload zone */}
            <div className="glass" style={{ padding: '1.5rem' }}>
                <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
                    <div className="form-group" style={{ flex: '0 1 220px' }}>
                        <label className="form-label">Document Type</label>
                        <select value={docType} onChange={e => setDocType(e.target.value)} className="form-select">
                            {DOC_TYPES.map(t => <option key={t} value={t}>{t.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</option>)}
                        </select>
                    </div>
                </div>

                <div
                    onDragOver={e => { e.preventDefault(); setDragging(true); }}
                    onDragLeave={() => setDragging(false)}
                    onDrop={e => { e.preventDefault(); setDragging(false); handleFiles(e.dataTransfer.files); }}
                    onClick={() => inputRef.current?.click()}
                    style={{
                        border: `2px dashed ${dragging ? 'var(--primary)' : 'var(--border)'}`,
                        borderRadius: 'var(--radius-md)', padding: '3rem', textAlign: 'center', cursor: 'pointer',
                        background: dragging ? 'rgba(79,142,247,0.06)' : 'rgba(255,255,255,0.01)',
                        transition: 'var(--transition)',
                    }}
                >
                    <input ref={inputRef} type="file" style={{ display: 'none' }} multiple onChange={e => handleFiles(e.target.files)} />
                    <UploadCloud size={40} color={dragging ? 'var(--primary)' : 'var(--text-muted)'} style={{ margin: '0 auto 0.875rem' }} />
                    {uploading ? (
                        <p style={{ color: 'var(--primary)', fontWeight: 600 }}>Uploading…</p>
                    ) : (
                        <>
                            <p style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                                {dragging ? 'Drop files here' : 'Drag & drop or click to upload'}
                            </p>
                            <p style={{ fontSize: '0.8125rem' }}>PDF, JPG, PNG, DOCX — max 50 MB</p>
                        </>
                    )}
                </div>
            </div>

            {/* Document grid */}
            <div>
                <h3 style={{ marginBottom: '0.875rem' }}>All Documents ({docs.length})</h3>
                {loading ? (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px,1fr))', gap: '1rem' }}>
                        {[...Array(4)].map((_, i) => <div key={i} className="skeleton" style={{ height: 120 }} />)}
                    </div>
                ) : docs.length === 0 ? (
                    <div className="glass" style={{ padding: '3rem', textAlign: 'center' }}>
                        <FileText size={32} color="var(--text-muted)" style={{ margin: '0 auto 0.75rem' }} />
                        <p style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>No documents yet</p>
                        <p>Upload your first document above</p>
                    </div>
                ) : (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px,1fr))', gap: '1rem' }}>
                        {docs.map(d => (
                            <div key={d.document_id} className="glass" style={{ padding: '1.125rem', display: 'flex', gap: '0.875rem', alignItems: 'flex-start', transition: 'var(--transition)' }}
                                onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--border-strong)'}
                                onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
                            >
                                <div style={{ background: 'rgba(79,142,247,0.1)', borderRadius: 8, padding: '0.625rem', flexShrink: 0, display: 'flex' }}>
                                    <FileIcon type={d.content_type} />
                                </div>
                                <div style={{ flex: 1, minWidth: 0 }}>
                                    <p className="truncate" style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.875rem', marginBottom: '0.2rem' }}>{d.file_name}</p>
                                    <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                                        {d.document_type?.replace(/_/g, ' ')} · {fmtSize(d.file_size || 0)} · {fmtDate(d.uploaded_at)}
                                    </p>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <ProcBadge status={d.processing_status} />
                                        <button className="btn btn-ghost btn-icon btn-sm" title="Download">
                                            <Download size={13} color="var(--text-muted)" />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
