import streamlit as st
import sys
import os
import re
import json
import pandas as pd
import requests

# Import tvé stávající třídy ze souboru hledat_kategorie.py
from hledat_kategorie import HeurekaAllInOne

st.set_page_config(
    page_title="Heureka PRODUCTNAME Validator",
    page_icon="🛠️",
    layout="centered"
)

# --- KONFIGURACE PROPOJENÍ NA GOOGLE FORMS & SHEETS ---
# Opravená URL adresa bez parametru ?submit=Submit, aby Google nehlásil chybu 401
FORM_SUBMIT_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdx_14tJk8-OKVj4z5LzywFWu9AYxNgWBe6G3JybgPHzQb-0g/formResponse"
ENTRY_SLOVO = "entry.58576357"
ENTRY_KAT = "entry.985762954"

# Odkaz na CSV export tvé Google tabulky (pro čtení naučených entit)
GSHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1rNi3o-glbbZJa_fepFaNWvbf1p2eyD7VZmYGCYT1tPk/pub?output=csv"

def nacti_naucene_entity_online():
    """Načte dříve schválená slova přímo z online Google Sheets tabulky."""
    vychozi = {"značka": [], "určení": [], "plemeno": [], "příchuť": [], "produktová řada": []}
    try:
        response = requests.get(GSHEET_CSV_URL, timeout=3)
        if response.status_code == 200:
            from io import StringIO
            df = pd.read_csv(StringIO(response.text))
            
            # Normalizace názvů sloupců (odstranění mezer, malá písmena)
            df.columns = [c.strip().lower() for c in df.columns]
            
            # Dynamické vyhledání sloupců podle tvé nové tabulky (Slovo, Kategorie)
            target_kat = "kategorie" if "kategorie" in df.columns else (df.columns[2] if len(df.columns) > 2 else df.columns[0])
            target_slovo = "slovo" if "slovo" in df.columns else (df.columns[1] if len(df.columns) > 1 else df.columns[0])

            for _, row in df.iterrows():
                if pd.isna(row[target_kat]) or pd.isna(row[target_slovo]):
                    continue
                kat = str(row[target_kat]).strip().lower()
                slovo = str(row[target_slovo]).strip().lower()
                
                # Zařazení do interních šuplíků podle klíčových slov
                if "výrobce" in kat or "značka" in kat:
                    kat_key = "značka"
                elif "věk" in kat or "určení" in kat:
                    kat_key = "určení"
                elif "plemeno" in kat or "velikost" in kat:
                    kat_key = "plemeno"
                elif "příchuť" in kat or "príchuť" in kat:
                    kat_key = "příchuť"
                else:
                    kat_key = "produktová řada"
                    
                if slovo and slovo != "nan" and slovo not in vychozi[kat_key]:
                    vychozi[kat_key].append(slovo)
        return vychozi
    except Exception:
        return vychozi

def uloz_naučenou_entitu_online(kategorie, hodnota):
    """Odešle nové slovo na pozadí přes Google Form rovnou do tvé Google tabulky s diagnostikou chyb."""
    cista_hodnota = hodnota.strip().lower()
    cista_kategorie = kategorie.strip().lower()
    
    # Příprava dat pro Google Form request
    form_data = {
        ENTRY_SLOVO: cista_hodnota,
        ENTRY_KAT: cista_kategorie
    }
    
    try:
        # Simulace odeslání formuláře na pozadí
        res = requests.post(FORM_SUBMIT_URL, data=form_data, timeout=4)
        
        # Pokud Google vrátí cokoli jiného než kód 200 (Úspěch), vypíšeme to červeně uživateli
        if res.status_code != 200:
            st.error(f"⚠️ Google Form odmítl zápis (Chybový status: {res.status_code}).")
            
        return res.status_code == 200
    except Exception as e:
        st.error(f"❌ Chyba sítě při odesílání: {e}")
        return False

# Bezpečné načtení online paměti z Google Sheets při startu
naucene_entity = nacti_naucene_entity_online()

@st.cache_resource
def nacti_nastroj():
    return HeurekaAllInOne()

nastroj = nacti_nastroj()

jazyk = st.radio(
    "🌐 Language / Jazyk:",
    options=["CZ", "EN"],
    horizontal=True
)

