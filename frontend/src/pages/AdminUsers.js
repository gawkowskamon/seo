import React, { useState, useEffect } from 'react';
import { Users, Plus, Shield, ShieldOff, UserX, Loader2, Mail, Lock, User, X, Check, AlertCircle } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Switch } from '../components/ui/switch';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { toast } from 'sonner';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const AdminUsers = () => {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [creating, setCreating] = useState(false);
  const [updatingUser, setUpdatingUser] = useState(null);

  // Create form
  const [newEmail, setNewEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newFullName, setNewFullName] = useState('');
  const [newIsAdmin, setNewIsAdmin] = useState(false);

  const fetchUsers = async () => {
    try {
      const res = await axios.get(`${BACKEND_URL}/api/admin/users`);
      setUsers(res.data);
    } catch (err) {
      toast.error('Blad ladowania uzytkownikow');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleCreate = async () => {
    if (!newEmail || !newPassword) {
      toast.error('Wypelnij email i haslo');
      return;
    }
    setCreating(true);
    try {
      await axios.post(`${BACKEND_URL}/api/admin/users`, {
        email: newEmail,
        password: newPassword,
        full_name: newFullName,
        is_admin: newIsAdmin
      });
      toast.success('Uzytkownik utworzony');
      setShowCreateDialog(false);
      setNewEmail('');
      setNewPassword('');
      setNewFullName('');
      setNewIsAdmin(false);
      fetchUsers();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Blad tworzenia uzytkownika';
      toast.error(msg);
    } finally {
      setCreating(false);
    }
  };

  const handleToggleAdmin = async (userId, currentIsAdmin) => {
    setUpdatingUser(userId);
    try {
      await axios.put(`${BACKEND_URL}/api/admin/users/${userId}`, {
        is_admin: !currentIsAdmin
      });
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, is_admin: !currentIsAdmin } : u));
      toast.success(!currentIsAdmin ? 'Nadano uprawnienia admina' : 'Odebrano uprawnienia admina');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Blad aktualizacji';
      toast.error(msg);
    } finally {
      setUpdatingUser(null);
    }
  };

  const handleToggleActive = async (userId, currentIsActive) => {
    setUpdatingUser(userId);
    try {
      if (currentIsActive) {
        await axios.delete(`${BACKEND_URL}/api/admin/users/${userId}`);
      } else {
        await axios.put(`${BACKEND_URL}/api/admin/users/${userId}`, {
          is_active: true
        });
      }
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, is_active: !currentIsActive } : u));
      toast.success(currentIsActive ? 'Uzytkownik dezaktywowany' : 'Uzytkownik aktywowany');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Blad aktualizacji';
      toast.error(msg);
    } finally {
      setUpdatingUser(null);
    }
  };

  const activeUsers = users.filter(u => u.is_active !== false);
  const inactiveUsers = users.filter(u => u.is_active === false);

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Zarzadzanie uzytkownikami</h1>
        <Button onClick={() => setShowCreateDialog(true)} className="gap-2" data-testid="admin-create-user-button">
          <Plus size={18} />
          Nowe konto
        </Button>
      </div>

      {/* Stats */}
      <div className="stats-grid" style={{ marginBottom: 24 }}>
        <div className="stat-card">
          <div className="stat-card-label">Aktywni uzytkownicy</div>
          <div className="stat-card-value">{activeUsers.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Administratorzy</div>
          <div className="stat-card-value" style={{ color: '#F28C28' }}>{users.filter(u => u.is_admin).length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Laczna liczba artykulow</div>
          <div className="stat-card-value">{users.reduce((sum, u) => sum + (u.article_count || 0), 0)}</div>
        </div>
      </div>

      {/* Users table */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: 40 }}>
          <Loader2 size={28} className="animate-spin" style={{ color: '#04389E', margin: '0 auto' }} />
        </div>
      ) : (
        <div className="articles-table">
          <table>
            <thead>
              <tr>
                <th>Uzytkownik</th>
                <th>Email</th>
                <th>Rola</th>
                <th>Artykuly</th>
                <th>Data utworzenia</th>
                <th>Status</th>
                <th>Akcje</th>
              </tr>
            </thead>
            <tbody>
              {activeUsers.map(u => {
                const isSelf = u.id === currentUser?.id;
                const isUpdating = updatingUser === u.id;
                return (
                  <tr key={u.id} data-testid="admin-user-row">
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <div style={{
                          width: 32, height: 32, borderRadius: '50%',
                          background: u.is_admin ? '#F28C28' : '#04389E',
                          color: 'white',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          fontSize: 13, fontWeight: 600, flexShrink: 0
                        }}>
                          {(u.full_name || u.email || '?')[0].toUpperCase()}
                        </div>
                        <div>
                          <div style={{ fontWeight: 600, fontSize: 14 }}>
                            {u.full_name || 'Brak nazwy'}
                            {isSelf && <span style={{ fontSize: 11, color: 'hsl(215, 16%, 55%)', marginLeft: 6 }}>(Ty)</span>}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td style={{ fontSize: 13, color: 'hsl(215, 16%, 40%)' }}>{u.email}</td>
                    <td>
                      {u.is_admin ? (
                        <Badge style={{ background: 'hsl(34, 90%, 94%)', color: '#F28C28', border: '1px solid hsl(34, 80%, 85%)' }}>
                          <Shield size={12} style={{ marginRight: 4 }} />
                          Admin
                        </Badge>
                      ) : (
                        <Badge variant="outline" style={{ color: 'hsl(215, 16%, 50%)' }}>
                          Uzytkownik
                        </Badge>
                      )}
                    </td>
                    <td style={{ fontSize: 14, fontWeight: 500 }}>{u.article_count || 0}</td>
                    <td style={{ fontSize: 13, color: 'hsl(215, 16%, 50%)' }}>
                      {u.created_at ? new Date(u.created_at).toLocaleDateString('pl-PL') : '-'}
                    </td>
                    <td>
                      <Badge style={{ background: 'hsl(158, 55%, 94%)', color: 'hsl(158, 55%, 28%)', border: '1px solid hsl(158, 55%, 85%)' }}>
                        Aktywny
                      </Badge>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: 6 }}>
                        <Button
                          size="sm"
                          variant={u.is_admin ? "outline" : "default"}
                          onClick={() => handleToggleAdmin(u.id, u.is_admin)}
                          disabled={isSelf || isUpdating}
                          style={{ fontSize: 12, padding: '4px 10px', height: 30 }}
                          data-testid="admin-toggle-role-button"
                        >
                          {isUpdating ? (
                            <Loader2 size={12} className="animate-spin" />
                          ) : u.is_admin ? (
                            <><ShieldOff size={12} style={{ marginRight: 4 }} />Odbierz admin</>
                          ) : (
                            <><Shield size={12} style={{ marginRight: 4 }} />Nadaj admin</>
                          )}
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleToggleActive(u.id, true)}
                          disabled={isSelf || isUpdating}
                          style={{ fontSize: 12, padding: '4px 10px', height: 30, color: 'hsl(0, 60%, 45%)' }}
                          data-testid="admin-deactivate-user-button"
                        >
                          <UserX size={12} style={{ marginRight: 4 }} />
                          Dezaktywuj
                        </Button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Inactive users */}
      {inactiveUsers.length > 0 && (
        <div style={{ marginTop: 24 }}>
          <h3 style={{ fontSize: 16, fontFamily: "'Instrument Serif', Georgia, serif", marginBottom: 12, color: 'hsl(215, 16%, 45%)' }}>
            Dezaktywowani ({inactiveUsers.length})
          </h3>
          <div className="articles-table">
            <table>
              <thead>
                <tr>
                  <th>Uzytkownik</th>
                  <th>Email</th>
                  <th>Akcje</th>
                </tr>
              </thead>
              <tbody>
                {inactiveUsers.map(u => (
                  <tr key={u.id} style={{ opacity: 0.6 }}>
                    <td style={{ fontWeight: 500 }}>{u.full_name || 'Brak nazwy'}</td>
                    <td style={{ fontSize: 13 }}>{u.email}</td>
                    <td>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleToggleActive(u.id, false)}
                        disabled={updatingUser === u.id}
                        style={{ fontSize: 12, padding: '4px 10px', height: 30 }}
                        data-testid="admin-reactivate-user-button"
                      >
                        <Check size={12} style={{ marginRight: 4 }} />
                        Aktywuj
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Create user dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent style={{ maxWidth: 440 }}>
          <DialogHeader>
            <DialogTitle style={{ fontFamily: "'Instrument Serif', Georgia, serif", fontSize: 22 }}>
              Nowe konto uzytkownika
            </DialogTitle>
          </DialogHeader>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 16, padding: '8px 0' }}>
            <div>
              <label style={{ fontSize: 13, fontWeight: 600, color: 'hsl(222, 47%, 11%)', display: 'block', marginBottom: 6 }}>
                Imie i nazwisko
              </label>
              <div style={{ position: 'relative' }}>
                <User size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'hsl(215, 16%, 55%)' }} />
                <Input
                  value={newFullName}
                  onChange={(e) => setNewFullName(e.target.value)}
                  placeholder="Jan Kowalski"
                  style={{ paddingLeft: 36 }}
                  data-testid="admin-new-user-name"
                />
              </div>
            </div>

            <div>
              <label style={{ fontSize: 13, fontWeight: 600, color: 'hsl(222, 47%, 11%)', display: 'block', marginBottom: 6 }}>
                Adres email
              </label>
              <div style={{ position: 'relative' }}>
                <Mail size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'hsl(215, 16%, 55%)' }} />
                <Input
                  type="email"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  placeholder="email@firma.pl"
                  style={{ paddingLeft: 36 }}
                  data-testid="admin-new-user-email"
                />
              </div>
            </div>

            <div>
              <label style={{ fontSize: 13, fontWeight: 600, color: 'hsl(222, 47%, 11%)', display: 'block', marginBottom: 6 }}>
                Haslo
              </label>
              <div style={{ position: 'relative' }}>
                <Lock size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'hsl(215, 16%, 55%)' }} />
                <Input
                  type="text"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Min. 6 znakow"
                  style={{ paddingLeft: 36 }}
                  data-testid="admin-new-user-password"
                />
              </div>
            </div>

            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '12px 14px', borderRadius: 10,
              background: newIsAdmin ? 'hsl(34, 90%, 96%)' : 'hsl(210, 22%, 98%)',
              border: `1px solid ${newIsAdmin ? 'hsl(34, 80%, 85%)' : 'hsl(214, 18%, 88%)'}`,
              transition: 'all 0.15s'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Shield size={16} style={{ color: newIsAdmin ? '#F28C28' : 'hsl(215, 16%, 55%)' }} />
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: 'hsl(222, 47%, 11%)' }}>Uprawnienia admina</div>
                  <div style={{ fontSize: 12, color: 'hsl(215, 16%, 50%)' }}>Dostep do wszystkich artykulow i zarzadzania uzytkownikami</div>
                </div>
              </div>
              <Switch
                checked={newIsAdmin}
                onCheckedChange={setNewIsAdmin}
                data-testid="admin-new-user-admin-toggle"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>Anuluj</Button>
            <Button
              onClick={handleCreate}
              disabled={creating || !newEmail || !newPassword}
              className="gap-1"
              data-testid="admin-create-user-submit"
            >
              {creating ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />}
              Utworz konto
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AdminUsers;
