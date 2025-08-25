import streamlit as st
from supabase import create_client, Client
import pandas as pd

# --- KONFIGURASI SUPABASE ---
# Ganti dengan URL dan Key dari proyek Supabase Anda.
# Sebaiknya simpan ini sebagai environment variables atau Streamlit secrets.
SUPABASE_URL = st.secrets["supabase_url"]
SUPABASE_KEY = st.secrets["supabase_key"]

# Inisialisasi koneksi ke Supabase
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Gagal terhubung ke Supabase: {e}")
    st.stop()

# --- FUNGSI HELPER ---

def get_user_id():
    """Mendapatkan ID pengguna yang sedang login dari session."""
    if 'user' in st.session_state and st.session_state.user:
        return st.session_state.user.id
    return None

# --- TAMPILAN APLIKASI ---

st.set_page_config(page_title="Todo App Komunitas", page_icon="📝", layout="centered")
st.title("📝 Todo App Komunitas")
st.write("Aplikasi untuk mengelola daftar tugas Anda, didukung oleh Supabase & Streamlit.")

# --- LOGIKA OTENTIKASI & TAMPILAN ---

# Inisialisasi session state jika belum ada
if 'user' not in st.session_state:
    st.session_state.user = None

# Jika pengguna belum login, tampilkan form login/register
if st.session_state.user is None:
    login_tab, register_tab = st.tabs(["🔐 Login", "✍️ Register"])

    # Tab Login
    with login_tab:
        st.subheader("Masuk ke Akun Anda")
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

            if submitted:
                try:
                    response = supabase.auth.sign_in_with_password({
                        "email": email,
                        "password": password
                    })
                    st.session_state.user = response.user
                    st.rerun() # Muat ulang halaman untuk masuk ke dashboard
                except Exception as e:
                    st.error(f"Gagal login: Pastikan email dan password benar.")

    # Tab Register
    with register_tab:
        st.subheader("Buat Akun Baru")
        with st.form("register_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Konfirmasi Password", type="password")
            submitted = st.form_submit_button("Register")

            if submitted:
                if password != confirm_password:
                    st.error("Password tidak cocok!")
                elif not email or not password:
                    st.warning("Email dan password tidak boleh kosong.")
                else:
                    try:
                        response = supabase.auth.sign_up({
                            "email": email,
                            "password": password,
                        })
                        st.success("Registrasi berhasil! Silakan cek email Anda untuk verifikasi dan kemudian login.")
                    except Exception as e:
                        st.error(f"Gagal mendaftar: {e}")

# --- DASHBOARD (Tampil setelah login berhasil) ---
else:
    st.sidebar.subheader(f"Selamat datang,")
    st.sidebar.markdown(f"**{st.session_state.user.email}**")
    if st.sidebar.button("Logout"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()

    st.header("Dashboard Tugas Anda")

    # Form untuk menambah tugas baru
    with st.form("new_task_form", clear_on_submit=True):
        new_task_desc = st.text_input("➕ Tambah tugas baru:", placeholder="Contoh: Belajar Supabase")
        submitted = st.form_submit_button("Tambah")
        if submitted and new_task_desc:
            user_id = get_user_id()
            
# Form untuk menambah tugas baru
with st.form("new_task_form", clear_on_submit=True):
    new_task_desc = st.text_input("➕ Tambah tugas baru:", placeholder="Contoh: Belajar Supabase")
    submitted = st.form_submit_button("Tambah")
    if submitted and new_task_desc:
        user_id = get_user_id()

        # --- TAMBAHKAN BARIS DEBUG INI ---
        st.info(f"DEBUG: Mencoba menambah tugas untuk user_id: {user_id}")
        # --------------------------------

        if user_id:
            try:
                supabase.table("tasks").insert({
                    "description": new_task_desc,
                    "user_id": user_id
                }).execute()
                st.toast("Tugas berhasil ditambahkan!")
                st.rerun() # Tambahkan rerun untuk refresh instan
            except Exception as e:
                st.error(f"Gagal menambah tugas: {e}")
        else:
            st.error("DEBUG: Gagal mendapatkan user_id. Sesi mungkin tidak valid.")

            
            if user_id:
                try:
                    supabase.table("tasks").insert({
                        "description": new_task_desc,
                        "user_id": user_id
                    }).execute()
                    st.toast("Tugas berhasil ditambahkan!")
                except Exception as e:
                    st.error(f"Gagal menambah tugas: {e}")

    st.markdown("---")

    # Menampilkan daftar tugas
    st.subheader("Daftar Tugas")
    user_id = get_user_id()
    if user_id:
        try:
            response = supabase.table("tasks").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
            tasks = response.data

            if not tasks:
                st.info("Anda belum memiliki tugas. Silakan tambahkan di atas.")
            else:
                for task in tasks:
                    cols = st.columns((1, 10, 2))
                    # Checkbox untuk status selesai
                    is_completed = cols[0].checkbox("", value=task['is_completed'], key=f"check_{task['id']}")
                    if is_completed != task['is_completed']:
                        supabase.table("tasks").update({"is_completed": is_completed}).eq("id", task['id']).execute()
                        st.rerun()

                    # Deskripsi tugas
                    task_description = f"~~{task['description']}~~" if is_completed else task['description']
                    cols[1].markdown(task_description)

                    # Tombol Hapus
                    if cols[2].button("🗑️", key=f"del_{task['id']}"):
                        supabase.table("tasks").delete().eq("id", task['id']).execute()
                        st.toast(f"Tugas '{task['description']}' dihapus.")
                        st.rerun()

        except Exception as e:
            st.error(f"Gagal mengambil data tugas: {e}")

