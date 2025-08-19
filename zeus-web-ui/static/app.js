// Zeus EAA Compliance Tool - React Frontend
const { useState, useEffect } = React;

// Main App Component
const App = () => {
    const [activeTab, setActiveTab] = useState('process');
    const [jobs, setJobs] = useState([]);
    const [clusterStatus, setClusterStatus] = useState({});
    const [loading, setLoading] = useState(false);

    // Fetch jobs and cluster status
    const fetchData = async () => {
        try {
            const [jobsResponse, clusterResponse] = await Promise.all([
                fetch('/api/v1/jobs'),
                fetch('/api/v1/cluster/status')
            ]);
            
            if (jobsResponse.ok) {
                const jobsData = await jobsResponse.json();
                setJobs(jobsData.jobs || []);
            }
            
            if (clusterResponse.ok) {
                const clusterData = await clusterResponse.json();
                setClusterStatus(clusterData);
            }
        } catch (error) {
            console.error('Error fetching data:', error);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 5000); // Refresh every 5 seconds
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="container-fluid">
            {/* Header */}
            <nav className="navbar navbar-expand-lg navbar-dark bg-primary mb-4">
                <div className="container">
                    <span className="navbar-brand">
                        <i className="fas fa-video me-2"></i>
                        Zeus EAA Compliance Tool
                    </span>
                    <div className="navbar-text">
                        <i className="fas fa-server me-1"></i>
                        Cluster: {clusterStatus.cluster_name || 'Loading...'}
                        <span className={`badge ms-2 ${clusterStatus.health_status === 'healthy' ? 'bg-success' : 'bg-warning'}`}>
                            {clusterStatus.health_status || 'Unknown'}
                        </span>
                    </div>
                </div>
            </nav>

            <div className="container">
                {/* Navigation Tabs */}
                <ul className="nav nav-tabs mb-4">
                    <li className="nav-item">
                        <button 
                            className={`nav-link ${activeTab === 'process' ? 'active' : ''}`}
                            onClick={() => setActiveTab('process')}
                        >
                            <i className="fas fa-upload me-1"></i>
                            Process Video
                        </button>
                    </li>
                    <li className="nav-item">
                        <button 
                            className={`nav-link ${activeTab === 'jobs' ? 'active' : ''}`}
                            onClick={() => setActiveTab('jobs')}
                        >
                            <i className="fas fa-list me-1"></i>
                            Jobs ({jobs.length})
                        </button>
                    </li>
                    <li className="nav-item">
                        <button 
                            className={`nav-link ${activeTab === 'cluster' ? 'active' : ''}`}
                            onClick={() => setActiveTab('cluster')}
                        >
                            <i className="fas fa-server me-1"></i>
                            Cluster
                        </button>
                    </li>
                </ul>

                {/* Tab Content */}
                <div className="tab-content">
                    {activeTab === 'process' && <ProcessVideoTab onJobSubmitted={fetchData} />}
                    {activeTab === 'jobs' && <JobsTab jobs={jobs} onRefresh={fetchData} />}
                    {activeTab === 'cluster' && <ClusterTab clusterStatus={clusterStatus} onRefresh={fetchData} />}
                </div>
            </div>
        </div>
    );
};

