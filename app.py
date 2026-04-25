import streamlit as st
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

st.set_page_config(page_title="Emosi NPC RPG", page_icon="🧙", layout="wide")
st.title("🧠 Sistem Emosi NPC RPG")

PERTANYAAN = [
    {
        "id": "q1", "nomor": 1,
        "konteks": "🗣️ Pembukaan Percakapan",
        "teks": "Bagaimana cara pemain **memulai percakapan** dengan NPC ini?",
        "pilihan": [
            {"label": "🤝 Menyapa dengan ramah dan menggunakan nama/gelar NPC",
             "efek": {"dialog": 35, "kharisma": 20}, "fakta": "pembukaan_ramah"},
            {"label": "💬 Langsung ke inti pembicaraan tanpa basa-basi",
             "efek": {"dialog": 15}, "fakta": "pembukaan_netral"},
            {"label": "😤 Berbicara dengan nada tinggi atau terkesan menuntut",
             "efek": {"dialog": -20, "kharisma": -15}, "fakta": "pembukaan_kasar"},
        ],
    },
    {
        "id": "q2", "nomor": 2,
        "konteks": "🏰 Riwayat dengan Faksi NPC",
        "teks": "Apa **riwayat hubungan** pemain dengan faksi NPC ini sebelumnya?",
        "pilihan": [
            {"label": "🌟 Pernah membantu faksi beberapa kali (quest, donasi, dll.)",
             "efek": {"reputasi": 45}, "fakta": "riwayat_bersahabat"},
            {"label": "🤷 Belum pernah berinteraksi dengan faksi ini",
             "efek": {"reputasi": 0}, "fakta": "riwayat_netral"},
            {"label": "⚔️ Pernah menyerang atau mengkhianati anggota faksi",
             "efek": {"reputasi": -40}, "fakta": "riwayat_bermusuhan"},
        ],
    },
    {
        "id": "q3", "nomor": 3,
        "konteks": "📜 Bukti dan Kredensial",
        "teks": "Apakah pemain membawa **kredensial** yang diakui faksi (surat, lencana, simbol)?",
        "pilihan": [
            {"label": "✅ Ya — membawa simbol resmi atau surat rekomendasi dari tokoh faksi",
             "efek": {"reputasi": 25, "kharisma": 10}, "fakta": "bawa_kredensial"},
            {"label": "📦 Ada, tapi hanya barang biasa tanpa nilai khusus bagi faksi",
             "efek": {"reputasi": 5}, "fakta": "bawa_biasa"},
            {"label": "❌ Tidak membawa apa-apa",
             "efek": {}, "fakta": "tanpa_kredensial"},
        ],
    },
    {
        "id": "q4", "nomor": 4,
        "konteks": "⭐ Reputasi Umum di Wilayah",
        "teks": "Bagaimana **reputasi pemain** secara umum di wilayah NPC ini?",
        "pilihan": [
            {"label": "🦸 Pahlawan / tokoh terhormat yang dikenal luas",
             "efek": {"kharisma": 35, "reputasi": 10}, "fakta": "reputasi_pahlawan"},
            {"label": "🧑 Orang biasa, tidak dikenal secara khusus",
             "efek": {"kharisma": 5}, "fakta": "reputasi_biasa"},
            {"label": "💀 Buronan / penjahat yang dikenal negatif di wilayah ini",
             "efek": {"kharisma": -30, "reputasi": -15}, "fakta": "reputasi_buruk"},
        ],
    },
    {
        "id": "q5", "nomor": 5,
        "konteks": "🎯 Tujuan Pembicaraan",
        "teks": "Apa **tujuan utama** pemain datang berbicara dengan NPC ini?",
        "pilihan": [
            {"label": "🤲 Menawarkan bantuan atau kerja sama yang menguntungkan faksi",
             "efek": {"dialog": 25, "reputasi": 15}, "fakta": "tujuan_bantu"},
            {"label": "🗺️ Mencari informasi, quest, atau transaksi biasa",
             "efek": {"dialog": 10}, "fakta": "tujuan_netral"},
            {"label": "🔫 Menuntut sesuatu, memberikan ultimatum, atau mengancam",
             "efek": {"dialog": -25, "kharisma": -10}, "fakta": "tujuan_mengancam"},
        ],
    },
    {
        "id": "q6", "nomor": 6,
        "konteks": "🎁 Tawaran atau Imbalan",
        "teks": "Apakah pemain **menawarkan sesuatu** yang bernilai dalam pembicaraan ini?",
        "pilihan": [
            {"label": "💎 Ya — menawarkan hadiah berharga, informasi eksklusif, atau emas",
             "efek": {"dialog": 20, "kharisma": 15}, "fakta": "tawaran_berharga"},
            {"label": "🪙 Ya — menawarkan sesuatu tapi nilainya biasa saja",
             "efek": {"dialog": 8}, "fakta": "tawaran_biasa"},
            {"label": "🤚 Tidak menawarkan apapun",
             "efek": {}, "fakta": "tanpa_tawaran"},
        ],
    },
    {
        "id": "q7", "nomor": 7,
        "konteks": "👂 Sikap Saat NPC Berbicara",
        "teks": "Bagaimana sikap pemain saat **NPC sedang berbicara**?",
        "pilihan": [
            {"label": "🙏 Mendengarkan dengan penuh perhatian dan merespons dengan tepat",
             "efek": {"kharisma": 20, "dialog": 15}, "fakta": "sikap_mendengarkan"},
            {"label": "😐 Mendengarkan seperlunya, respons standar",
             "efek": {"kharisma": 5}, "fakta": "sikap_netral"},
            {"label": "🙄 Sering memotong pembicaraan atau terlihat tidak sabar",
             "efek": {"kharisma": -20, "dialog": -10}, "fakta": "sikap_memotong"},
        ],
    },
    {
        "id": "q8", "nomor": 8,
        "konteks": "🔤 Pilihan Kata dan Bahasa",
        "teks": "Bagaimana **kualitas pilihan kata** yang digunakan pemain?",
        "pilihan": [
            {"label": "📖 Menggunakan bahasa formal yang menghormati budaya dan nilai faksi",
             "efek": {"dialog": 20, "kharisma": 10}, "fakta": "kata_baik"},
            {"label": "💬 Bahasa sehari-hari, tidak ada yang menyinggung",
             "efek": {"dialog": 10}, "fakta": "kata_biasa"},
            {"label": "🤬 Menggunakan kata-kata yang menyinggung atau tabu bagi faksi",
             "efek": {"dialog": -25, "reputasi": -10}, "fakta": "kata_buruk"},
        ],
    },
]

