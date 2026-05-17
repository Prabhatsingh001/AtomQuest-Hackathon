import { useQuery } from '@tanstack/react-query';
import { usersApi } from '@/api/users';

export default function MyTeam() {
    const { data: team = [], isLoading: loading } = useQuery({
        queryKey: ['myTeam'],
        queryFn: () => usersApi.getTeam(),
        staleTime: 1000 * 60 * 2,
    });

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <h1 className="text-lg font-bold text-zinc-900">My Team Roster</h1>

            {loading ? (
                <div className="space-y-3">{[1, 2, 3].map(i => <div key={i} className="bg-zinc-100 rounded-xl h-16 animate-pulse" />)}</div>
            ) : team.length === 0 ? (
                <p className="text-center py-16 text-zinc-400 text-sm">No direct reports found</p>
            ) : (
                <div className="bg-white border border-zinc-200 rounded-xl overflow-x-auto max-w-full">
                    <table className="w-full text-sm min-w-[500px]">
                        <thead>
                            <tr>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-zinc-500 uppercase tracking-wider bg-zinc-50 border-b border-zinc-200">Employee</th>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-zinc-500 uppercase tracking-wider bg-zinc-50 border-b border-zinc-200">Email</th>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-zinc-500 uppercase tracking-wider bg-zinc-50 border-b border-zinc-200">Department</th>
                            </tr>
                        </thead>
                        <tbody>
                            {team.map((user) => (
                                <tr key={user.id} className="border-b border-zinc-100 last:border-b-0 hover:bg-zinc-50/60 transition-colors">
                                    <td className="px-4 py-3.5 font-medium text-zinc-800">{user.full_name}</td>
                                    <td className="px-4 py-3.5 text-zinc-500">{user.email}</td>
                                    <td className="px-4 py-3.5 text-zinc-600">{user.department_name || '-'}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}
