import streamlit as st
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

st.set_page_config(page_title="Emosi NPC RPG", page_icon="🧙", layout="wide")
st.title("🧠 Sistem Emosi NPC RPG")
st.write("Sesuaikan parameter interaksi pemain untuk melihat reaksi NPC secara realistis.")

# ============================================================
#  FUZZY SYSTEM
# ============================================================
@st.cache_resource
def create_fuzzy_system():
    # --- Antecedent ---
    dialog    = ctrl.Antecedent(np.arange(0, 101, 1), 'dialog')
    kharisma  = ctrl.Antecedent(np.arange(0, 101, 1), 'kharisma')
    reputasi  = ctrl.Antecedent(np.arange(0, 101, 1), 'reputasi')

    # --- Consequent ---
    emosi = ctrl.Consequent(np.arange(0, 101, 1), 'emosi', defuzzify_method='centroid')

    # --- Membership Functions (trapmf di ujung agar full coverage) ---
    dialog['buruk']  = fuzz.trapmf(dialog.universe,   [0, 0, 25, 45])
    dialog['biasa']  = fuzz.trimf(dialog.universe,    [30, 50, 70])
    dialog['baik']   = fuzz.trapmf(dialog.universe,   [55, 75, 100, 100])

    kharisma['rendah'] = fuzz.trapmf(kharisma.universe, [0, 0, 25, 45])
    kharisma['sedang'] = fuzz.trimf(kharisma.universe,  [30, 50, 70])
    kharisma['tinggi'] = fuzz.trapmf(kharisma.universe, [55, 75, 100, 100])

    reputasi['bermusuhan'] = fuzz.trapmf(reputasi.universe, [0, 0, 25, 45])
    reputasi['netral']     = fuzz.trimf(reputasi.universe,  [30, 50, 70])
    reputasi['bersahabat'] = fuzz.trapmf(reputasi.universe, [55, 75, 100, 100])

    emosi['marah']  = fuzz.trapmf(emosi.universe, [0, 0, 25, 45])
    emosi['netral'] = fuzz.trimf(emosi.universe,  [30, 50, 70])
    emosi['senang'] = fuzz.trapmf(emosi.universe, [55, 75, 100, 100])

    # --- Rules (27 rules, full combination + kharisma modifiers) ---
    rules = [
        # Dialog BURUK
        ctrl.Rule(dialog['buruk'] & reputasi['bermusuhan'] & kharisma['rendah'], emosi['marah']),
        ctrl.Rule(dialog['buruk'] & reputasi['bermusuhan'] & kharisma['sedang'], emosi['marah']),
        ctrl.Rule(dialog['buruk'] & reputasi['bermusuhan'] & kharisma['tinggi'], emosi['marah']),
        ctrl.Rule(dialog['buruk'] & reputasi['netral']     & kharisma['rendah'], emosi['marah']),
        ctrl.Rule(dialog['buruk'] & reputasi['netral']     & kharisma['sedang'], emosi['marah']),
        ctrl.Rule(dialog['buruk'] & reputasi['netral']     & kharisma['tinggi'], emosi['netral']),
        ctrl.Rule(dialog['buruk'] & reputasi['bersahabat'] & kharisma['rendah'], emosi['netral']),
        ctrl.Rule(dialog['buruk'] & reputasi['bersahabat'] & kharisma['sedang'], emosi['netral']),
        ctrl.Rule(dialog['buruk'] & reputasi['bersahabat'] & kharisma['tinggi'], emosi['netral']),

        # Dialog BIASA
        ctrl.Rule(dialog['biasa'] & reputasi['bermusuhan'] & kharisma['rendah'], emosi['marah']),
        ctrl.Rule(dialog['biasa'] & reputasi['bermusuhan'] & kharisma['sedang'], emosi['marah']),
        ctrl.Rule(dialog['biasa'] & reputasi['bermusuhan'] & kharisma['tinggi'], emosi['netral']),
        ctrl.Rule(dialog['biasa'] & reputasi['netral']     & kharisma['rendah'], emosi['marah']),
        ctrl.Rule(dialog['biasa'] & reputasi['netral']     & kharisma['sedang'], emosi['netral']),
        ctrl.Rule(dialog['biasa'] & reputasi['netral']     & kharisma['tinggi'], emosi['senang']),
        ctrl.Rule(dialog['biasa'] & reputasi['bersahabat'] & kharisma['rendah'], emosi['netral']),
        ctrl.Rule(dialog['biasa'] & reputasi['bersahabat'] & kharisma['sedang'], emosi['senang']),
        ctrl.Rule(dialog['biasa'] & reputasi['bersahabat'] & kharisma['tinggi'], emosi['senang']),

        # Dialog BAIK
        ctrl.Rule(dialog['baik'] & reputasi['bermusuhan'] & kharisma['rendah'], emosi['netral']),
        ctrl.Rule(dialog['baik'] & reputasi['bermusuhan'] & kharisma['sedang'], emosi['netral']),
        ctrl.Rule(dialog['baik'] & reputasi['bermusuhan'] & kharisma['tinggi'], emosi['senang']),
        ctrl.Rule(dialog['baik'] & reputasi['netral']     & kharisma['rendah'], emosi['netral']),
        ctrl.Rule(dialog['baik'] & reputasi['netral']     & kharisma['sedang'], emosi['senang']),
        ctrl.Rule(dialog['baik'] & reputasi['netral']     & kharisma['tinggi'], emosi['senang']),
        ctrl.Rule(dialog['baik'] & reputasi['bersahabat'] & kharisma['rendah'], emosi['senang']),
        ctrl.Rule(dialog['baik'] & reputasi['bersahabat'] & kharisma['sedang'], emosi['senang']),
        ctrl.Rule(dialog['baik'] & reputasi['bersahabat'] & kharisma['tinggi'], emosi['senang']),
    ]

    ctrl_system = ctrl.ControlSystem(rules)
    return ctrl_system, dialog, kharisma, reputasi, emosi