SKOR_AWAL = {"dialog": 50, "kharisma": 50, "reputasi": 50}

RULES_PAKAR = [
    ("R01", {"dialog": "buruk",  "kharisma": "rendah", "reputasi": "bermusuhan"}, "marah",  1.00, "Semua faktor negatif — pasti marah"),
    ("R02", {"dialog": "buruk",  "kharisma": "sedang", "reputasi": "bermusuhan"}, "marah",  0.90, "Dialog buruk + reputasi bermusuhan — marah"),
    ("R03", {"dialog": "buruk",  "kharisma": "tinggi", "reputasi": "bermusuhan"}, "marah",  0.75, "Dialog buruk + bermusuhan, kharisma sedikit membantu — marah"),
    ("R04", {"dialog": "buruk",  "kharisma": "rendah", "reputasi": "netral"},     "marah",  0.85, "Dialog buruk + kharisma rendah + reputasi netral — marah"),
    ("R05", {"dialog": "buruk",  "kharisma": "sedang", "reputasi": "netral"},     "marah",  0.70, "Dialog buruk + reputasi netral — marah"),
    ("R06", {"dialog": "buruk",  "kharisma": "tinggi", "reputasi": "netral"},     "netral", 0.70, "Dialog buruk tapi kharisma tinggi + netral — netral"),
    ("R07", {"dialog": "buruk",  "kharisma": "rendah", "reputasi": "bersahabat"},"netral", 0.75, "Dialog buruk tapi punya reputasi baik — netral"),
    ("R08", {"dialog": "buruk",  "kharisma": "sedang", "reputasi": "bersahabat"},"netral", 0.80, "Dialog buruk + reputasi bersahabat + sedang — netral"),
    ("R09", {"dialog": "buruk",  "kharisma": "tinggi", "reputasi": "bersahabat"},"netral", 0.80, "Dialog buruk tapi semua faktor lain baik — netral"),
    ("R10", {"dialog": "biasa",  "kharisma": "rendah", "reputasi": "bermusuhan"}, "marah",  0.85, "Dialog biasa + kharisma rendah + bermusuhan — marah"),
    ("R11", {"dialog": "biasa",  "kharisma": "sedang", "reputasi": "bermusuhan"}, "marah",  0.75, "Dialog biasa + reputasi bermusuhan — cenderung marah"),
    ("R12", {"dialog": "biasa",  "kharisma": "tinggi", "reputasi": "bermusuhan"}, "netral", 0.70, "Dialog biasa + kharisma tinggi tapi bermusuhan — netral"),
    ("R13", {"dialog": "biasa",  "kharisma": "rendah", "reputasi": "netral"},     "marah",  0.65, "Dialog biasa + kharisma rendah + netral — cenderung marah"),
    ("R14", {"dialog": "biasa",  "kharisma": "sedang", "reputasi": "netral"},     "netral", 0.80, "Dialog biasa + semua sedang — netral"),
    ("R15", {"dialog": "biasa",  "kharisma": "tinggi", "reputasi": "netral"},     "senang", 0.75, "Dialog biasa + kharisma tinggi + netral — senang"),
    ("R16", {"dialog": "biasa",  "kharisma": "rendah", "reputasi": "bersahabat"},"netral", 0.70, "Dialog biasa + reputasi bagus tapi kharisma rendah — netral"),
    ("R17", {"dialog": "biasa",  "kharisma": "sedang", "reputasi": "bersahabat"},"senang", 0.80, "Dialog biasa + reputasi bersahabat + sedang — senang"),
    ("R18", {"dialog": "biasa",  "kharisma": "tinggi", "reputasi": "bersahabat"},"senang", 0.90, "Dialog biasa + semua faktor lain baik — senang"),
    ("R19", {"dialog": "baik",   "kharisma": "rendah", "reputasi": "bermusuhan"}, "netral", 0.75, "Dialog baik tapi reputasi buruk + kharisma rendah — netral"),
    ("R20", {"dialog": "baik",   "kharisma": "sedang", "reputasi": "bermusuhan"}, "netral", 0.80, "Dialog baik + kharisma sedang tapi bermusuhan — netral"),
    ("R21", {"dialog": "baik",   "kharisma": "tinggi", "reputasi": "bermusuhan"}, "senang", 0.70, "Dialog baik + kharisma tinggi mengatasi reputasi buruk — senang"),
    ("R22", {"dialog": "baik",   "kharisma": "rendah", "reputasi": "netral"},     "netral", 0.70, "Dialog baik + reputasi netral tapi kharisma rendah — netral"),
    ("R23", {"dialog": "baik",   "kharisma": "sedang", "reputasi": "netral"},     "senang", 0.85, "Dialog baik + reputasi netral + kharisma sedang — senang"),
    ("R24", {"dialog": "baik",   "kharisma": "tinggi", "reputasi": "netral"},     "senang", 0.90, "Dialog baik + kharisma tinggi + netral — sangat senang"),
    ("R25", {"dialog": "baik",   "kharisma": "rendah", "reputasi": "bersahabat"},"senang", 0.80, "Dialog baik + reputasi bagus walaupun kharisma rendah — senang"),
    ("R26", {"dialog": "baik",   "kharisma": "sedang", "reputasi": "bersahabat"},"senang", 0.95, "Dialog baik + semua faktor positif — sangat senang"),
    ("R27", {"dialog": "baik",   "kharisma": "tinggi", "reputasi": "bersahabat"},"senang", 1.00, "Semua faktor positif — pasti senang"),
]

