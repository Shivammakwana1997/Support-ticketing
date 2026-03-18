'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

export default function AgentDashboard() {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTickets = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/v1/tickets/demo-list');
        const data = await res.json();
        setTickets(data);
      } catch (error) {
        console.error('Failed to fetch tickets:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTickets();
  }, []);

  return (
    <div className="min-h-screen bg-neutral-100 flex flex-col">
      <header className="bg-amber-700 text-white p-4 flex justify-between items-center shadow-md">
        <h1 className="font-semibold text-lg">Agent Support Dashboard</h1>
        <div className="flex gap-4">
          <span className="text-amber-200 text-sm">Role: Administrator</span>
          <Link href="/" className="text-amber-200 hover:text-white text-sm">Back to Home</Link>
        </div>
      </header>

      <main className="flex-1 max-w-5xl w-full mx-auto p-4 flex flex-col bg-white my-4 rounded-xl shadow-sm border border-neutral-200">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold text-neutral-800">Recent Customer Tickets</h2>
          <button onClick={() => window.location.reload()} className="text-sm bg-neutral-200 hover:bg-neutral-300 px-3 py-1 rounded">Refresh</button>
        </div>

        {loading ? (
          <div className="text-center p-8 text-neutral-500 animate-pulse">Loading active tickets...</div>
        ) : tickets.length === 0 ? (
          <div className="text-center p-8 text-neutral-500 bg-neutral-50 rounded-lg border border-neutral-100">
            No active tickets. Waiting for customer inquiries...
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-neutral-50 border-b border-neutral-200">
                  <th className="p-3 text-sm font-semibold text-neutral-600">Ticket #</th>
                  <th className="p-3 text-sm font-semibold text-neutral-600">Customer Subject</th>
                  <th className="p-3 text-sm font-semibold text-neutral-600">Category</th>
                  <th className="p-3 text-sm font-semibold text-neutral-600">Priority</th>
                  <th className="p-3 text-sm font-semibold text-neutral-600">Status</th>
                </tr>
              </thead>
              <tbody>
                {tickets.map(t => (
                  <tr key={t.id} className="border-b border-neutral-100 hover:bg-neutral-50 transition-colors">
                    <td className="p-3 text-sm font-mono text-neutral-500">{t.ticket_number}</td>
                    <td className="p-3 text-sm font-medium text-neutral-800">{t.subject}</td>
                    <td className="p-3">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium uppercase ${
                        t.category === 'fraud' ? 'bg-red-100 text-red-800' :
                        t.category === 'otp_issue' ? 'bg-orange-100 text-orange-800' :
                        t.category === 'password_reset' ? 'bg-blue-100 text-blue-800' :
                        'bg-neutral-100 text-neutral-800'
                      }`}>
                        {t.category.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="p-3">
                      <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-bold uppercase ${
                        t.priority === 'urgent' ? 'bg-red-600 text-white' :
                        t.priority === 'high' ? 'bg-orange-500 text-white' :
                        t.priority === 'medium' ? 'bg-blue-500 text-white' :
                        'bg-neutral-500 text-white'
                      }`}>
                        {t.priority}
                      </span>
                    </td>
                    <td className="p-3">
                      <span className="text-sm text-green-600 font-medium">Open</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}
