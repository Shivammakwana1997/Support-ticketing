import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen bg-neutral-50 flex flex-col items-center justify-center p-8">
      <div className="max-w-2xl text-center">
        <h1 className="text-4xl font-bold tracking-tight text-neutral-900 mb-6">
          Banking AI Copilot Demo
        </h1>
        <p className="text-lg text-neutral-600 mb-8">
          Welcome to the Banking AI Copilot demo. Choose your role below to experience the ticketing system.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Link href="/customer/chat" className="block p-8 bg-white border border-neutral-200 rounded-xl hover:shadow-lg transition-all text-left group">
            <h2 className="text-xl font-semibold text-neutral-900 mb-2 group-hover:text-primary-600 transition-colors">
              Customer View
            </h2>
            <p className="text-neutral-500 mb-4">
              Experience the AI chatbot interface. Report a stolen card or an OTP issue to see automatic ticket creation and routing.
            </p>
            <span className="inline-flex items-center text-primary-600 font-medium">
              Start Chat &rarr;
            </span>
          </Link>

          <Link href="/agent/dashboard" className="block p-8 bg-white border border-neutral-200 rounded-xl hover:shadow-lg transition-all text-left group">
            <h2 className="text-xl font-semibold text-neutral-900 mb-2 group-hover:text-amber-600 transition-colors">
              Agent/Admin View
            </h2>
            <p className="text-neutral-500 mb-4">
              Access the support dashboard to view tickets automatically categorized and prioritized by the AI.
            </p>
            <span className="inline-flex items-center text-amber-600 font-medium">
              Open Dashboard &rarr;
            </span>
          </Link>
        </div>
      </div>
    </div>
  );
}