def kategorikan(skor):
    if skor < 40: return "rendah"
    elif skor > 60: return "tinggi"
    else: return "sedang"

def kategorikan_dialog(skor):
    if skor < 40: return "buruk"
    elif skor > 60: return "baik"
    else: return "biasa"

def kategorikan_reputasi(skor):
    if skor < 40: return "bermusuhan"
    elif skor > 60: return "bersahabat"
    else: return "netral"

def inferensi_pakar(skor_dialog, skor_kharisma, skor_reputasi):
    kategori = {
        "dialog":   kategorikan_dialog(skor_dialog),
        "kharisma": kategorikan(skor_kharisma),
        "reputasi": kategorikan_reputasi(skor_reputasi),
    }
    cf_emosi = {"marah": [], "netral": [], "senang": []}
    fired = []
    for rule_id, kondisi, emosi_out, cf, deskripsi in RULES_PAKAR:
        if all(kategori.get(k) == v for k, v in kondisi.items()):
            cf_emosi[emosi_out].append(cf)
            fired.append({"id": rule_id, "emosi": emosi_out, "cf": cf, "deskripsi": deskripsi})
    cf_final = {}
    for emosi_key, cf_list in cf_emosi.items():
        if not cf_list:
            cf_final[emosi_key] = 0.0
        else:
            hasil = 1.0
            for c in cf_list:
                hasil *= (1.0 - c)
            cf_final[emosi_key] = round(1.0 - hasil, 4)
    emosi_terpilih = max(cf_final, key=cf_final.get)
    total = sum(cf_final.values())
    skor_0_100 = round((cf_final[emosi_terpilih] / max(total, 0.001)) * 100, 1)
    return {"kategori": kategori, "fired_rules": fired,
            "cf_final": cf_final, "emosi_terpilih": emosi_terpilih, "skor": skor_0_100}