# ============================================================
#  EXPERT SYSTEM (Forward Chaining)
# ============================================================
class SistemPakar:
    """
    Sistem Pakar berbasis aturan produksi (IF-THEN) dengan forward chaining.
    Setiap aturan memiliki bobot kepercayaan (Certainty Factor).
    """

    RULES = [
        # (ID, kondisi_dict, emosi_output, CF, deskripsi_rule)
        # CF: 0.0 – 1.0 (tingkat kepercayaan rule)

        # --- MARAH ---
        ("R01", {"dialog": "buruk", "reputasi": "bermusuhan", "kharisma": "rendah"},
         "marah", 1.0, "Dialog buruk + reputasi bermusuhan + kharisma rendah → pasti marah"),

        ("R02", {"dialog": "buruk", "reputasi": "bermusuhan", "kharisma": "sedang"},
         "marah", 0.9, "Dialog buruk + reputasi bermusuhan + kharisma sedang → sangat marah"),

        ("R03", {"dialog": "buruk", "reputasi": "bermusuhan", "kharisma": "tinggi"},
         "marah", 0.75, "Dialog buruk + reputasi bermusuhan walaupun kharisma tinggi → marah"),

        ("R04", {"dialog": "buruk", "reputasi": "netral", "kharisma": "rendah"},
         "marah", 0.85, "Dialog buruk + reputasi netral + kharisma rendah → marah"),

        ("R05", {"dialog": "buruk", "reputasi": "netral", "kharisma": "sedang"},
         "marah", 0.7, "Dialog buruk + reputasi netral + kharisma sedang → marah"),

        ("R06", {"dialog": "biasa", "reputasi": "bermusuhan", "kharisma": "rendah"},
         "marah", 0.85, "Dialog biasa + reputasi bermusuhan + kharisma rendah → marah"),

        ("R07", {"dialog": "biasa", "reputasi": "bermusuhan", "kharisma": "sedang"},
         "marah", 0.75, "Dialog biasa + reputasi bermusuhan + kharisma sedang → marah"),

        ("R08", {"dialog": "biasa", "reputasi": "netral", "kharisma": "rendah"},
         "marah", 0.65, "Dialog biasa + reputasi netral + kharisma rendah → cenderung marah"),

        # --- NETRAL ---
        ("R09", {"dialog": "buruk", "reputasi": "netral", "kharisma": "tinggi"},
         "netral", 0.7, "Dialog buruk tapi kharisma tinggi + reputasi netral → netral"),

        ("R10", {"dialog": "buruk", "reputasi": "bersahabat", "kharisma": "rendah"},
         "netral", 0.75, "Dialog buruk + reputasi bersahabat + kharisma rendah → netral"),

        ("R11", {"dialog": "buruk", "reputasi": "bersahabat", "kharisma": "sedang"},
         "netral", 0.8, "Dialog buruk + reputasi bersahabat + kharisma sedang → netral"),

        ("R12", {"dialog": "buruk", "reputasi": "bersahabat", "kharisma": "tinggi"},
         "netral", 0.8, "Dialog buruk + reputasi bersahabat + kharisma tinggi → netral"),

        ("R13", {"dialog": "biasa", "reputasi": "bermusuhan", "kharisma": "tinggi"},
         "netral", 0.7, "Dialog biasa + reputasi bermusuhan tapi kharisma tinggi → netral"),

        ("R14", {"dialog": "biasa", "reputasi": "netral", "kharisma": "sedang"},
         "netral", 0.8, "Dialog biasa + reputasi netral + kharisma sedang → netral"),

        ("R15", {"dialog": "biasa", "reputasi": "bersahabat", "kharisma": "rendah"},
         "netral", 0.7, "Dialog biasa + reputasi bersahabat + kharisma rendah → netral"),

        ("R16", {"dialog": "baik", "reputasi": "bermusuhan", "kharisma": "rendah"},
         "netral", 0.75, "Dialog baik + reputasi bermusuhan + kharisma rendah → netral"),

        ("R17", {"dialog": "baik", "reputasi": "bermusuhan", "kharisma": "sedang"},
         "netral", 0.8, "Dialog baik + reputasi bermusuhan + kharisma sedang → netral"),

        ("R18", {"dialog": "baik", "reputasi": "netral", "kharisma": "rendah"},
         "netral", 0.7, "Dialog baik + reputasi netral + kharisma rendah → netral"),

        # --- SENANG ---
        ("R19", {"dialog": "biasa", "reputasi": "netral", "kharisma": "tinggi"},
         "senang", 0.75, "Dialog biasa + reputasi netral + kharisma tinggi → senang"),

        ("R20", {"dialog": "biasa", "reputasi": "bersahabat", "kharisma": "sedang"},
         "senang", 0.8, "Dialog biasa + reputasi bersahabat + kharisma sedang → senang"),

        ("R21", {"dialog": "biasa", "reputasi": "bersahabat", "kharisma": "tinggi"},
         "senang", 0.9, "Dialog biasa + reputasi bersahabat + kharisma tinggi → senang"),

        ("R22", {"dialog": "baik", "reputasi": "bermusuhan", "kharisma": "tinggi"},
         "senang", 0.7, "Dialog baik + kharisma tinggi meski reputasi bermusuhan → senang"),

        ("R23", {"dialog": "baik", "reputasi": "netral", "kharisma": "sedang"},
         "senang", 0.85, "Dialog baik + reputasi netral + kharisma sedang → senang"),

        ("R24", {"dialog": "baik", "reputasi": "netral", "kharisma": "tinggi"},
         "senang", 0.9, "Dialog baik + reputasi netral + kharisma tinggi → sangat senang"),

        ("R25", {"dialog": "baik", "reputasi": "bersahabat", "kharisma": "rendah"},
         "senang", 0.8, "Dialog baik + reputasi bersahabat walaupun kharisma rendah → senang"),

        ("R26", {"dialog": "baik", "reputasi": "bersahabat", "kharisma": "sedang"},
         "senang", 0.95, "Dialog baik + reputasi bersahabat + kharisma sedang → sangat senang"),

        ("R27", {"dialog": "baik", "reputasi": "bersahabat", "kharisma": "tinggi"},
         "senang", 1.0, "Dialog baik + reputasi bersahabat + kharisma tinggi → pasti senang"),
    ]

    @staticmethod
    def kategorikan(nilai, rendah_max=45, sedang_center=50, tinggi_min=55):
        """Kategorikan nilai numerik ke kelas linguistik."""
        if nilai <= rendah_max:
            return "rendah_atau_buruk_atau_bermusuhan"
        elif nilai >= tinggi_min:
            return "tinggi_atau_baik_atau_bersahabat"
        else:
            return "sedang_atau_biasa_atau_netral"

    @staticmethod
    def kategorikan_dialog(v):
        if v <= 40: return "buruk"
        elif v >= 60: return "baik"
        else: return "biasa"

    @staticmethod
    def kategorikan_kharisma(v):
        if v <= 40: return "rendah"
        elif v >= 60: return "tinggi"
        else: return "sedang"

    @staticmethod
    def kategorikan_reputasi(v):
        if v <= 40: return "bermusuhan"
        elif v >= 60: return "bersahabat"
        else: return "netral"

    @classmethod
    def inferensi(cls, dialog_val, kharisma_val, reputasi_val):
        """
        Forward chaining: cocokkan fakta dengan antecedent rules.
        Agregasi CF: CF_final = 1 - ∏(1 - CF_i) untuk rules sejenis.
        """
        fakta = {
            "dialog":   cls.kategorikan_dialog(dialog_val),
            "kharisma": cls.kategorikan_kharisma(kharisma_val),
            "reputasi": cls.kategorikan_reputasi(reputasi_val),
        }

        # Kumpulkan CF per emosi
        cf_emosi = {"marah": [], "netral": [], "senang": []}
        fired_rules = []

        for rule_id, kondisi, emosi_out, cf, deskripsi in cls.RULES:
            # Cek apakah semua kondisi cocok dengan fakta
            cocok = all(fakta.get(k) == v for k, v in kondisi.items())
            if cocok:
                cf_emosi[emosi_out].append(cf)
                fired_rules.append({
                    "id": rule_id,
                    "emosi": emosi_out,
                    "cf": cf,
                    "deskripsi": deskripsi,
                })

        # Agregasi CF dengan kombinasi paralel: CF = 1 - ∏(1-CFi)
        cf_final = {}
        for emosi_key, cf_list in cf_emosi.items():
            if not cf_list:
                cf_final[emosi_key] = 0.0
            else:
                hasil = 1.0
                for c in cf_list:
                    hasil *= (1.0 - c)
                cf_final[emosi_key] = round(1.0 - hasil, 4)

        # Emosi dengan CF tertinggi
        emosi_terpilih = max(cf_final, key=cf_final.get)
        total = sum(cf_final.values())
        skor_0_100 = round((cf_final[emosi_terpilih] / max(total, 0.001)) * 100, 1)

        return {
            "fakta":          fakta,
            "fired_rules":    fired_rules,
            "cf_final":       cf_final,
            "emosi_terpilih": emosi_terpilih,
            "skor":           skor_0_100,
        }


