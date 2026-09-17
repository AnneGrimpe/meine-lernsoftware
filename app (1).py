import streamlit as st
import random
from datetime import datetime, timezone
from supabase import create_client

st.set_page_config(
    page_title="Meine Lernsoftware",
    page_icon="📚",
    layout="centered"
)


# ==================================================
# SUPABASE-VERBINDUNG
# ==================================================

@st.cache_resource
def supabase_verbinden():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_SECRET_KEY"]
    except KeyError:
        st.error(
            "Die Supabase-Zugangsdaten fehlen. "
            "Trage SUPABASE_URL und SUPABASE_SECRET_KEY "
            "in den Streamlit-Secrets ein."
        )
        st.stop()

    return create_client(url, key)


supabase = supabase_verbinden()


# ==================================================
# STARTDATEN
# ==================================================

def startdaten_anlegen():
    standardfaecher = [
        "Buchführung",
        "Excel",
        "Recht",
        "Kaufmännische Kommunikation",
        "Geschäftsprozesse"
    ]

    vorhandene = supabase.table("faecher").select("name").execute().data
    vorhandene_namen = {eintrag["name"] for eintrag in vorhandene}

    fehlende = [
        {"name": fach}
        for fach in standardfaecher
        if fach not in vorhandene_namen
    ]

    if fehlende:
        supabase.table("faecher").insert(fehlende).execute()


def beispiel_pruefungsfragen_anlegen():
    vorhandene = (
        supabase.table("pruefungsfragen")
        .select("id")
        .limit(1)
        .execute()
        .data
    )

    if vorhandene:
        return

    beispiele = [
        {
            "fach": "Recht",
            "frage": "Was beschreibt den Besitz?",
            "antwort_a": "Die rechtliche Herrschaft über eine Sache",
            "antwort_b": "Die tatsächliche Herrschaft über eine Sache",
            "antwort_c": "Das Recht, eine Sache zu verkaufen",
            "antwort_d": "Die vollständige Bezahlung einer Sache",
            "richtig": "B",
            "erklaerung": "Besitz bedeutet die tatsächliche Herrschaft über eine Sache."
        },
        {
            "fach": "Recht",
            "frage": "Welches Beispiel ist ein einseitiges Rechtsgeschäft?",
            "antwort_a": "Kaufvertrag",
            "antwort_b": "Mietvertrag",
            "antwort_c": "Kündigung",
            "antwort_d": "Werkvertrag",
            "richtig": "C",
            "erklaerung": "Bei einer Kündigung genügt grundsätzlich die Willenserklärung einer Seite."
        },
        {
            "fach": "Buchführung",
            "frage": "Was ist eine Bilanz?",
            "antwort_a": "Eine Gegenüberstellung von Vermögen und Kapital",
            "antwort_b": "Eine Liste aller Kunden",
            "antwort_c": "Eine Rechnung an einen Lieferanten",
            "antwort_d": "Eine Aufstellung nur der Schulden",
            "richtig": "A",
            "erklaerung": "Die Bilanz stellt Aktiva und Passiva zu einem bestimmten Zeitpunkt gegenüber."
        },
        {
            "fach": "Excel",
            "frage": "Welche Funktion addiert mehrere Zahlen oder Zellbereiche?",
            "antwort_a": "WENN",
            "antwort_b": "SUMME",
            "antwort_c": "ZÄHLENWENN",
            "antwort_d": "MITTELWERTWENN",
            "richtig": "B",
            "erklaerung": "SUMME wird zum Addieren von Zahlen und Zellbereichen verwendet."
        },
        {
            "fach": "Geschäftsprozesse",
            "frage": "Was beschreibt das Minimalprinzip?",
            "antwort_a": "Mit festen Mitteln den größtmöglichen Erfolg erzielen",
            "antwort_b": "Ein festgelegtes Ziel mit möglichst wenig Mitteln erreichen",
            "antwort_c": "Möglichst viele Produkte herstellen",
            "antwort_d": "Die Kosten unabhängig vom Ziel erhöhen",
            "richtig": "B",
            "erklaerung": "Beim Minimalprinzip ist das Ziel vorgegeben und der Mitteleinsatz soll möglichst gering sein."
        }
    ]

    supabase.table("pruefungsfragen").insert(beispiele).execute()