@st.cache_resource
def create_fuzzy_system():
    dialog   = ctrl.Antecedent(np.arange(0, 101, 1), "dialog")
    kharisma = ctrl.Antecedent(np.arange(0, 101, 1), "kharisma")
    reputasi = ctrl.Antecedent(np.arange(0, 101, 1), "reputasi")
    emosi    = ctrl.Consequent(np.arange(0, 101, 1), "emosi", defuzzify_method="centroid")
    dialog["buruk"]  = fuzz.trapmf(dialog.universe,   [0, 0, 25, 45])
    dialog["biasa"]  = fuzz.trimf(dialog.universe,    [30, 50, 70])
    dialog["baik"]   = fuzz.trapmf(dialog.universe,   [55, 75, 100, 100])
    kharisma["rendah"] = fuzz.trapmf(kharisma.universe, [0, 0, 25, 45])
    kharisma["sedang"] = fuzz.trimf(kharisma.universe,  [30, 50, 70])
    kharisma["tinggi"] = fuzz.trapmf(kharisma.universe, [55, 75, 100, 100])
    reputasi["bermusuhan"] = fuzz.trapmf(reputasi.universe, [0, 0, 25, 45])
    reputasi["netral"]     = fuzz.trimf(reputasi.universe,  [30, 50, 70])
    reputasi["bersahabat"] = fuzz.trapmf(reputasi.universe, [55, 75, 100, 100])
    emosi["marah"]  = fuzz.trapmf(emosi.universe, [0, 0, 25, 45])
    emosi["netral"] = fuzz.trimf(emosi.universe,  [30, 50, 70])
    emosi["senang"] = fuzz.trapmf(emosi.universe, [55, 75, 100, 100])
    rules = [
        ctrl.Rule(dialog["buruk"]  & reputasi["bermusuhan"] & kharisma["rendah"], emosi["marah"]),
        ctrl.Rule(dialog["buruk"]  & reputasi["bermusuhan"] & kharisma["sedang"], emosi["marah"]),
        ctrl.Rule(dialog["buruk"]  & reputasi["bermusuhan"] & kharisma["tinggi"], emosi["marah"]),
        ctrl.Rule(dialog["buruk"]  & reputasi["netral"]     & kharisma["rendah"], emosi["marah"]),
        ctrl.Rule(dialog["buruk"]  & reputasi["netral"]     & kharisma["sedang"], emosi["marah"]),
        ctrl.Rule(dialog["buruk"]  & reputasi["netral"]     & kharisma["tinggi"], emosi["netral"]),
        ctrl.Rule(dialog["buruk"]  & reputasi["bersahabat"] & kharisma["rendah"], emosi["netral"]),
        ctrl.Rule(dialog["buruk"]  & reputasi["bersahabat"] & kharisma["sedang"], emosi["netral"]),
        ctrl.Rule(dialog["buruk"]  & reputasi["bersahabat"] & kharisma["tinggi"], emosi["netral"]),
        ctrl.Rule(dialog["biasa"]  & reputasi["bermusuhan"] & kharisma["rendah"], emosi["marah"]),
        ctrl.Rule(dialog["biasa"]  & reputasi["bermusuhan"] & kharisma["sedang"], emosi["marah"]),
        ctrl.Rule(dialog["biasa"]  & reputasi["bermusuhan"] & kharisma["tinggi"], emosi["netral"]),
        ctrl.Rule(dialog["biasa"]  & reputasi["netral"]     & kharisma["rendah"], emosi["marah"]),
        ctrl.Rule(dialog["biasa"]  & reputasi["netral"]     & kharisma["sedang"], emosi["netral"]),
        ctrl.Rule(dialog["biasa"]  & reputasi["netral"]     & kharisma["tinggi"], emosi["senang"]),
        ctrl.Rule(dialog["biasa"]  & reputasi["bersahabat"] & kharisma["rendah"], emosi["netral"]),
        ctrl.Rule(dialog["biasa"]  & reputasi["bersahabat"] & kharisma["sedang"], emosi["senang"]),
        ctrl.Rule(dialog["biasa"]  & reputasi["bersahabat"] & kharisma["tinggi"], emosi["senang"]),
        ctrl.Rule(dialog["baik"]   & reputasi["bermusuhan"] & kharisma["rendah"], emosi["netral"]),
        ctrl.Rule(dialog["baik"]   & reputasi["bermusuhan"] & kharisma["sedang"], emosi["netral"]),
        ctrl.Rule(dialog["baik"]   & reputasi["bermusuhan"] & kharisma["tinggi"], emosi["senang"]),
        ctrl.Rule(dialog["baik"]   & reputasi["netral"]     & kharisma["rendah"], emosi["netral"]),
        ctrl.Rule(dialog["baik"]   & reputasi["netral"]     & kharisma["sedang"], emosi["senang"]),
        ctrl.Rule(dialog["baik"]   & reputasi["netral"]     & kharisma["tinggi"], emosi["senang"]),
        ctrl.Rule(dialog["baik"]   & reputasi["bersahabat"] & kharisma["rendah"], emosi["senang"]),
        ctrl.Rule(dialog["baik"]   & reputasi["bersahabat"] & kharisma["sedang"], emosi["senang"]),
        ctrl.Rule(dialog["baik"]   & reputasi["bersahabat"] & kharisma["tinggi"], emosi["senang"]),
    ]
    return ctrl.ControlSystem(rules), dialog, kharisma, reputasi, emosi

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