# ============================================================
#  HELPER UI
# ============================================================
EMOSI_CONFIG = {
    "marah":  {"emoji": "💢", "warna": "error",   "label": "MARAH",
               "narasi": "NPC mencabut senjata dan siap menyerang!"},
    "netral": {"emoji": "💬", "warna": "warning",  "label": "NETRAL",
               "narasi": "NPC menjawab dingin, ingin percakapan cepat selesai."},
    "senang": {"emoji": "✨", "warna": "success",  "label": "SENANG",
               "narasi": "NPC tersenyum dan bersedia membantu (info rahasia / quest / diskon)!"},
}

def tampilkan_hasil_emosi(skor, emosi_label):
    cfg = EMOSI_CONFIG[emosi_label]
    st.metric("Skor Emosi NPC", f"{skor:.1f} / 100")
    st.progress(skor / 100)
    getattr(st, cfg["warna"])(f"{cfg['emoji']} NPC {cfg['label']}! {cfg['narasi']}")


def plot_membership_functions(var, nilai_input, judul):
    """Plot semua MF + garis input saat ini."""
    fig, ax = plt.subplots(figsize=(5, 2.8))
    colors = {"buruk": "#e74c3c", "biasa": "#f39c12", "baik": "#2ecc71",
              "rendah": "#e74c3c", "sedang": "#f39c12", "tinggi": "#2ecc71",
              "bermusuhan": "#e74c3c", "netral": "#f39c12", "bersahabat": "#2ecc71",
              "marah": "#e74c3c", "senang": "#2ecc71"}
    patches = []
    for term_name in var.terms:
        mf = var[term_name].mf
        color = colors.get(term_name, "steelblue")
        ax.plot(var.universe, mf, color=color, linewidth=2)
        ax.fill_between(var.universe, mf, alpha=0.15, color=color)
        patches.append(mpatches.Patch(color=color, label=term_name))

    ax.axvline(x=nilai_input, color="navy", linestyle="--", linewidth=1.5, label=f"Input={nilai_input}")
    ax.set_title(judul, fontsize=10, fontweight="bold")
    ax.set_xlabel("Nilai (0–100)", fontsize=8)
    ax.set_ylabel("Derajat Keanggotaan", fontsize=8)
    ax.set_ylim(-0.05, 1.15)
    ax.legend(handles=patches + [plt.Line2D([0], [0], color='navy', linestyle='--', label=f'Input={nilai_input}')],
              fontsize=7, loc="upper right")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def plot_cf_bar(cf_final):
    """Bar chart Certainty Factor untuk sistem pakar."""
    fig, ax = plt.subplots(figsize=(5, 2.8))
    emosi_list  = list(cf_final.keys())
    cf_values   = [cf_final[e] for e in emosi_list]
    warna_bar   = ["#e74c3c", "#f39c12", "#2ecc71"]
    bars = ax.barh(emosi_list, cf_values, color=warna_bar, edgecolor="white", height=0.5)
    for bar, val in zip(bars, cf_values):
        ax.text(val + 0.01, bar.get_y() + bar.get_height() / 2,
                f"{val:.3f}", va='center', fontsize=9, fontweight='bold')
    ax.set_xlim(0, 1.15)
    ax.set_xlabel("Certainty Factor (CF)", fontsize=9)
    ax.set_title("Keyakinan Sistem Pakar per Emosi", fontsize=10, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    fig.tight_layout()
    return fig


# ============================================================
#  INPUT PANEL
# ============================================================
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    dialog_input   = st.slider("🗣️ Kualitas Dialog (0–100)",   0, 100, 60)
with col2:
    kharisma_input = st.slider("⭐ Kharisma Pemain (0–100)",   0, 100, 50)
with col3:
    reputasi_input = st.slider("🏅 Reputasi Faksi (0–100)",    0, 100, 40)

# Quick examples
st.subheader("🎮 Contoh Skenario Cepat")
ex_cols = st.columns(5)
examples = {
    "Pujian tulus":       (85, 70, 60),
    "Ancaman keras":      (15, 30, 20),
    "Tanya info quest":   (70, 55, 50),
    "Hina faksi":         (10, 25, 10),
    "Minta bantuan":      (80, 80, 65),
}
for col, (label, (d, k, r)) in zip(ex_cols, examples.items()):
    if col.button(label, use_container_width=True):
        dialog_input   = d
        kharisma_input = k
        reputasi_input = r
        st.rerun()

st.markdown("---")

# ============================================================
#  TAB: Fuzzy vs Sistem Pakar
# ============================================================
tab_fuzzy, tab_pakar, tab_perbandingan = st.tabs([
    "🔮 Logika Fuzzy",
    "🧩 Sistem Pakar",
    "⚖️ Perbandingan Hasil",
])

# ─────────────────────────────────────────────
# TAB 1 – LOGIKA FUZZY
# ─────────────────────────────────────────────
with tab_fuzzy:
    st.subheader("🔮 Inferensi Logika Fuzzy (Mamdani)")
    st.caption("Menggunakan fungsi keanggotaan trapesium/segitiga + defuzzifikasi centroid.")

    if st.button("💬 Hitung dengan Fuzzy", type="primary", use_container_width=True, key="btn_fuzzy"):
        with st.spinner("Menghitung..."):
            try:
                ctrl_sys, d_var, k_var, r_var, e_var = create_fuzzy_system()
                sim = ctrl.ControlSystemSimulation(ctrl_sys)
                sim.input['dialog']   = dialog_input
                sim.input['kharisma'] = kharisma_input
                sim.input['reputasi'] = reputasi_input
                sim.compute()
                skor_fuzzy = sim.output['emosi']

                if skor_fuzzy < 40:
                    emosi_fuzzy = "marah"
                elif skor_fuzzy <= 60:
                    emosi_fuzzy = "netral"
                else:
                    emosi_fuzzy = "senang"

                st.session_state["fuzzy_skor"]  = skor_fuzzy
                st.session_state["fuzzy_emosi"] = emosi_fuzzy
                st.session_state["fuzzy_sim"]   = sim
                st.session_state["fuzzy_vars"]  = (d_var, k_var, r_var, e_var)

            except Exception as e:
                st.error(f"❌ Error komputasi fuzzy: {e}")
                st.info("Coba geser slider agar nilai tidak tepat di perbatasan antar kategori (mis. 50 → 48 atau 52).")

    if "fuzzy_skor" in st.session_state:
        skor_f = st.session_state["fuzzy_skor"]
        emosi_f = st.session_state["fuzzy_emosi"]

        tampilkan_hasil_emosi(skor_f, emosi_f)

        st.subheader("📈 Visualisasi Fungsi Keanggotaan")
        d_var, k_var, r_var, e_var = st.session_state["fuzzy_vars"]

        col_a, col_b = st.columns(2)
        with col_a:
            st.pyplot(plot_membership_functions(d_var,   dialog_input,   "Dialog"))
            st.pyplot(plot_membership_functions(k_var,   kharisma_input, "Kharisma"))
        with col_b:
            st.pyplot(plot_membership_functions(r_var,   reputasi_input, "Reputasi"))
            st.pyplot(plot_membership_functions(e_var,   skor_f,         "Output: Emosi"))

        with st.expander("ℹ️ Cara kerja sistem fuzzy ini"):
            st.markdown("""
**Alur inferensi Mamdani:**
1. **Fuzzifikasi** – nilai numerik input dikonversi ke derajat keanggotaan tiap term linguistik.
2. **Evaluasi rule** – setiap rule dievaluasi dengan operator `AND = min(μ1, μ2, μ3)`.
3. **Agregasi** – semua output rule untuk emosi yang sama digabungkan dengan `max`.
4. **Defuzzifikasi** – metode **centroid** mengubah area output fuzzy menjadi skor 0–100.

**Fungsi Keanggotaan:**
- Kategori ujung (`buruk`, `baik`, `rendah`, `tinggi`, dll.) menggunakan **trapesium** agar full coverage.
- Kategori tengah (`biasa`, `sedang`, `netral`) menggunakan **segitiga**.
- Total: **27 rules** mencakup semua kombinasi 3×3×3 tanpa konflik.
""")

# ─────────────────────────────────────────────
# TAB 2 – SISTEM PAKAR
# ─────────────────────────────────────────────
with tab_pakar:
    st.subheader("🧩 Inferensi Sistem Pakar (Forward Chaining)")
    st.caption("Menggunakan aturan produksi IF-THEN dengan Certainty Factor (CF) dan agregasi paralel.")

    if st.button("🔍 Konsultasi Sistem Pakar", type="primary", use_container_width=True, key="btn_pakar"):
        hasil = SistemPakar.inferensi(dialog_input, kharisma_input, reputasi_input)
        st.session_state["pakar_hasil"] = hasil

    if "pakar_hasil" in st.session_state:
        hasil = st.session_state["pakar_hasil"]
        emosi_p  = hasil["emosi_terpilih"]
        skor_p   = hasil["skor"]
        cf_final = hasil["cf_final"]
        fakta    = hasil["fakta"]
        fired    = hasil["fired_rules"]

        # Fakta yang dikenali
        st.markdown("**🔎 Fakta yang Dikenali:**")
        fc1, fc2, fc3 = st.columns(3)
        fc1.info(f"🗣️ Dialog: **{fakta['dialog'].upper()}**")
        fc2.info(f"⭐ Kharisma: **{fakta['kharisma'].upper()}**")
        fc3.info(f"🏅 Reputasi: **{fakta['reputasi'].upper()}**")

        st.divider()
        tampilkan_hasil_emosi(skor_p, emosi_p)

        col_left, col_right = st.columns([1, 1])
        with col_left:
            st.pyplot(plot_cf_bar(cf_final))
        with col_right:
            for emosi_key, cf_val in cf_final.items():
                label = emosi_key.upper()
                st.metric(f"CF {label}", f"{cf_val:.4f}")

        st.divider()
        st.subheader(f"📋 Rule yang Aktif ({len(fired)} rule)")
        if fired:
            for r in fired:
                color_badge = {"marah": "🔴", "netral": "🟡", "senang": "🟢"}
                st.markdown(
                    f"**{r['id']}** {color_badge.get(r['emosi'], '⚪')} "
                    f"`CF={r['cf']:.2f}` → _{r['deskripsi']}_"
                )
        else:
            st.warning("Tidak ada rule yang aktif. Periksa nilai input.")

        with st.expander("ℹ️ Cara kerja sistem pakar ini"):
            st.markdown("""
**Komponen Sistem Pakar:**
- **Basis Pengetahuan** – 27 aturan produksi `IF kondisi THEN emosi` dengan CF (Certainty Factor).
- **Mesin Inferensi** – Forward Chaining: mulai dari **fakta** (nilai input dikategorikan), lalu cocokkan dengan antecedent rule.
- **Agregasi CF Paralel** – Jika beberapa rule mendukung emosi yang sama:
  `CF_gabungan = 1 − ∏(1 − CF_i)`
- **Keputusan** – Emosi dengan CF tertinggi dipilih sebagai output final.
- **Fasilitas Penjelasan** – Semua rule yang aktif ditampilkan (transparansi keputusan).

**Kategorisasi input (crisp):**
| Nilai | Dialog | Kharisma | Reputasi |
|-------|--------|----------|----------|
| ≤ 40  | Buruk  | Rendah   | Bermusuhan |
| 41–59 | Biasa  | Sedang   | Netral |
| ≥ 60  | Baik   | Tinggi   | Bersahabat |
""")

# ─────────────────────────────────────────────
# TAB 3 – PERBANDINGAN
# ─────────────────────────────────────────────
with tab_perbandingan:
    st.subheader("⚖️ Perbandingan Hasil Kedua Sistem")

    has_fuzzy = "fuzzy_skor"  in st.session_state
    has_pakar = "pakar_hasil" in st.session_state

    if not has_fuzzy and not has_pakar:
        st.info("Jalankan kedua sistem terlebih dahulu dari tab masing-masing untuk melihat perbandingan.")
    else:
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("### 🔮 Logika Fuzzy")
            if has_fuzzy:
                cfg = EMOSI_CONFIG[st.session_state["fuzzy_emosi"]]
                st.metric("Skor", f"{st.session_state['fuzzy_skor']:.1f}/100")
                st.metric("Emosi", f"{cfg['emoji']} {cfg['label']}")
            else:
                st.warning("Belum dihitung.")

        with c2:
            st.markdown("### 🧩 Sistem Pakar")
            if has_pakar:
                hasil_p = st.session_state["pakar_hasil"]
                cfg = EMOSI_CONFIG[hasil_p["emosi_terpilih"]]
                st.metric("Skor", f"{hasil_p['skor']:.1f}/100")
                st.metric("Emosi", f"{cfg['emoji']} {cfg['label']}")
            else:
                st.warning("Belum dikonsultasi.")

        if has_fuzzy and has_pakar:
            st.divider()
            emosi_f = st.session_state["fuzzy_emosi"]
            emosi_p = st.session_state["pakar_hasil"]["emosi_terpilih"]

            if emosi_f == emosi_p:
                st.success(f"✅ Kedua sistem **sepakat**: NPC akan **{emosi_f.upper()}**.")
            else:
                st.warning(
                    f"⚠️ Kedua sistem **berbeda pendapat**:\n"
                    f"- Fuzzy → **{emosi_f.upper()}**\n"
                    f"- Sistem Pakar → **{emosi_p.upper()}**\n\n"
                    f"Ini bisa terjadi karena fuzzy menangani gradasi nilai (mis. 59 masih 'cukup netral'), "
                    f"sedangkan sistem pakar melakukan kategorisasi tegas."
                )

            st.markdown("""
#### 📌 Kapan Menggunakan Mana?
| Aspek | Logika Fuzzy | Sistem Pakar |
|---|---|---|
| **Input** | Nilai kontinyu (0–100) | Kategori tegas |
| **Keputusan** | Gradasi / halus | Tegas / crisp |
| **Transparansi** | Sedang (MF + rule) | Tinggi (rule + CF terlihat) |
| **Kompleksitas** | Lebih tinggi | Lebih sedang |
| **Cocok untuk** | Simulasi realistis | Debuggable, auditabel |
""")

st.markdown("---")
st.caption("v2.0 · Fuzzy Mamdani (27 rules, trapmf) + Sistem Pakar Forward Chaining (27 rules, CF) · RPG NPC Emotion Engine")