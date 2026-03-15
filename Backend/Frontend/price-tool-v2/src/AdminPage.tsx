import React, { useState, useEffect } from "react";
import { Box, Typography, Tabs, Tab, Button, TextField, Table, TableBody, TableCell, TableHead, TableRow, IconButton, Dialog, DialogTitle, DialogContent, DialogActions } from "@mui/material";
import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import AddIcon from "@mui/icons-material/Add";

const API = "/api";

function headers(userId: number) {
  return { "Content-Type": "application/json", "X-User-Id": String(userId) };
}

type TabValue = "users" | "mdgm" | "pcrs";

interface AdminPageProps {
  loggedInUser: { id?: number; role: string; email: string; name?: string } | null;
}

export default function AdminPage({ loggedInUser }: AdminPageProps) {
  const [tab, setTab] = useState<TabValue>("users");
  const [users, setUsers] = useState<Array<{ id: number; name: string; email: string; role: string; therapeutic_area?: string; countries?: string[] }>>([]);
  const [mdgmRows, setMdgmRows] = useState<Array<Record<string, unknown>>>([]);
  const [pcrs, setPcrs] = useState<Array<{ pcr_id_display: string; country?: string; status?: string; product_name?: string }>>([]);
  const [loading, setLoading] = useState(false);
  const [mdgmDialog, setMdgmDialog] = useState<"create" | "edit" | null>(null);
  const [editingMdgm, setEditingMdgm] = useState<Record<string, unknown> | null>(null);
  const [pcrUpdateDialog, setPcrUpdateDialog] = useState<string | null>(null);
  const [pcrUpdateForm, setPcrUpdateForm] = useState({ status: "", proposed_price: "" });

  const userId = loggedInUser?.id ?? 0;
  const isAdmin = (loggedInUser?.role || "").toLowerCase() === "admin";

  useEffect(() => {
    if (!isAdmin || !userId) return;
    if (tab === "users") loadUsers();
    if (tab === "mdgm") loadMdgm();
    if (tab === "pcrs") loadPcrs();
  }, [tab, userId, isAdmin]);

  const loadUsers = () => {
    setLoading(true);
    fetch(`${API}/users`)
      .then((r) => r.json())
      .then((d) => setUsers(d.users || []))
      .catch(() => setUsers([]))
      .finally(() => setLoading(false));
  };

  const loadMdgm = () => {
    setLoading(true);
    fetch(`${API}/admin/mdgm?limit=100`, { headers: { "X-User-Id": String(userId) } })
      .then((r) => r.json())
      .then((d) => setMdgmRows(d.rows || []))
      .catch(() => setMdgmRows([]))
      .finally(() => setLoading(false));
  };

  const loadPcrs = () => {
    setLoading(true);
    fetch(`${API}/pcrs`, { headers: { "X-User-Id": String(userId) } })
      .then((r) => r.json())
      .then((d) => setPcrs(d.pcrs || []))
      .catch(() => setPcrs([]))
      .finally(() => setLoading(false));
  };

  const createMdgm = () => {
    const body = {
      sku_id: (document.getElementById("mdgm-sku_id") as HTMLInputElement)?.value?.trim() || "SKU-1",
      country: (document.getElementById("mdgm-country") as HTMLInputElement)?.value?.trim() || "IN",
      therapeutic_area: (document.getElementById("mdgm-ta") as HTMLInputElement)?.value?.trim() || "CMC",
      brand: (document.getElementById("mdgm-brand") as HTMLInputElement)?.value?.trim() || "EUTHYROX",
      channel: (document.getElementById("mdgm-channel") as HTMLInputElement)?.value?.trim() || "Retail",
    };
    fetch(`${API}/admin/mdgm`, { method: "POST", headers: headers(userId), body: JSON.stringify(body) })
      .then((r) => { if (!r.ok) return r.json().then((e) => { throw new Error(e.detail || JSON.stringify(e)); }); return r.json(); })
      .then(() => { setMdgmDialog(null); loadMdgm(); })
      .catch((e) => alert(e.message));
  };

  const updateMdgm = (rowId: number) => {
    const price = (document.getElementById("mdgm-edit-price") as HTMLInputElement)?.value;
    const body: Record<string, unknown> = {};
    if (price !== undefined && price !== "") body.current_price_eur = parseFloat(price);
    if (Object.keys(body).length === 0) { setMdgmDialog(null); setEditingMdgm(null); return; }
    fetch(`${API}/admin/mdgm/${rowId}`, { method: "PUT", headers: headers(userId), body: JSON.stringify(body) })
      .then((r) => { if (!r.ok) return r.json().then((e) => { throw new Error(e.detail || "Failed"); }); setMdgmDialog(null); setEditingMdgm(null); loadMdgm(); })
      .catch((e) => alert(e.message));
  };

  const deleteMdgm = (rowId: number) => {
    if (!confirm("Delete this MDGM row?")) return;
    fetch(`${API}/admin/mdgm/${rowId}`, { method: "DELETE", headers: { "X-User-Id": String(userId) } })
      .then((r) => { if (!r.ok) return r.json().then((e) => { throw new Error(e.detail || "Failed"); }); loadMdgm(); })
      .catch((e) => alert(e.message));
  };

  const deletePcr = (pcrId: string) => {
    if (!confirm(`Delete PCR ${pcrId}?`)) return;
    fetch(`${API}/admin/pcrs/${pcrId}`, { method: "DELETE", headers: { "X-User-Id": String(userId) } })
      .then((r) => { if (!r.ok) return r.json().then((e) => { throw new Error(e.detail || "Failed"); }); loadPcrs(); })
      .catch((e) => alert(e.message));
  };

  const updatePcr = () => {
    if (!pcrUpdateDialog) return;
    const body: Record<string, string> = {};
    if (pcrUpdateForm.status) body.status = pcrUpdateForm.status;
    if (pcrUpdateForm.proposed_price) body.proposed_price = pcrUpdateForm.proposed_price;
    if (Object.keys(body).length === 0) { setPcrUpdateDialog(null); return; }
    fetch(`${API}/admin/pcrs/${pcrUpdateDialog}`, {
      method: "PUT",
      headers: headers(userId),
      body: JSON.stringify(body),
    })
      .then((r) => { if (!r.ok) return r.json().then((e) => { throw new Error(e.detail || "Failed"); }); setPcrUpdateDialog(null); loadPcrs(); })
      .catch((e) => alert(e.message));
  };

  if (!isAdmin) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography color="error">Admin only. Your role: {loggedInUser?.role || "—"}.</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h5" sx={{ mb: 2 }}>Admin – Test backend features</Typography>
      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label="Users" value="users" />
        <Tab label="MDGM (SKUs)" value="mdgm" />
        <Tab label="Admin PCRs" value="pcrs" />
      </Tabs>

      {tab === "users" && (
        <>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            User creation and country/role assignment are developers-only. Read-only list; assigned countries shown for reference.
          </Typography>
          {loading ? <Typography>Loading...</Typography> : (
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>ID</TableCell><TableCell>Name</TableCell><TableCell>Email</TableCell>
                  <TableCell>Role</TableCell><TableCell>Assigned countries</TableCell><TableCell>TA</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {users.map((u) => (
                  <TableRow key={u.id}>
                    <TableCell>{u.id}</TableCell>
                    <TableCell>{u.name}</TableCell>
                    <TableCell>{u.email}</TableCell>
                    <TableCell>{u.role}</TableCell>
                    <TableCell>{u.countries?.length ? u.countries.join(", ") : "—"}</TableCell>
                    <TableCell>{u.therapeutic_area ?? "—"}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </>
      )}

      {tab === "mdgm" && (
        <>
          <Button startIcon={<AddIcon />} onClick={() => setMdgmDialog("create")} sx={{ mb: 2 }}>Add MDGM row</Button>
          {loading ? <Typography>Loading...</Typography> : (
            <Table size="small">
              <TableHead>
                <TableRow><TableCell>id</TableCell><TableCell>sku_id</TableCell><TableCell>country</TableCell><TableCell>channel</TableCell><TableCell>price_type</TableCell><TableCell>current_price_eur</TableCell><TableCell></TableCell></TableRow>
              </TableHead>
              <TableBody>
                {mdgmRows.map((r) => (
                  <TableRow key={String(r.id)}>
                    <TableCell>{String(r.id)}</TableCell>
                    <TableCell>{String(r.sku_id)}</TableCell>
                    <TableCell>{String(r.country)}</TableCell>
                    <TableCell>{String(r.channel ?? "—")}</TableCell>
                    <TableCell>{String(r.price_type ?? "—")}</TableCell>
                    <TableCell>{r.current_price_eur != null ? String(r.current_price_eur) : "—"}</TableCell>
                    <TableCell>
                      <IconButton size="small" onClick={() => { setEditingMdgm(r); setMdgmDialog("edit"); }}><EditIcon /></IconButton>
                      <IconButton size="small" onClick={() => deleteMdgm(Number(r.id))}><DeleteIcon /></IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </>
      )}

      {tab === "pcrs" && (
        <>
          {loading ? <Typography>Loading...</Typography> : (
            <Table size="small">
              <TableHead>
                <TableRow><TableCell>pcr_id</TableCell><TableCell>country</TableCell><TableCell>status</TableCell><TableCell>product_name</TableCell><TableCell></TableCell></TableRow>
              </TableHead>
              <TableBody>
                {pcrs.map((p) => (
                  <TableRow key={p.pcr_id_display}>
                    <TableCell>{p.pcr_id_display}</TableCell>
                    <TableCell>{p.country ?? "—"}</TableCell>
                    <TableCell>{p.status ?? "—"}</TableCell>
                    <TableCell>{p.product_name ?? "—"}</TableCell>
                    <TableCell>
                      <IconButton size="small" onClick={() => { setPcrUpdateDialog(p.pcr_id_display); setPcrUpdateForm({ status: p.status ?? "", proposed_price: "" }); }}><EditIcon /></IconButton>
                      <IconButton size="small" onClick={() => deletePcr(p.pcr_id_display)}><DeleteIcon /></IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </>
      )}

      <Dialog open={mdgmDialog === "create"} onClose={() => setMdgmDialog(null)}>
        <DialogTitle>Create MDGM row</DialogTitle>
        <DialogContent>
          <TextField id="mdgm-sku_id" fullWidth label="sku_id" defaultValue="SKU-NEW" margin="dense" />
          <TextField id="mdgm-country" fullWidth label="country" defaultValue="IN" margin="dense" />
          <TextField id="mdgm-ta" fullWidth label="therapeutic_area" defaultValue="CMC" margin="dense" />
          <TextField id="mdgm-brand" fullWidth label="brand" defaultValue="EUTHYROX" margin="dense" />
          <TextField id="mdgm-channel" fullWidth label="channel" defaultValue="Retail" margin="dense" />
        </DialogContent>
        <DialogActions><Button onClick={() => setMdgmDialog(null)}>Cancel</Button><Button onClick={createMdgm}>Create</Button></DialogActions>
      </Dialog>

      <Dialog open={mdgmDialog === "edit" && !!editingMdgm} onClose={() => { setMdgmDialog(null); setEditingMdgm(null); }}>
        <DialogTitle>Edit MDGM (current_price_eur)</DialogTitle>
        <DialogContent>
          <TextField id="mdgm-edit-price" fullWidth label="current_price_eur" type="number" defaultValue={editingMdgm?.current_price_eur} margin="dense" />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setMdgmDialog(null); setEditingMdgm(null); }}>Cancel</Button>
          <Button onClick={() => editingMdgm && updateMdgm(Number(editingMdgm.id))}>Save</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={!!pcrUpdateDialog} onClose={() => setPcrUpdateDialog(null)}>
        <DialogTitle>Admin update PCR</DialogTitle>
        <DialogContent>
          <TextField fullWidth label="status" value={pcrUpdateForm.status} onChange={(e) => setPcrUpdateForm((f) => ({ ...f, status: e.target.value }))} placeholder="draft, local_approved, ..." margin="dense" />
          <TextField fullWidth label="proposed_price" value={pcrUpdateForm.proposed_price} onChange={(e) => setPcrUpdateForm((f) => ({ ...f, proposed_price: e.target.value }))} margin="dense" />
        </DialogContent>
        <DialogActions><Button onClick={() => setPcrUpdateDialog(null)}>Cancel</Button><Button onClick={updatePcr}>Save</Button></DialogActions>
      </Dialog>

    </Box>
  );
}