def plot_mf(var, nilai_input, judul):
    fig, ax = plt.subplots(figsize=(5, 2.8))
    colors = {"buruk": "#e74c3c", "biasa": "#f39c12", "baik": "#2ecc71",
              "rendah": "#e74c3c", "sedang": "#f39c12", "tinggi": "#2ecc71",
              "bermusuhan": "#e74c3c", "netral": "#f39c12", "bersahabat": "#2ecc71",
              "marah": "#e74c3c", "senang": "#2ecc71"}
    patches = []
    for term in var.terms:
        c = colors.get(term, "steelblue")
        ax.plot(var.universe, var[term].mf, color=c, linewidth=2)
        ax.fill_between(var.universe, var[term].mf, alpha=0.15, color=c)
        patches.append(mpatches.Patch(color=c, label=term))
    ax.axvline(x=nilai_input, color="navy", linestyle="--", linewidth=1.5)
    ax.set_title(judul, fontsize=10, fontweight="bold")
    ax.set_xlabel("Nilai (0-100)", fontsize=8)
    ax.set_ylabel("Keanggotaan", fontsize=8)
    ax.set_ylim(-0.05, 1.15)
    ax.legend(handles=patches + [plt.Line2D([0],[0],color="navy",linestyle="--",
              label=f"Input={nilai_input:.0f}")], fontsize=7, loc="upper right")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig

def plot_cf_bar(cf_final):
    fig, ax = plt.subplots(figsize=(5, 2.5))
    emosi_list = list(cf_final.keys())
    bars = ax.barh(emosi_list, [cf_final[e] for e in emosi_list],
                   color=["#e74c3c","#f39c12","#2ecc71"], edgecolor="white", height=0.5)
    for bar, val in zip(bars, [cf_final[e] for e in emosi_list]):
        ax.text(val+0.01, bar.get_y()+bar.get_height()/2,
                f"{val:.3f}", va="center", fontsize=9, fontweight="bold")
    ax.set_xlim(0, 1.15)
    ax.set_xlabel("Certainty Factor (CF)", fontsize=9)
    ax.set_title("Keyakinan Sistem Pakar per Emosi", fontsize=10, fontweight="bold")
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    return fig

def plot_radar(d, k, r):
    labels  = ["Dialog", "Kharisma", "Reputasi"]
    values  = [d, k, r]
    angles  = np.linspace(0, 2*np.pi, 3, endpoint=False).tolist()
    values += values[:1]; angles += angles[:1]
    fig, ax = plt.subplots(figsize=(3.5, 3.5), subplot_kw=dict(polar=True))
    ax.plot(angles, values, "o-", linewidth=2, color="#3498db")
    ax.fill(angles, values, alpha=0.2, color="#3498db")
    ax.set_xticks(angles[:-1]); ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylim(0, 100); ax.set_yticks([25,50,75,100])
    ax.set_yticklabels(["25","50","75","100"], fontsize=7)
    ax.axhline(y=40, color="#e74c3c", linestyle="--", alpha=0.5, linewidth=1)
    ax.axhline(y=60, color="#2ecc71", linestyle="--", alpha=0.5, linewidth=1)
    ax.set_title("Profil Skor Pemain", fontsize=10, fontweight="bold", pad=15)
    fig.tight_layout()
    return fig

def reset_pakar():
    st.session_state["sp_step"]  = 0
    st.session_state["sp_skor"]  = dict(SKOR_AWAL)
    st.session_state["sp_fakta"] = []
    st.session_state["sp_log"]   = []
    st.session_state["sp_hasil"] = None

for k, v in [("sp_step",0),("sp_skor",dict(SKOR_AWAL)),
             ("sp_fakta",[]),("sp_log",[]),("sp_hasil",None),("fuzzy_done",False)]:
    if k not in st.session_state:
        st.session_state[k] = v

