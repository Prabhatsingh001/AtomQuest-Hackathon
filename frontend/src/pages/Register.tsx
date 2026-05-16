import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authApi } from '@/api/auth';
import { departmentsApi } from '@/api/departments';
import { useAuthStore } from '@/store/authStore';
import toast from 'react-hot-toast';
import type { Department } from '@/types';

export default function Register() {
  const [form, setForm] = useState({ email: '', full_name: '', password: '', confirmPassword: '', department_id: '' });
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const navigate = useNavigate();

  useEffect(() => {
    departmentsApi
      .listActive()
      .then(setDepartments)
      .catch(() => setDepartments([]));
  }, []);

  const validate = () => {
    const errs: Record<string, string> = {};
    if (!form.email) errs.email = 'Email is required';
    if (!form.full_name) errs.full_name = 'Name is required';
    if (form.password.length < 6) errs.password = 'Minimum 6 characters';
    if (form.password !== form.confirmPassword) errs.confirmPassword = 'Passwords do not match';
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    try {
      await authApi.register({
        email: form.email,
        full_name: form.full_name,
        password: form.password,
        department_id: form.department_id || undefined,
      });

      toast.success('Account created. Please wait for an admin to activate it before signing in.', { duration: 6000 });
      navigate('/login');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Registration failed';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const set = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm({ ...form, [field]: e.target.value });

  const inputCls = "w-full px-3.5 py-2.5 bg-white border border-zinc-200 rounded-lg text-sm text-zinc-900 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-900/10 focus:border-zinc-400 transition-all";

  return (
    <div className="min-h-screen flex items-center justify-center bg-zinc-50">
      <div className="w-full max-w-sm px-4">
        <div className="mb-10">
          <h1 className="text-2xl font-bold text-zinc-900 tracking-tight">Create account</h1>
          <p className="text-sm text-zinc-400 mt-1">
            Join the AtomQuest Goal Portal
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-1.5">Full Name</label>
            <input id="register-name" className={inputCls} placeholder="John Doe"
              value={form.full_name} onChange={set('full_name')} required />
            {errors.full_name && <p className="text-red-600 text-xs mt-1">{errors.full_name}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-1.5">Email</label>
            <input id="register-email" type="email" className={inputCls} placeholder="you@company.com"
              value={form.email} onChange={set('email')} required />
            {errors.email && <p className="text-red-600 text-xs mt-1">{errors.email}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-1.5">Department <span className="text-zinc-400 font-normal">(optional)</span></label>
            <select
              id="register-dept"
              className={inputCls}
              value={form.department_id}
              onChange={(e) => setForm({ ...form, department_id: e.target.value })}
            >
              <option value="">No department</option>
              {departments.map((dept) => (
                <option key={dept.id} value={dept.id}>{dept.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-1.5">Password</label>
            <input id="register-password" type="password" className={inputCls} placeholder="Min 6 characters"
              value={form.password} onChange={set('password')} required />
            {errors.password && <p className="text-red-600 text-xs mt-1">{errors.password}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-1.5">Confirm Password</label>
            <input id="register-confirm" type="password" className={inputCls} placeholder="Re-enter password"
              value={form.confirmPassword} onChange={set('confirmPassword')} required />
            {errors.confirmPassword && <p className="text-red-600 text-xs mt-1">{errors.confirmPassword}</p>}
          </div>

          <button
            id="register-button"
            type="submit"
            disabled={loading}
            className="w-full py-2.5 text-sm font-medium text-white bg-zinc-900 rounded-lg hover:bg-zinc-800 transition-colors disabled:opacity-40 disabled:pointer-events-none mt-2"
          >
            {loading ? 'Creating account...' : 'Create account'}
          </button>
        </form>

        <p className="text-center text-sm text-zinc-400 mt-6">
          Already have an account?{' '}
          <Link to="/login" className="text-zinc-900 font-medium hover:underline">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