# ==================================================
# LERNFÄCHER
# ==================================================

def faecher_laden():
    daten = (
        supabase.table("faecher")
        .select("name")
        .order("name")
        .execute()
        .data
    )

    return [eintrag["name"] for eintrag in daten]


def fach_hinzufuegen(name):
    name = name.strip()

    if not name:
        return False, "Bitte gib einen Namen ein."

    try:
        supabase.table("faecher").insert({"name": name}).execute()
        return True, "Lernfach wurde erstellt."
    except Exception as fehler:
        if "duplicate" in str(fehler).lower() or "unique" in str(fehler).lower():
            return False, "Dieses Lernfach gibt es bereits."
        return False, f"Das Lernfach konnte nicht gespeichert werden: {fehler}"


def fach_umbenennen(alter_name, neuer_name):
    neuer_name = neuer_name.strip()

    if not neuer_name:
        return False, "Bitte gib einen Namen ein."

    if alter_name == neuer_name:
        return False, "Der Name wurde nicht geändert."

    try:
        # Erst prüfen, ob der neue Name bereits existiert.
        vorhanden = (
            supabase.table("faecher")
            .select("id")
            .eq("name", neuer_name)
            .execute()
            .data
        )

        if vorhanden:
            return False, "Ein Fach mit diesem Namen existiert bereits."

        supabase.table("faecher").update(
            {"name": neuer_name}
        ).eq("name", alter_name).execute()

        supabase.table("karten").update(
            {"fach": neuer_name}
        ).eq("fach", alter_name).execute()

        supabase.table("bewertungen").update(
            {"fach": neuer_name}
        ).eq("fach", alter_name).execute()

        supabase.table("pruefungsfragen").update(
            {"fach": neuer_name}
        ).eq("fach", alter_name).execute()

        return True, "Lernfach wurde umbenannt."

    except Exception as fehler:
        return False, f"Das Lernfach konnte nicht umbenannt werden: {fehler}"


def fach_loeschen(name):
    karten = (
        supabase.table("karten")
        .select("id")
        .eq("fach", name)
        .execute()
        .data
    )

    bewertungen = (
        supabase.table("bewertungen")
        .select("id")
        .eq("fach", name)
        .execute()
        .data
    )

    pruefungsfragen = (
        supabase.table("pruefungsfragen")
        .select("id")
        .eq("fach", name)
        .execute()
        .data
    )

    if karten or bewertungen or pruefungsfragen:
        return False, (
            "Das Fach kann noch nicht gelöscht werden. "
            "Es enthält noch Lernkarten, Lernergebnisse oder Prüfungsfragen."
        )

    supabase.table("faecher").delete().eq("name", name).execute()
    return True, "Lernfach wurde gelöscht."


# ==================================================
# KARTEIKARTEN
# ==================================================

def karten_laden(fach):
    daten = (
        supabase.table("karten")
        .select("id, frage, antwort")
        .eq("fach", fach)
        .order("id")
        .execute()
        .data
    )

    return [
        (eintrag["id"], eintrag["frage"], eintrag["antwort"])
        for eintrag in daten
    ]


def karte_hinzufuegen(fach, frage, antwort):
    supabase.table("karten").insert({
        "fach": fach,
        "frage": frage,
        "antwort": antwort
    }).execute()


def karte_bearbeiten(karten_id, fach, alte_frage, neue_frage, antwort):
    supabase.table("karten").update({
        "frage": neue_frage,
        "antwort": antwort
    }).eq("id", karten_id).execute()

    # Vorhandene Lernbewertungen bleiben erhalten,
    # bekommen aber den neuen Fragetext.
    supabase.table("bewertungen").update({
        "frage": neue_frage
    }).eq("fach", fach).eq("frage", alte_frage).execute()


def karte_loeschen(karten_id, fach, frage):
    supabase.table("karten").delete().eq("id", karten_id).execute()

    supabase.table("bewertungen").delete().eq(
        "fach", fach
    ).eq(
        "frage", frage
    ).execute()


