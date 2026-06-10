'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { clearToken, getMyTeam, Player } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';

export default function TeamPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  const [teamName, setTeamName] = useState('');
  const [players, setPlayers] = useState<Player[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isAuthenticated === false) return;

    if (isAuthenticated) {
      getMyTeam()
        .then((data) => {
          setTeamName(data.teamName);
          setPlayers(data.players);
        })
        .catch(() => {
          setError('Erro ao carregar o time. Tente fazer login novamente.');
        })
        .finally(() => setLoading(false));
    }
  }, [isAuthenticated]);

  function handleLogout() {
    clearToken();
    router.replace('/login');
  }

  if (isAuthenticated === null || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="text-center">
          <p className="text-red-400 mb-4">{error}</p>
          <button
            onClick={handleLogout}
            className="px-4 py-2 bg-accent text-surface font-semibold rounded-lg"
          >
            Voltar ao login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-700/50 bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">⚽</span>
            <div>
              <h1 className="text-xl font-bold text-white">{teamName}</h1>
              <p className="text-slate-400 text-sm">{players.length} jogadores</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white border border-slate-600 hover:border-slate-500 rounded-lg transition-colors"
          >
            Sair
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8">
        <div className="bg-card border border-slate-700/50 rounded-xl overflow-hidden shadow-2xl">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700/50 bg-surface/50">
                  <th className="px-4 py-3 text-left text-slate-400 font-medium w-16">#</th>
                  <th className="px-4 py-3 text-left text-slate-400 font-medium">Nome</th>
                  <th className="px-4 py-3 text-left text-slate-400 font-medium w-20">Pos.</th>
                  <th className="px-4 py-3 text-left text-slate-400 font-medium w-16">Idade</th>
                  <th className="px-4 py-3 text-left text-slate-400 font-medium">Nacionalidade</th>
                  <th className="px-4 py-3 text-right text-slate-400 font-medium w-20">OVR</th>
                </tr>
              </thead>
              <tbody>
                {players.map((player, index) => (
                  <tr
                    key={player.id}
                    className={`border-b border-slate-700/30 ${
                      index % 2 === 0 ? 'bg-transparent' : 'bg-surface/30'
                    } hover:bg-accent/5 transition-colors`}
                  >
                    <td className="px-4 py-3 font-mono text-accent font-semibold">
                      {player.shirtNumber}
                    </td>
                    <td className="px-4 py-3 font-medium text-white">
                      {player.name}
                    </td>
                    <td className="px-4 py-3">
                      <span className="inline-block px-2 py-0.5 bg-slate-700 text-slate-300 rounded text-xs font-medium">
                        {player.position}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-300">{player.age}</td>
                    <td className="px-4 py-3 text-slate-300">{player.nationality}</td>
                    <td className="px-4 py-3 text-right">
                      <span
                        className={`font-bold ${
                          player.overall >= 80
                            ? 'text-accent'
                            : player.overall >= 70
                              ? 'text-yellow-400'
                              : 'text-slate-400'
                        }`}
                      >
                        {player.overall}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}
