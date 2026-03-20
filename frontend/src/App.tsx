import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { 
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid
} from 'recharts';
import { 
  TrendingUp, TrendingDown, Wallet, Search, Upload, Trash2, 
  ChevronLeft, ChevronRight, Calendar as CalendarIcon
} from 'lucide-react';
import { format, parseISO, isToday, isYesterday, startOfMonth, endOfMonth, isWithinInterval } from 'date-fns';
import { fr } from 'date-fns/locale';
import './App.css';

export interface Transaction {
  id: number;
  date: string;
  label: string;
  debit: number | null;
  credit: number | null;
  family: string;
  category: string;
  subcategory: string;
}

const API_URL = 'http://localhost:8000';
const PAGE_SIZE = 25;
const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'];

function App() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [chartLevel, setChartLevel] = useState<'family' | 'category'>('family');
  const [selectedFamily, setSelectedFamily] = useState<string | null>(null);
  const [selectedMonth, setSelectedMonth] = useState<string | null>(null); // Format: "YYYY-MM"
  const [uploadStatus, setUploadStatus] = useState<{message: string, type: 'success' | 'error' | null}>({message: '', type: null});
  
  const [currentPage, setCurrentPage] = useState(1);

  const fetchData = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/transactions/`);
      const data = response.data;
      setTransactions(data);
      
      // Auto-select most recent month if not set
      if (data.length > 0 && !selectedMonth) {
        const sorted = [...data].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
        const latestDate = parseISO(sorted[0].date);
        setSelectedMonth(format(latestDate, 'yyyy-MM'));
      }
    } catch (error) {
      console.error("Error fetching transactions:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);
  useEffect(() => { setCurrentPage(1); }, [searchTerm, selectedFamily, selectedMonth]);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    try {
      setUploadStatus({message: 'Analyse en cours...', type: null});
      await axios.delete(`${API_URL}/transactions/`);
      await axios.post(`${API_URL}/upload/`, formData);
      setUploadStatus({message: 'Importation réussie !', type: 'success'});
      fetchData();
    } catch (error) {
      setUploadStatus({message: 'Erreur d\'importation.', type: 'error'});
    }
    setTimeout(() => setUploadStatus({message: '', type: null}), 5000);
  };

  const clearData = async () => {
    if (!window.confirm("Tout supprimer ?")) return;
    try {
      await axios.delete(`${API_URL}/transactions/`);
      setTransactions([]);
      setSelectedMonth(null);
    } catch (error) {
      console.error("Error:", error);
    }
  };

  // Extract available months from data
  const availableMonths = useMemo(() => {
    const months = new Set<string>();
    transactions.forEach(t => months.add(format(parseISO(t.date), 'yyyy-MM')));
    return Array.from(months).sort().reverse();
  }, [transactions]);

  const families = useMemo(() => {
    const f = new Set(transactions.map(t => t.family));
    return Array.from(f).sort();
  }, [transactions]);

  // Filter transactions by Month AND Search AND Family
  const allFilteredTransactions = useMemo(() => {
    return transactions.filter(t => {
      const tDate = parseISO(t.date);
      const matchesMonth = !selectedMonth || format(tDate, 'yyyy-MM') === selectedMonth;
      const matchesSearch = t.label.toLowerCase().includes(searchTerm.toLowerCase()) ||
                            t.category.toLowerCase().includes(searchTerm.toLowerCase()) ||
                            t.subcategory.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesFamily = !selectedFamily || t.family === selectedFamily;
      return matchesMonth && matchesSearch && matchesFamily;
    }).sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  }, [transactions, searchTerm, selectedFamily, selectedMonth]);

  // Monthly stats (for the selected month)
  const stats = useMemo(() => {
    const income = allFilteredTransactions.reduce((sum, t) => sum + (t.credit || 0), 0);
    const expenses = allFilteredTransactions.reduce((sum, t) => sum + (t.debit || 0), 0);
    return { income, expenses, balance: income - expenses };
  }, [allFilteredTransactions]);

  // Data for the Donut Chart (filtered by month)
  const donutData = useMemo(() => {
    const dataMap: Record<string, number> = {};
    allFilteredTransactions.forEach(t => {
      if (t.debit) {
        const key = chartLevel === 'family' ? t.family : t.category;
        dataMap[key] = (dataMap[key] || 0) + t.debit;
      }
    });
    return Object.entries(dataMap)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value);
  }, [allFilteredTransactions, chartLevel]);

  // Data for the Historical Bar Chart (all months)
  const trendData = useMemo(() => {
    const trendMap: Record<string, { month: string, revenus: number, depenses: number }> = {};
    transactions.forEach(t => {
      const m = format(parseISO(t.date), 'yyyy-MM');
      if (!trendMap[m]) trendMap[m] = { month: format(parseISO(t.date), 'MMM yy', { locale: fr }), revenus: 0, depenses: 0 };
      if (t.credit) trendMap[m].revenus += t.credit;
      if (t.debit) trendMap[m].depenses += t.debit;
    });
    return Object.values(trendMap).sort((a, b) => {
      // Re-parse for sorting
      return 0; // Simplified for this view, availableMonths is already sorted
    }).reverse().slice(0, 6).reverse(); // Last 6 months
  }, [transactions]);

  const paginatedTransactions = useMemo(() => {
    const start = (currentPage - 1) * PAGE_SIZE;
    return allFilteredTransactions.slice(start, start + PAGE_SIZE);
  }, [allFilteredTransactions, currentPage]);

  const totalPages = Math.ceil(allFilteredTransactions.length / PAGE_SIZE);

  const formatDate = (dateStr: string) => {
    const d = parseISO(dateStr);
    if (isToday(d)) return "Aujourd'hui";
    if (isYesterday(d)) return "Hier";
    return format(d, 'dd MMM yyyy', { locale: fr });
  };

  if (loading && transactions.length === 0) {
    return <div className="loading-container"><div className="loader"></div>Chargement de MonArgent...</div>;
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="logo"><Wallet size={32} color="#6366f1" /><h1>MonArgent</h1></div>
        <div className="header-actions">
          <div className="search-bar"><Search size={18} color="#64748b" /><input type="text" placeholder="Rechercher..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)}/></div>
          <label className="upload-btn"><Upload size={18} />Importer<input type="file" hidden onChange={handleFileUpload} accept=".xlsx,.xls" /></label>
          <button className="clear-btn" onClick={clearData} title="Supprimer tout"><Trash2 size={18} /></button>
        </div>
      </header>

      {uploadStatus.message && <div className={`toast ${uploadStatus.type || 'info'}`}>{uploadStatus.message}</div>}

      <main className="dashboard">
        {/* Month Selector Bar */}
        <div className="month-selector">
          <CalendarIcon size={20} color="#6366f1" />
          <div className="month-chips">
            <button className={`chip ${!selectedMonth ? 'active' : ''}`} onClick={() => setSelectedMonth(null)}>Tout l'historique</button>
            {availableMonths.map(m => (
              <button 
                key={m} 
                className={`chip ${selectedMonth === m ? 'active' : ''}`} 
                onClick={() => setSelectedMonth(m)}
              >
                {format(parseISO(`${m}-01`), 'MMMM yyyy', { locale: fr })}
              </button>
            ))}
          </div>
        </div>

        <section className="stats-grid">
          <div className="stat-card balance">
            <div className="stat-label">Solde {selectedMonth ? "du mois" : "Total"}</div>
            <div className="stat-value">{stats.balance.toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })}</div>
            <Wallet className="stat-icon" />
          </div>
          <div className="stat-card income">
            <div className="stat-label">Revenus {selectedMonth ? "du mois" : ""}</div>
            <div className="stat-value">+{stats.income.toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })}</div>
            <TrendingUp className="stat-icon" />
          </div>
          <div className="stat-card expenses">
            <div className="stat-label">Dépenses {selectedMonth ? "du mois" : ""}</div>
            <div className="stat-value">-{stats.expenses.toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })}</div>
            <TrendingDown className="stat-icon" />
          </div>
        </section>

        <div className="main-layout">
          <aside className="sidebar">
            {/* Donut Chart */}
            <div className="chart-card">
              <div className="chart-header">
                <h3>Répartition {selectedMonth ? "mensuelle" : ""}</h3>
                <div className="toggle-group">
                  <button className={chartLevel === 'family' ? 'active' : ''} onClick={() => setChartLevel('family')}>Familles</button>
                  <button className={chartLevel === 'category' ? 'active' : ''} onClick={() => setChartLevel('category')}>Cats</button>
                </div>
              </div>
              <div className="chart-container">
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie data={donutData} cx="50%" cy="50%" innerRadius={60} outerRadius={85} paddingAngle={5} dataKey="value">
                      {donutData.map((_, index) => <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />)}
                    </Pie>
                    <Tooltip formatter={(v: number) => v.toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })} />
                    <Legend verticalAlign="bottom" />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Historical Trend Chart */}
            <div className="chart-card trend-card">
              <h3>Tendance (6 derniers mois)</h3>
              <div className="chart-container">
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={trendData}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="month" fontSize={10} />
                    <YAxis fontSize={10} hide />
                    <Tooltip />
                    <Bar dataKey="revenus" fill="#10b981" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="depenses" fill="#ef4444" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </aside>

          <div className="content-area">
            <div className="filter-chips">
              <button className={`chip ${!selectedFamily ? 'active' : ''}`} onClick={() => setSelectedFamily(null)}>Toutes catégories</button>
              {families.map(f => <button key={f} className={`chip ${selectedFamily === f ? 'active' : ''}`} onClick={() => setSelectedFamily(f)}>{f}</button>)}
            </div>

            <section className="transactions-section">
              <div className="table-header">
                <h3>{selectedMonth ? `Opérations de ${format(parseISO(`${selectedMonth}-01`), 'MMMM yyyy', { locale: fr })}` : "Toutes les opérations"}</h3>
                <span className="count">{allFilteredTransactions.length} transactions</span>
              </div>
              <div className="table-container">
                <table>
                  <thead><tr><th>Date</th><th>Catégorisation</th><th>Libellé</th><th className="amount-col">Montant</th></tr></thead>
                  <tbody>
                    {paginatedTransactions.map(t => (
                      <tr key={t.id}>
                        <td className="date-cell">{formatDate(t.date)}</td>
                        <td className="category-cell">
                          <span className={`tag family ${t.family.toLowerCase().replace(/[^a-z0-9]/g, '-')}`}>{t.family}</span>
                          <span className="subcategory">{t.category}</span>
                        </td>
                        <td className="label-cell" title={t.label}>{t.label}</td>
                        <td className={`amount-col ${t.debit ? 'debit' : 'credit'}`}>{t.debit ? `-${t.debit.toFixed(2)} €` : `+${t.credit?.toFixed(2)} €`}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {totalPages > 1 && (
                <div className="pagination">
                  <button disabled={currentPage === 1} onClick={() => setCurrentPage(p => p - 1)} className="page-btn"><ChevronLeft size={18} /> Précédent</button>
                  <span className="page-info">Page {currentPage} / {totalPages}</span>
                  <button disabled={currentPage === totalPages} onClick={() => setCurrentPage(p => p + 1)} className="page-btn">Suivant <ChevronRight size={18} /></button>
                </div>
              )}
            </section>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