# ==================================================
# LERNBEWERTUNGEN
# ==================================================

def bewertung_speichern(fach, frage, status):
    supabase.table("bewertungen").insert({
        "fach": fach,
        "frage": frage,
        "status": status,
        "datum": datetime.now(timezone.utc).isoformat()
    }).execute()


def statistik_laden(fach):
    daten = (
        supabase.table("bewertungen")
        .select("status")
        .eq("fach", fach)
        .execute()
        .data
    )

    statistik = {
        "gewusst": 0,
        "unsicher": 0,
        "nicht_gewusst": 0
    }

    for eintrag in daten:
        status = eintrag["status"]
        if status in statistik:
            statistik[status] += 1

    return statistik


def schwierige_karten_laden(fach):
    daten = (
        supabase.table("bewertungen")
        .select("frage, status")
        .eq("fach", fach)
        .execute()
        .data
    )

    karten = {}

    for eintrag in daten:
        frage = eintrag["frage"]
        status = eintrag["status"]

        if frage not in karten:
            karten[frage] = {
                "gewusst": 0,
                "unsicher": 0,
                "nicht_gewusst": 0
            }

        if status in karten[frage]:
            karten[frage][status] += 1

    schwierige = []

    for frage, werte in karten.items():
        punkte = (
            werte["nicht_gewusst"] * 2
            + werte["unsicher"]
        )

        if punkte > 0:
            schwierige.append((punkte, frage, werte))

    schwierige.sort(reverse=True)
    return schwierige[:5]


# ==================================================
# PRÜFUNGSFRAGEN
# ==================================================

def pruefungsfragen_laden(fach):
    daten = (
        supabase.table("pruefungsfragen")
        .select(
            "id, frage, antwort_a, antwort_b, antwort_c, "
            "antwort_d, richtig, erklaerung"
        )
        .eq("fach", fach)
        .order("id")
        .execute()
        .data
    )

    return [
        (
            eintrag["id"],
            eintrag["frage"],
            eintrag["antwort_a"],
            eintrag["antwort_b"],
            eintrag["antwort_c"],
            eintrag["antwort_d"],
            eintrag["richtig"],
            eintrag.get("erklaerung") or ""
        )
        for eintrag in daten
    ]


def pruefungsfrage_hinzufuegen(
    fach,
    frage,
    antwort_a,
    antwort_b,
    antwort_c,
    antwort_d,
    richtig,
    erklaerung
):
    supabase.table("pruefungsfragen").insert({
        "fach": fach,
        "frage": frage,
        "antwort_a": antwort_a,
        "antwort_b": antwort_b,
        "antwort_c": antwort_c,
        "antwort_d": antwort_d,
        "richtig": richtig,
        "erklaerung": erklaerung
    }).execute()


def pruefungsfrage_bearbeiten(
    frage_id,
    frage,
    antwort_a,
    antwort_b,
    antwort_c,
    antwort_d,
    richtig,
    erklaerung
):
    supabase.table("pruefungsfragen").update({
        "frage": frage,
        "antwort_a": antwort_a,
        "antwort_b": antwort_b,
        "antwort_c": antwort_c,
        "antwort_d": antwort_d,
        "richtig": richtig,
        "erklaerung": erklaerung
    }).eq("id", frage_id).execute()


def pruefungsfrage_loeschen(frage_id):
    supabase.table("pruefungsfragen").delete().eq("id", frage_id).execute()


# ==================================================
# START
# ==================================================

try:
    startdaten_anlegen()
    beispiel_pruefungsfragen_anlegen()
    faecher = faecher_laden()
except Exception as fehler:
    st.error(
        "Die Verbindung zu Supabase konnte nicht hergestellt werden "
        "oder die Tabellen sind noch nicht korrekt eingerichtet."
    )
    st.code(str(fehler))
    st.stop()


# Lernmodus
if "kartennummer" not in st.session_state:
    st.session_state.kartennummer = 0

if "antwort_anzeigen" not in st.session_state:
    st.session_state.antwort_anzeigen = False

if "letztes_fach" not in st.session_state:
    st.session_state.letztes_fach = None


