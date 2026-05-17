import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import toast from 'react-hot-toast';

const DEMOS = [
  { label: 'Admin', email: 'admin@atomquest.com', password: 'password' },
  { label: 'Manager', email: 'manager@atomquest.com', password: 'password' },
  { label: 'Employee', email: 'employee@atomquest.com', password: 'password' },
];

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
    } catch (err: any) {
      toast.error(err.response?.data?.message || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  const handleDemo = async (d: typeof DEMOS[0]) => {
    setEmail(d.email);
    setPassword(d.password);
    setLoading(true);
    try {
      await login(d.email, d.password);
    } catch {
      toast.error('Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-zinc-50">
      <div className="w-full max-w-sm px-4">
        <div className="mb-10">
          <h1 className="text-2xl font-bold text-zinc-900 tracking-tight">AtomQuest</h1>
          <p className="text-sm text-zinc-400 mt-1">Sign in to the Goal Portal</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-1.5">Email</label>
            <input
              id="email-input"
              type="email"
              className="w-full px-3.5 py-2.5 bg-white border border-zinc-200 rounded-lg text-sm text-zinc-900 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-900/10 focus:border-zinc-400 transition-all"
              placeholder="you@atomquest.com"
              value={email} onChange={(e) => setEmail(e.target.value)} required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-1.5">Password</label>
            <input
              id="password-input"
              type="password"
              className="w-full px-3.5 py-2.5 bg-white border border-zinc-200 rounded-lg text-sm text-zinc-900 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-900/10 focus:border-zinc-400 transition-all"
              placeholder="Enter password"
              value={password} onChange={(e) => setPassword(e.target.value)} required
            />
          </div>
          <button
            id="login-button"
            type="submit"
            disabled={loading}
            className="w-full py-2.5 text-sm font-medium text-white bg-zinc-900 rounded-lg hover:bg-zinc-800 transition-colors disabled:opacity-40 disabled:pointer-events-none"
          >
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>

        <div className="mt-8 pt-6 border-t border-zinc-200">
          <p className="text-xs text-zinc-400 mb-3 font-medium">Quick access</p>
          <div className="flex flex-wrap gap-2">
            {DEMOS.map((d) => (
              <button key={d.label} onClick={() => handleDemo(d)} disabled={loading}
                className="flex-1 min-w-[100px] py-2.5 px-2 text-xs font-medium text-zinc-600 bg-white border border-zinc-200 rounded-lg hover:bg-zinc-50 hover:border-zinc-300 transition-colors disabled:opacity-50 text-center">
                {d.label}
              </button>
            ))}
          </div>
        </div>

        <p className="text-center text-sm text-zinc-400 mt-6">
          Don't have an account?{' '}
          <Link to="/register" className="text-zinc-900 font-medium hover:underline">Create one</Link>
        </p>
      </div>
    </div>
  );
}
