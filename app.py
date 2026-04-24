import streamlit as st
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import matplotlib.pyplot as plt

st.set_page_config(page_title="Emosi NPC RPG", page_icon="🧙", layout="wide")
st.title("🧠 Sistem Logika Fuzzy RPG: Emosi NPC")
st.write("Sesuaikan parameter interaksi pemain untuk melihat reaksi NPC secara realistis.")

# ====================== FUZZY SYSTEM (Cached) ======================
@st.cache_resource
def create_fuzzy_system():
    # --- Input ---
    dialog = ctrl.Antecedent(np.arange(0, 101, 1), 'dialog')
    kharisma = ctrl.Antecedent(np.arange(0, 101, 1), 'kharisma')
    reputasi = ctrl.Antecedent(np.arange(0, 101, 1), 'reputasi')

    # --- Output ---
    emosi = ctrl.Consequent(np.arange(0, 101, 1), 'emosi')

    # --- Membership Functions ---
    dialog['buruk'] = fuzz.trimf(dialog.universe, [0, 0, 45])
    dialog['biasa'] = fuzz.trimf(dialog.universe, [30, 50, 70])
    dialog['baik'] = fuzz.trimf(dialog.universe, [55, 100, 100])

    kharisma['rendah'] = fuzz.trimf(kharisma.universe, [0, 0, 45])
    kharisma['sedang'] = fuzz.trimf(kharisma.universe, [30, 50, 70])
    kharisma['tinggi'] = fuzz.trimf(kharisma.universe, [55, 100, 100])

    reputasi['bermusuhan'] = fuzz.trimf(reputasi.universe, [0, 0, 45])
    reputasi['netral'] = fuzz.trimf(reputasi.universe, [30, 50, 70])
    reputasi['bersahabat'] = fuzz.trimf(reputasi.universe, [55, 100, 100])

    emosi['marah'] = fuzz.trimf(emosi.universe, [0, 0, 45])
    emosi['netral'] = fuzz.trimf(emosi.universe, [30, 50, 70])
    emosi['senang'] = fuzz.trimf(emosi.universe, [55, 100, 100])

    # --- RULES ---
    rules = [
        ctrl.Rule(dialog['buruk'] & reputasi['bermusuhan'], emosi['marah']),
        ctrl.Rule(dialog['buruk'] & reputasi['netral'], emosi['marah']),
        ctrl.Rule(dialog['buruk'] & reputasi['bersahabat'], emosi['netral']),
        ctrl.Rule(dialog['buruk'] & kharisma['tinggi'], emosi['netral']),
        ctrl.Rule(dialog['buruk'] & kharisma['rendah'] & reputasi['bermusuhan'], emosi['marah']),
        ctrl.Rule(dialog['biasa'] & reputasi['bermusuhan'], emosi['marah']),
        ctrl.Rule(dialog['biasa'] & reputasi['netral'], emosi['netral']),
        ctrl.Rule(dialog['biasa'] & reputasi['bersahabat'], emosi['senang']),
        ctrl.Rule(dialog['biasa'] & kharisma['rendah'], emosi['marah']),
        ctrl.Rule(dialog['biasa'] & kharisma['tinggi'] & reputasi['netral'], emosi['senang']),
        ctrl.Rule(dialog['baik'] & reputasi['bermusuhan'], emosi['netral']),
        ctrl.Rule(dialog['baik'] & reputasi['netral'], emosi['senang']),
        ctrl.Rule(dialog['baik'] & reputasi['bersahabat'], emosi['senang']),
        ctrl.Rule(dialog['baik'] & kharisma['tinggi'], emosi['senang']),
        ctrl.Rule(reputasi['bermusuhan'] & kharisma['rendah'], emosi['marah']),
        ctrl.Rule(reputasi['bersahabat'] & kharisma['tinggi'], emosi['senang']),
        ctrl.Rule(dialog['baik'] & kharisma['rendah'] & reputasi['bermusuhan'], emosi['netral']),
        ctrl.Rule(dialog['biasa'] & kharisma['sedang'] & reputasi['netral'], emosi['netral']),
        ctrl.Rule(dialog['buruk'] & kharisma['sedang'] & reputasi['bersahabat'], emosi['netral']),
        ctrl.Rule(dialog['baik'] & kharisma['sedang'] & reputasi['bermusuhan'], emosi['netral']),
    ]

    ctrl_system = ctrl.ControlSystem(rules)
    return ctrl_system, dialog, kharisma, reputasi, emosi


# ====================== UI ======================
col1, col2, col3 = st.columns(3)

with col1:
    dialog_input = st.slider("Kualitas Pilihan Dialog (0-100)", 0, 100, 60, help="Seberapa baik pilihan dialog pemain")

with col2:
    kharisma_input = st.slider("Kharisma Pemain (0-100)", 0, 100, 50, help="Kemampuan persuasi / karisma pemain")

with col3:
    reputasi_input = st.slider("Reputasi Faksi (0-100)", 0, 100, 40, help="Seberapa baik reputasi pemain di mata faksi NPC")

# Contoh dialog cepat
st.subheader("🎮 Contoh Pilihan Dialog")
ex_cols = st.columns(5)
examples = {
    "Pujian tulus": (85, 70, 60),
    "Ancaman": (15, 40, 20),
    "Tanya info quest": (70, 55, 50),
    "Hina faksi": (10, 30, 10),
    "Minta bantuan ramah": (80, 80, 65)
}

for col, (label, (d, k, r)) in zip(ex_cols, examples.items()):
    if col.button(label, use_container_width=True):
        dialog_input = d
        kharisma_input = k
        reputasi_input = r
        st.rerun()

# Tombol hitung
if st.button("💬 Bicara dengan NPC", type="primary", use_container_width=True):
    sim_system, dialog_var, kharisma_var, reputasi_var, emosi_var = create_fuzzy_system()
    sim = ctrl.ControlSystemSimulation(sim_system)

    sim.input['dialog'] = dialog_input
    sim.input['kharisma'] = kharisma_input
    sim.input['reputasi'] = reputasi_input

    try:
        sim.compute()
        skor_emosi = sim.output['emosi']

        st.subheader(f"Skor Emosi NPC: {skor_emosi:.1f} / 100")
        st.progress(skor_emosi / 100)

        if skor_emosi < 40:
            st.error("💢 NPC MARAH! Mereka mencabut senjata dan siap menyerang.")
        elif 40 <= skor_emosi <= 60:
            st.warning("💬 NPC NETRAL. Mereka menjawab dingin dan ingin percakapan cepat selesai.")
        else:
            st.success("✨ NPC SENANG! Mereka tersenyum dan bersedia membantu (info rahasia / quest / diskon).")

        # Visualisasi Membership
        st.subheader("📈 Visualisasi Fuzzy Membership")
        viz1, viz2 = st.columns(2)
        
        with viz1:
            dialog_var.view(sim=sim)
            st.pyplot(plt.gcf())
            plt.close()
            st.caption("Dialog Quality")
            
        with viz2:
            reputasi_var.view(sim=sim)
            st.pyplot(plt.gcf())
            plt.close()
            st.caption("Reputasi Faksi")

    except Exception as e:
        st.error(f"Terjadi error: {e}. Coba nilai lain atau hubungi developer.")

st.caption("Versi improved • 3 input • 24 rules • No sparse system • Siap dipakai di game RPG Anda")