tab_pakar, tab_fuzzy, tab_banding = st.tabs([
    "🧩 Sistem Pakar (Konsultasi)",
    "🔮 Logika Fuzzy",
    "⚖️ Perbandingan",
])

# ── TAB 1: SISTEM PAKAR ──────────────────────────────────────────────────────
with tab_pakar:
    st.subheader("🧩 Konsultasi Sistem Pakar NPC")
    st.caption("Sistem pakar mengajukan 8 pertanyaan situasional. Jawaban Anda membentuk basis fakta untuk menentukan emosi NPC.")

    step    = st.session_state["sp_step"]
    total_q = len(PERTANYAAN)

    if step == 0:
        st.info("""
**Cara kerja konsultasi:**
1. Sistem mengajukan **8 pertanyaan** tentang situasi interaksi pemain dengan NPC.
2. Setiap jawaban mengumpulkan fakta dan mempengaruhi skor `Dialog`, `Kharisma`, `Reputasi`.
3. Setelah selesai, **forward chaining** mencocokkan fakta dengan 27 aturan produksi.
4. **Certainty Factor (CF)** diagregasi — emosi NPC ditentukan.
5. Seluruh chain penalaran ditampilkan secara transparan.
        """)
        if st.button("▶️ Mulai Konsultasi", type="primary", use_container_width=True):
            reset_pakar()
            st.session_state["sp_step"] = 1
            st.rerun()

    elif 1 <= step <= total_q:
        q = PERTANYAAN[step - 1]
        st.progress(step / total_q, text=f"Pertanyaan {step} dari {total_q}")

        sc = st.session_state["sp_skor"]
        g1, g2, g3 = st.columns(3)
        def d(v): return f"{v-50:+.0f}" if v != 50 else None
        g1.metric("🗣️ Dialog",   f"{sc['dialog']:.0f}/100",   delta=d(sc['dialog']))
        g2.metric("⭐ Kharisma", f"{sc['kharisma']:.0f}/100", delta=d(sc['kharisma']))
        g3.metric("🏅 Reputasi", f"{sc['reputasi']:.0f}/100", delta=d(sc['reputasi']))

        st.divider()
        st.markdown(f"#### {q['konteks']}")
        st.markdown(f"**❓ {q['teks']}**")
        st.markdown("")

        for idx, pilihan in enumerate(q["pilihan"]):
            if st.button(pilihan["label"], key=f"q{step}_p{idx}", use_container_width=True):
                for dim, delta in pilihan["efek"].items():
                    st.session_state["sp_skor"][dim] = max(0, min(100,
                        st.session_state["sp_skor"][dim] + delta))
                st.session_state["sp_fakta"].append(pilihan["fakta"])
                efek_str = ", ".join(f"{k} {v:+d}" for k,v in pilihan["efek"].items()) if pilihan["efek"] else "tidak ada efek"
                st.session_state["sp_log"].append({
                    "nomor": q["nomor"], "konteks": q["konteks"],
                    "jawaban": pilihan["label"], "efek": efek_str, "fakta": pilihan["fakta"],
                })
                st.session_state["sp_step"] += 1
                st.rerun()

        if step > 1:
            st.markdown("")
            if st.button("⬅️ Kembali ke pertanyaan sebelumnya", use_container_width=True):
                if st.session_state["sp_log"]:
                    last = st.session_state["sp_log"].pop()
                    st.session_state["sp_fakta"].pop()
                    skor_baru = dict(SKOR_AWAL)
                    for entry in st.session_state["sp_log"]:
                        q_idx = entry["nomor"] - 1
                        for pil in PERTANYAAN[q_idx]["pilihan"]:
                            if pil["fakta"] == entry["fakta"]:
                                for dim, delta in pil["efek"].items():
                                    skor_baru[dim] = max(0, min(100, skor_baru[dim] + delta))
                                break
                    st.session_state["sp_skor"] = skor_baru
                st.session_state["sp_step"] -= 1
                st.rerun()

    else:
        sc = st.session_state["sp_skor"]
        if st.session_state["sp_hasil"] is None:
            st.session_state["sp_hasil"] = inferensi_pakar(sc["dialog"], sc["kharisma"], sc["reputasi"])

        hasil = st.session_state["sp_hasil"]
        st.success("✅ Konsultasi selesai! Berikut hasil diagnosis sistem pakar.")

        st.subheader("📊 Skor Akhir Pemain")
        cr, cs = st.columns([1.2, 0.8])
        with cr:
            c1, c2, c3 = st.columns(3)
            c1.metric("🗣️ Dialog",   f"{sc['dialog']:.0f}/100")
            c2.metric("⭐ Kharisma", f"{sc['kharisma']:.0f}/100")
            c3.metric("🏅 Reputasi", f"{sc['reputasi']:.0f}/100")
            kat = hasil["kategori"]
            st.info(f"Kategori: Dialog **{kat['dialog'].upper()}** · Kharisma **{kat['kharisma'].upper()}** · Reputasi **{kat['reputasi'].upper()}**")
            st.markdown("> *Batas: < 40 buruk/rendah/bermusuhan | 40–60 biasa/sedang/netral | > 60 baik/tinggi/bersahabat*")
        with cs:
            st.pyplot(plot_radar(sc["dialog"], sc["kharisma"], sc["reputasi"]))

        st.divider()
        st.subheader("🎭 Diagnosis Emosi NPC")
        tampilkan_hasil_emosi(hasil["skor"], hasil["emosi_terpilih"])

        badge = {"marah": "🔴", "netral": "🟡", "senang": "🟢"}
        col_cf, col_bar = st.columns(2)
        with col_cf:
            for ek, cv in hasil["cf_final"].items():
                st.metric(f"{badge[ek]} CF {ek.upper()}", f"{cv:.4f}")
        with col_bar:
            st.pyplot(plot_cf_bar(hasil["cf_final"]))

        st.divider()
        st.subheader(f"🔗 Chain Penalaran — {len(hasil['fired_rules'])} Rule Aktif")
        for r in hasil["fired_rules"]:
            st.markdown(f"**{r['id']}** {badge.get(r['emosi'],'⚪')} `CF={r['cf']:.2f}` → _{r['deskripsi']}_")
        if not hasil["fired_rules"]:
            st.warning("Tidak ada rule yang aktif.")

        with st.expander("📋 Riwayat Jawaban dan Efek Skor"):
            for entry in st.session_state["sp_log"]:
                st.markdown(
                    f"**Q{entry['nomor']}** — {entry['konteks']}  \n"
                    f"Jawaban: _{entry['jawaban']}_  \n"
                    f"Efek skor: `{entry['efek']}` · Fakta: `{entry['fakta']}`"
                )
                st.markdown("---")

        with st.expander("ℹ️ Cara kerja mesin inferensi"):
            st.markdown("""
**Forward Chaining — Langkah per Langkah:**
1. **Akuisisi Fakta** — Tiap jawaban menambah skor ke dimensi dialog, kharisma, reputasi.
2. **Kategorisasi** — Skor akhir dikelompokkan ke kelas linguistik (< 40 / 40–60 / > 60).
3. **Pencocokan Rule** — 27 aturan produksi dievaluasi. Rule yang antecedent-nya cocok dinyatakan aktif (fired).
4. **Agregasi CF Paralel** — Untuk emosi yang sama: `CF_gabung = 1 − ∏(1 − CFᵢ)`.
5. **Keputusan** — Emosi dengan CF gabungan tertinggi dipilih sebagai output.
            """)

        st.divider()
        if st.button("🔄 Ulangi Konsultasi", use_container_width=True):
            reset_pakar()
            st.rerun()