# Prüfungsmodus
if "pruefung_aktiv" not in st.session_state:
    st.session_state.pruefung_aktiv = False

if "pruefung_fragen" not in st.session_state:
    st.session_state.pruefung_fragen = []

if "pruefung_index" not in st.session_state:
    st.session_state.pruefung_index = 0

if "pruefung_punkte" not in st.session_state:
    st.session_state.pruefung_punkte = 0

if "pruefung_beantwortet" not in st.session_state:
    st.session_state.pruefung_beantwortet = False

if "pruefung_auswahl" not in st.session_state:
    st.session_state.pruefung_auswahl = None

if "pruefung_ergebnisse" not in st.session_state:
    st.session_state.pruefung_ergebnisse = []

if "pruefung_run" not in st.session_state:
    st.session_state.pruefung_run = 0


# ==================================================
# OBERFLÄCHE
# ==================================================

st.title("📚 Meine Lernsoftware")

st.write(
    "Lerne Karteikarten, verwalte deine Lerninhalte "
    "und trainiere im Prüfungsmodus."
)

st.caption("☁️ Lerninhalte und Fortschritt werden dauerhaft in Supabase gespeichert.")

st.divider()


tab_lernen, tab_pruefung, tab_karten, tab_pruefungsfragen, tab_faecher = st.tabs([
    "📚 Lernen",
    "🎯 Prüfungsmodus",
    "⚙️ Karten verwalten",
    "📝 Prüfungsfragen",
    "📁 Lernfächer"
])


# ==================================================
# TAB: LERNEN
# ==================================================

with tab_lernen:
    st.header("📚 Lernmodus")

    fach = st.selectbox(
        "Wähle ein Fach:",
        ["Bitte auswählen"] + faecher,
        key="fach_lernen"
    )

    if fach != "Bitte auswählen":
        if st.session_state.letztes_fach != fach:
            st.session_state.kartennummer = 0
            st.session_state.antwort_anzeigen = False
            st.session_state.letztes_fach = fach

        karten = karten_laden(fach)

        if not karten:
            st.warning(
                "Für dieses Fach gibt es noch keine Karten. "
                "Du kannst unter „⚙️ Karten verwalten“ welche anlegen."
            )

        else:
            if st.session_state.kartennummer >= len(karten):
                st.session_state.kartennummer = 0

            _, frage, antwort = karten[st.session_state.kartennummer]

            st.success(f"📘 Fach: **{fach}**")

            st.subheader(
                f"Karte {st.session_state.kartennummer + 1} von {len(karten)}"
            )

            st.progress(
                (st.session_state.kartennummer + 1) / len(karten)
            )

            st.markdown("### ❓ Frage")
            st.info(frage)

            if st.button("💡 Antwort anzeigen", key="lern_antwort"):
                st.session_state.antwort_anzeigen = True

            if st.session_state.antwort_anzeigen:
                st.markdown("### 💡 Antwort")
                st.success(antwort)

                st.write("### Wie gut wusstest du die Antwort?")

                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button(
                        "❌ Nicht gewusst",
                        use_container_width=True
                    ):
                        bewertung_speichern(
                            fach,
                            frage,
                            "nicht_gewusst"
                        )
                        st.session_state.kartennummer += 1
                        st.session_state.antwort_anzeigen = False
                        st.rerun()

                with col2:
                    if st.button(
                        "🟡 Unsicher",
                        use_container_width=True
                    ):
                        bewertung_speichern(
                            fach,
                            frage,
                            "unsicher"
                        )
                        st.session_state.kartennummer += 1
                        st.session_state.antwort_anzeigen = False
                        st.rerun()

                with col3:
                    if st.button(
                        "✅ Gewusst",
                        use_container_width=True
                    ):
                        bewertung_speichern(
                            fach,
                            frage,
                            "gewusst"
                        )
                        st.session_state.kartennummer += 1
                        st.session_state.antwort_anzeigen = False
                        st.rerun()

            st.divider()
            st.header("📊 Dein Lernfortschritt")

            statistik = statistik_laden(fach)

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "✅ Gewusst",
                statistik["gewusst"]
            )

            col2.metric(
                "🟡 Unsicher",
                statistik["unsicher"]
            )

            col3.metric(
                "❌ Nicht gewusst",
                statistik["nicht_gewusst"]
            )

            gesamt = (
                statistik["gewusst"]
                + statistik["unsicher"]
                + statistik["nicht_gewusst"]
            )

            if gesamt > 0:
                prozent = statistik["gewusst"] / gesamt * 100

                st.write(
                    f"Du hast bisher **{gesamt} Karten** "
                    f"in **{fach}** bewertet."
                )

                st.write(
                    f"✅ **{prozent:.1f} %** hast du gewusst."
                )

                st.progress(statistik["gewusst"] / gesamt)

            schwierige = schwierige_karten_laden(fach)

            if schwierige:
                st.divider()
                st.header("🎯 Diese Karten solltest du wiederholen")

                for _, schwierige_frage, werte in schwierige:
                    st.write(f"**{schwierige_frage}**")
                    st.caption(
                        f"❌ {werte['nicht_gewusst']} × nicht gewusst | "
                        f"🟡 {werte['unsicher']} × unsicher | "
                        f"✅ {werte['gewusst']} × gewusst"
                    )


