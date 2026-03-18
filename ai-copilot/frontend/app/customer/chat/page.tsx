'use client';

import { useState } from 'react';
import Link from 'next/link';

export default function CustomerChat() {
  const [messages, setMessages] = useState([
    { id: '1', type: 'ai', text: 'Hello! I am your Banking AI Copilot. How can I help you today? You can ask me about stolen cards, OTP issues, or password resets.' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [ticketCreated, setTicketCreated] = useState(false);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { id: Date.now().toString(), type: 'user', text: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      // Call the FastAPI backend to create a ticket based on the message
      const res = await fetch('http://localhost:8000/api/v1/tickets/demo-create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage.text })
      });

      const data = await res.json();

      if (res.ok) {
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          type: 'ai',
          text: `I understand. I have automatically created a ticket for this issue. Ticket #${data.ticket_number} has been assigned to the ${data.category} queue with ${data.priority} priority. An agent will be with you shortly.`
        }]);
        setTicketCreated(true);
      } else {
        throw new Error(data.detail || 'Failed to create ticket');
      }
    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        type: 'ai',
        text: 'Sorry, I encountered an error while processing your request. Please try again later.'
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-neutral-100 flex flex-col">
      <header className="bg-blue-900 text-white p-4 flex justify-between items-center shadow-md">
        <h1 className="font-semibold text-lg">Secure Bank Support</h1>
        <Link href="/" className="text-blue-200 hover:text-white text-sm">Back to Home</Link>
      </header>

      <main className="flex-1 max-w-3xl w-full mx-auto p-4 flex flex-col bg-white my-4 rounded-xl shadow-sm border border-neutral-200">
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map(msg => (
            <div key={msg.id} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] rounded-2xl p-4 ${msg.type === 'user' ? 'bg-blue-600 text-white rounded-br-none' : 'bg-neutral-100 text-neutral-800 rounded-bl-none'}`}>
                {msg.text}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-neutral-100 text-neutral-500 rounded-2xl p-4 rounded-bl-none animate-pulse">
                AI is typing...
              </div>
            </div>
          )}
        </div>

        <form onSubmit={handleSend} className="p-4 border-t border-neutral-100 flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message here..."
            className="flex-1 p-3 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading || ticketCreated}
          />
          <button
            type="submit"
            disabled={loading || ticketCreated || !input.trim()}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            Send
          </button>
        </form>
      </main>
    </div>
  );
}
