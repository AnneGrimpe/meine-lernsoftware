import streamlit as st
import sqlite3
import random
from datetime import datetime

st.set_page_config(
    page_title="Meine Lernsoftware",
    page_icon="📚",
    layout="centered"
)

DB = "lernsoftware.db"


# ==================================================
# DATENBANK
# ==================================================

def verbindung_oeffnen():
    return sqlite3.connect(DB)


def datenbank_starten():
    verbindung = verbindung_oeffnen()
    cursor = verbindung.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS faecher (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS karten (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fach TEXT NOT NULL,
            frage TEXT NOT NULL,
            antwort TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bewertungen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fach TEXT NOT NULL,
            frage TEXT NOT NULL,
            status TEXT NOT NULL,
            datum TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pruefungsfragen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fach TEXT NOT NULL,
            frage TEXT NOT NULL,
            antwort_a TEXT NOT NULL,
            antwort_b TEXT NOT NULL,
            antwort_c TEXT NOT NULL,
            antwort_d TEXT NOT NULL,
            richtig TEXT NOT NULL,
            erklaerung TEXT
        )
    """)

    standardfaecher = [
        "Buchführung",
        "Excel",
        "Recht",
        "Kaufmännische Kommunikation",
        "Geschäftsprozesse"
    ]

    for fach in standardfaecher:
        cursor.execute(
            "INSERT OR IGNORE INTO faecher (name) VALUES (?)",
            (fach,)
        )

    # Vorhandene Fächer aus Karten und Prüfungsfragen übernehmen
    cursor.execute("""
        INSERT OR IGNORE INTO faecher (name)
        SELECT DISTINCT fach FROM karten WHERE fach <> ''
    """)
    cursor.execute("""
        INSERT OR IGNORE INTO faecher (name)
        SELECT DISTINCT fach FROM pruefungsfragen WHERE fach <> ''
    """)

    verbindung.commit()
    verbindung.close()


def beispiel_pruefungsfragen_anlegen():
    verbindung = verbindung_oeffnen()
    cursor = verbindung.cursor()

    cursor.execute("SELECT COUNT(*) FROM pruefungsfragen")
    anzahl = cursor.fetchone()[0]

    if anzahl == 0:
        beispiele = [
            (
                "Recht",
                "Was beschreibt den Besitz?",
                "Die rechtliche Herrschaft über eine Sache",
                "Die tatsächliche Herrschaft über eine Sache",
                "Das Recht, eine Sache zu verkaufen",
                "Die vollständige Bezahlung einer Sache",
                "B",
                "Besitz bedeutet die tatsächliche Herrschaft über eine Sache."
            ),
            (
                "Recht",
                "Welches Beispiel ist ein einseitiges Rechtsgeschäft?",
                "Kaufvertrag",
                "Mietvertrag",
                "Kündigung",
                "Werkvertrag",
                "C",
                "Bei einer Kündigung genügt grundsätzlich die Willenserklärung einer Seite."
            ),
            (
                "Buchführung",
                "Was ist eine Bilanz?",
                "Eine Gegenüberstellung von Vermögen und Kapital",
                "Eine Liste aller Kunden",
                "Eine Rechnung an einen Lieferanten",
                "Eine Aufstellung nur der Schulden",
                "A",
                "Die Bilanz stellt Aktiva und Passiva zu einem bestimmten Zeitpunkt gegenüber."
            ),
            (
                "Excel",
                "Welche Funktion addiert mehrere Zahlen oder Zellbereiche?",
                "WENN",
                "SUMME",
                "ZÄHLENWENN",
                "MITTELWERTWENN",
                "B",
                "SUMME wird zum Addieren von Zahlen und Zellbereichen verwendet."
            ),
            (
                "Geschäftsprozesse",
                "Was beschreibt das Minimalprinzip?",
                "Mit festen Mitteln den größtmöglichen Erfolg erzielen",
                "Ein festgelegtes Ziel mit möglichst wenig Mitteln erreichen",
                "Möglichst viele Produkte herstellen",
                "Die Kosten unabhängig vom Ziel erhöhen",
                "B",
                "Beim Minimalprinzip ist das Ziel vorgegeben und der Mitteleinsatz soll möglichst gering sein."
            )
        ]

        cursor.executemany("""
            INSERT INTO pruefungsfragen
            (fach, frage, antwort_a, antwort_b, antwort_c, antwort_d, richtig, erklaerung)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, beispiele)

    verbindung.commit()
    verbindung.close()