# ==================================================
# TAB: PRÜFUNGSMODUS
# ==================================================

with tab_pruefung:
    st.header("🎯 Prüfungsmodus")

    if not st.session_state.pruefung_aktiv:
        st.write(
            "Wähle ein Fach und die Anzahl der Fragen. "
            "Die Fragen werden zufällig ausgewählt."
        )

        if not faecher:
            st.warning("Lege zuerst ein Lernfach an.")
        else:
            pruefung_fach = st.selectbox(
                "Prüfungsfach:",
                faecher,
                key="pruefung_fach_auswahl"
            )

            verfuegbare_fragen = pruefungsfragen_laden(
                pruefung_fach
            )

            st.info(
                f"Für **{pruefung_fach}** sind aktuell "
                f"**{len(verfuegbare_fragen)} Prüfungsfragen** gespeichert."
            )

            if verfuegbare_fragen:
                max_fragen = min(
                    20,
                    len(verfuegbare_fragen)
                )

                anzahl_fragen = st.number_input(
                    "Wie viele Fragen möchtest du beantworten?",
                    min_value=1,
                    max_value=max_fragen,
                    value=min(5, max_fragen),
                    step=1
                )

                if st.button(
                    "🚀 Prüfung starten",
                    type="primary"
                ):
                    st.session_state.pruefung_run += 1

                    st.session_state.pruefung_fragen = random.sample(
                        verfuegbare_fragen,
                        int(anzahl_fragen)
                    )

                    st.session_state.pruefung_index = 0
                    st.session_state.pruefung_punkte = 0
                    st.session_state.pruefung_beantwortet = False
                    st.session_state.pruefung_auswahl = None
                    st.session_state.pruefung_ergebnisse = []
                    st.session_state.pruefung_aktiv = True

                    st.rerun()

            else:
                st.warning(
                    "Für dieses Fach gibt es noch keine "
                    "Multiple-Choice-Fragen. "
                    "Lege sie unter „📝 Prüfungsfragen“ an."
                )

    else:
        fragen = st.session_state.pruefung_fragen
        index = st.session_state.pruefung_index

        if index < len(fragen):
            (
                frage_id,
                frage,
                antwort_a,
                antwort_b,
                antwort_c,
                antwort_d,
                richtig,
                erklaerung
            ) = fragen[index]

            st.subheader(
                f"Frage {index + 1} von {len(fragen)}"
            )

            st.progress(
                (index + 1) / len(fragen)
            )

            st.markdown(
                f"### {frage}"
            )

            antworten = {
                "A": antwort_a,
                "B": antwort_b,
                "C": antwort_c,
                "D": antwort_d
            }

            if not st.session_state.pruefung_beantwortet:
                auswahl = st.radio(
                    "Wähle eine Antwort:",
                    ["A", "B", "C", "D"],
                    index=None,
                    format_func=lambda x: f"{x}) {antworten[x]}",
                    key=(
                        f"mc_{st.session_state.pruefung_run}_"
                        f"{frage_id}_{index}"
                    )
                )

                if st.button("✅ Antwort prüfen"):
                    if auswahl is None:
                        st.warning(
                            "Bitte wähle zuerst eine Antwort aus."
                        )

                    else:
                        st.session_state.pruefung_auswahl = auswahl
                        ist_richtig = auswahl == richtig

                        if ist_richtig:
                            st.session_state.pruefung_punkte += 1

                        st.session_state.pruefung_ergebnisse.append({
                            "frage": frage,
                            "auswahl": auswahl,
                            "richtig": richtig,
                            "ist_richtig": ist_richtig
                        })

                        st.session_state.pruefung_beantwortet = True
                        st.rerun()

            else:
                auswahl = st.session_state.pruefung_auswahl

                st.write(
                    f"**Deine Antwort:** "
                    f"{auswahl}) {antworten[auswahl]}"
                )

                if auswahl == richtig:
                    st.success("✅ Richtig!")

                else:
                    st.error("❌ Leider falsch.")
                    st.success(
                        f"Richtige Antwort: "
                        f"**{richtig}) {antworten[richtig]}**"
                    )

                if erklaerung:
                    st.info(
                        f"💡 Erklärung: {erklaerung}"
                    )

                if st.button("➡️ Nächste Frage"):
                    st.session_state.pruefung_index += 1
                    st.session_state.pruefung_beantwortet = False
                    st.session_state.pruefung_auswahl = None
                    st.rerun()

        else:
            punkte = st.session_state.pruefung_punkte
            gesamt = len(fragen)

            prozent = (
                punkte / gesamt * 100
                if gesamt
                else 0
            )

            st.success("🏁 Prüfung beendet!")
            st.header("📊 Deine Auswertung")

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Punkte",
                f"{punkte} / {gesamt}"
            )

            col2.metric(
                "Richtig",
                punkte
            )

            col3.metric(
                "Ergebnis",
                f"{prozent:.1f} %"
            )

            st.progress(
                prozent / 100
            )

            st.subheader("📝 Fragenübersicht")

            for nr, ergebnis in enumerate(
                st.session_state.pruefung_ergebnisse,
                start=1
            ):
                symbol = (
                    "✅"
                    if ergebnis["ist_richtig"]
                    else "❌"
                )

                with st.expander(
                    f"{symbol} Frage {nr}: "
                    f"{ergebnis['frage']}"
                ):
                    st.write(
                        f"Deine Auswahl: "
                        f"**{ergebnis['auswahl']}**"
                    )

                    st.write(
                        f"Richtige Antwort: "
                        f"**{ergebnis['richtig']}**"
                    )

            if st.button(
                "🔄 Neue Prüfung starten",
                type="primary"
            ):
                st.session_state.pruefung_aktiv = False
                st.session_state.pruefung_fragen = []
                st.session_state.pruefung_index = 0
                st.session_state.pruefung_punkte = 0
                st.session_state.pruefung_beantwortet = False
                st.session_state.pruefung_auswahl = None
                st.session_state.pruefung_ergebnisse = []

                st.rerun()


