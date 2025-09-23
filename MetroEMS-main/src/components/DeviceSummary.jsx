import React from 'react';

const DeviceSummary = ({ device }) => {
  const d = device || {};
  const name = d.name || d.systemName || 'Station Radio';
  const type = d.type || d.device_type || 'Station Radio';
  const status = d.status || (d.connection_verified ? 'Online' : 'Unknown');
  const ip = d.ip || d.ipAddress || d.ip_address || 'N/A';
  const location = d.location || 'N/A';
  const lastChecked = d.last_verified || d.lastChecked || new Date().toLocaleString();
  const description = d.description || 'Station Radio device managed by MetroEMS.';

  return (
    <div className="bg-white/10 backdrop-blur-md rounded-xl shadow-lg p-6 mt-8 max-w-md mx-auto">
      <h2 className="text-2xl font-bold text-white mb-4">Device Summary</h2>
      <div className="text-blue-100 mb-2"><strong>Name:</strong> {name}</div>
      <div className="text-blue-100 mb-2"><strong>Type:</strong> {type}</div>
      <div className="text-blue-100 mb-2"><strong>Status:</strong> {status}</div>
      <div className="text-blue-100 mb-2"><strong>IP Address:</strong> {ip}</div>
      <div className="text-blue-100 mb-2"><strong>Location:</strong> {location}</div>
      <div className="text-blue-100 mb-2"><strong>Last Checked:</strong> {lastChecked}</div>
      <div className="text-blue-100 mb-2"><strong>Description:</strong> {description}</div>
    </div>
  );
};

export default DeviceSummary;