# ── TAB 2: FUZZY ─────────────────────────────────────────────────────────────
with tab_fuzzy:
    st.subheader("🔮 Inferensi Logika Fuzzy (Mamdani)")
    st.caption("Input nilai numerik 0–100 langsung ke mesin fuzzy.")

    c1, c2, c3 = st.columns(3)
    with c1: dialog_in   = st.slider("🗣️ Kualitas Dialog (0–100)",  0, 100, 60)
    with c2: kharisma_in = st.slider("⭐ Kharisma Pemain (0–100)",  0, 100, 50)
    with c3: reputasi_in = st.slider("🏅 Reputasi Faksi (0–100)",   0, 100, 40)

    st.subheader("🎮 Contoh Skenario Cepat")
    ex_cols = st.columns(5)
    examples = {"Pujian tulus":(85,70,60),"Ancaman keras":(15,30,20),
                "Tanya info quest":(70,55,50),"Hina faksi":(10,25,10),"Minta bantuan":(80,80,65)}
    for col, (label, (d,k,r)) in zip(ex_cols, examples.items()):
        if col.button(label, use_container_width=True, key=f"ex_{label}"):
            dialog_in=d; kharisma_in=k; reputasi_in=r
            st.rerun()

    if st.button("💬 Hitung dengan Fuzzy", type="primary", use_container_width=True):
        with st.spinner("Menghitung..."):
            try:
                cs_, dv, kv, rv, ev = create_fuzzy_system()
                sim = ctrl.ControlSystemSimulation(cs_)
                sim.input["dialog"]   = dialog_in
                sim.input["kharisma"] = kharisma_in
                sim.input["reputasi"] = reputasi_in
                sim.compute()
                sf = sim.output["emosi"]
                ef = "marah" if sf < 40 else ("netral" if sf <= 60 else "senang")
                st.session_state.update({
                    "fuzzy_skor": sf, "fuzzy_emosi": ef,
                    "fuzzy_inputs": (dialog_in, kharisma_in, reputasi_in),
                    "fuzzy_vars": (dv, kv, rv, ev), "fuzzy_done": True,
                })
            except Exception as e:
                st.error(f"Error: {e}")
                st.info("Coba geser slider dari nilai batas tepat (mis. 40 → 38 atau 42).")

    if st.session_state.get("fuzzy_done"):
        sf = st.session_state["fuzzy_skor"]
        ef = st.session_state["fuzzy_emosi"]
        di, ki, ri = st.session_state["fuzzy_inputs"]
        dv, kv, rv, ev = st.session_state["fuzzy_vars"]
        tampilkan_hasil_emosi(sf, ef)
        st.subheader("📈 Visualisasi Fungsi Keanggotaan")
        ca, cb = st.columns(2)
        with ca:
            st.pyplot(plot_mf(dv, di, "Dialog"))
            st.pyplot(plot_mf(kv, ki, "Kharisma"))
        with cb:
            st.pyplot(plot_mf(rv, ri, "Reputasi"))
            st.pyplot(plot_mf(ev, sf, "Output: Emosi"))