# ==================================================
# TAB: KARTEN VERWALTEN
# ==================================================

with tab_karten:
    st.header("⚙️ Karteikarten verwalten")

    if not faecher:
        st.warning(
            "Lege zuerst ein Lernfach an."
        )

    else:
        fach_verwaltung = st.selectbox(
            "Fach auswählen:",
            faecher,
            key="fach_verwaltung"
        )

        st.subheader(
            "➕ Neue Karte erstellen"
        )

        with st.form(
            "neue_karte"
        ):
            neue_frage = st.text_input(
                "Frage:"
            )

            neue_antwort = st.text_area(
                "Antwort:"
            )

            speichern = st.form_submit_button(
                "💾 Karte speichern"
            )

            if speichern:
                if not neue_frage.strip():
                    st.error(
                        "Bitte gib eine Frage ein."
                    )

                elif not neue_antwort.strip():
                    st.error(
                        "Bitte gib eine Antwort ein."
                    )

                else:
                    karte_hinzufuegen(
                        fach_verwaltung,
                        neue_frage.strip(),
                        neue_antwort.strip()
                    )

                    st.success(
                        "✅ Karte wurde gespeichert."
                    )

                    st.rerun()

        st.divider()

        vorhandene_karten = karten_laden(
            fach_verwaltung
        )

        st.subheader(
            f"📝 Vorhandene Karten "
            f"({len(vorhandene_karten)})"
        )

        if vorhandene_karten:
            auswahl = st.selectbox(
                "Karte auswählen:",
                vorhandene_karten,
                format_func=lambda x: x[1]
            )

            karten_id, alte_frage, alte_antwort = auswahl

            frage_neu = st.text_input(
                "Frage bearbeiten:",
                value=alte_frage,
                key=f"frage_{karten_id}"
            )

            antwort_neu = st.text_area(
                "Antwort bearbeiten:",
                value=alte_antwort,
                key=f"antwort_{karten_id}"
            )

            col1, col2 = st.columns(2)

            with col1:
                if st.button(
                    "💾 Änderungen speichern"
                ):
                    karte_bearbeiten(
                        karten_id,
                        fach_verwaltung,
                        alte_frage,
                        frage_neu.strip(),
                        antwort_neu.strip()
                    )

                    st.success(
                        "✅ Änderungen wurden gespeichert."
                    )

                    st.rerun()

            with col2:
                if st.button(
                    "🗑️ Karte löschen"
                ):
                    karte_loeschen(
                        karten_id,
                        fach_verwaltung,
                        alte_frage
                    )

                    st.rerun()

        else:
            st.info(
                "In diesem Fach gibt es noch keine Karten."
            )