# ==================================================
# LERNFÄCHER
# ==================================================

def faecher_laden():
    verbindung = verbindung_oeffnen()
    cursor = verbindung.cursor()
    cursor.execute("SELECT name FROM faecher ORDER BY name")
    ergebnisse = cursor.fetchall()
    verbindung.close()
    return [x[0] for x in ergebnisse]


def fach_hinzufuegen(name):
    name = name.strip()

    if not name:
        return False, "Bitte gib einen Namen ein."

    verbindung = verbindung_oeffnen()
    cursor = verbindung.cursor()

    try:
        cursor.execute("INSERT INTO faecher (name) VALUES (?)", (name,))
        verbindung.commit()
        verbindung.close()
        return True, "Lernfach wurde erstellt."
    except sqlite3.IntegrityError:
        verbindung.close()
        return False, "Dieses Lernfach gibt es bereits."


def fach_umbenennen(alter_name, neuer_name):
    neuer_name = neuer_name.strip()

    if not neuer_name:
        return False, "Bitte gib einen Namen ein."

    if alter_name == neuer_name:
        return False, "Der Name wurde nicht geändert."

    verbindung = verbindung_oeffnen()
    cursor = verbindung.cursor()

    try:
        cursor.execute(
            "UPDATE faecher SET name = ? WHERE name = ?",
            (neuer_name, alter_name)
        )
        cursor.execute(
            "UPDATE karten SET fach = ? WHERE fach = ?",
            (neuer_name, alter_name)
        )
        cursor.execute(
            "UPDATE bewertungen SET fach = ? WHERE fach = ?",
            (neuer_name, alter_name)
        )
        cursor.execute(
            "UPDATE pruefungsfragen SET fach = ? WHERE fach = ?",
            (neuer_name, alter_name)
        )

        verbindung.commit()
        verbindung.close()
        return True, "Lernfach wurde umbenannt."
    except sqlite3.IntegrityError:
        verbindung.close()
        return False, "Ein Fach mit diesem Namen existiert bereits."


def fach_loeschen(name):
    verbindung = verbindung_oeffnen()
    cursor = verbindung.cursor()

    cursor.execute("SELECT COUNT(*) FROM karten WHERE fach = ?", (name,))
    kartenanzahl = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM bewertungen WHERE fach = ?", (name,))
    bewertungen = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM pruefungsfragen WHERE fach = ?",
        (name,)
    )
    pruefungsanzahl = cursor.fetchone()[0]

    if kartenanzahl > 0 or bewertungen > 0 or pruefungsanzahl > 0:
        verbindung.close()
        return False, (
            "Das Fach kann noch nicht gelöscht werden. "
            "Es enthält noch Lernkarten, Lernergebnisse oder Prüfungsfragen."
        )

    cursor.execute("DELETE FROM faecher WHERE name = ?", (name,))
    verbindung.commit()
    verbindung.close()
    return True, "Lernfach wurde gelöscht."


# ==================================================
# KARTEIKARTEN
# ==================================================

def karten_laden(fach):
    verbindung = verbindung_oeffnen()
    cursor = verbindung.cursor()
    cursor.execute("""
        SELECT id, frage, antwort
        FROM karten
        WHERE fach = ?
        ORDER BY id
    """, (fach,))
    daten = cursor.fetchall()
    verbindung.close()
    return daten


def karte_hinzufuegen(fach, frage, antwort):
    verbindung = verbindung_oeffnen()
    cursor = verbindung.cursor()
    cursor.execute("""
        INSERT INTO karten (fach, frage, antwort)
        VALUES (?, ?, ?)
    """, (fach, frage, antwort))
    verbindung.commit()
    verbindung.close()


def karte_bearbeiten(karten_id, fach, alte_frage, neue_frage, antwort):
    verbindung = verbindung_oeffnen()
    cursor = verbindung.cursor()

    cursor.execute("""
        UPDATE karten
        SET frage = ?, antwort = ?
        WHERE id = ?
    """, (neue_frage, antwort, karten_id))

    cursor.execute("""
        UPDATE bewertungen
        SET frage = ?
        WHERE fach = ? AND frage = ?
    """, (neue_frage, fach, alte_frage))

    verbindung.commit()
    verbindung.close()