# ── TAB 3: PERBANDINGAN ───────────────────────────────────────────────────────
with tab_banding:
    st.subheader("⚖️ Perbandingan Hasil Kedua Sistem")
    has_fuzzy = st.session_state.get("fuzzy_done", False)
    has_pakar = st.session_state.get("sp_hasil") is not None

    if not has_fuzzy and not has_pakar:
        st.info("Jalankan konsultasi sistem pakar dan/atau hitung fuzzy terlebih dahulu.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 🧩 Sistem Pakar")
            if has_pakar:
                hp = st.session_state["sp_hasil"]
                cfg = EMOSI_CONFIG[hp["emosi_terpilih"]]
                st.metric("Emosi",        f"{cfg['emoji']} {cfg['label']}")
                st.metric("Skor",         f"{hp['skor']:.1f}/100")
                st.metric("CF tertinggi", f"{max(hp['cf_final'].values()):.4f}")
            else:
                st.warning("Konsultasi sistem pakar belum selesai.")
        with c2:
            st.markdown("### 🔮 Logika Fuzzy")
            if has_fuzzy:
                cfg = EMOSI_CONFIG[st.session_state["fuzzy_emosi"]]
                di, ki, ri = st.session_state["fuzzy_inputs"]
                st.metric("Emosi", f"{cfg['emoji']} {cfg['label']}")
                st.metric("Skor",  f"{st.session_state['fuzzy_skor']:.1f}/100")
                st.metric("Input", f"D={di} · K={ki} · R={ri}")
            else:
                st.warning("Fuzzy belum dihitung.")

        if has_fuzzy and has_pakar:
            st.divider()
            ef = st.session_state["fuzzy_emosi"]
            ep = st.session_state["sp_hasil"]["emosi_terpilih"]
            if ef == ep:
                st.success(f"✅ Kedua sistem **sepakat**: NPC akan **{ef.upper()}**.")
            else:
                st.warning(
                    f"⚠️ Kedua sistem **berbeda pendapat**:\n"
                    f"- Sistem Pakar → **{ep.upper()}**\n"
                    f"- Logika Fuzzy → **{ef.upper()}**\n\n"
                    "Fuzzy menangani gradasi nilai secara kontinyu, "
                    "sementara sistem pakar mengkategorikan secara tegas."
                )

        st.markdown("""
#### 📌 Perbedaan Utama Kedua Pendekatan

| Aspek | Sistem Pakar | Logika Fuzzy |
|---|---|---|
| **Input** | Tanya-jawab pilihan ganda (8 pertanyaan) | Nilai numerik slider (0–100) |
| **Proses** | Forward chaining + Certainty Factor | Fuzzifikasi → Evaluasi rule → Defuzzifikasi |
| **Output** | Kategori tegas + skor CF | Skor kontinyu 0–100 |
| **Transparansi** | Tinggi (rule aktif + riwayat jawaban) | Sedang (perlu baca grafik MF) |
| **Kemudahan input** | Intuitif, cocok untuk pengguna non-teknis | Perlu estimasi nilai numerik |
| **Cocok untuk** | Sistem konsultasi, auditabel | Simulasi realtime, game engine |
        """)

st.markdown("---")
st.caption("v3.0 · Sistem Pakar (8 pertanyaan, 27 rules, CF forward chaining) + Fuzzy Mamdani (27 rules, trapmf)")