# ==================================================
# TAB: PRÜFUNGSFRAGEN VERWALTEN
# ==================================================

with tab_pruefungsfragen:
    st.header(
        "📝 Multiple-Choice-Fragen verwalten"
    )

    if not faecher:
        st.warning(
            "Lege zuerst ein Lernfach an."
        )

    else:
        fach_mc = st.selectbox(
            "Fach:",
            faecher,
            key="fach_mc"
        )

        st.subheader(
            "➕ Neue Prüfungsfrage"
        )

        with st.form(
            "neue_pruefungsfrage"
        ):
            frage = st.text_area(
                "Frage:"
            )

            antwort_a = st.text_input(
                "Antwort A:"
            )

            antwort_b = st.text_input(
                "Antwort B:"
            )

            antwort_c = st.text_input(
                "Antwort C:"
            )

            antwort_d = st.text_input(
                "Antwort D:"
            )

            richtig = st.selectbox(
                "Welche Antwort ist richtig?",
                ["A", "B", "C", "D"]
            )

            erklaerung = st.text_area(
                "Erklärung zur richtigen Antwort (optional):"
            )

            speichern = st.form_submit_button(
                "💾 Prüfungsfrage speichern"
            )

            if speichern:
                felder = [
                    frage,
                    antwort_a,
                    antwort_b,
                    antwort_c,
                    antwort_d
                ]

                if any(
                    not feld.strip()
                    for feld in felder
                ):
                    st.error(
                        "Bitte fülle die Frage und "
                        "alle vier Antworten aus."
                    )

                else:
                    pruefungsfrage_hinzufuegen(
                        fach_mc,
                        frage.strip(),
                        antwort_a.strip(),
                        antwort_b.strip(),
                        antwort_c.strip(),
                        antwort_d.strip(),
                        richtig,
                        erklaerung.strip()
                    )

                    st.success(
                        "✅ Prüfungsfrage gespeichert."
                    )

                    st.rerun()

        st.divider()

        gespeicherte_mc = pruefungsfragen_laden(
            fach_mc
        )

        st.subheader(
            f"Vorhandene Prüfungsfragen "
            f"({len(gespeicherte_mc)})"
        )

        if gespeicherte_mc:
            mc_auswahl = st.selectbox(
                "Prüfungsfrage auswählen:",
                gespeicherte_mc,
                format_func=lambda x: x[1],
                key="mc_bearbeiten"
            )

            (
                frage_id,
                alte_frage,
                alt_a,
                alt_b,
                alt_c,
                alt_d,
                alt_richtig,
                alt_erklaerung
            ) = mc_auswahl

            frage_neu = st.text_area(
                "Frage bearbeiten:",
                value=alte_frage,
                key=f"mc_frage_{frage_id}"
            )

            a_neu = st.text_input(
                "Antwort A bearbeiten:",
                value=alt_a,
                key=f"mc_a_{frage_id}"
            )

            b_neu = st.text_input(
                "Antwort B bearbeiten:",
                value=alt_b,
                key=f"mc_b_{frage_id}"
            )

            c_neu = st.text_input(
                "Antwort C bearbeiten:",
                value=alt_c,
                key=f"mc_c_{frage_id}"
            )

            d_neu = st.text_input(
                "Antwort D bearbeiten:",
                value=alt_d,
                key=f"mc_d_{frage_id}"
            )

            richtig_neu = st.selectbox(
                "Richtige Antwort:",
                ["A", "B", "C", "D"],
                index=[
                    "A",
                    "B",
                    "C",
                    "D"
                ].index(alt_richtig),
                key=f"mc_richtig_{frage_id}"
            )

            erklaerung_neu = st.text_area(
                "Erklärung:",
                value=alt_erklaerung,
                key=f"mc_erklaerung_{frage_id}"
            )

            col1, col2 = st.columns(2)

            with col1:
                if st.button(
                    "💾 Prüfungsfrage ändern"
                ):
                    pruefungsfrage_bearbeiten(
                        frage_id,
                        frage_neu.strip(),
                        a_neu.strip(),
                        b_neu.strip(),
                        c_neu.strip(),
                        d_neu.strip(),
                        richtig_neu,
                        erklaerung_neu.strip()
                    )

                    st.rerun()

            with col2:
                if st.button(
                    "🗑️ Prüfungsfrage löschen"
                ):
                    pruefungsfrage_loeschen(
                        frage_id
                    )

                    st.rerun()

        else:
            st.info(
                "In diesem Fach gibt es noch "
                "keine Prüfungsfragen."
            )