def karte_loeschen(karten_id, fach, frage):
    verbindung = verbindung_oeffnen()
    cursor = verbindung.cursor()

    cursor.execute("DELETE FROM karten WHERE id = ?", (karten_id,))
    cursor.execute("""
        DELETE FROM bewertungen
        WHERE fach = ? AND frage = ?
    """, (fach, frage))

    verbindung.commit()
    verbindung.close()


# ==================================================
# LERNBEWERTUNGEN
# ==================================================

def bewertung_speichern(fach, frage, status):
    verbindung = verbindung_oeffnen()
    cursor = verbindung.cursor()

    cursor.execute("""
        INSERT INTO bewertungen (fach, frage, status, datum)
        VALUES (?, ?, ?, ?)
    """, (
        fach,
        frage,
        status,
        datetime.now().strftime("%d.%m.%Y %H:%M")
    ))

    verbindung.commit()
    verbindung.close()


def statistik_laden(fach):
    verbindung = verbindung_oeffnen()
    cursor = verbindung.cursor()

    cursor.execute("""
        SELECT status, COUNT(*)
        FROM bewertungen
        WHERE fach = ?
        GROUP BY status
    """, (fach,))

    ergebnisse = cursor.fetchall()
    verbindung.close()

    statistik = {
        "gewusst": 0,
        "unsicher": 0,
        "nicht_gewusst": 0
    }

    for status, anzahl in ergebnisse:
        statistik[status] = anzahl

    return statistik


# ==================================================
# PRÜFUNGSFRAGEN
# ==================================================

def pruefungsfragen_laden(fach):
    verbindung = verbindung_oeffnen()
    cursor = verbindung.cursor()

    cursor.execute("""
        SELECT id, frage, antwort_a, antwort_b, antwort_c, antwort_d,
               richtig, COALESCE(erklaerung, '')
        FROM pruefungsfragen
        WHERE fach = ?
        ORDER BY id
    """, (fach,))

    daten = cursor.fetchall()
    verbindung.close()
    return daten