# --- DYNAMICKÝ PŘEKLADAČ ROZHRANÍ (CZ / EN) ---
if jazyk == "EN":
    txt = {
        "title": "🛠️ Heureka PRODUCTNAME Validator",
        "subtitle": "Product name check according to categories (Secured online version)",
        "desc": "Select the target Heureka category and then insert your product name.",
        "cat_label": "### 1️⃣ Search for the target Heureka category:",
        "cat_placeholder": "Type category name...",
        "cat_select_prompt": "👉 Select the exact match from found categories:",
        "cat_rules_title": "📌 **System rules defined for the chosen category:**",
        "structure_label": "**Defined name structure:**",
        "example_label": "**Real example pattern:**",
        "no_rule": "No rule is defined for this category yet.",
        "input_label": "### 2️⃣ Insert a real PRODUCTNAME from your e-shop to audit:",
        "input_placeholder": "Insert product name...",
        "heading_analysis": "### 🔍 Detailed Name Audit Results",
        "val_balast_found": "🔴 **Marketing ballast:** Remove forbidden words:",
        "val_info_note": "ℹ️ *The tool draws its live memory directly from your Google Sheets.*",
        "status_found": "✅ Found",
        "status_missing": "❌ Missing",
        "msg_missing_general": "Specification for segment '{}' is missing in the name.",
        "msg_missing_brand": "Manufacturer or Brand is missing in the product name.",
        "msg_missing_power": "Power specification (W) is missing in the product name.",
        "msg_missing_voltage": "Voltage specification (V) is missing in the product name.",
        "msg_missing_current": "Current specification (A/mAh) is missing in the product name.",
        "msg_missing_pct": "Percentage content expression (%) is missing.",
        "msg_missing_weight": "Weight or quantity (e.g. 12 kg) is missing.",
        "msg_missing_dim": "Dimension or metric value is missing.",
        "msg_missing_code": "Product code or type designation (e.g. CP1500) is missing.",
        "msg_missing_breed": "Breed size specification is missing.",
        "msg_missing_volume": "Volume specification is missing.",
        "msg_missing_pcs": "Number of pieces or package size is missing.",
        "msg_missing_year": "Four-digit model year is missing.",
        "msg_missing_color": "Color specification is missing.",
        "msg_missing_type": "Generic product type name is missing.",
        "msg_missing_comp": "Composition specification is missing.",
        "msg_missing_wheels": "Wheel type specification is missing.",
        "msg_missing_age": "Age designation (e.g. puppy, adult) is missing.",
        "msg_missing_func": "Functional feed designation is missing.",
        "msg_missing_flavor": "Detectable flavor is missing.",
        "msg_missing_line": "Product line for segment '{}' is missing.",
        "btn_learn": "Teach parameter online ✍️",
        "btn_learn_input": "Enter a word from the name that represents {}:",
        "btn_learn_submit": "Send online to Google Sheets",
        "btn_learn_success": "Parameter sent to your Google Sheets database! It will apply on next load.",
        "table_title": "### 📋 Clear Summary Table of the Audit:",
        "table_col1": "Segment", "table_col2": "Status", "table_col3": "Value / Note",
        "cat_err": "❌ No Heureka category was found for this expression."
    }
else:
    txt = {
        "title": "🛠️ Heureka PRODUCTNAME Validator",
        "subtitle": "Kontrola názvů produktů podle kategorií (Propojeno s Google Sheets)",
        "desc": "Vyberte cílovou kategorii na Heurece a následně vložte název produktu.",
        "cat_label": "### 1️⃣ Vyhledejte cílovou kategorii produktu na Heurece:",
        "cat_placeholder": "Zadejte hledanou kategorii...",
        "cat_select_prompt": "👉 Vyberte přesnou shodu z nalezených kategorií:",
        "cat_rules_title": "📌 **Systémová pravidla pro zvolenou kategorii:**",
        "structure_label": "**Definovaná struktura názvu:**",
        "example_label": "**Vzorový reálný příklad:**",
        "no_rule": "Pro tuto kategorii není definováno žádné pravidlo.",
        "input_label": "### 2️⃣ Nyní vložte reálný PRODUCTNAME z vašeho e-shopu k porovnání:",
        "input_placeholder": "Vložte název...",
        "heading_analysis": "### 🔍 Výsledek detailního auditu názvu",
        "val_balast_found": "🔴 **Marketingový balast:** Odstraňte zakázaná slova:",
        "val_info_note": "ℹ️ *Nástroj čerpá živou paměť přímo z vaší Google Sheets tabulky.*",
        "status_found": "✅ Nalezeno",
        "status_missing": "❌ Chybí",
        "msg_missing_general": "V názvu chybí specifikace pro segment '{}'",
        "msg_missing_brand": "V názvu chybí výrobce či značka.",
        "msg_missing_power": "V názvu chybí specifikace výkonu (W).",
        "msg_missing_voltage": "V názvu chybí specifikace napětí (V).",
        "msg_missing_current": "V názvu chybí intenzita proudové složky (A/mAh).",
        "msg_missing_pct": "V názvu chybí procentuální vyjádření obsahu (%).",
        "msg_missing_weight": "V názvu chybí hmotnost nebo množství (např. 12 kg).",
        "msg_missing_dim": "V názvu chybí rozměrový nebo metrický údaj.",
        "msg_missing_code": "V názvu chybí produktový kód nebo typové označení (např. CP1500).",
        "msg_missing_breed": "V názvu chybí určení velikosti plemene.",
        "msg_missing_volume": "V názvu chybí specifikace objemu.",
        "msg_missing_pcs": "V názvu chybí počet kusů nebo balení.",
        "msg_missing_year": "V názvu chybí čtyřmístný modelový rok.",
        "msg_missing_color": "V názvu chybí specifikace barvy.",
        "msg_missing_type": "V názvu chybí druhový název produktu.",
        "msg_missing_comp": "V názvu chybí specifikace složení.",
        "msg_missing_wheels": "V názvu chybí specifikace typu kol.",
        "msg_missing_age": "V názvu chybí určení věku (např. puppy, adult).",
        "msg_missing_func": "V názvu chybí funkční označení krmiva.",
        "msg_missing_flavor": "V názvu chybí detekovatelná příchuť.",
        "msg_missing_line": "V názvu chybí produktová řada pro segment '{}'.",
        "btn_learn": "Naučit nástroj parametr online ✍️",
        "btn_learn_input": "Zadejte slovo z názvu, které reprezentuje {}:",
        "btn_learn_submit": "Odeslat do Google Sheets",
        "btn_learn_success": "Parametr byl odeslán do vaší Google Sheets databáze! Projeví se při dalším načtení.",
        "table_title": "### 📋 Přehledná výsledná tabulka auditu:",
        "table_col1": "Segment", "table_col2": "Stav", "table_col3": "Hodnota / Poznámka",
        "cat_err": "❌ Pro tento výraz nebyla nalezena žádná Heureka kategorie."
    }

