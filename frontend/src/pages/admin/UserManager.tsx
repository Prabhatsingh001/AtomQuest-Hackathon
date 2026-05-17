import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { adminApi } from '@/api/admin';
import { approvalsApi } from '@/api/approvals';
import type { User, Cycle } from '@/types';
import { Plus, Edit2, Unlock, ShieldAlert } from 'lucide-react';
import toast from 'react-hot-toast';
import { RoleBadge } from '@/components/shared/RoleBadge';

const inputCls = "w-full px-3 py-2 bg-white border border-zinc-200 rounded-lg text-sm text-zinc-900 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-900/10 focus:border-zinc-400 transition-all";

export default function UserManager() {
    const queryClient = useQueryClient();
    const [editing, setEditing] = useState<User | null>(null);
    const [isNew, setIsNew] = useState(false);
    const [unlockingId, setUnlockingId] = useState<string | null>(null);
    const [deptName, setDeptName] = useState('');
    const [savingDept, setSavingDept] = useState(false);

    const [form, setForm] = useState({
        email: '', full_name: '', password: '', role: 'employee', department_id: '', manager_id: '', is_active: true
    });

    const { data: users = [], isLoading: loadingUsers } = useQuery({
        queryKey: ['users'],
        queryFn: () => adminApi.getUsers(),
        staleTime: 1000 * 60 * 2,
    });

    const { data: departments = [], isLoading: loadingDepts } = useQuery({
        queryKey: ['departments'],
        queryFn: () => adminApi.getDepartments(),
        staleTime: 1000 * 60 * 2,
    });

    const { data: cycles = [] } = useQuery({
        queryKey: ['cycles'],
        queryFn: () => adminApi.getCycles().catch(() => []),
        staleTime: 1000 * 60 * 2,
    });

    const activeCycle = cycles.find((c: Cycle) => c.is_active) || null;
    const loading = loadingUsers || loadingDepts;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            if (isNew) {
                await adminApi.createUser({
                    ...form,
                    department_id: form.department_id || undefined,
                    manager_id: form.manager_id || undefined,
                });
                toast.success('User created');
            } else if (editing) {
                await adminApi.updateUser(editing.id, {
                    full_name: form.full_name,
                    role: form.role as any,
                    department_id: form.department_id || undefined,
                    manager_id: form.manager_id || undefined,
                    is_active: form.is_active,
                });
                toast.success('User updated');
            }
            setEditing(null);
            setIsNew(false);
            queryClient.invalidateQueries({ queryKey: ['users'] });
        } catch (err: any) {
            toast.error(err.response?.data?.detail || 'Operation failed');
        }
    };

    const openEdit = (u: User) => {
        setForm({
            email: u.email, full_name: u.full_name, role: u.role, password: '',
            department_id: u.department_id || '', manager_id: u.manager_id || '', is_active: u.is_active
        });
        setEditing(u);
        setIsNew(false);
    };

    const openNew = () => {
        setForm({ email: '', full_name: '', password: '', role: 'employee', department_id: '', manager_id: '', is_active: true });
        setIsNew(true);
        setEditing(null);
    };

    const createDepartment = async () => {
        if (!deptName.trim()) return;
        setSavingDept(true);
        try {
            await adminApi.createDepartment(deptName.trim());
            setDeptName('');
            queryClient.invalidateQueries({ queryKey: ['departments'] });
            toast.success('Department created');
        } catch (err: any) {
            toast.error(err.response?.data?.detail || 'Failed to create department');
        } finally {
            setSavingDept(false);
        }
    };

    const deactivateDepartment = async (deptId: string) => {
        setSavingDept(true);
        try {
            await adminApi.deactivateDepartment(deptId);
            queryClient.invalidateQueries({ queryKey: ['departments'] });
            toast.success('Department deactivated');
        } catch (err: any) {
            toast.error(err.response?.data?.detail || 'Failed to deactivate department');
        } finally {
            setSavingDept(false);
        }
    };

    const handleUnlock = async (userId: string) => {
        if (!activeCycle) {
            toast.error('No active cycle found');
            return;
        }
        setUnlockingId(userId);
        try {
            const sheet = await adminApi.getUserSheet(userId, activeCycle.id);
            await approvalsApi.unlock(sheet.id, "Admin manual override");
            toast.success('Goal sheet unlocked and returned to draft');
        } catch (err: any) {
            if (err.response?.status === 404) {
                toast.error('User has no goal sheet for the active cycle');
            } else {
                toast.error(err.response?.data?.message || 'Failed to unlock sheet');
            }
        } finally {
            setUnlockingId(null);
        }
    };

    return (
        <div className="max-w-5xl mx-auto space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-lg font-bold text-zinc-900">User Management</h1>
                <button onClick={openNew}
                    className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-white bg-zinc-900 rounded-lg hover:bg-zinc-800 transition-colors">
                    <Plus className="w-4 h-4" /> Add User
                </button>
            </div>

            <div className="flex flex-col lg:flex-row gap-6">
                {/* Table */}
                <div className="flex-1 min-w-0 bg-white border border-zinc-200 rounded-xl overflow-x-auto max-w-full shadow-sm">
                    <table className="w-full text-sm text-left min-w-[500px]">
                        <thead>
                            <tr>
                                <th className="px-4 py-3 font-semibold text-zinc-500 uppercase tracking-wider bg-zinc-50 border-b border-zinc-200 text-xs">Name</th>
                                <th className="px-4 py-3 font-semibold text-zinc-500 uppercase tracking-wider bg-zinc-50 border-b border-zinc-200 text-xs">Email</th>
                                <th className="px-4 py-3 font-semibold text-zinc-500 uppercase tracking-wider bg-zinc-50 border-b border-zinc-200 text-xs">Role</th>
                                <th className="px-4 py-3 font-semibold text-zinc-500 uppercase tracking-wider bg-zinc-50 border-b border-zinc-200 text-xs">Dept</th>
                                <th className="px-4 py-3 font-semibold text-zinc-500 uppercase tracking-wider bg-zinc-50 border-b border-zinc-200 text-xs w-10"></th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? <tr><td colSpan={5} className="p-8 text-center text-zinc-400">Loading...</td></tr> :
                                users.map(u => (
                                    <tr key={u.id} className={`border-b border-zinc-100 last:border-b-0 transition-colors ${!u.is_active ? 'bg-zinc-50 opacity-60' : 'hover:bg-zinc-50'}`}>
                                        <td className="px-4 py-3 font-medium text-zinc-800">
                                            {u.full_name}
                                            {!u.is_active && <span className="ml-2 text-[10px] uppercase font-bold text-red-500">Deactivated</span>}
                                        </td>
                                        <td className="px-4 py-3 text-zinc-500">{u.email}</td>
                                        <td className="px-4 py-3"><RoleBadge role={u.role} /></td>
                                        <td className="px-4 py-3 text-zinc-600">{u.department_name || '-'}</td>
                                        <td className="px-4 py-3 text-right">
                                            <div className="flex items-center justify-end gap-1">
                                                <button title="Unlock User's Active Goal Sheet" onClick={() => handleUnlock(u.id)} disabled={unlockingId === u.id} className="p-1.5 text-amber-500 hover:text-amber-700 hover:bg-amber-50 rounded-md transition-colors disabled:opacity-50">
                                                    {unlockingId === u.id ? <ShieldAlert className="w-3.5 h-3.5 animate-pulse" /> : <Unlock className="w-3.5 h-3.5" />}
                                                </button>
                                                <button title="Edit User" onClick={() => openEdit(u)} className="p-1.5 text-zinc-400 hover:text-zinc-700 hover:bg-zinc-200 rounded-md transition-colors">
                                                    <Edit2 className="w-3.5 h-3.5" />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                        </tbody>
                    </table>
                </div>

                {/* Form Panel */}
                {(isNew || editing) && (
                    <div className="w-full lg:w-80 shrink-0 bg-white border border-zinc-200 rounded-xl p-5 self-start sticky top-20 shadow-sm">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="font-semibold text-zinc-900">{isNew ? 'New User' : 'Edit User'}</h2>
                            <button onClick={() => { setIsNew(false); setEditing(null); }} className="text-zinc-400 hover:text-zinc-600 text-sm">Cancel</button>
                        </div>

                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="block text-xs font-medium text-zinc-700 mb-1">Full Name</label>
                                <input required className={inputCls} value={form.full_name} onChange={e => setForm({ ...form, full_name: e.target.value })} />
                            </div>
                            <div>
                                <label className="block text-xs font-medium text-zinc-700 mb-1">Email {editing && "(Cannot edit)"}</label>
                                <input required type="email" disabled={!!editing} className={`${inputCls} disabled:bg-zinc-50 disabled:text-zinc-400`} value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} />
                            </div>
                            {isNew && (
                                <div>
                                    <label className="block text-xs font-medium text-zinc-700 mb-1">Password</label>
                                    <input required minLength={6} type="password" className={inputCls} value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} />
                                </div>
                            )}
                            <div>
                                <label className="block text-xs font-medium text-zinc-700 mb-1">Role</label>
                                <select className={inputCls} value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}>
                                    <option value="employee">Employee</option>
                                    <option value="manager">Manager</option>
                                    <option value="admin">Admin</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-xs font-medium text-zinc-700 mb-1">Department</label>
                                <select className={inputCls} value={form.department_id} onChange={e => setForm({ ...form, department_id: e.target.value })}>
                                    <option value="">No department</option>
                                    {departments.filter(d => d.is_active).map(d => (
                                        <option key={d.id} value={d.id}>{d.name}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-xs font-medium text-zinc-700 mb-1">Manager</label>
                                <select className={inputCls} value={form.manager_id} onChange={e => setForm({ ...form, manager_id: e.target.value })}>
                                    <option value="">No manager</option>
                                    {users.filter(u => u.role === 'manager' || u.role === 'admin').map(u => (
                                        <option key={u.id} value={u.id}>{u.full_name}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="flex items-center gap-2 pt-2 pb-1">
                                <input type="checkbox" id="active-user-check" checked={form.is_active} onChange={e => setForm({ ...form, is_active: e.target.checked })} className="rounded border-zinc-300 text-zinc-900 focus:ring-zinc-900" />
                                <label htmlFor="active-user-check" className="text-sm text-zinc-700">Account is active</label>
                            </div>
                            <button type="submit" className="w-full py-2 text-sm font-medium text-white bg-zinc-900 rounded-lg hover:bg-zinc-800 transition-colors mt-2">
                                {isNew ? 'Create' : 'Save Changes'}
                            </button>
                        </form>
                    </div>
                )}
            </div>

            <div className="bg-white border border-zinc-200 rounded-xl p-5">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="font-semibold text-zinc-900">Departments</h2>
                </div>
                <div className="flex gap-2 mb-4">
                    <input
                        className={inputCls}
                        placeholder="New department name"
                        value={deptName}
                        onChange={(e) => setDeptName(e.target.value)}
                    />
                    <button
                        type="button"
                        onClick={createDepartment}
                        disabled={savingDept || !deptName.trim()}
                        className="px-3 py-2 text-sm font-medium text-white bg-zinc-900 rounded-lg hover:bg-zinc-800 transition-colors disabled:opacity-50"
                    >
                        Add
                    </button>
                </div>
                <div className="space-y-2">
                    {departments.map((dept) => (
                        <div key={dept.id} className="flex items-center justify-between rounded-lg border border-zinc-100 px-3 py-2">
                            <div className="min-w-0">
                                <p className="text-sm font-medium text-zinc-900 truncate">{dept.name}</p>
                                <p className="text-xs text-zinc-400">{dept.employee_count || 0} employees</p>
                            </div>
                            <button
                                type="button"
                                onClick={() => deactivateDepartment(dept.id)}
                                disabled={!dept.is_active || (dept.employee_count || 0) > 0 || savingDept}
                                className="px-2.5 py-1.5 text-xs font-medium rounded-md border border-zinc-200 text-zinc-600 hover:bg-zinc-50 disabled:opacity-40"
                            >
                                {dept.is_active ? 'Deactivate' : 'Inactive'}
                            </button>
                        </div>
                    ))}
                    {departments.length === 0 && <p className="text-sm text-zinc-400">No departments yet.</p>}
                </div>
            </div>
        </div>
    );
}