def pruefungsfrage_hinzufuegen(
    fach, frage, antwort_a, antwort_b, antwort_c, antwort_d, richtig, erklaerung
):
    verbindung = verbindung_oeffnen()
    cursor = verbindung.cursor()

    cursor.execute("""
        INSERT INTO pruefungsfragen
        (fach, frage, antwort_a, antwort_b, antwort_c, antwort_d, richtig, erklaerung)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        fach, frage, antwort_a, antwort_b, antwort_c, antwort_d, richtig, erklaerung
    ))

    verbindung.commit()
    verbindung.close()


def pruefungsfrage_bearbeiten(
    frage_id, frage, antwort_a, antwort_b, antwort_c, antwort_d, richtig, erklaerung
):
    verbindung = verbindung_oeffnen()
    cursor = verbindung.cursor()

    cursor.execute("""
        UPDATE pruefungsfragen
        SET frage = ?, antwort_a = ?, antwort_b = ?, antwort_c = ?,
            antwort_d = ?, richtig = ?, erklaerung = ?
        WHERE id = ?
    """, (
        frage, antwort_a, antwort_b, antwort_c, antwort_d,
        richtig, erklaerung, frage_id
    ))

    verbindung.commit()
    verbindung.close()


def pruefungsfrage_loeschen(frage_id):
    verbindung = verbindung_oeffnen()
    cursor = verbindung.cursor()
    cursor.execute("DELETE FROM pruefungsfragen WHERE id = ?", (frage_id,))
    verbindung.commit()
    verbindung.close()


# ==================================================
# START
# ==================================================

datenbank_starten()
beispiel_pruefungsfragen_anlegen()
faecher = faecher_laden()

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


st.title("📚 Meine Lernsoftware")
st.write("Lernen, Karteikarten verwalten und Prüfungen üben.")
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
            st.warning("Für dieses Fach gibt es noch keine Karten.")
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
                    if st.button("❌ Nicht gewusst", use_container_width=True):
                        bewertung_speichern(fach, frage, "nicht_gewusst")
                        st.session_state.kartennummer += 1
                        st.session_state.antwort_anzeigen = False
                        st.rerun()

                with col2:
                    if st.button("🟡 Unsicher", use_container_width=True):
                        bewertung_speichern(fach, frage, "unsicher")
                        st.session_state.kartennummer += 1
                        st.session_state.antwort_anzeigen = False
                        st.rerun()

                with col3:
                    if st.button("✅ Gewusst", use_container_width=True):
                        bewertung_speichern(fach, frage, "gewusst")
                        st.session_state.kartennummer += 1
                        st.session_state.antwort_anzeigen = False
                        st.rerun()

            st.divider()
            st.header("📊 Dein Lernfortschritt")

            statistik = statistik_laden(fach)
            col1, col2, col3 = st.columns(3)

            col1.metric("✅ Gewusst", statistik["gewusst"])
            col2.metric("🟡 Unsicher", statistik["unsicher"])
            col3.metric("❌ Nicht gewusst", statistik["nicht_gewusst"])


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

        pruefung_fach = st.selectbox(
            "Prüfungsfach:",
            faecher,
            key="pruefung_fach_auswahl"
        )

        verfuegbare_fragen = pruefungsfragen_laden(pruefung_fach)

        st.info(
            f"Für **{pruefung_fach}** sind aktuell "
            f"**{len(verfuegbare_fragen)} Prüfungsfragen** gespeichert."
        )

        if verfuegbare_fragen:
            max_fragen = min(20, len(verfuegbare_fragen))

            anzahl_fragen = st.number_input(
                "Wie viele Fragen möchtest du beantworten?",
                min_value=1,
                max_value=max_fragen,
                value=min(5, max_fragen),
                step=1
            )

            if st.button("🚀 Prüfung starten", type="primary"):
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
                "Für dieses Fach gibt es noch keine Multiple-Choice-Fragen. "
                "Lege sie im Reiter „📝 Prüfungsfragen“ an."
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

            st.subheader(f"Frage {index + 1} von {len(fragen)}")
            st.progress((index + 1) / len(fragen))
            st.markdown(f"### {frage}")

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
                    key=f"mc_{st.session_state.pruefung_run}_{frage_id}_{index}"
                )

                if st.button("✅ Antwort prüfen"):
                    if auswahl is None:
                        st.warning("Bitte wähle zuerst eine Antwort aus.")
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
                    f"**Deine Antwort:** {auswahl}) {antworten[auswahl]}"
                )

                if auswahl == richtig:
                    st.success("✅ Richtig!")
                else:
                    st.error("❌ Leider falsch.")
                    st.success(
                        f"Richtige Antwort: **{richtig}) {antworten[richtig]}**"
                    )

                if erklaerung:
                    st.info(f"💡 Erklärung: {erklaerung}")

                if st.button("➡️ Nächste Frage"):
                    st.session_state.pruefung_index += 1
                    st.session_state.pruefung_beantwortet = False
                    st.session_state.pruefung_auswahl = None
                    st.rerun()

        else:
            punkte = st.session_state.pruefung_punkte
            gesamt = len(fragen)
            prozent = (punkte / gesamt * 100) if gesamt else 0

            st.success("🏁 Prüfung beendet!")
            st.header("📊 Deine Auswertung")

            col1, col2, col3 = st.columns(3)
            col1.metric("Punkte", f"{punkte} / {gesamt}")
            col2.metric("Richtig", punkte)
            col3.metric("Ergebnis", f"{prozent:.1f} %")

            st.progress(prozent / 100)

            st.subheader("📝 Fragenübersicht")

            for nr, ergebnis in enumerate(
                st.session_state.pruefung_ergebnisse,
                start=1
            ):
                symbol = "✅" if ergebnis["ist_richtig"] else "❌"

                with st.expander(
                    f"{symbol} Frage {nr}: {ergebnis['frage']}"
                ):
                    st.write(
                        f"Deine Auswahl: **{ergebnis['auswahl']}**"
                    )
                    st.write(
                        f"Richtige Antwort: **{ergebnis['richtig']}**"
                    )

            if st.button("🔄 Neue Prüfung starten", type="primary"):
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
        st.warning("Lege zuerst ein Lernfach an.")
    else:
        fach_verwaltung = st.selectbox(
            "Fach auswählen:",
            faecher,
            key="fach_verwaltung"
        )

        st.subheader("➕ Neue Karte erstellen")

        with st.form("neue_karte"):
            neue_frage = st.text_input("Frage:")
            neue_antwort = st.text_area("Antwort:")
            speichern = st.form_submit_button("💾 Karte speichern")

            if speichern:
                if not neue_frage.strip():
                    st.error("Bitte gib eine Frage ein.")
                elif not neue_antwort.strip():
                    st.error("Bitte gib eine Antwort ein.")
                else:
                    karte_hinzufuegen(
                        fach_verwaltung,
                        neue_frage.strip(),
                        neue_antwort.strip()
                    )
                    st.success("✅ Karte wurde gespeichert.")
                    st.rerun()

        st.divider()
        vorhandene_karten = karten_laden(fach_verwaltung)

        st.subheader(
            f"📝 Vorhandene Karten ({len(vorhandene_karten)})"
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
                if st.button("💾 Änderungen speichern"):
                    karte_bearbeiten(
                        karten_id,
                        fach_verwaltung,
                        alte_frage,
                        frage_neu,
                        antwort_neu
                    )
                    st.rerun()

            with col2:
                if st.button("🗑️ Karte löschen"):
                    karte_loeschen(
                        karten_id,
                        fach_verwaltung,
                        alte_frage
                    )
                    st.rerun()


# ==================================================
# TAB: PRÜFUNGSFRAGEN VERWALTEN
# ==================================================

with tab_pruefungsfragen:
    st.header("📝 Multiple-Choice-Fragen verwalten")

    fach_mc = st.selectbox(
        "Fach:",
        faecher,
        key="fach_mc"
    )

    st.subheader("➕ Neue Prüfungsfrage")

    with st.form("neue_pruefungsfrage"):
        frage = st.text_area("Frage:")
        antwort_a = st.text_input("Antwort A:")
        antwort_b = st.text_input("Antwort B:")
        antwort_c = st.text_input("Antwort C:")
        antwort_d = st.text_input("Antwort D:")

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
                frage, antwort_a, antwort_b,
                antwort_c, antwort_d
            ]

            if any(not feld.strip() for feld in felder):
                st.error(
                    "Bitte fülle die Frage und alle vier Antworten aus."
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
                st.success("✅ Prüfungsfrage gespeichert.")
                st.rerun()

    st.divider()
    gespeicherte_mc = pruefungsfragen_laden(fach_mc)

    st.subheader(
        f"Vorhandene Prüfungsfragen ({len(gespeicherte_mc)})"
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
            index=["A", "B", "C", "D"].index(alt_richtig),
            key=f"mc_richtig_{frage_id}"
        )

        erklaerung_neu = st.text_area(
            "Erklärung:",
            value=alt_erklaerung,
            key=f"mc_erklaerung_{frage_id}"
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("💾 Prüfungsfrage ändern"):
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
            if st.button("🗑️ Prüfungsfrage löschen"):
                pruefungsfrage_loeschen(frage_id)
                st.rerun()


# ==================================================
# TAB: LERNFÄCHER
# ==================================================

with tab_faecher:
    st.header("📁 Lernfächer verwalten")

    st.subheader("➕ Neues Lernfach")

    with st.form("neues_fach"):
        neuer_fachname = st.text_input(
            "Name des Lernfachs:",
            placeholder="z. B. Personalwirtschaft"
        )
        fach_speichern = st.form_submit_button(
            "➕ Lernfach erstellen"
        )

        if fach_speichern:
            erfolg, meldung = fach_hinzufuegen(neuer_fachname)

            if erfolg:
                st.success(meldung)
                st.rerun()
            else:
                st.error(meldung)

    st.divider()

    if faecher:
        st.subheader("✏️ Lernfach umbenennen")

        fach_zum_umbenennen = st.selectbox(
            "Lernfach auswählen:",
            faecher,
            key="fach_umbenennen"
        )

        neuer_name = st.text_input(
            "Neuer Name:",
            value=fach_zum_umbenennen
        )

        if st.button("💾 Namen ändern"):
            erfolg, meldung = fach_umbenennen(
                fach_zum_umbenennen,
                neuer_name
            )

            if erfolg:
                st.success(meldung)
                st.rerun()
            else:
                st.error(meldung)

        st.divider()
        st.subheader("🗑️ Lernfach löschen")

        fach_zum_loeschen = st.selectbox(
            "Lernfach zum Löschen:",
            faecher,
            key="fach_loeschen"
        )

        st.warning(
            "Ein Fach kann nur gelöscht werden, wenn darin keine "
            "Lernkarten, Lernergebnisse oder Prüfungsfragen mehr gespeichert sind."
        )

        if st.button("🗑️ Lernfach löschen", type="primary"):
            erfolg, meldung = fach_loeschen(fach_zum_loeschen)

            if erfolg:
                st.success(meldung)
                st.rerun()
            else:
                st.error(meldung)