// Process Video Tab Component
const ProcessVideoTab = ({ onJobSubmitted }) => {
    const [formData, setFormData] = useState({
        video_url: '',
        priority: 'normal',
        compliance_level: 'eaa',
        whisper_model: 'large-v3',
        num_passes: 5,
        user_id: '',
        organization: ''
    });
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setResult(null);

        try {
            const response = await fetch('/api/v1/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData),
            });

            const data = await response.json();

            if (response.ok) {
                setResult({ success: true, data });
                onJobSubmitted();
                // Reset form
                setFormData({
                    ...formData,
                    video_url: '',
                    user_id: '',
                    organization: ''
                });
            } else {
                setResult({ success: false, error: data.detail });
            }
        } catch (error) {
            setResult({ success: false, error: error.message });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="row">
            <div className="col-md-8">
                <div className="card">
                    <div className="card-header">
                        <h5 className="card-title mb-0">
                            <i className="fas fa-video me-2"></i>
                            Submit Video for Processing
                        </h5>
                    </div>
                    <div className="card-body">
                        <form onSubmit={handleSubmit}>
                            <div className="mb-3">
                                <label className="form-label">Video URL *</label>
                                <input
                                    type="url"
                                    className="form-control"
                                    value={formData.video_url}
                                    onChange={(e) => setFormData({...formData, video_url: e.target.value})}
                                    placeholder="https://storage.blob.core.windows.net/input/video.mp4"
                                    required
                                />
                                <div className="form-text">Azure Blob Storage URL or accessible video URL</div>
                            </div>

                            <div className="row">
                                <div className="col-md-6">
                                    <div className="mb-3">
                                        <label className="form-label">Priority</label>
                                        <select
                                            className="form-select"
                                            value={formData.priority}
                                            onChange={(e) => setFormData({...formData, priority: e.target.value})}
                                        >
                                            <option value="low">Low</option>
                                            <option value="normal">Normal</option>
                                            <option value="high">High</option>
                                            <option value="urgent">Urgent</option>
                                        </select>
                                    </div>
                                </div>
                                <div className="col-md-6">
                                    <div className="mb-3">
                                        <label className="form-label">Compliance Level</label>
                                        <select
                                            className="form-select"
                                            value={formData.compliance_level}
                                            onChange={(e) => setFormData({...formData, compliance_level: e.target.value})}
                                        >
                                            <option value="wcag_aa">WCAG 2.1 AA</option>
                                            <option value="eaa">EAA (European Accessibility Act)</option>
                                            <option value="section_508">Section 508</option>
                                        </select>
                                    </div>
                                </div>
                            </div>

                            <div className="row">
                                <div className="col-md-6">
                                    <div className="mb-3">
                                        <label className="form-label">Whisper Model</label>
                                        <select
                                            className="form-select"
                                            value={formData.whisper_model}
                                            onChange={(e) => setFormData({...formData, whisper_model: e.target.value})}
                                        >
                                            <option value="tiny">Tiny (Fast)</option>
                                            <option value="base">Base</option>
                                            <option value="small">Small</option>
                                            <option value="medium">Medium</option>
                                            <option value="large">Large</option>
                                            <option value="large-v3">Large v3 (Best Quality)</option>
                                        </select>
                                    </div>
                                </div>
                                <div className="col-md-6">
                                    <div className="mb-3">
                                        <label className="form-label">Number of Passes</label>
                                        <input
                                            type="number"
                                            className="form-control"
                                            value={formData.num_passes}
                                            onChange={(e) => setFormData({...formData, num_passes: parseInt(e.target.value)})}
                                            min="1"
                                            max="10"
                                        />
                                        <div className="form-text">More passes = better quality, longer processing time</div>
                                    </div>
                                </div>
                            </div>

                            <div className="row">
                                <div className="col-md-6">
                                    <div className="mb-3">
                                        <label className="form-label">User ID</label>
                                        <input
                                            type="text"
                                            className="form-control"
                                            value={formData.user_id}
                                            onChange={(e) => setFormData({...formData, user_id: e.target.value})}
                                            placeholder="user@company.com"
                                        />
                                    </div>
                                </div>
                                <div className="col-md-6">
                                    <div className="mb-3">
                                        <label className="form-label">Organization</label>
                                        <input
                                            type="text"
                                            className="form-control"
                                            value={formData.organization}
                                            onChange={(e) => setFormData({...formData, organization: e.target.value})}
                                            placeholder="Company Name"
                                        />
                                    </div>
                                </div>
                            </div>

                            <button
                                type="submit"
                                className="btn btn-primary"
                                disabled={loading || !formData.video_url}
                            >
                                {loading ? (
                                    <>
                                        <span className="spinner-border spinner-border-sm me-2"></span>
                                        Processing...
                                    </>
                                ) : (
                                    <>
                                        <i className="fas fa-play me-2"></i>
                                        Start Processing
                                    </>
                                )}
                            </button>
                        </form>
                    </div>
                </div>
            </div>

            <div className="col-md-4">
                <div className="card">
                    <div className="card-header">
                        <h6 className="card-title mb-0">Processing Pipeline</h6>
                    </div>
                    <div className="card-body">
                        <div className="d-flex align-items-center mb-2">
                            <i className="fas fa-upload text-primary me-2"></i>
                            <small>1. Video Upload & Validation</small>
                        </div>
                        <div className="d-flex align-items-center mb-2">
                            <i className="fas fa-microchip text-primary me-2"></i>
                            <small>2. GPU-Accelerated Transcription</small>
                        </div>
                        <div className="d-flex align-items-center mb-2">
                            <i className="fas fa-sync text-primary me-2"></i>
                            <small>3. Multi-Pass Processing</small>
                        </div>
                        <div className="d-flex align-items-center mb-2">
                            <i className="fas fa-check-circle text-primary me-2"></i>
                            <small>4. EAA Compliance Validation</small>
                        </div>
                        <div className="d-flex align-items-center">
                            <i className="fas fa-download text-primary me-2"></i>
                            <small>5. Subtitle Export (SRT, WebVTT)</small>
                        </div>
                    </div>
                </div>

                {result && (
                    <div className={`alert mt-3 ${result.success ? 'alert-success' : 'alert-danger'}`}>
                        <h6 className="alert-heading">
                            {result.success ? (
                                <><i className="fas fa-check-circle me-2"></i>Success!</>
                            ) : (
                                <><i className="fas fa-exclamation-triangle me-2"></i>Error</>
                            )}
                        </h6>
                        {result.success ? (
                            <div>
                                <p className="mb-1">Job ID: <code>{result.data.job_id}</code></p>
                                <p className="mb-0">Status: <span className="badge bg-info">{result.data.status}</span></p>
                            </div>
                        ) : (
                            <p className="mb-0">{result.error}</p>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

// Jobs Tab Component
const JobsTab = ({ jobs, onRefresh }) => {
    const [selectedJob, setSelectedJob] = useState(null);
    const [jobDetails, setJobDetails] = useState({});

    const fetchJobDetails = async (jobId) => {
        try {
            const response = await fetch(`/api/v1/jobs/${jobId}`);
            if (response.ok) {
                const data = await response.json();
                setJobDetails(prev => ({ ...prev, [jobId]: data }));
            }
        } catch (error) {
            console.error('Error fetching job details:', error);
        }
    };

    const getStatusBadge = (status) => {
        const statusMap = {
            'queued': 'bg-secondary',
            'processing': 'bg-primary',
            'transcribing': 'bg-info',
            'completed': 'bg-success',
            'failed': 'bg-danger'
        };
        return statusMap[status] || 'bg-secondary';
    };

    const getPriorityBadge = (priority) => {
        const priorityMap = {
            'low': 'bg-light text-dark',
            'normal': 'bg-info',
            'high': 'bg-warning text-dark',
            'urgent': 'bg-danger'
        };
        return priorityMap[priority] || 'bg-info';
    };

    return (
        <div>
            <div className="d-flex justify-content-between align-items-center mb-3">
                <h5>Processing Jobs</h5>
                <button className="btn btn-outline-primary btn-sm" onClick={onRefresh}>
                    <i className="fas fa-sync-alt me-1"></i>
                    Refresh
                </button>
            </div>

            {jobs.length === 0 ? (
                <div className="text-center py-5">
                    <i className="fas fa-inbox fa-3x text-muted mb-3"></i>
                    <h5 className="text-muted">No jobs found</h5>
                    <p className="text-muted">Submit a video for processing to see jobs here.</p>
                </div>
            ) : (
                <div className="table-responsive">
                    <table className="table table-hover">
                        <thead>
                            <tr>
                                <th>Job Name</th>
                                <th>Status</th>
                                <th>Priority</th>
                                <th>Created</th>
                                <th>Request ID</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {jobs.map((job) => (
                                <tr key={job.name}>
                                    <td>
                                        <code className="small">{job.name}</code>
                                    </td>
                                    <td>
                                        <span className={`badge ${getStatusBadge(job.status)}`}>
                                            {job.status}
                                        </span>
                                    </td>
                                    <td>
                                        <span className={`badge ${getPriorityBadge(job.priority)}`}>
                                            {job.priority}
                                        </span>
                                    </td>
                                    <td>
                                        <small>{new Date(job.created).toLocaleString()}</small>
                                    </td>
                                    <td>
                                        <code className="small">{job.request_id}</code>
                                    </td>
                                    <td>
                                        <button
                                            className="btn btn-sm btn-outline-info"
                                            onClick={() => {
                                                setSelectedJob(job);
                                                fetchJobDetails(job.request_id);
                                            }}
                                        >
                                            <i className="fas fa-info-circle"></i>
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Job Details Modal */}
            {selectedJob && (
                <div className="modal fade show d-block" style={{backgroundColor: 'rgba(0,0,0,0.5)'}}>
                    <div className="modal-dialog modal-lg">
                        <div className="modal-content">
                            <div className="modal-header">
                                <h5 className="modal-title">Job Details</h5>
                                <button
                                    type="button"
                                    className="btn-close"
                                    onClick={() => setSelectedJob(null)}
                                ></button>
                            </div>
                            <div className="modal-body">
                                <JobDetailsComponent 
                                    job={selectedJob} 
                                    details={jobDetails[selectedJob.request_id]} 
                                />
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

// Job Details Component
const JobDetailsComponent = ({ job, details }) => {
    if (!details) {
        return (
            <div className="text-center">
                <div className="spinner-border" role="status">
                    <span className="visually-hidden">Loading...</span>
                </div>
            </div>
        );
    }

    return (
        <div>
            <div className="row mb-3">
                <div className="col-md-6">
                    <strong>Job ID:</strong> <code>{details.job_id}</code>
                </div>
                <div className="col-md-6">
                    <strong>Status:</strong> 
                    <span className={`badge ms-2 ${details.status === 'completed' ? 'bg-success' : 'bg-info'}`}>
                        {details.status}
                    </span>
                </div>
            </div>

            <div className="row mb-3">
                <div className="col-md-6">
                    <strong>Created:</strong> {new Date(details.created_at).toLocaleString()}
                </div>
                {details.updated_at && (
                    <div className="col-md-6">
                        <strong>Updated:</strong> {new Date(details.updated_at).toLocaleString()}
                    </div>
                )}
            </div>

            {details.metrics && (
                <div className="mb-3">
                    <h6>Processing Metrics</h6>
                    <div className="row">
                        <div className="col-md-3">
                            <div className="text-center">
                                <div className="h5 text-primary">{details.metrics.cpu_usage?.toFixed(1)}%</div>
                                <small className="text-muted">CPU Usage</small>
                            </div>
                        </div>
                        <div className="col-md-3">
                            <div className="text-center">
                                <div className="h5 text-info">{details.metrics.memory_usage}</div>
                                <small className="text-muted">Memory (MB)</small>
                            </div>
                        </div>
                        <div className="col-md-3">
                            <div className="text-center">
                                <div className="h5 text-success">{details.metrics.gpu_utilization?.toFixed(1)}%</div>
                                <small className="text-muted">GPU Usage</small>
                            </div>
                        </div>
                        <div className="col-md-3">
                            <div className="text-center">
                                <div className="h5 text-warning">{details.metrics.processing_time?.toFixed(1)}s</div>
                                <small className="text-muted">Processing Time</small>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {details.outputs && (
                <div className="mb-3">
                    <h6>Output Files</h6>
                    <div className="list-group">
                        {Object.entries(details.outputs).map(([format, url]) => (
                            <a
                                key={format}
                                href={url}
                                className="list-group-item list-group-item-action"
                                target="_blank"
                                rel="noopener noreferrer"
                            >
                                <i className="fas fa-download me-2"></i>
                                {format.toUpperCase()} Subtitles
                                <i className="fas fa-external-link-alt ms-2 small"></i>
                            </a>
                        ))}
                    </div>
                </div>
            )}

            {details.error_details && (
                <div className="alert alert-danger">
                    <h6 className="alert-heading">Error Details</h6>
                    <pre className="mb-0 small">{details.error_details}</pre>
                </div>
            )}
        </div>
    );
};

// Cluster Tab Component
const ClusterTab = ({ clusterStatus, onRefresh }) => {
    const [scaleNodeCount, setScaleNodeCount] = useState(2);
    const [scaling, setScaling] = useState(false);

    const handleScale = async () => {
        setScaling(true);
        try {
            const response = await fetch(`/api/v1/cluster/scale?node_count=${scaleNodeCount}`, {
                method: 'POST'
            });
            if (response.ok) {
                alert('Cluster scaling initiated successfully!');
                onRefresh();
            } else {
                const error = await response.json();
                alert(`Scaling failed: ${error.detail}`);
            }
        } catch (error) {
            alert(`Scaling error: ${error.message}`);
        } finally {
            setScaling(false);
        }
    };

    return (
        <div className="row">
            <div className="col-md-8">
                <div className="card">
                    <div className="card-header">
                        <h5 className="card-title mb-0">
                            <i className="fas fa-server me-2"></i>
                            Cluster Status
                        </h5>
                    </div>
                    <div className="card-body">
                        <div className="row">
                            <div className="col-md-3">
                                <div className="text-center mb-3">
                                    <div className="h3 text-primary">{clusterStatus.node_count || 0}</div>
                                    <small className="text-muted">Nodes</small>
                                </div>
                            </div>
                            <div className="col-md-3">
                                <div className="text-center mb-3">
                                    <div className="h3 text-info">{clusterStatus.active_jobs || 0}</div>
                                    <small className="text-muted">Active Jobs</small>
                                </div>
                            </div>
                            <div className="col-md-3">
                                <div className="text-center mb-3">
                                    <div className="h3 text-warning">{clusterStatus.queue_depth || 0}</div>
                                    <small className="text-muted">Queue Depth</small>
                                </div>
                            </div>
                            <div className="col-md-3">
                                <div className="text-center mb-3">
                                    <div className={`h3 ${clusterStatus.health_status === 'healthy' ? 'text-success' : 'text-danger'}`}>
                                        <i className={`fas ${clusterStatus.health_status === 'healthy' ? 'fa-check-circle' : 'fa-exclamation-triangle'}`}></i>
                                    </div>
                                    <small className="text-muted">Health</small>
                                </div>
                            </div>
                        </div>

                        <hr />

                        <div className="row">
                            <div className="col-md-6">
                                <h6>Cluster Information</h6>
                                <table className="table table-sm">
                                    <tbody>
                                        <tr>
                                            <td><strong>Cluster Name:</strong></td>
                                            <td>{clusterStatus.cluster_name || 'N/A'}</td>
                                        </tr>
                                        <tr>
                                            <td><strong>Status:</strong></td>
                                            <td>
                                                <span className={`badge ${clusterStatus.health_status === 'healthy' ? 'bg-success' : 'bg-warning'}`}>
                                                    {clusterStatus.health_status || 'Unknown'}
                                                </span>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td><strong>Node Count:</strong></td>
                                            <td>{clusterStatus.node_count || 'N/A'}</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                            <div className="col-md-6">
                                <h6>Quick Actions</h6>
                                <button className="btn btn-outline-primary btn-sm me-2" onClick={onRefresh}>
                                    <i className="fas fa-sync-alt me-1"></i>
                                    Refresh Status
                                </button>
                                <a href="/docs" className="btn btn-outline-info btn-sm" target="_blank">
                                    <i className="fas fa-book me-1"></i>
                                    API Docs
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="col-md-4">
                <div className="card">
                    <div className="card-header">
                        <h6 className="card-title mb-0">
                            <i className="fas fa-expand-arrows-alt me-2"></i>
                            Cluster Scaling
                        </h6>
                    </div>
                    <div className="card-body">
                        <div className="mb-3">
                            <label className="form-label">Target Node Count</label>
                            <input
                                type="number"
                                className="form-control"
                                value={scaleNodeCount}
                                onChange={(e) => setScaleNodeCount(parseInt(e.target.value))}
                                min="1"
                                max="50"
                            />
                            <div className="form-text">Scale cluster between 1-50 nodes</div>
                        </div>
                        <button
                            className="btn btn-warning btn-sm w-100"
                            onClick={handleScale}
                            disabled={scaling}
                        >
                            {scaling ? (
                                <>
                                    <span className="spinner-border spinner-border-sm me-2"></span>
                                    Scaling...
                                </>
                            ) : (
                                <>
                                    <i className="fas fa-expand-arrows-alt me-2"></i>
                                    Scale Cluster
                                </>
                            )}
                        </button>
                        <div className="alert alert-warning mt-3 small">
                            <i className="fas fa-exclamation-triangle me-1"></i>
                            <strong>Caution:</strong> Scaling affects costs and may interrupt running jobs.
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

// Render the app
ReactDOM.render(<App />, document.getElementById('app'));