@st.cache_data
def nacti_surova_pravidla_přimo_ze_souboru(lang):
    nazev_souboru = "pravidla_en.txt" if lang == "EN" else "pravidla.txt"
    cesta_k_souboru = os.path.join(os.path.dirname(os.path.abspath(__file__)), nazev_souboru)
    if not os.path.exists(cesta_k_souboru):
        cesta_k_souboru = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pravidla.txt")
    if not os.path.exists(cesta_k_souboru):
        return []
    try:
        with open(cesta_k_souboru, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except:
        return []

surova_pravidla = nacti_surova_pravidla_přimo_ze_souboru(jazyk)

@st.cache_data
def extrahuj_zname_znacky(pravidla_list):
    znacky = set()
    zakazana_krata_slova = ["baterie", "set", "software", "pouzdro", "obal", "autopotah", "dětská", "dětský", "příkrm", "pro", "proti", "nad", "pod", "v", "se", "na", "s", "za", "kočárek", "kočík", "battery", "case", "cover"]
    for radek in pravidla_list:
        casti_hlavni = re.split(r'\s*[–——|]\s*|\s*-\s*', radek.strip(), maxsplit=1)
        if len(casti_hlavni) > 1:
            zbytek = casti_hlavni[1].strip()
            casti_prikladu = re.split(r'\s*[–—-]\s*(?=[^|]*$)', zbytek, maxsplit=1)
            if len(casti_prikladu) > 1:
                priklad = casti_prikladu[1].strip()
                prvni_slovo = priklad.split()[0].strip("!,.:-–—")
                if len(prvni_slovo) > 1 and prvni_slovo.lower() not in zakazana_krata_slova:
                    znacky.add(prvni_slovo.lower())
    return znacky

zname_znacky_db = extrahuj_zname_znacky(surova_pravidla)

# --- SLOVNÍKY PARAMETRŮ ---
SLOVNIK_BAREV = ["černá", "černý", "čorná", "černé", "black", "bílá", "bílý", "bílé", "white", "červená", "červený", "červené", "red", "modrá", "modrý", "modré", "blue", "stříbrná", "stříbrný", "silver", "šedá", "šedý", "grey", "gray", "zlatá", "zlatý", "gold", "růžová", "růžový", "pink", "zelená", "zelený", "green", "žlutá", "žlutý", "yellow", "nerez", "nerezová", "chrom", "chromová", "antracit", "antracitová", "fialová", "fialový", "purple", "oranžová", "oranžový", "orange", "béžová", "béžový", "beige", "graphite", "grafit", "grafitová", "tonal"]
SLOVNIK_KOL = ["nafukovací", "pěnová", "pěnové", "plastová", "plastové", "gelová", "gelové", "gumová", "gumové", "otočná", "pevná", "nafukovacie", "penové", "plastové", "gélové", "gumené"]
SLOVNIK_VEKU = ["adult", "adults", "kitten", "kittens", "junior", "juniors", "senior", "seniors", "mature", "geriatric", "kotě", "štěně", "štěňata", "štěňat", "štěňatům", "mačiatko", "šteňa", "šteňatá", "šteňatám", "pro štěňata", "pre šteňatá", "pro dospělé", "pre dospelých"]
PLEMENO_REGEXY = [
    r"\b(pro\s+)?velk(á|é|ých|ým)\s+plemen(a|o|ům)?\b", r"\b(pro\s+)?středn(í|ích|ím)\s+plemen(a|o|ům)?\b",
    r"\b(pro\s+)?mal(á|é|ých|ým)\s+plemen(a|o|ům)?\b", r"\b(pro\s+)?obř(í|ích)\s+plemen(a|o|ům)?\b",
    r"\b(pro\s+)?(mini|maxi|medium|giant|small|large)\s+(breed|plemena|plemeno)?\b", r"\b(pro\s+)?(velké|malé|střední)\s+psy\b"
]
SLOVNIK_OZNACENI = ["aktivní", "sterilizované", "kastrované", "venkovní", "indoor", "outdoor", "sterilised", "sensitive", "light", "hairball", "urinary", "gastrointestinal", "hypoallergenic"]
SLOVNIK_PRICHUTI = ["kuřecí", "hovězí", "losos", "tuňák", "kachna", "krůtí", "jehněčí", "ryba", "králík", "vepřové", "zvěřina", "srnčí", "divočák", "kuře", "hovädzie", "morčacie", "jahňacie", "králik", "ryby", "kuracie", "lamb", "rice", "salmon", "chicken", "beef", "turkey"]
POVOLENE_RADY_CHOVATELSTVI = ["breed", "nutrition", "care", "life", "fitmin", "premium", "plus", "active", "mini", "medium", "maxi", "giant", "sensitive", "hypoallergenic", "life care"]
SLOVNIK_OBECNE_VATY = ["wireless", "bluetooth", "usb", "charging", "charger", "adapter", "cable", "power", "smart", "herní", "gaming", "nabíjecí", "univerzální", "universal", "originální", "original", "dětský", "dětská", "víceúčelový", "kombinovaný", "sportovní", "kočárek", "příkrm", "autosedačka", "pouzdro", "kryt", "obal", "case", "cover", "sklo", "glass", "ochranné", "náhradní", "sada", "set", "pack", "mini", "max", "pro", "plus", "standardní", "standard", "klasický", "klasická", "classic", "běžný", "běžná", "nový", "nová", "new", "top", "retro", "všestranný", "žehlicí", "prkno", "excentrická", "excentrický", "úhlová", "úhlový", "vibrační", "pásová", "pásový", "kotoučová", "kotoučový", "přímočará", "přímočarý", "pokosová", "stolní", "ruční", "bruska", "brúsky", "akumulátorová", "aku", "elektrická", "elektrický", "mokré", "suché", "šťavnaté", "krmivo", "granule", "konzerva", "kapsička", "mix", "příchuť", "plemen", "rasy", "jehněčí", "rýže", "dog", "fototiskárna", "tiskárna"]
METRICKE_JEDNOTKY = ["cm", "mm", "m", "w", "v", "g", "kg", "l", "ml", "cl"]

st.title(txt["title"])
st.subheader(txt["subtitle"])
st.write(txt["desc"])
st.divider()

st.markdown(txt["cat_label"])
hledany_vyraz_kat = st.text_input("vyhledavac_kategorie_input", placeholder=txt["cat_placeholder"], label_visibility="collapsed")

if hledany_vyraz_kat.strip():
    shody_kategorii = nastroj.vyhledej_presnou_logikou(hledany_vyraz_kat.strip())
    
    if shody_kategorii:
        nalezeny_seznam_cest = [shoda['cesta'] for shoda in shody_kategorii if shoda.get('cesta')]
        st.write("")
        st.markdown(txt["cat_select_prompt"])
        
        vybrana_cesta = st.selectbox("Nalezené kategorie:", options=["-- Vyberte přesnou kategorii --"] + nalezeny_seznam_cest, index=0, label_visibility="collapsed")
        
        if vybrana_cesta and vybrana_cesta != "-- Vyberte přesnou kategorii --":
            koncova_kat_surova = vybrana_cesta.split('|')[-1].strip()
            koncova_kat = koncova_kat_surova.lower()
            
            pravidlo_vyrez, priklad_vyrez = None, None
            for radek in surova_pravidla:
                if isinstance(radek, str) and radek.strip():
                    casti_hlavni = re.split(r'\s*[–——|]\s*|\s*-\s*', radek.strip(), maxsplit=1)
                    if casti_hlavni and casti_hlavni[0].strip().lower() == koncova_kat:
                        zbytek_radku = casti_hlavni[1].strip() if len(casti_hlavni) > 1 else ""
                        casti_prikladu = re.split(r'\s*[–—-]\s*(?=[^|]*$)', zbytek_radku, maxsplit=1)
                        if len(casti_prikladu) > 1:
                            pravidlo_vyrez, priklad_vyrez = casti_prikladu[0].strip(), casti_prikladu[1].strip()
                        else:
                            pravidlo_vyrez = zbytek_radku
                        break
            
            st.write("")
            st.markdown(txt["cat_rules_title"])
            st.info(f"`{vybrana_cesta}`")
            
            if pravidlo_vyrez:
                obsah_boxu = f"{txt['structure_label']} `{pravidlo_vyrez}`"
                if priklad_vyrez: obsah_boxu += f"\n\n{txt['example_label']} **{priklad_vyrez}**"
                st.warning(obsah_boxu)
                
                st.divider()
                st.markdown(txt["input_label"])
                jmeno_input = st.text_input("vstupni_pole_validator", placeholder=txt["input_placeholder"], label_visibility="collapsed", key="vstupni_pole_validator")
                
                if jmeno_input.strip():
                    jmeno = jmeno_input.strip()
                    jmeno_lower = jmeno.lower()
                    
                    balast_list = ["akce", "akčná", "sleva", "zľava", "výprodej", "výpredaj", "doprava zdarma", "poštovné zdarma", "skladem", "skladom", "novinka", "tip", "sale", "free shipping", "action"]
                    nalezeny_balast = [b for b in balast_list if b in jmeno_lower]
                    if "!" in jmeno: nalezeny_balast.append("!")
                        
                    if nalezeny_balast:
                        st.error(f"{txt['val_balast_found']} `{'`, `'.join(set(nalezeny_balast))}`.")
                    
                    segmenty_pravidla = [s.strip() for s in pravidlo_vyrez.split('|') if s.strip()]
                    zbyvajici_text_jmena = jmeno
                    
                    kmeny_kategorie = [w[:4] for w in koncova_kat.split() if len(w) > 3 and w not in ["pro", "proti", "nad", "pod", "dětské", "dětský"]]
                    ma_obecne_slovo_kategorie = False
                    slova_docasna = zbyvajici_text_jmena.split()
                    for skl in slova_docasna:
                        skl_low = skl.lower().strip("!,.:-–—()")
                        for kmen in kmeny_kategorie:
                            if skl_low.startswith(kmen):
                                ma_obecne_slovo_kategorie = True
                                zbyvajici_text_jmena = zbyvajici_text_jmena.replace(skl, "", 1)
                                break
                    
                    # --- EXTRAKCE PARAMETRŮ ---
                    match_rozmer_x = re.search(r'\b\d+[\s]*(?:mm|cm|m)?[\s]*[xX✕vV][\s]*\d+[\s]*(?:mm|cm|m)?\b', zbyvajici_text_jmena)
                    val_rozmer_x = match_rozmer_x.group(0) if match_rozmer_x else None
                    if val_rozmer_x: zbyvajici_text_jmena = zbyvajici_text_jmena.replace(val_rozmer_x, "", 1)

                    match_vykon = re.search(r'\b\d+[\s]*[Ww]\b', zbyvajici_text_jmena)
                    val_vykon = match_vykon.group(0) if match_vykon else None
                    if val_vykon: zbyvajici_text_jmena = zbyvajici_text_jmena.replace(val_vykon, "", 1)

                    match_napeti = re.search(r'\b\d+(?:[\s,.]\d+)?[\s]*[Vv]\b', zbyvajici_text_jmena)
                    val_napeti = match_napeti.group(0) if match_napeti else None
                    if val_napeti: zbyvajici_text_jmena = zbyvajici_text_jmena.replace(val_napeti, "", 1)

                    match_proud = re.search(r'\b\d+[\s]*(?:[Aa]|mAh|mah)\b', zbyvajici_text_jmena)
                    val_proud = match_proud.group(0) if match_proud else None
                    if val_proud: zbyvajici_text_jmena = zbyvajici_text_jmena.replace(val_proud, "", 1)

                    match_procenta = re.search(r'\b\d+[\s]*%', zbyvajici_text_jmena)
                    val_procenta = match_procenta.group(0) if match_procenta else None
                    if val_procenta: zbyvajici_text_jmena = zbyvajici_text_jmena.replace(val_procenta, "", 1)

                    match_delka = re.search(r'\b\d+(?:-\d+)?[\s]*(?:mm|cm|m|U|l|cl|ml)\b', zbyvajici_text_jmena)
                    val_delka = match_delka.group(0) if match_delka else None
                    if val_delka: zbyvajici_text_jmena = zbyvajici_text_jmena.replace(val_delka, "", 1)

                    match_vahu = re.search(r'\b\d+(?:[\s,.]\d+)?[\s]*(?:g|kg|g/m2|g/m²)\b', zbyvajici_text_jmena)
                    val_vahu = match_vahu.group(0) if match_vahu else None
                    if val_vahu: zbyvajici_text_jmena = zbyvajici_text_jmena.replace(val_vahu, "", 1)

                    match_kusy = re.search(r'\b\d+[\s]*(?:ks|kus|kusů|lic|licencí|porcí|tbl|balení|pack)\b', zbyvajici_text_jmena, re.IGNORECASE)
                    val_kusy = match_kusy.group(0) if match_kusy else None
                    if val_kusy: zbyvajici_text_jmena = zbyvajici_text_jmena.replace(val_kusy, "", 1)

                    match_rok = re.search(r'\b20[0-2][0-9]\b', zbyvajici_text_jmena)
                    val_rok = match_rok.group(0) if match_rok else None
                    if val_rok: zbyvajici_text_jmena = zbyvajici_text_jmena.replace(val_rok, "", 1)

                    match_kod = re.search(r'\b[A-Za-z]+\d+[A-Za-z]*\b|\b[A-Z0-9]{2,}-[A-Z0-9]{3,}(?:-[A-Z0-9]+)?\b|\b[A-Z0-9]{4,}\/[A-Z0-9]{2,}\b', zbyvajici_text_jmena)
                    val_kod = match_kod.group(0) if match_kod else None
                    if val_kod: zbyvajici_text_jmena = zbyvajici_text_jmena.replace(val_kod, "", 1)
                    
                    val_barva = None
                    slova_pro_barvu = zbyvajici_text_jmena.lower().split()
                    for barva in SLOVNIK_BAREV:
                        if barva in slova_pro_barvu:
                            match_b_tvar = re.search(r'\b' + re.escape(barva) + r'\b', zbyvajici_text_jmena, re.IGNORECASE)
                            if match_b_tvar:
                                val_barva = match_b_tvar.group(0)
                                zbyvajici_text_jmena = zbyvajici_text_jmena.replace(val_barva, "", 1)
                                break
                    
                    # DETEKCE ZNAČKY S ONLINE PAMĚTÍ
                    val_znacka = None
                    for znacka in list(zname_znacky_db) + naucene_entity.get("značka", []):
                        if len(znacka) > 2:
                            token_regex = re.search(r'\b' + re.escape(znacka) + r'\b', zbyvajici_text_jmena, re.IGNORECASE)
                            if token_regex and token_regex.group(0).lower() not in SLOVNIK_OBECNE_VATY:
                                val_znacka = token_regex.group(0)
                                zbyvajici_text_jmena = zbyvajici_text_jmena.replace(val_znacka, "", 1)
                                break
                    
                    if not val_znacka:
                        slova_zbytkova_brand = [s.strip("!,.:-–—() ") for s in zbyvajici_text_jmena.split() if s.strip()]
                        for s in slova_zbytkova_brand:
                            if s and s[0].isupper() and not s.isdigit() and len(s) > 2 and s.lower() not in SLOVNIK_OBECNE_VATY:
                                val_znacka = s
                                zbyvajici_text_jmena = zbyvajici_text_jmena.replace(val_znacka, "", 1)
                                break

                    st.write("")
                    st.markdown(f"### {txt['heading_analysis']}")
                    
                    data_pro_tabulku = []
                    
                    for seg in segmenty_pravidla:
                        cisty_nazev_seg = re.split(r'\s*[–-]\s*', seg)[0].strip()
                        seg_lower = cisty_nazev_seg.lower()
                        
                        nalezeny_obsah = None
                        typ_chyby_msg = txt["msg_missing_general"].format(cisty_nazev_seg)
                        
                        if "výrobce" in seg_lower or "značka" in seg_lower: m_key = "značka"
                        elif "věk" in seg_lower or "určení" in seg_lower: m_key = "určení"
                        elif "plemeno" in seg_lower or "velikost" in seg_lower: m_key = "plemeno"
                        elif "příchuť" in seg_lower or "príchuť" in seg_lower: m_key = "příchuť"
                        else: m_key = "produktová řada"
                        
                        naucene_pro_tento_seg = naucene_entity.get(m_key, [])
                        for n_word in naucene_pro_tento_seg:
                            if n_word in zbyvajici_text_jmena.lower():
                                match_n = re.search(r'\b' + re.escape(n_word) + r'\b', zbyvajici_text_jmena, re.IGNORECASE)
                                if match_n:
                                    nalezeny_obsah = match_n.group(0)
                                    zbyvajici_text_jmena = zbyvajici_text_jmena.replace(nalezeny_obsah, "", 1)
                                    break
                        
                        if not nalezeny_obsah:
                            if "výrobce" in seg_lower or "značka" in seg_lower:
                                if val_znacka: nalezeny_obsah = val_znacka
                                else: typ_chyby_msg = txt["msg_missing_brand"]
                            elif "výkon" in seg_lower:
                                if val_vykon: nalezeny_obsah = val_vykon
                                else: typ_chyby_msg = txt["msg_missing_power"]
                            elif "napětí" in seg_lower:
                                if val_napeti: nalezeny_obsah = val_napeti
                                else: typ_chyby_msg = txt["msg_missing_voltage"]
                            elif "proud" in seg_lower:
                                if val_proud: nalezeny_obsah = val_proud
                                else: typ_chyby_msg = txt["msg_missing_current"]
                            elif "alkohol" in seg_lower or "%" in seg_lower:
                                if val_procenta: nalezeny_obsah = val_procenta
                                else: typ_chyby_msg = txt["msg_missing_pct"]
                            elif "množství" in seg_lower or "hmotnost" in seg_lower or "váha" in seg_lower or "gramáž" in seg_lower:
                                hodnota_vahy_baleni = val_vahu if val_vahu else val_kusy
                                if hodnota_vahy_baleni: nalezeny_obsah = hodnota_vahy_baleni
                                else: typ_chyby_msg = txt["msg_missing_weight"]
                            elif "rozměr" in seg_lower or "šířka" in seg_lower or "délka" in seg_lower or "průměr" in seg_lower:
                                hodnota_rozmeru = val_rozmer_x if val_rozmer_x else val_delka
                                if hodnota_rozmeru and not ("složení" in seg_lower): nalezeny_obsah = hodnota_rozmeru
                                else: typ_chyby_msg = txt["msg_missing_dim"]
                            elif "číslo" in seg_lower or "kód" in seg_lower or "iso" in seg_lower or "typové označení" in seg_lower or "typové" in seg_lower:
                                if val_kod: nalezeny_obsah = val_kod
                                else: typ_chyby_msg = txt["msg_missing_code"]
                            elif "velikost" in seg_lower or "velikost plemene" in seg_lower or "plemeno" in seg_lower:
                                nalezena_vel = None
                                for p_regex in PLEMENO_REGEXY:
                                    match_v = re.search(p_regex, zbyvajici_text_jmena, re.IGNORECASE)
                                    if match_v: nalezena_vel = match_v.group(0); break
                                if nalezena_vel:
                                    nalezeny_obsah = nalezena_vel
                                    zbyvajici_text_jmena = zbyvajici_text_jmena.replace(nalezena_vel, "", 1)
                                else: typ_chyby_msg = txt["msg_missing_breed"]
                            elif "objem" in seg_lower:
                                if val_delka: nalezeny_obsah = val_delka
                                else: typ_chyby_msg = txt["msg_missing_volume"]
                            elif "kusů" in seg_lower or "balení" in seg_lower or "licenc" in seg_lower or "porcí" in seg_lower:
                                if val_kusy: nalezeny_obsah = val_kusy
                                else: typ_chyby_msg = txt["msg_missing_pcs"]
                            elif "rok" in seg_lower or "ročník" in seg_lower:
                                if val_rok: nalezeny_obsah = val_rok
                                else: typ_chyby_msg = txt["msg_missing_year"]
                            elif "barva" in seg_lower or "odstín" in seg_lower or "varianta" in seg_lower:
                                if val_barva: nalezeny_obsah = val_barva
                                else: typ_chyby_msg = txt["msg_missing_color"]
                            elif "název" in seg_lower or "druh" in seg_lower or "podrobnější" in seg_lower:
                                if ma_obecne_slovo_kategorie: nalezeny_obsah = "Určeno názvem kategorie" if jazyk == "CZ" else "Determined by category name"
                                else: typ_chyby_msg = txt["msg_missing_type"]
                            elif "složení" in seg_lower:
                                if val_rozmer_x: nalezeny_obsah = val_rozmer_x
                                else: typ_chyby_msg = txt["msg_missing_comp"]
                            else:
                                slova_zbytkova = [w.strip("!,.:-–—()+ ") for w in zbyvajici_text_jmena.split() if w.strip()]
                                slova_zbytkova = [w for w in slova_zbytkova if w.lower() not in ["pro", "sedící", "děti", "a", "s", "v", "kočárek", "kočík", "for", "with"]]
                                
                                if "kol" in seg_lower:
                                    nalezene_kolo = None
                                    for k_word in slova_zbytkova:
                                        if k_word.lower() in SLOVNIK_KOL: nalezene_kolo = k_word; break
                                    if nalezene_kolo:
                                        nalezeny_obsah = nalezene_kolo
                                        zbyvajici_text_jmena = zbyvajici_text_jmena.replace(nalezene_kolo, "", 1)
                                    else: typ_chyby_msg = txt["msg_missing_wheels"]
                                elif "věk" in seg_lower or "určení" in seg_lower:
                                    zbyvajici_text_lower = zbyvajici_text_jmena.lower()
                                    nalezeny_vek = None
                                    for v_word in sorted(SLOVNIK_VEKU, key=len, reverse=True):
                                        if v_word in zbyvajici_text_lower:
                                            match_v = re.search(r'\b' + re.escape(v_word) + r'\b', zbyvajici_text_jmena, re.IGNORECASE)
                                            if match_v: nalezeny_vek = match_v.group(0); break
                                    if nalezeny_vek:
                                        nalezeny_obsah = nalezeny_vek
                                        zbyvajici_text_jmena = zbyvajici_text_jmena.replace(nalezeny_vek, "", 1)
                                    else: typ_chyby_msg = txt["msg_missing_age"]
                                elif "označení" in seg_lower or "specifikace" in seg_lower:
                                    nalezene_ozn = None
                                    for o_word in slova_zbytkova:
                                        if o_word.lower() in SLOVNIK_OZNACENI: nalezene_ozn = o_word; break
                                    if nalezene_ozn:
                                        nalezeny_obsah = nalezene_ozn
                                        zbyvajici_text_jmena = zbyvajici_text_jmena.replace(nalezene_ozn, "", 1)
                                    else: typ_chyby_msg = txt["msg_missing_func"]
                                elif "příchuť" in seg_lower or "príchuť" in seg_lower:
                                    zbyvajici_text_lower = zbyvajici_text_jmena.lower()
                                    nalezena_prichut = None
                                    for p_word in sorted(SLOVNIK_PRICHUTI, key=len, reverse=True):
                                        if p_word in zbyvajici_text_lower:
                                            match_p = re.search(r'\b' + re.escape(p_word) + r'\b', zbyvajici_text_jmena, re.IGNORECASE)
                                            if match_p: nalezena_prichut = match_p.group(0); break
                                    if nalezena_prichut:
                                        nalezeny_obsah = nalezena_prichut
                                        zbyvajici_text_jmena = zbyvajici_text_jmena.replace(nalezena_prichut, "", 1)
                                    else: typ_chyby_msg = txt["msg_missing_flavor"]
                                else:
                                    regularni_slovo = None
                                    kandidati = [w for w in slova_zbytkova if w.lower() not in SLOVNIK_OBECNE_VATY and w.lower() not in METRICKE_JEDNOTKY and w.lower() not in SLOVNIK_VEKU and w.lower() not in SLOVNIK_OZNACENI and w.lower() not in SLOVNIK_PRICHUTI]
                                    if kandidati:
                                        potencialni_rada = kandidati[0]
                                        je_kod = bool(re.search(r'(?=.*[A-Za-z])(?=.*\d)', potencialni_rada))
                                        je_znama_rada = potencialni_rada.lower() in POVOLENE_RADY_CHOVATELSTVI
                                        if je_kod or je_znama_rada:
                                            idx_v_puvodnim = slova_zbytkova.index(potencialni_rada)
                                            uceleny_blok = [potencialni_rada]
                                            for i in range(1, 3):
                                                if idx_v_puvodnim + i < len(slova_zbytkova):
                                                    dalsi_slovo = slova_zbytkova[idx_v_puvodnim + i]
                                                    if dalsi_slovo.isdigit() or dalsi_slovo.lower() in ["care", "nutrition", "plus", "premium", "life"]:
                                                        uceleny_blok.append(dalsi_slovo)
                                            regularni_slovo = " ".join(uceleny_blok)
                                    if regularni_slovo:
                                        nalezeny_obsah = regularni_slovo
                                        for slot in uceleny_blok: zbyvajici_text_jmena = zbyvajici_text_jmena.replace(slot, "", 1)
                                    else: typ_chyby_msg = txt["msg_missing_line"].format(cisty_nazev_seg)
                        
                        if nalezeny_obsah:
                            st.success(f"**{cisty_nazev_seg}: {txt['status_found']}**\n\n➔ `{nalezeny_obsah}`")
                            data_pro_tabulku.append({txt["table_col1"]: cisty_nazev_seg, txt["table_col2"]: txt["status_found"], txt["table_col3"]: nalezeny_obsah})
                        else:
                            st.error(f"**{cisty_nazev_seg}: {txt['status_missing']}**\n\n➔ *{typ_chyby_msg}*")
                            data_pro_tabulku.append({txt["table_col1"]: cisty_nazev_seg, txt["table_col2"]: txt["status_missing"], txt["table_col3"]: typ_chyby_msg})
                            
                            with st.expander(txt["btn_learn"]):
                                text_k_nauceni = st.text_input(
                                    txt["btn_learn_input"].format(cisty_nazev_seg), 
                                    key=f"input_override_{cisty_nazev_seg}_{seg}"
                                )
                                if st.button(txt["btn_learn_submit"], key=f"btn_override_{cisty_nazev_seg}_{seg}"):
                                    if text_k_nauceni.strip():
                                        if uloz_naučenou_entitu_online(m_key, text_k_nauceni):
                                            st.success(txt["btn_learn_success"])
                                            st.cache_data.clear()
                                            st.rerun()
                                            
                    st.write("")
                    st.markdown(txt["table_title"])
                    df_vysledky = pd.DataFrame(data_pro_tabulku)
                    st.dataframe(df_vysledky, use_container_width=True, hide_index=True)
                                            
                    st.write("")
                    st.markdown(txt["val_info_note"])
            else:
                st.error(txt["no_rule"])
    else:
        st.error(txt["cat_err"])