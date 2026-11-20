import React, { useState, useEffect } from 'react';

// API Base URL (Relative works with Vite proxy and when served by Django)
const API_BASE = '/api';

export default function App() {
  const [currentTab, setCurrentTab] = useState('dashboard');
  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authMode, setAuthMode] = useState('login'); // 'login' or 'register'
  const [authError, setAuthError] = useState('');

  // Modals & Feedback
  const [showAddLogModal, setShowAddLogModal] = useState(false);
  const [inspectLog, setInspectLog] = useState(null);
  const [toast, setToast] = useState(null);

  // Data States
  const [dashboardData, setDashboardData] = useState(null);
  const [logsData, setLogsData] = useState({ results: [], count: 0, num_pages: 1, current_page: 1 });
  const [logsLoading, setLogsLoading] = useState(false);
  const [logFilter, setLogFilter] = useState({ q: '', level: '', from: '', to: '', page: 1 });
  const [notifications, setNotifications] = useState({ results: [], unresolved_count: 0 });
  const [notifFilter, setNotifFilter] = useState('unresolved');
  const [settingsData, setSettingsData] = useState(null);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  // 1. Check current logged-in user on mount
  useEffect(() => {
    fetch(`${API_BASE}/auth/me/`)
      .then((res) => res.json())
      .then((data) => {
        if (data.authenticated) {
          setUser(data.user);
        }
      })
      .catch(() => {})
      .finally(() => setAuthLoading(false));
  }, []);

  // 2. Load data based on active tab
  useEffect(() => {
    if (currentTab === 'dashboard') {
      loadDashboard();
    } else if (currentTab === 'logs') {
      loadLogs();
    } else if (currentTab === 'notifications') {
      loadNotifications();
    } else if (currentTab === 'settings') {
      loadSettings();
    }
  }, [currentTab, logFilter, notifFilter]);

  const loadDashboard = () => {
    fetch(`${API_BASE}/dashboard/`)
      .then((res) => res.json())
      .then((data) => setDashboardData(data))
      .catch((err) => console.error(err));
  };

  const loadLogs = () => {
    setLogsLoading(true);
    const params = new URLSearchParams();
    if (logFilter.q) params.append('q', logFilter.q);
    if (logFilter.level) params.append('level', logFilter.level);
    if (logFilter.from) params.append('from', logFilter.from);
    if (logFilter.to) params.append('to', logFilter.to);
    params.append('page', logFilter.page);

    fetch(`${API_BASE}/logs/?${params.toString()}`)
      .then((res) => res.json())
      .then((data) => setLogsData(data))
      .catch((err) => console.error(err))
      .finally(() => setLogsLoading(false));
  };

  const loadNotifications = () => {
    fetch(`${API_BASE}/notifications/?status=${notifFilter}`)
      .then((res) => res.json())
      .then((data) => setNotifications(data))
      .catch((err) => console.error(err));
  };

  const loadSettings = () => {
    fetch(`${API_BASE}/settings/`)
      .then((res) => res.json())
      .then((data) => setSettingsData(data))
      .catch((err) => console.error(err));
  };

  // Auth Handlers
  const handleAuthSubmit = (e) => {
    e.preventDefault();
    setAuthError('');
    const form = e.target;
    const username = form.username.value;
    const password = form.password.value;

    if (authMode === 'login') {
      fetch(`${API_BASE}/auth/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })
        .then(async (res) => {
          const data = await res.json();
          if (res.ok) {
            setUser(data.user);
            setShowAuthModal(false);
            showToast(`Welcome back, ${data.user.username}!`);
            loadDashboard();
          } else {
            setAuthError(data.error || 'Login failed.');
          }
        })
        .catch(() => setAuthError('Connection error.'));
    } else {
      const email = form.email.value;
      const role = form.role.value;
      fetch(`${API_BASE}/auth/register/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password, role }),
      })
        .then(async (res) => {
          const data = await res.json();
          if (res.ok) {
            setUser(data.user);
            setShowAuthModal(false);
            showToast(`Account created as ${data.user.role}!`);
            loadDashboard();
          } else {
            setAuthError(data.error || 'Registration failed.');
          }
        })
        .catch(() => setAuthError('Connection error.'));
    }
  };

  const handleLogout = () => {
    fetch(`${API_BASE}/auth/logout/`, { method: 'POST' }).then(() => {
      setUser(null);
      showToast('Signed out successfully.');
      loadDashboard();
    });
  };

  // Action: Add New Log
  const handleAddLog = (e) => {
    e.preventDefault();
    const form = e.target;
    const app = form.custom_app && form.source_application.value === 'Other'
      ? form.custom_app.value
      : form.source_application.value;

    const payload = {
      source_application: app,
      message: form.message.value,
      severity: form.severity.value === 'AUTO' ? null : form.severity.value,
      ip_address: form.ip_address.value || null,
      status_code: form.status_code.value ? parseInt(form.status_code.value, 10) : null,
    };

    fetch(`${API_BASE}/logs/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
      .then(async (res) => {
        const data = await res.json();
        if (res.ok) {
          setShowAddLogModal(false);
          showToast(`Log recorded! Auto-classified as ${data.severity} (${data.category_display}).`);
          if (currentTab === 'logs') loadLogs();
          else loadDashboard();
        } else {
          alert(data.error || 'Error recording log.');
        }
      })
      .catch(() => alert('Network error.'));
  };

  // Action: Delete Log
  const handleDeleteLog = (logId) => {
    if (!window.confirm('Delete this log record?')) return;
    fetch(`${API_BASE}/logs/${logId}/`, { method: 'DELETE' })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          showToast('Log entry deleted.');
          if (inspectLog && inspectLog.id === logId) setInspectLog(null);
          loadLogs();
        }
      });
  };

  // Action: Resolve Notification
  const handleResolveAlert = (alertId) => {
    fetch(`${API_BASE}/notifications/${alertId}/resolve/`, { method: 'POST' })
      .then((res) => res.json())
      .then(() => {
        showToast('Notification marked as resolved.');
        loadNotifications();
        if (currentTab === 'dashboard') loadDashboard();
      });
  };

  // Action: Seed Demo Logs
  const handleSeedDemoLogs = () => {
    fetch(`${API_BASE}/settings/seed/`, { method: 'POST' })
      .then((res) => res.json())
      .then((data) => {
        showToast(`Generated ${data.count} sample demo logs!`);
        if (currentTab === 'dashboard') loadDashboard();
        if (currentTab === 'logs') loadLogs();
      });
  };

  // Action: Clear All Logs
  const handleClearAllLogs = () => {
    if (!window.confirm('Reset and clear all server logs and notifications?')) return;
    fetch(`${API_BASE}/settings/clear/`, { method: 'POST' })
      .then((res) => res.json())
      .then(() => {
        showToast('All logs and notifications have been cleared.');
        if (currentTab === 'dashboard') loadDashboard();
        if (currentTab === 'logs') loadLogs();
      });
  };

  const unresolvedCount = dashboardData?.counts?.notifications ?? notifications.unresolved_count ?? 0;

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <a className="brand" href="#" onClick={() => setCurrentTab('dashboard')}>
          <div className="brand-icon">CW</div>
          <div>
            <div className="brand-name">Civic<span>Watch</span></div>
            <span className="brand-sub">SERVER LOG MONITOR</span>
          </div>
        </a>

        <div className="nav-section-title">Navigation</div>
        <ul className="nav-links">
          <li>
            <button
              className={`nav-link ${currentTab === 'dashboard' ? 'active' : ''}`}
              onClick={() => setCurrentTab('dashboard')}
            >
              <span className="nav-icon">▦</span>
              <span className="nav-label-text">Dashboard</span>
            </button>
          </li>
          <li>
            <button
              className={`nav-link ${currentTab === 'logs' ? 'active' : ''}`}
              onClick={() => setCurrentTab('logs')}
            >
              <span className="nav-icon">≡</span>
              <span className="nav-label-text">All Logs</span>
            </button>
          </li>
          <li>
            <button
              className={`nav-link ${currentTab === 'notifications' ? 'active' : ''}`}
              onClick={() => setCurrentTab('notifications')}
            >
              <span className="nav-icon">🔔</span>
              <span className="nav-label-text">Notifications</span>
              {unresolvedCount > 0 && <span className="nav-badge">{unresolvedCount}</span>}
            </button>
          </li>
          <li>
            <button
              className={`nav-link ${currentTab === 'settings' ? 'active' : ''}`}
              onClick={() => setCurrentTab('settings')}
            >
              <span className="nav-icon">⚙️</span>
              <span className="nav-label-text">Settings</span>
            </button>
          </li>
        </ul>

        <div className="sidebar-footer">
          <div className="status-indicator"></div>
          <div>
            <strong style={{ fontSize: '11px', display: 'block', color: '#1e293b' }}>System Online</strong>
            <small style={{ fontSize: '10px', color: '#64748b' }}>Logging Service Active</small>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="main-wrapper">
        {/* Topbar */}
        <header className="topbar">
          <div className="page-heading">
            {currentTab === 'dashboard' && 'Dashboard Overview'}
            {currentTab === 'logs' && 'Server Logs Explorer'}
            {currentTab === 'notifications' && 'Incident Notifications'}
            {currentTab === 'settings' && 'System Settings & Demo Tools'}
          </div>

          <div className="topbar-right">
            <button className="btn-add-log" onClick={() => setShowAddLogModal(true)}>
              <span>＋</span> Add Log
            </button>

            {user ? (
              <div className="user-profile">
                <div className="user-avatar">{user.username.charAt(0).toUpperCase()}</div>
                <div className="user-meta">
                  <span className="user-name">{user.username}</span>
                  <span className={`role-badge ${user.is_admin ? 'admin' : ''}`}>
                    {user.role}
                  </span>
                </div>
                <button className="btn-logout" onClick={handleLogout} title="Sign Out">
                  Sign out ↗
                </button>
              </div>
            ) : (
              <div className="user-profile">
                <button
                  className="btn btn-primary btn-sm"
                  onClick={() => { setAuthMode('login'); setShowAuthModal(true); }}
                >
                  Sign In
                </button>
                <button
                  className="btn btn-outline btn-sm"
                  onClick={() => { setAuthMode('register'); setShowAuthModal(true); }}
                >
                  Register
                </button>
              </div>
            )}
          </div>
        </header>

        {/* Body View */}
        <main className="content-body">
          {toast && (
            <div className={`toast-alert toast-${toast.type}`}>
              <span>{toast.message}</span>
              <button
                onClick={() => setToast(null)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '14px' }}
              >
                ✕
              </button>
            </div>
          )}

          {currentTab === 'dashboard' && (
            <DashboardView
              data={dashboardData}
              onNavigateLogs={() => setCurrentTab('logs')}
              onInspectLog={(l) => setInspectLog(l)}
              onResolveAlert={handleResolveAlert}
            />
          )}

          {currentTab === 'logs' && (
            <LogsView
              data={logsData}
              filter={logFilter}
              loading={logsLoading}
              user={user}
              onFilterChange={(newF) => setLogFilter({ ...logFilter, ...newF, page: 1 })}
              onPageChange={(page) => setLogFilter({ ...logFilter, page })}
              onInspectLog={(l) => setInspectLog(l)}
              onDeleteLog={handleDeleteLog}
            />
          )}

          {currentTab === 'notifications' && (
            <NotificationsView
              notifications={notifications}
              filter={notifFilter}
              onFilterChange={(st) => setNotifFilter(st)}
              onResolve={handleResolveAlert}
            />
          )}

          {currentTab === 'settings' && (
            <SettingsView
              user={user}
              data={settingsData}
              onSeedLogs={handleSeedDemoLogs}
              onClearLogs={handleClearAllLogs}
              showToast={showToast}
              onReloadSettings={loadSettings}
            />
          )}
        </main>
      </div>

      {/* --- MODAL: Add New Log --- */}
      {showAddLogModal && (
        <div className="modal-overlay" onClick={() => setShowAddLogModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="panel-title" style={{ fontSize: '17px' }}>Add New Server Log</h3>
              <button className="modal-close" onClick={() => setShowAddLogModal(false)}>✕</button>
            </div>
            <form onSubmit={handleAddLog}>
              <div className="form-group">
                <label className="form-label">Application / Service</label>
                <select name="source_application" className="form-select" defaultValue="Student Portal">
                  <option value="Student Portal">Student Portal</option>
                  <option value="Exam System">Examination System</option>
                  <option value="Fee Gateway">Fee Payment Gateway</option>
                  <option value="Auth Service">Authentication Service</option>
                  <option value="Database Server">Database Server</option>
                  <option value="Library System">Library System</option>
                  <option value="Other">Other / Custom</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Log Message / Error Description</label>
                <textarea
                  name="message"
                  className="form-textarea"
                  rows="3"
                  placeholder="e.g. Database connection timed out or Login failed for user roll_9021"
                  required
                ></textarea>
                <small style={{ fontSize: '10px', color: '#64748b', display: 'block', marginTop: '4px' }}>
                  Keywords like 'error', 'failed', 'timeout', or 'login' will be automatically analyzed.
                </small>
              </div>

              <div className="form-group">
                <label className="form-label">Log Level</label>
                <select name="severity" className="form-select" defaultValue="AUTO">
                  <option value="AUTO">⚡ Auto-classify based on content (Recommended)</option>
                  <option value="INFO">INFO (Normal event)</option>
                  <option value="WARNING">WARNING (Potential issue)</option>
                  <option value="ERROR">ERROR (Application failure)</option>
                  <option value="CRITICAL">CRITICAL (System crash / security exploit)</option>
                </select>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
                <div>
                  <label className="form-label">Client IP (Optional)</label>
                  <input type="text" name="ip_address" className="form-input" placeholder="192.168.1.15" />
                </div>
                <div>
                  <label className="form-label">HTTP Status (Optional)</label>
                  <input type="number" name="status_code" className="form-input" placeholder="e.g. 500, 401, 200" />
                </div>
              </div>

              <div style={{ background: '#f8fafc', padding: '12px', borderRadius: '8px', fontSize: '11px', color: '#475569', marginBottom: '16px' }}>
                ⚡ <strong>Local Classifier:</strong> The engine will sanitize sensitive words and automatically assign the appropriate level and incident alert.
              </div>

              <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                <button type="button" className="btn btn-outline" onClick={() => setShowAddLogModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Record & Classify Log →
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* --- MODAL: Inspect Log Details --- */}
      {inspectLog && (
        <div className="modal-overlay" onClick={() => setInspectLog(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h3 className="panel-title" style={{ fontSize: '17px' }}>Log Event Details</h3>
                <span style={{ fontSize: '11px', color: '#64748b' }}>ID: {inspectLog.id}</span>
              </div>
              <button className="modal-close" onClick={() => setInspectLog(null)}>✕</button>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <span className="form-label">Log Level & Category</span>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <span className={`badge badge-${inspectLog.severity.toLowerCase()}`}>
                  {inspectLog.severity}
                </span>
                <span style={{ fontSize: '12px', fontWeight: 600 }}>{inspectLog.category_display}</span>
              </div>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <span className="form-label">Sanitized Message</span>
              <pre style={{
                background: '#f8fafc',
                border: '1px solid #e2e8f0',
                padding: '12px',
                borderRadius: '8px',
                fontSize: '11px',
                whiteSpace: 'pre-wrap',
                fontFamily: 'monospace'
              }}>
                {inspectLog.message}
              </pre>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '12px', marginBottom: '16px' }}>
              <div>
                <span style={{ color: '#64748b', display: 'block' }}>Application:</span>
                <strong>{inspectLog.source_application}</strong>
              </div>
              <div>
                <span style={{ color: '#64748b', display: 'block' }}>Recorded Time:</span>
                <span>{inspectLog.timestamp}</span>
              </div>
              <div>
                <span style={{ color: '#64748b', display: 'block' }}>Client IP:</span>
                <code>{inspectLog.ip_address || '—'}</code>
              </div>
              <div>
                <span style={{ color: '#64748b', display: 'block' }}>HTTP Status:</span>
                <span>{inspectLog.status_code || '—'}</span>
              </div>
              <div style={{ gridColumn: 'span 2' }}>
                <span style={{ color: '#64748b', display: 'block' }}>Classification Reason:</span>
                <span>{inspectLog.classification_reason || 'Standard rule match'} ({inspectLog.confidence ? `${inspectLog.confidence}% confidence` : 'Rule match'})</span>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
              {user?.is_admin && (
                <button
                  className="btn btn-danger btn-sm"
                  onClick={() => handleDeleteLog(inspectLog.id)}
                >
                  Delete Log
                </button>
              )}
              <button className="btn btn-outline btn-sm" onClick={() => setInspectLog(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* --- MODAL: Authentication (Login / Register) --- */}
      {showAuthModal && (
        <div className="modal-overlay" onClick={() => setShowAuthModal(false)}>
          <div className="modal-card" style={{ maxWidth: '420px' }} onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h3 className="panel-title" style={{ fontSize: '18px' }}>
                  {authMode === 'login' ? 'Sign In to Workspace' : 'Create Officer Account'}
                </h3>
                <span style={{ fontSize: '11px', color: '#64748b' }}>
                  {authMode === 'login' ? 'Enter credentials to proceed' : 'Choose your role and register'}
                </span>
              </div>
              <button className="modal-close" onClick={() => setShowAuthModal(false)}>✕</button>
            </div>

            {authError && (
              <div style={{ background: '#fef2f2', border: '1px solid #fecaca', color: '#b91c1c', padding: '8px 12px', borderRadius: '6px', fontSize: '12px', marginBottom: '14px' }}>
                {authError}
              </div>
            )}

            <form onSubmit={handleAuthSubmit}>
              <div className="form-group">
                <label className="form-label">Username</label>
                <input type="text" name="username" className="form-input" required autoFocus />
              </div>

              {authMode === 'register' && (
                <>
                  <div className="form-group">
                    <label className="form-label">Email Address</label>
                    <input type="email" name="email" className="form-input" required />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Account Role</label>
                    <select name="role" className="form-select" defaultValue="User">
                      <option value="User">Regular User (View dashboard & logs)</option>
                      <option value="Admin">Administrator (Manage logs & alerts)</option>
                    </select>
                  </div>
                </>
              )}

              <div className="form-group">
                <label className="form-label">Password</label>
                <input type="password" name="password" className="form-input" required />
                {authMode === 'register' && (
                  <small style={{ fontSize: '10px', color: '#64748b', display: 'block', marginTop: '3px' }}>
                    Minimum 8 characters.
                  </small>
                )}
              </div>

              <button type="submit" className="btn btn-primary w-100" style={{ width: '100%', padding: '10px', marginTop: '6px' }}>
                {authMode === 'login' ? 'Sign In →' : 'Register Account →'}
              </button>

              <div style={{ textAlign: 'center', marginTop: '16px', fontSize: '12px', color: '#64748b' }}>
                {authMode === 'login' ? (
                  <>
                    Don't have an account?{' '}
                    <button
                      type="button"
                      onClick={() => { setAuthMode('register'); setAuthError(''); }}
                      style={{ background: 'none', border: 'none', color: 'var(--primary)', fontWeight: 600, cursor: 'pointer' }}
                    >
                      Register here
                    </button>
                  </>
                ) : (
                  <>
                    Already have an account?{' '}
                    <button
                      type="button"
                      onClick={() => { setAuthMode('login'); setAuthError(''); }}
                      style={{ background: 'none', border: 'none', color: 'var(--primary)', fontWeight: 600, cursor: 'pointer' }}
                    >
                      Sign in
                    </button>
                  </>
                )}
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

// -------------------------------------------------------------
// View 1: Dashboard
// -------------------------------------------------------------
function DashboardView({ data, onNavigateLogs, onInspectLog, onResolveAlert }) {
  if (!data) return <div style={{ padding: '20px', color: '#64748b' }}>Loading dashboard telemetry...</div>;

  const counts = data.counts || {};
  const recentLogs = data.recent_logs || [];
  const recentAlerts = data.recent_alerts || [];
  const daily = data.daily || [];

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Operational Overview</h1>
          <p className="page-subtitle">Summary of server events, automated level distribution, and incident alerts.</p>
        </div>
        <button className="btn btn-outline btn-sm" onClick={onNavigateLogs}>
          Explore All Logs →
        </button>
      </div>

      {/* 4 Clean Stat Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-header">
            <span>Total Logs</span>
            <div className="stat-icon" style={{ background: '#eef2ff', color: '#4f46e5' }}>≡</div>
          </div>
          <div className="stat-value">{counts.total ?? 0}</div>
          <div className="stat-desc">All recorded events</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span>Info Logs</span>
            <div className="stat-icon" style={{ background: '#ecfdf5', color: '#10b981' }}>✓</div>
          </div>
          <div className="stat-value" style={{ color: '#059669' }}>{counts.info ?? 0}</div>
          <div className="stat-desc">Normal application activities</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span>Warnings</span>
            <div className="stat-icon" style={{ background: '#fffbeb', color: '#d97706' }}>△</div>
          </div>
          <div className="stat-value" style={{ color: '#d97706' }}>{counts.warnings ?? 0}</div>
          <div className="stat-desc">Retries & potential issues</div>
        </div>

        <div className="stat-card accent-red">
          <div className="stat-header">
            <span>Errors & Critical</span>
            <div className="stat-icon" style={{ background: '#fef2f2', color: '#ef4444' }}>!</div>
          </div>
          <div className="stat-value" style={{ color: '#dc2626' }}>{counts.errors ?? 0}</div>
          <div className="stat-desc">{counts.critical ?? 0} critical failures flagged</div>
        </div>
      </div>

      {/* Charts Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '16px', marginBottom: '24px' }}>
        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">7-Day Log Activity Trend</h2>
              <p className="panel-desc">Daily events ingested across connected services</p>
            </div>
          </div>
          <SimpleAreaChart data={daily} />
        </div>

        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Level Distribution</h2>
              <p className="panel-desc">Proportion of events by classified severity</p>
            </div>
          </div>
          <SimpleDonutChart counts={counts} />
        </div>
      </div>

      {/* Tables Row: Recent Logs + Recent Alerts */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '16px' }}>
        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Recent Server Logs</h2>
              <p className="panel-desc">Latest classified telemetry records</p>
            </div>
            <button className="btn btn-outline btn-sm" onClick={onNavigateLogs}>
              View All →
            </button>
          </div>

          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>TIME</th>
                  <th>APPLICATION</th>
                  <th>LEVEL</th>
                  <th>MESSAGE</th>
                  <th>ACTION</th>
                </tr>
              </thead>
              <tbody>
                {recentLogs.map((log) => (
                  <tr key={log.id} className={log.severity === 'CRITICAL' ? 'critical-row' : log.severity === 'ERROR' ? 'error-row' : ''}>
                    <td style={{ whiteSpace: 'nowrap' }}>{log.timestamp.slice(5, 16)}</td>
                    <td><strong>{log.source_application}</strong></td>
                    <td>
                      <span className={`badge badge-${log.severity.toLowerCase()}`}>
                        {log.severity}
                      </span>
                    </td>
                    <td title={log.message}>{log.message.length > 55 ? `${log.message.slice(0, 55)}...` : log.message}</td>
                    <td>
                      <button className="btn btn-outline btn-sm" onClick={() => onInspectLog(log)}>
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
                {recentLogs.length === 0 && (
                  <tr>
                    <td colSpan="5" style={{ textAlign: 'center', padding: '24px', color: '#94a3b8' }}>
                      No logs collected yet. Use "Add Log" to record an event.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Notifications Card */}
        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Active Notifications</h2>
              <p className="panel-desc">Unresolved alerts requiring review</p>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {recentAlerts.map((alt) => (
              <div key={alt.id} style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '10px 12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                  <span className={`badge badge-${alt.severity.toLowerCase()}`}>{alt.severity}</span>
                  <small style={{ fontSize: '10px', color: '#94a3b8' }}>{alt.created_at.slice(5, 16)}</small>
                </div>
                <div style={{ fontSize: '11px', fontWeight: 600, color: '#1e293b', marginBottom: '6px' }}>
                  {alt.description}
                </div>
                <button
                  className="btn btn-outline btn-sm"
                  style={{ fontSize: '10px', padding: '2px 8px' }}
                  onClick={() => onResolveAlert(alt.id)}
                >
                  ✓ Mark Resolved
                </button>
              </div>
            ))}
            {recentAlerts.length === 0 && (
              <div style={{ textAlign: 'center', padding: '24px 10px', color: '#94a3b8', fontSize: '12px' }}>
                ✓ No active notifications. All systems are operational.
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

// -------------------------------------------------------------
// View 2: All Logs Explorer
// -------------------------------------------------------------
function LogsView({ data, filter, loading, user, onFilterChange, onPageChange, onInspectLog, onDeleteLog }) {
  const [qInput, setQInput] = useState(filter.q || '');

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    onFilterChange({ q: qInput });
  };

  const handleLevelClick = (lvl) => {
    onFilterChange({ level: filter.level === lvl ? '' : lvl });
  };

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Server Logs Explorer</h1>
          <p className="page-subtitle">Search, filter, inspect, and export application log records.</p>
        </div>
        <a href={`${API_BASE}/logs/export/?q=${encodeURIComponent(filter.q)}&level=${filter.level}`} className="btn btn-outline" download>
          ↓ Export CSV
        </a>
      </div>

      {/* Filter Toolbar */}
      <div className="panel" style={{ padding: '16px', marginBottom: '16px' }}>
        <form onSubmit={handleSearchSubmit} style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', alignItems: 'center' }}>
          <div style={{ flex: '1 1 240px' }}>
            <input
              type="text"
              className="form-input"
              placeholder="Search by keyword, application, or IP..."
              value={qInput}
              onChange={(e) => setQInput(e.target.value)}
            />
          </div>

          <div style={{ display: 'flex', gap: '6px' }}>
            {['', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'].map((lvl) => (
              <button
                key={lvl}
                type="button"
                className={`btn btn-sm ${filter.level === lvl ? 'btn-primary' : 'btn-outline'}`}
                onClick={() => handleLevelClick(lvl)}
              >
                {lvl === '' ? 'All Levels' : lvl}
              </button>
            ))}
          </div>

          <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
            <input
              type="date"
              className="form-input"
              style={{ width: '135px' }}
              value={filter.from}
              onChange={(e) => onFilterChange({ from: e.target.value })}
              title="From Date"
            />
            <span style={{ color: '#94a3b8' }}>–</span>
            <input
              type="date"
              className="form-input"
              style={{ width: '135px' }}
              value={filter.to}
              onChange={(e) => onFilterChange({ to: e.target.value })}
              title="To Date"
            />
          </div>

          <button type="submit" className="btn btn-primary btn-sm">Filter</button>
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={() => { setQInput(''); onFilterChange({ q: '', level: '', from: '', to: '' }); }}
          >
            Reset
          </button>
        </form>
      </div>

      {/* Table Panel */}
      <div className="panel" style={{ padding: '0', overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--line)', display: 'flex', justifyContent: 'space-between' }}>
          <strong style={{ fontSize: '13px' }}>Matching Events ({data.count ?? 0})</strong>
          {loading && <span style={{ fontSize: '11px', color: '#6366f1' }}>Updating records...</span>}
        </div>

        <div className="table-responsive">
          <table className="data-table">
            <thead>
              <tr>
                <th>TIMESTAMP</th>
                <th>APPLICATION</th>
                <th>LEVEL</th>
                <th>CATEGORY</th>
                <th>MESSAGE</th>
                <th>IP</th>
                <th>ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              {data.results.map((log) => (
                <tr key={log.id} className={log.severity === 'CRITICAL' ? 'critical-row' : log.severity === 'ERROR' ? 'error-row' : ''}>
                  <td style={{ whiteSpace: 'nowrap', fontSize: '11px' }}>{log.timestamp}</td>
                  <td><strong>{log.source_application}</strong></td>
                  <td>
                    <span className={`badge badge-${log.severity.toLowerCase()}`}>
                      {log.severity}
                    </span>
                  </td>
                  <td><small style={{ color: '#64748b' }}>{log.category_display}</small></td>
                  <td title={log.message}>{log.message.length > 70 ? `${log.message.slice(0, 70)}...` : log.message}</td>
                  <td><code>{log.ip_address || '—'}</code></td>
                  <td>
                    <div style={{ display: 'flex', gap: '6px' }}>
                      <button className="btn btn-outline btn-sm" onClick={() => onInspectLog(log)}>Inspect</button>
                      {user?.is_admin && (
                        <button className="btn btn-danger btn-sm" onClick={() => onDeleteLog(log.id)}>Delete</button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {data.results.length === 0 && (
                <tr>
                  <td colSpan="7" style={{ textAlign: 'center', padding: '36px', color: '#94a3b8' }}>
                    No matching log entries found for the selected query.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {data.num_pages > 1 && (
          <div style={{ padding: '12px 20px', borderTop: '1px solid var(--line)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px' }}>
            <button
              className="btn btn-outline btn-sm"
              disabled={!data.has_previous}
              onClick={() => onPageChange(data.current_page - 1)}
            >
              ← Previous
            </button>
            <span style={{ color: '#64748b' }}>
              Page {data.current_page} of {data.num_pages}
            </span>
            <button
              className="btn btn-outline btn-sm"
              disabled={!data.has_next}
              onClick={() => onPageChange(data.current_page + 1)}
            >
              Next →
            </button>
          </div>
        )}
      </div>
    </>
  );
}

// -------------------------------------------------------------
// View 3: Notifications
// -------------------------------------------------------------
function NotificationsView({ notifications, filter, onFilterChange, onResolve }) {
  const alerts = notifications.results || [];

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Incident Notifications</h1>
          <p className="page-subtitle">Critical failure events and automated anomaly triggers.</p>
        </div>
        <div style={{ display: 'flex', gap: '6px' }}>
          {['unresolved', 'resolved', 'all'].map((st) => (
            <button
              key={st}
              className={`btn btn-sm ${filter === st ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => onFilterChange(st)}
            >
              {st === 'unresolved' ? `Unresolved (${notifications.unresolved_count})` : st.charAt(0).toUpperCase() + st.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="panel" style={{ padding: 0, overflow: 'hidden' }}>
        <div className="table-responsive">
          <table className="data-table">
            <thead>
              <tr>
                <th>TIME</th>
                <th>SEVERITY</th>
                <th>SOURCE</th>
                <th>DESCRIPTION</th>
                <th>STATUS</th>
                <th>ACTION</th>
              </tr>
            </thead>
            <tbody>
              {alerts.map((alt) => (
                <tr key={alt.id} style={{ background: alt.state !== 'RESOLVED' ? '#fffdfa' : '' }}>
                  <td style={{ whiteSpace: 'nowrap' }}>{alt.created_at}</td>
                  <td>
                    <span className={`badge badge-${alt.severity.toLowerCase()}`}>{alt.severity}</span>
                  </td>
                  <td><strong>{alt.source_application}</strong></td>
                  <td>
                    <div style={{ fontWeight: 600 }}>{alt.description}</div>
                    {alt.recommended_action && (
                      <small style={{ color: '#64748b', display: 'block' }}>{alt.recommended_action}</small>
                    )}
                  </td>
                  <td>
                    {alt.state === 'RESOLVED' ? (
                      <span className="badge badge-info">Resolved</span>
                    ) : (
                      <span className="badge badge-error">Active</span>
                    )}
                  </td>
                  <td>
                    {alt.state !== 'RESOLVED' ? (
                      <button className="btn btn-outline btn-sm" onClick={() => onResolve(alt.id)}>
                        ✓ Mark as Resolved
                      </button>
                    ) : (
                      <small style={{ color: '#94a3b8' }}>Handled by {alt.handled_by || 'Admin'}</small>
                    )}
                  </td>
                </tr>
              ))}
              {alerts.length === 0 && (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', padding: '36px', color: '#94a3b8' }}>
                    No incident notifications in this view.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}

// -------------------------------------------------------------
// View 4: Settings & College Demo Tools
// -------------------------------------------------------------
function SettingsView({ user, data, onSeedLogs, onClearLogs, showToast, onReloadSettings }) {
  const [threshold, setThreshold] = useState(data?.current_threshold || '5');

  useEffect(() => {
    if (data?.current_threshold) setThreshold(data.current_threshold);
  }, [data]);

  const handleUpdateThreshold = (e) => {
    e.preventDefault();
    fetch(`${API_BASE}/settings/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ auth_threshold: threshold }),
    })
      .then((res) => res.json())
      .then((d) => {
        if (d.success) {
          showToast(`Threshold updated to ${d.current_threshold} attempts.`);
          onReloadSettings();
        } else {
          alert(d.error || 'Failed to update.');
        }
      });
  };

  const sys = data?.sys_info || {};

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Settings & Demo Utilities</h1>
          <p className="page-subtitle">Configure anomaly thresholds, review user permissions, and run demo utilities.</p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {/* Left Card: User & Role info */}
        <div>
          <div className="panel">
            <h2 className="panel-title" style={{ marginBottom: '12px' }}>Account & Permissions</h2>
            {user ? (
              <div style={{ fontSize: '13px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
                  <div className="user-avatar" style={{ width: '40px', height: '40px', fontSize: '16px' }}>
                    {user.username.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <strong>{user.username}</strong>
                    <div style={{ fontSize: '11px', color: '#64748b' }}>{user.email}</div>
                  </div>
                </div>
                <div style={{ background: '#f8fafc', padding: '12px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                  <div style={{ marginBottom: '4px' }}>
                    Role: <span className={`badge ${user.is_admin ? 'badge-critical' : 'badge-info'}`}>{user.role}</span>
                  </div>
                  <small style={{ color: '#64748b' }}>
                    {user.is_admin
                      ? 'Administrator privileges: Full access to inspect, add, delete logs, resolve alerts, and reset the database.'
                      : 'Regular User privileges: Access to view dashboard, search logs, add new logs, and view notifications.'}
                  </small>
                </div>
              </div>
            ) : (
              <div style={{ color: '#64748b', fontSize: '12px' }}>
                Not currently signed in. Use the Sign In button in the topbar to access full role features.
              </div>
            )}
          </div>

          {/* Threshold Card */}
          <div className="panel">
            <h2 className="panel-title" style={{ marginBottom: '8px' }}>Auth Anomaly Threshold</h2>
            <p className="panel-desc" style={{ marginBottom: '14px' }}>
              Number of failed authentication attempts from the same IP within 10 minutes required to trigger a brute-force alert.
            </p>
            <form onSubmit={handleUpdateThreshold} style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <input
                type="number"
                min="2"
                max="50"
                className="form-input"
                style={{ width: '100px' }}
                value={threshold}
                onChange={(e) => setThreshold(e.target.value)}
              />
              <button type="submit" className="btn btn-primary btn-sm">Update</button>
            </form>
          </div>
        </div>

        {/* Right Card: College Demo Tools & Environment */}
        <div>
          <div className="panel" style={{ borderTop: '3px solid var(--primary)' }}>
            <h2 className="panel-title" style={{ marginBottom: '8px' }}>College Project Demo Tools</h2>
            <p className="panel-desc" style={{ marginBottom: '16px' }}>
              One-click testing tools designed for live student evaluations and demonstrations.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                <strong style={{ fontSize: '12px', color: '#1e293b' }}>⚡ Seed Sample Demo Logs</strong>
                <p style={{ fontSize: '11px', color: '#64748b', margin: '4px 0 10px' }}>
                  Generates 10 realistic logs across Student Portal, Fee Gateway, and Database Server with mixed INFO, WARNING, and ERROR severities.
                </p>
                <button className="btn btn-outline btn-sm" onClick={onSeedLogs}>
                  Generate 10 Sample Logs
                </button>
              </div>

              {user?.is_admin && (
                <div style={{ background: '#fef2f2', padding: '14px', borderRadius: '8px', border: '1px solid #fecaca' }}>
                  <strong style={{ fontSize: '12px', color: '#991b1b' }}>🗑 Reset & Clear All Records</strong>
                  <p style={{ fontSize: '11px', color: '#b91c1c', margin: '4px 0 10px' }}>
                    Wipes all log entries and notifications so you can start a clean demonstration.
                  </p>
                  <button className="btn btn-danger btn-sm" onClick={onClearLogs}>
                    Clear All Logs & Alerts
                  </button>
                </div>
              )}
            </div>
          </div>

          <div className="panel">
            <h2 className="panel-title" style={{ marginBottom: '12px' }}>Environment Diagnostics</h2>
            <table className="data-table" style={{ fontSize: '12px' }}>
              <tbody>
                <tr>
                  <td style={{ color: '#64748b' }}>Frontend Framework:</td>
                  <td><strong>React 18 (Vite SPA)</strong></td>
                </tr>
                <tr>
                  <td style={{ color: '#64748b' }}>Backend Framework:</td>
                  <td><strong>Django {sys.django_version || '6.1'} (REST Framework)</strong></td>
                </tr>
                <tr>
                  <td style={{ color: '#64748b' }}>Database Engine:</td>
                  <td><code>{sys.database || 'SQLite'}</code></td>
                </tr>
                <tr>
                  <td style={{ color: '#64748b' }}>Total Logs in DB:</td>
                  <td><strong>{sys.total_logs ?? 0}</strong></td>
                </tr>
                <tr>
                  <td style={{ color: '#64748b' }}>Active Alerts:</td>
                  <td><strong>{sys.total_alerts ?? 0}</strong></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </>
  );
}

// -------------------------------------------------------------
// Lightweight SVG Visual Charts
// -------------------------------------------------------------
function SimpleDonutChart({ counts }) {
  const info = counts.info || 0;
  const warnings = counts.warnings || 0;
  const critical = counts.critical || 0;
  const errors = Math.max(0, (counts.errors || 0) - critical);
  const total = info + warnings + errors + critical;

  if (total === 0) {
    return <div style={{ textAlign: 'center', padding: '40px', color: '#94a3b8', fontSize: '12px' }}>No log data for chart.</div>;
  }

  // Percentages
  const pInfo = (info / total) * 100;
  const pWarn = (warnings / total) * 100;
  const pErr = (errors / total) * 100;
  const pCrit = (critical / total) * 100;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '14px' }}>
      <div style={{ width: '100%', height: '14px', display: 'flex', borderRadius: '7px', overflow: 'hidden', background: '#f1f5f9' }}>
        {pInfo > 0 && <div style={{ width: `${pInfo}%`, background: '#10b981' }} title={`Info: ${info}`} />}
        {pWarn > 0 && <div style={{ width: `${pWarn}%`, background: '#f59e0b' }} title={`Warning: ${warnings}`} />}
        {pErr > 0 && <div style={{ width: `${pErr}%`, background: '#ef4444' }} title={`Error: ${errors}`} />}
        {pCrit > 0 && <div style={{ width: `${pCrit}%`, background: '#b91c1c' }} title={`Critical: ${critical}`} />}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', width: '100%', fontSize: '11px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#10b981' }} />
          <span>Info: <strong>{info}</strong> ({Math.round(pInfo)}%)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#f59e0b' }} />
          <span>Warning: <strong>{warnings}</strong> ({Math.round(pWarn)}%)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#ef4444' }} />
          <span>Error: <strong>{errors}</strong> ({Math.round(pErr)}%)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#b91c1c' }} />
          <span>Critical: <strong>{critical}</strong> ({Math.round(pCrit)}%)</span>
        </div>
      </div>
    </div>
  );
}

function SimpleAreaChart({ data }) {
  if (!data || data.length === 0) {
    return <div style={{ textAlign: 'center', padding: '40px', color: '#94a3b8', fontSize: '12px' }}>No daily trend data available yet.</div>;
  }

  const maxVal = Math.max(...data.map((d) => d.total), 5);
  const chartHeight = 160;
  const chartWidth = 500;
  const padding = 20;

  const points = data.map((d, index) => {
    const x = padding + (index / (data.length - 1 || 1)) * (chartWidth - padding * 2);
    const y = chartHeight - padding - (d.total / maxVal) * (chartHeight - padding * 2);
    return { x, y, day: String(d.day).slice(5), total: d.total };
  });

  const pathD = points.reduce((acc, p, i) => `${acc} ${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`, '');
  const areaD = `${pathD} L ${points[points.length - 1].x} ${chartHeight - padding} L ${points[0].x} ${chartHeight - padding} Z`;

  return (
    <div style={{ width: '100%', overflowX: 'auto' }}>
      <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} style={{ width: '100%', height: '170px' }}>
        <defs>
          <linearGradient id="chartGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#6366f1" stopOpacity="0.25" />
            <stop offset="100%" stopColor="#6366f1" stopOpacity="0.0" />
          </linearGradient>
        </defs>

        {/* Base axis */}
        <line x1={padding} y1={chartHeight - padding} x2={chartWidth - padding} y2={chartHeight - padding} stroke="#e2e8f0" strokeWidth="1" />

        {/* Area fill */}
        <path d={areaD} fill="url(#chartGrad)" />

        {/* Line */}
        <path d={pathD} fill="none" stroke="#6366f1" strokeWidth="2.5" />

        {/* Points and Labels */}
        {points.map((p, i) => (
          <g key={i}>
            <circle cx={p.x} cy={p.y} r="3.5" fill="#6366f1" stroke="#ffffff" strokeWidth="1.5" />
            <text x={p.x} y={chartHeight - 4} fontSize="9" fill="#94a3b8" textAnchor="middle">
              {p.day}
            </text>
            {p.total > 0 && (
              <text x={p.x} y={p.y - 7} fontSize="9" fontWeight="700" fill="#4f46e5" textAnchor="middle">
                {p.total}
              </text>
            )}
          </g>
        ))}
      </svg>
    </div>
  );
}