# ==================================================
# TAB: LERNFÄCHER
# ==================================================

with tab_faecher:
    st.header(
        "📁 Lernfächer verwalten"
    )

    st.subheader(
        "➕ Neues Lernfach"
    )

    with st.form(
        "neues_fach"
    ):
        neuer_fachname = st.text_input(
            "Name des Lernfachs:",
            placeholder="z. B. Personalwirtschaft"
        )

        fach_speichern = st.form_submit_button(
            "➕ Lernfach erstellen"
        )

        if fach_speichern:
            erfolg, meldung = fach_hinzufuegen(
                neuer_fachname
            )

            if erfolg:
                st.success(
                    meldung
                )
                st.rerun()

            else:
                st.error(
                    meldung
                )

    st.divider()

    if faecher:
        st.subheader(
            "✏️ Lernfach umbenennen"
        )

        fach_zum_umbenennen = st.selectbox(
            "Lernfach auswählen:",
            faecher,
            key="fach_umbenennen"
        )

        neuer_name = st.text_input(
            "Neuer Name:",
            value=fach_zum_umbenennen
        )

        if st.button(
            "💾 Namen ändern"
        ):
            erfolg, meldung = fach_umbenennen(
                fach_zum_umbenennen,
                neuer_name
            )

            if erfolg:
                st.success(
                    meldung
                )
                st.rerun()

            else:
                st.error(
                    meldung
                )

        st.divider()

        st.subheader(
            "🗑️ Lernfach löschen"
        )

        fach_zum_loeschen = st.selectbox(
            "Lernfach zum Löschen:",
            faecher,
            key="fach_loeschen"
        )

        st.warning(
            "Ein Fach kann nur gelöscht werden, "
            "wenn darin keine Lernkarten, Lernergebnisse "
            "oder Prüfungsfragen mehr gespeichert sind."
        )

        if st.button(
            "🗑️ Lernfach löschen",
            type="primary"
        ):
            erfolg, meldung = fach_loeschen(
                fach_zum_loeschen
            )

            if erfolg:
                st.success(
                    meldung
                )
                st.rerun()

            else:
                st.error(
                    meldung
                )
