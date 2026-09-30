import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox, Button, RadioButtons
import numpy as np
import os
from datetime import datetime
import csv
from matplotlib.backends.backend_pdf import PdfPages
import threading
# PARTIE 1 : EXTRACTION ET NETTOYAGE DES DONNÉES
# Cette section gère la lecture des données brutes, le nettoyage et le prétraitement
# Dictionnaire pour convertir les mois français en numéros
mois_fr = {
    "janv.": "01", "févr.": "02", "mars": "03", "avr.": "04",
    "mai": "05", "juin": "06", "juil.": "07", "août": "08",
    "sept.": "09", "oct.": "10", "nov.": "11", "déc.": "12"
}
def convertir_date(date_str):
    if pd.isna(date_str):
        return None
    try:
        # Remplacer le mois français par son numéro
        for mois, num in mois_fr.items():
            if mois in date_str:
                date_str = date_str.replace(mois, num)
                break
        return pd.to_datetime(date_str, format="%d/%m/%y %I:%M %p").strftime("%Y-%m-%d")
    except:
        return None
def nettoyer_type_demande(type_str):
    if pd.isna(type_str):
        return type_str
    type_str = str(type_str).strip().lower()
    # Standardiser les types liés à l'affichage
    if "affichage" in type_str:
        return "Anomalie-Affichage"
    return type_str
def lire_fichier_csv(nom_fichier):
    #Lit un fichier CSV en utilisant pandas avec gestion de la mémoire.
    return pd.read_csv(nom_fichier, encoding="utf-8", low_memory=False)
def filtrer_colonnes(df):
    # Sélection des colonnes pertinentes
    df_filtre = df[[
        'ID de ticket', 'Création', 'Priorité', "Champs personnalisés (Type d'assistance)",
        "Catégorie d'état", 'Champs personnalisés (Compagnie)', 'Type de ticket']].rename(columns={
        'ID de ticket': 'id',
        'Création': 'date',
        'Priorité': 'priorite',
        "Champs personnalisés (Type d'assistance)": 'type_demande',
        "Catégorie d'état": 'statut',
        'Champs personnalisés (Compagnie)': 'compagnie',
        'Type de ticket': 'classification'
    })
    # Conversion et nettoyage des dates et types
    df_filtre['date'] = df_filtre['date'].apply(convertir_date)
    df_filtre['type_demande'] = df_filtre['type_demande'].apply(nettoyer_type_demande)
    # Sauvegarde des données nettoyées
    df_filtre.to_csv("donnees_filtrees.csv", index=False, encoding="utf-8-sig")

# PARTIE 2 : CHARGEMENT DES DONNÉES ET INITIALISATION
# Cette section charge les données nettoyées et prépare l'environnement pour la visualisation
# Chargement des données nettoyées
df = pd.read_csv("donnees_filtrees.csv", encoding="utf-8-sig")
df['date'] = pd.to_datetime(df['date'], errors='coerce')
df = df.dropna(subset=['date'])  # Suppression des dates invalides
# Détermination de la période couverte par les données
min_date = df['date'].min().date()
max_date = df['date'].max().date()
# Correspondance entre les noms affichés et les colonnes du DataFrame
colonnes_disponibles = {
    "Compagnie d'assurance": "compagnie",
    "Type de demande": "type_demande",
    "Priorité": "priorite",
    "Classification": "classification",
    "Statut": "statut"
}
# Palette de couleurs pour les graphiques
colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'cyan', 'magenta',
          'teal', 'darkgreen', 'maroon', 'navy', 'olive', 'indigo', 'peru', 'salmon', 'darkorange']
# PARTIE 3 : INTERFACE DE VISUALISATION INTERACTIVE
# Création de l'interface utilisateur avec Matplotlib widgets
# Création de la figure principale pour les contrôles et le graphique à barres
fig_main, ax_main = plt.subplots(figsize=(16, 10))
plt.subplots_adjust(left=0.22, right=0.95, bottom=0.15, top=0.90)
# Zone de texte pour la date de début
axbox_debut = plt.axes([0.03, 0.92, 0.12, 0.04])
text_box_debut = TextBox(axbox_debut, 'Début', initial=str(min_date))
axbox_debut.set_facecolor("#f9f9f9")
# Zone de texte pour la date de fin
axbox_fin = plt.axes([0.17, 0.92, 0.12, 0.04])
text_box_fin = TextBox(axbox_fin, 'Fin', initial=str(max_date))
axbox_fin.set_facecolor("#f9f9f9")
# Bouton pour générer le rapport Excel
bouton_ax = plt.axes([0.62, 0.92, 0.15, 0.04])
bouton = Button(bouton_ax, 'Générer un rapport excel')
bouton.label.set_color('black')
bouton_ax.set_facecolor('#d3d3d3')
# Bouton pour exporter tout en PDF
bouton_pdf_ax = plt.axes([0.80, 0.92, 0.15, 0.04])
bouton_pdf = Button(bouton_pdf_ax, 'Exporter tout en PDF')
bouton_pdf.label.set_color('black')
bouton_pdf_ax.set_facecolor('#d3d3d3')
# Boutons radio pour sélectionner la catégorie d'analyse
rax = plt.axes([0.03, 0.50, 0.15, 0.35]) 
radio = RadioButtons(rax, list(colonnes_disponibles.keys()), active=0)
for label in radio.labels:
    label.set_fontsize(8)
    label.set_color('#333333')
rax.set_facecolor('#f9f9f9')
# Boutons radio pour sélectionner le type de graphique
rax_chart_type = plt.axes([0.03, 0.30, 0.15, 0.15]) 
radio_chart_type = RadioButtons(rax_chart_type, ['Barres', 'Circulaire', 'Courbe'], active=0)
for label in radio_chart_type.labels:
    label.set_fontsize(8)
    label.set_color('#333333')
rax_chart_type.set_facecolor('#f9f9f9')
# Zone de message pour les retours utilisateur
msg_ax = plt.axes([0.30, 0.05, 0.65, 0.03])
msg_ax.axis("off")
msg_text = msg_ax.text(0.5, 0.5, '', ha='center', va='center', fontsize=10)
# PARTIE 4 : FONCTIONS DE VISUALISATION ET RAPPORT
# Implémentation des fonctionnalités d'analyse et d'export
# Variable globale pour gérer les événements de clic
click_cid = None
# Dictionnaire pour stocker les références aux figures secondaires ouvertes
open_secondary_figures = {}
def date_valide(date_str):
    try:
        pd.to_datetime(date_str)
        return True
    except:
        return False
def ajouter_bouton_export(fig_target, ax_target):
    # Positionnement du bouton en haut à droite
    bouton_ax_local = fig_target.add_axes([0.83, 0.92, 0.15, 0.05])
    bouton_pdf_local = Button(bouton_ax_local, 'Exporter PDF')
    bouton_ax_local.set_facecolor('#e0e0e0')
    # Variable pour le message de confirmation
    confirmation_text = None
    def exporter_local(event):
        nonlocal confirmation_text
        # Génération d'un nom de fichier unique avec timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        title = fig_target.canvas.manager.get_window_title() if fig_target.canvas.manager else 'graphique'
        nom_fichier = f"graphique_{title.replace(' ', '_').replace(':', '')}_{timestamp}.pdf"
        try:
            # Création du PDF
            with PdfPages(nom_fichier) as pdf:
                pdf.savefig(fig_target, bbox_inches='tight')
            # Suppression de l'ancien message s'il existe
            if confirmation_text and confirmation_text in fig_target.texts:
                confirmation_text.remove()
            # Affichage du message de confirmation
            confirmation_text = fig_target.text(
                0.5, 0.95,
                f"Exporté vers: {nom_fichier}", 
                ha='center', 
                va='top', 
                color='green', 
                fontsize=10,
                transform=fig_target.transFigure,
                bbox=dict(facecolor='white', alpha=0.9, edgecolor='green', boxstyle='round,pad=0.5')
            )
            fig_target.canvas.draw_idle()
            # Fonction pour supprimer le message après 3 secondes
            def remove_message():
                if confirmation_text and confirmation_text in fig_target.texts:
                    confirmation_text.remove()
                    fig_target.canvas.draw_idle()
            threading.Timer(3.0, remove_message).start()
        except Exception as e:
            # Gestion des erreurs
            if confirmation_text and confirmation_text in fig_target.texts:
                confirmation_text.remove()
            # Affichage du message d'erreur
            confirmation_text = fig_target.text(
                0.5, 0.95,
                f"Erreur d'export: {str(e)}", 
                ha='center', 
                va='top', 
                color='red', 
                fontsize=10,
                transform=fig_target.transFigure,
                bbox=dict(facecolor='white', alpha=0.9, edgecolor='red', boxstyle='round,pad=0.5')
            )
            fig_target.canvas.draw_idle()
            # Suppression du message d'erreur après 5 secondes
            threading.Timer(5.0, lambda: confirmation_text.remove() if confirmation_text else None).start()
    # Lier l'événement de clic au bouton
    bouton_pdf_local.on_clicked(exporter_local)
    # Conserver les références pour éviter le garbage collection
    fig_target.bouton_pdf_local_ref = bouton_pdf_local
    fig_target.bouton_ax_local_ref = bouton_ax_local
def afficher_types_par_compagnie(nom_compagnie, date_debut, date_fin, chart_type):
    # Filtrage des données pour la compagnie et la période sélectionnées
    df_filtre = df[(df['date'] >= date_debut) & (df['date'] <= date_fin)]
    df_filtre = df_filtre[df_filtre["compagnie"] == nom_compagnie]
    df_filtre["type_demande_filled"] = df_filtre["type_demande"].fillna("Autre")
    if df_filtre.empty:
        # Message d'erreur dans l'interface principale
        msg_text.set_text(f"Aucune donnée pour {nom_compagnie}")
        msg_text.set_color('red')
        fig_main.canvas.draw_idle()
        return
    # Création d'une nouvelle figure pour chaque analyse
    fig2, ax2 = plt.subplots(figsize=(14, 8))
    fig2.canvas.manager.set_window_title(f'Détail {nom_compagnie} ({chart_type})')
    # Graphique à barres horizontales
    if chart_type == 'Barres':
        stats = df_filtre["type_demande_filled"].value_counts().reset_index()
        stats.columns = ["Type de demande", "Nombre de tickets"]
        stats = stats.sort_values(by="Nombre de tickets", ascending=True).reset_index(drop=True)[::-1]
        total = stats["Nombre de tickets"].sum()
        y_pos = np.arange(len(stats))
        bars = ax2.barh(y_pos, stats["Nombre de tickets"], color=colors[:len(stats)])
        ax2.set_title(f"Analyse détaillée pour {nom_compagnie}\n{date_debut.strftime('%d/%m/%Y')} au {date_fin.strftime('%d/%m/%Y')} (Barres)", 
                     fontsize=14, pad=20)
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(stats["Type de demande"], fontsize=11)
        ax2.set_xlabel("Nombre de tickets", fontsize=12)
        max_value = stats["Nombre de tickets"].max()
        for bar in bars:
            width = bar.get_width()
            pourcentage = (width / total) * 100
            ax2.text(width + max_value * 0.02, bar.get_y() + bar.get_height()/2,
                     f"{int(width)} ({pourcentage:.1f}%)", 
                     va='center', fontsize=10)
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.grid(axis='x', linestyle='--', alpha=0.3)
        ax2.set_xlim(0, max_value * 1.25)
    # Graphique circulaire
    elif chart_type == 'Circulaire':
        stats = df_filtre["type_demande_filled"].value_counts()
        wedges, texts, autotexts = ax2.pie(stats, autopct='%1.1f%%', startangle=90, colors=colors[:len(stats)],
                                           pctdistance=0.85)
        # Création de la légende
        ax2.legend(wedges, stats.index, title="Types de demande", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        ax2.set_title(f"Répartition des types de demande pour {nom_compagnie}\n{date_debut.strftime('%d/%m/%Y')} au {date_fin.strftime('%d/%m/%Y')} (Circulaire)", 
                     fontsize=14, pad=20)
        ax2.axis('equal')
    # Graphique en courbe (évolution temporelle)
    elif chart_type == 'Courbe':
        df_daily = df_filtre.groupby(df_filtre['date'].dt.date).size().reset_index(name='Nombre de tickets')
        df_daily['date'] = pd.to_datetime(df_daily['date']) 
        if df_daily.empty:
            ax2.text(0.5, 0.5, "Aucune donnée quotidienne pour cette période.", 
                     horizontalalignment='center', verticalalignment='center', transform=ax2.transAxes, fontsize=12, color='gray')
        else:
            ax2.plot(df_daily['date'], df_daily['Nombre de tickets'], marker='o', linestyle='-', color='blue', label='Nombre de tickets')
            ax2.legend(title=f"Tickets pour {nom_compagnie}")

            ax2.set_title(f"Nombre de tickets par jour pour {nom_compagnie}\n{date_debut.strftime('%d/%m/%Y')} au {date_fin.strftime('%d/%m/%Y')} (Courbe)", 
                         fontsize=14, pad=20)
            ax2.set_xlabel("Date", fontsize=12)
            ax2.set_ylabel("Nombre de tickets", fontsize=12)
            ax2.grid(True, linestyle='--', alpha=0.6)
            fig2.autofmt_xdate()
    ajouter_bouton_export(fig2, ax2)
    plt.tight_layout()
    plt.show()
def update_graph(date_debut_str, date_fin_str, colonne, chart_type):
    global click_cid
    # Fonction utilitaire pour valider le format des dates
    def message_erreur_personnalise(date_str):
        """Valide le format et les valeurs d'une date."""
        if len(date_str) != 10 or date_str[4] != '-' or date_str[7] != '-':
            return "Format de date invalide. Utilisez AAAA-MM-JJ."
        try:
            annee, mois, jour = map(int, date_str.split('-'))
            if annee < 1900 or annee > 2100:
                return f"Année invalide dans la date : {date_str}"
            if mois < 1 or mois > 12:
                return f"Mois invalide dans la date : {date_str}"
            if jour < 1 or jour > 31:
                return f"Jour invalide dans la date : {date_str}"
        except:
            return f"Date invalide : {date_str}"
        return None
    # Validation des dates
    erreur_debut = message_erreur_personnalise(date_debut_str)
    erreur_fin = message_erreur_personnalise(date_fin_str)
    # Affichage des erreurs de date
    if erreur_debut or erreur_fin:
        ax_main.clear()
        msg = ""
        if erreur_debut:
            msg += f"Date de début invalide : {erreur_debut}\n"
        if erreur_fin:
            msg += f"Date de fin invalide : {erreur_fin}"
        msg_text.set_text(msg.strip())
        msg_text.set_color('red')
        fig_main.canvas.draw_idle()
        return
    # Conversion des dates
    try:
        date_debut = pd.to_datetime(date_debut_str)
        date_fin = pd.to_datetime(date_fin_str)
        if date_debut > date_fin:
            raise ValueError("start_after_end")
    except ValueError as e:
        ax_main.clear()
        if str(e) == "start_after_end":
            msg_text.set_text("La date de début ne peut pas être après la date de fin.")
        else:
            msg_text.set_text("Erreur de date. Vérifiez le format AAAA-MM-JJ.")
        msg_text.set_color('red')
        fig_main.canvas.draw_idle()
        return
    # Filtrage des données sur la période
    df_filtre = df[(df['date'] >= date_debut) & (df['date'] <= date_fin)]
    # Réinitialisation de l'affichage
    ax_main.clear() 
    msg_text.set_text("")
    # Vérification des données disponibles
    if df_filtre.empty:
        msg_text.set_text("Aucun ticket trouvé pour cette période.")
        msg_text.set_color('black')
        fig_main.canvas.draw_idle()
        if click_cid:
            fig_main.canvas.mpl_disconnect(click_cid)
            click_cid = None
        return
    # Gestion des différents types de graphiques
    current_ax = ax_main 
    if chart_type != 'Barres':
        # Création d'une nouvelle figure pour les graphiques non-barres
        fig_secondary, current_ax = plt.subplots(figsize=(14, 8))
        fig_secondary.canvas.manager.set_window_title(f'Analyse principale ({chart_type})')
    # Graphique à barres horizontales
    if chart_type == 'Barres':
        serie_categorie = df_filtre[colonne].fillna("Autre")
        stats = serie_categorie.value_counts().reset_index()
        stats.columns = ["Catégorie", "Nombre de tickets"]
        stats = stats.sort_values(by="Nombre de tickets", ascending=True).reset_index(drop=True)[::-1]
        total_tickets = stats["Nombre de tickets"].sum()
        y_pos = np.arange(len(stats))
        bars = current_ax.barh(y_pos, stats["Nombre de tickets"], color=colors[:len(stats)])
        current_ax.set_title(f"Analyse des tickets par catégorie ({chart_type})\n{date_debut.strftime('%d/%m/%Y')} au {date_fin.strftime('%d/%m/%Y')}", 
                     fontsize=14, pad=15)
        current_ax.set_yticks(y_pos)
        current_ax.set_yticklabels(stats["Catégorie"], fontsize=11)
        current_ax.set_xlabel("Nombre de tickets", fontsize=12)
        max_value = stats["Nombre de tickets"].max()
        for bar in bars:
            width = bar.get_width()
            pourcentage = (width / total_tickets) * 100
            current_ax.text(width + max_value * 0.02, bar.get_y() + bar.get_height()/2,
                    f"{int(width)} ({pourcentage:.1f}%)", 
                    va='center', fontsize=10)
        current_ax.spines['top'].set_visible(False)
        current_ax.spines['right'].set_visible(False)
        current_ax.grid(axis='x', linestyle='--', alpha=0.3)
        current_ax.set_xlim(0, max_value * 1.25)
        # Gestion des clics pour les analyses détaillées par compagnie
        if colonne == "compagnie":
            def on_click(event):
                if event.inaxes == current_ax:
                    for bar, label in zip(bars, stats["Catégorie"]):
                        if bar.contains(event)[0]:
                            afficher_types_par_compagnie(label, date_debut, date_fin, radio_chart_type.value_selected)
                            break
            if click_cid:
                fig_main.canvas.mpl_disconnect(click_cid)
            click_cid = fig_main.canvas.mpl_connect('button_press_event', on_click)
        else:
            if click_cid:
                fig_main.canvas.mpl_disconnect(click_cid)
                click_cid = None
        plt.tight_layout(rect=[0.22, 0.15, 0.95, 0.90])
        fig_main.canvas.draw_idle()
    # Graphique circulaire
    elif chart_type == 'Circulaire':
        serie_categorie = df_filtre[colonne].fillna("Autre")
        stats = serie_categorie.value_counts()
        wedges, texts, autotexts = current_ax.pie(stats, autopct='%1.1f%%', startangle=90, colors=colors[:len(stats)],
                                                  pctdistance=0.85)
        # Légende
        current_ax.legend(wedges, stats.index, title=colonnes_disponibles[radio.value_selected], loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        current_ax.set_title(f"Répartition des tickets par catégorie ({chart_type})\n{date_debut.strftime('%d/%m/%Y')} au {date_fin.strftime('%d/%m/%Y')}", 
                     fontsize=14, pad=15)
        current_ax.axis('equal') 
        
        if click_cid:
            fig_main.canvas.mpl_disconnect(click_cid)
            click_cid = None
        ajouter_bouton_export(fig_secondary, current_ax)
        plt.tight_layout()
        plt.show()
    # Graphique en courbe
    elif chart_type == 'Courbe':
        if colonne == "compagnie":
            daily_stats = df_filtre.groupby(['date', colonne]).size().unstack(fill_value=0)
            if not daily_stats.empty:
                for i, col_name in enumerate(daily_stats.columns):
                    current_ax.plot(daily_stats.index, daily_stats[col_name], label=col_name, color=colors[i % len(colors)], marker='o', markersize=4)
                current_ax.legend(title=colonnes_disponibles[radio.value_selected])
            else:
                current_ax.text(0.5, 0.5, "Aucune donnée pour la courbe.", horizontalalignment='center', verticalalignment='center', transform=current_ax.transAxes, fontsize=12, color='gray')
        else:
            daily_stats = df_filtre.groupby(df_filtre['date'].dt.date).size().reset_index(name='Nombre de tickets')
            daily_stats['date'] = pd.to_datetime(daily_stats['date'])
            if not daily_stats.empty:
                current_ax.plot(daily_stats['date'], daily_stats['Nombre de tickets'], marker='o', linestyle='-', color='blue', label='Nombre de tickets')
                current_ax.legend()
            else:
                current_ax.text(0.5, 0.5, "Aucune donnée pour la courbe.", horizontalalignment='center', verticalalignment='center', transform=current_ax.transAxes, fontsize=12, color='gray')
            
        current_ax.set_title(f"Tendance des tickets par jour ({chart_type})\n{date_debut.strftime('%d/%m/%Y')} au {date_fin.strftime('%d/%m/%Y')}", 
                     fontsize=14, pad=15)
        current_ax.set_xlabel("Date", fontsize=12)
        current_ax.set_ylabel("Nombre de tickets", fontsize=12)
        current_ax.grid(True, linestyle='--', alpha=0.6)
        fig_secondary.autofmt_xdate()
        if click_cid:
            fig_main.canvas.mpl_disconnect(click_cid)
            click_cid = None
        ajouter_bouton_export(fig_secondary, current_ax)
        plt.tight_layout()
        plt.show()
def generer_rapport(event):
    """Génère un rapport Excel complet des données analysées."""
    # Vérification des dates
    if not date_valide(text_box_debut.text) or not date_valide(text_box_fin.text):
        msg_text.set_text("Impossible de générer le rapport. Veuillez vérifier les dates saisies.")
        msg_text.set_color('red')
        fig_main.canvas.draw_idle()
        return
    try:
        # Validation des dates
        date_debut = pd.to_datetime(text_box_debut.text)
        date_fin = pd.to_datetime(text_box_fin.text)
        if date_debut > date_fin:
            msg_text.set_text("La date de début ne peut pas être après la date de fin.")
            msg_text.set_color('red')
            fig_main.canvas.draw_idle()
            return
    except:
        msg_text.set_text("Impossible de générer le rapport. Veuillez vérifier les dates saisies.")
        msg_text.set_color('red')
        fig_main.canvas.draw_idle()
        return
    # Filtrage des données
    df_filtre = df[(df['date'] >= date_debut) & (df['date'] <= date_fin)].copy()
    df_filtre['Nb demandes'] = 1
    # Vérification des données
    if df_filtre.empty:
        msg_text.set_text("Aucune donnée disponible pour ce rapport.")
        msg_text.set_color('red')
        fig_main.canvas.draw_idle()
        return
    try:
        # Création du fichier Excel
        with pd.ExcelWriter("rapport_analyse_tickets.xlsx", engine='xlsxwriter') as writer:
            # Feuille de résumé
            resume = pd.DataFrame({
                "Élément": ["Date début", "Date fin", "Total des tickets"],
                "Valeur": [date_debut.strftime("%Y-%m-%d"), date_fin.strftime("%Y-%m-%d"), len(df_filtre)]
            })
            resume.to_excel(writer, sheet_name="Résumé", index=False)
            worksheet = writer.sheets["Résumé"]
            for i, col in enumerate(resume.columns):
                worksheet.set_column(i, i, max(resume[col].astype(str).map(len).max(), len(col)) + 2)   
            # Analyses par catégorie
            regroupements = {
                "Compagnie": "compagnie",
                "Type de demande": "type_demande",
                "Priorité": "priorite",
                "Classification": "classification"
            }
            # Nettoyage des données
            df_filtre["compagnie"] = df_filtre["compagnie"].fillna("Autre")
            df_filtre["type_demande"] = df_filtre["type_demande"].fillna("Autre")
            # Création des feuilles par catégorie
            for nom_feuille, nom_colonne in regroupements.items():
                stats = df_filtre.groupby(nom_colonne)['Nb demandes'].sum().reset_index()
                stats.columns = [nom_feuille, "Nombre de demandes"]
                stats.to_excel(writer, sheet_name=f"Par {nom_feuille}", index=False)
                worksheet = writer.sheets[f"Par {nom_feuille}"]
                for i, col in enumerate(stats.columns):
                    worksheet.set_column(i, i, max(stats[col].astype(str).map(len).max(), len(col)) + 2)
            # Analyse détaillée par compagnie et type
            total_par_compagnie = df_filtre.groupby("compagnie").size().reset_index(name="Total demandes")
            top_types = df_filtre.groupby(["compagnie", "type_demande"]).size().reset_index(name="Nb")
            merged = pd.merge(top_types, total_par_compagnie, on="compagnie")
            merged["%"] = (merged["Nb"] / merged["Total demandes"] * 100).round(2)
            merged = merged.sort_values(["compagnie", "%"], ascending=[True, False])
            merged.rename(columns={"type_demande": "Type de demande"}, inplace=True)
            merged.to_excel(writer, sheet_name="Types par compagnie", index=False)
            worksheet = writer.sheets["Types par compagnie"]
            for i, col in enumerate(merged.columns):
                worksheet.set_column(i, i, max(merged[col].astype(str).map(len).max(), len(col)) + 2)
        # Message de succès
        msg_text.set_text("Rapport Excel généré avec succès.")
        msg_text.set_color('green')
    except Exception as e:
        # Message d'erreur
        msg_text.set_text(f"Erreur lors de la génération : {str(e)}")
        msg_text.set_color('red')
    # Mise à jour de l'affichage
    fig_main.canvas.draw_idle()
def exporter_tout_pdf(event):
    """Exporte tous les graphiques dans un seul fichier PDF."""
    # Vérification des dates
    if not date_valide(text_box_debut.text) or not date_valide(text_box_fin.text):
        msg_text.set_text("Impossible d'exporter en PDF. Veuillez vérifier les dates saisies.")
        msg_text.set_color('red')
        fig_main.canvas.draw_idle()
        return
    try:
        # Validation des dates
        date_debut = pd.to_datetime(text_box_debut.text)
        date_fin = pd.to_datetime(text_box_fin.text)
        if date_debut > date_fin:
            msg_text.set_text("La date de début ne peut pas être après la date de fin.")
            msg_text.set_color('red')
            fig_main.canvas.draw_idle()
            return
    except:
        msg_text.set_text("Impossible d'exporter en PDF. Veuillez vérifier les dates saisies.")
        msg_text.set_color('red')
        fig_main.canvas.draw_idle()
        return
    # Filtrage des données
    df_filtre = df[(df['date'] >= date_debut) & (df['date'] <= date_fin)].copy()
    # Vérification des données
    if df_filtre.empty:
        msg_text.set_text("Aucune donnée pour la période spécifiée.")
        msg_text.set_color('red')
        fig_main.canvas.draw_idle()
        return
    try:
        # Création du fichier PDF
        fichier_pdf = f"rapport_complet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        with PdfPages(fichier_pdf) as pdf:
            # Génération des graphiques pour chaque type et chaque catégorie
            chart_types_to_export = ['Barres', 'Circulaire', 'Courbe']
            for chart_type_export in chart_types_to_export:
                for nom, col in colonnes_disponibles.items():
                    fig_temp, ax_temp = plt.subplots(figsize=(14, 8))
                    # Graphique à barres
                    if chart_type_export == 'Barres':
                        stats = df_filtre[col].fillna("Autre").value_counts().reset_index()
                        stats.columns = ["Catégorie", "Nombre"]
                        stats = stats.sort_values(by="Nombre", ascending=True)[::-1]
                        y_pos = np.arange(len(stats))
                        bars = ax_temp.barh(y_pos, stats["Nombre"], color=colors[:len(stats)])
                        ax_temp.set_title(f"{nom} - {date_debut.strftime('%d/%m/%Y')} au {date_fin.strftime('%d/%m/%Y')} (Barres)", 
                                        fontsize=14, pad=15)
                        ax_temp.set_yticks(y_pos)
                        ax_temp.set_yticklabels(stats["Catégorie"], fontsize=11)
                        ax_temp.set_xlabel("Nombre de tickets", fontsize=12)
                        max_value = stats["Nombre"].max()
                        for bar in bars:
                            width = bar.get_width()
                            ax_temp.text(width + max_value * 0.02, bar.get_y() + bar.get_height()/2,
                                        f"{int(width)}", va='center', fontsize=10)
                        ax_temp.grid(axis='x', linestyle='--', alpha=0.3)
                    # Graphique circulaire
                    elif chart_type_export == 'Circulaire':
                        stats = df_filtre[col].fillna("Autre").value_counts()
                        wedges, texts, autotexts = ax_temp.pie(stats, autopct='%1.1f%%', startangle=90, colors=colors[:len(stats)],
                                                               pctdistance=0.85)
                        ax_temp.legend(wedges, stats.index, title=nom, loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))

                        ax_temp.set_title(f"Répartition des {nom.lower()} ({chart_type_export})\n{date_debut.strftime('%d/%m/%Y')} au {date_fin.strftime('%d/%m/%Y')}", 
                                        fontsize=14, pad=15)
                        ax_temp.axis('equal')
                    # Graphique en courbe
                    elif chart_type_export == 'Courbe':
                        if col == "compagnie":
                            daily_stats = df_filtre.groupby(['date', col]).size().unstack(fill_value=0)
                            if not daily_stats.empty:
                                for i, c_name in enumerate(daily_stats.columns):
                                    ax_temp.plot(daily_stats.index, daily_stats[c_name], label=c_name, color=colors[i % len(colors)], marker='o', markersize=4)
                                ax_temp.legend(title=nom)
                            else:
                                ax_temp.text(0.5, 0.5, "Aucune donnée pour la courbe.", horizontalalignment='center', verticalalignment='center', transform=ax_temp.transAxes, fontsize=12, color='gray')
                        else:
                            daily_stats = df_filtre.groupby(df_filtre['date'].dt.date).size().reset_index(name='Nombre de tickets')
                            daily_stats['date'] = pd.to_datetime(daily_stats['date'])
                            if not daily_stats.empty:
                                ax_temp.plot(daily_stats['date'], daily_stats['Nombre de tickets'], marker='o', linestyle='-', color='blue', label='Nombre de tickets')
                                ax_temp.legend()
                            else:
                                ax_temp.text(0.5, 0.5, "Aucune donnée pour la courbe.", horizontalalignment='center', verticalalignment='center', transform=ax_temp.transAxes, fontsize=12, color='gray')
                        
                        ax_temp.set_title(f"Tendance des tickets par jour ({chart_type_export})\n{date_debut.strftime('%d/%m/%Y')} au {date_fin.strftime('%d/%m/%Y')}", 
                                         fontsize=14, pad=15)
                        ax_temp.set_xlabel("Date", fontsize=12)
                        ax_temp.set_ylabel("Nombre de tickets", fontsize=12)
                        ax_temp.grid(True, linestyle='--', alpha=0.6)
                        fig_temp.autofmt_xdate()

                    plt.tight_layout()
                    pdf.savefig(fig_temp)
                    plt.close(fig_temp)
            # Analyses détaillées par compagnie
            companies = df_filtre['compagnie'].fillna("Autre").unique()
            for chart_type_export in chart_types_to_export:
                for company in companies:
                    df_company = df_filtre[df_filtre['compagnie'].fillna("Autre") == company]
                    df_company["type_demande_filled"] = df_company["type_demande"].fillna("Autre")
                    if not df_company.empty:
                        fig_company, ax_company = plt.subplots(figsize=(14, 8))
                        # Graphique à barres par compagnie
                        if chart_type_export == 'Barres':
                            stats_company = df_company["type_demande_filled"].value_counts().reset_index()
                            stats_company.columns = ["Type de demande", "Nombre de tickets"]
                            stats_company = stats_company.sort_values(by="Nombre de tickets", ascending=True).reset_index(drop=True)[::-1]
                            total_company = stats_company["Nombre de tickets"].sum()
                            y_pos_company = np.arange(len(stats_company))
                            bars_company = ax_company.barh(y_pos_company, stats_company["Nombre de tickets"], color=colors[:len(stats_company)])
                            ax_company.set_title(f"Analyse détaillée pour {company}\n{date_debut.strftime('%d/%m/%Y')} au {date_fin.strftime('%d/%m/%Y')} (Barres)", 
                                                 fontsize=14, pad=20)
                            ax_company.set_yticks(y_pos_company)
                            ax_company.set_yticklabels(stats_company["Type de demande"], fontsize=11)
                            ax_company.set_xlabel("Nombre de tickets", fontsize=12)
                            max_value_company = stats_company["Nombre de tickets"].max()
                            for bar in bars_company:
                                width = bar.get_width()
                                pourcentage = (width / total_company) * 100
                                ax_company.text(width + max_value_company * 0.02, bar.get_y() + bar.get_height()/2,
                                                f"{int(width)} ({pourcentage:.1f}%)", 
                                                va='center', fontsize=10)
                            ax_company.spines['top'].set_visible(False)
                            ax_company.spines['right'].set_visible(False)
                            ax_company.grid(axis='x', linestyle='--', alpha=0.3)
                            ax_company.set_xlim(0, max_value_company * 1.25)
                        # Graphique circulaire par compagnie
                        elif chart_type_export == 'Circulaire':
                            stats_company = df_company["type_demande_filled"].value_counts()
                            wedges_c, texts_c, autotexts_c = ax_company.pie(stats_company, autopct='%1.1f%%', startangle=90, colors=colors[:len(stats_company)],
                                                                            pctdistance=0.85)
                            ax_company.legend(wedges_c, stats_company.index, title="Types de demande", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))

                            ax_company.set_title(f"Répartition des types de demande pour {company}\n{date_debut.strftime('%d/%m/%Y')} au {date_fin.strftime('%d/%m/%Y')} (Circulaire)", 
                                                 fontsize=14, pad=20)
                            ax_company.axis('equal')

                        # Graphique en courbe par compagnie
                        elif chart_type_export == 'Courbe':
                            daily_company_stats = df_company.groupby(df_company['date'].dt.date).size().reset_index(name='Nombre de tickets')
                            daily_company_stats['date'] = pd.to_datetime(daily_company_stats['date'])
                            if not daily_company_stats.empty:
                                ax_company.plot(daily_company_stats['date'], daily_company_stats['Nombre de tickets'], marker='o', linestyle='-', color='blue', label='Nombre de tickets')
                                ax_company.legend()
                            else:
                                ax_company.text(0.5, 0.5, "Aucune donnée quotidienne pour cette période.", horizontalalignment='center', verticalalignment='center', transform=ax_company.transAxes, fontsize=12, color='gray')
                            ax_company.set_title(f"Nombre de tickets par jour pour {company}\n{date_debut.strftime('%d/%m/%Y')} au {date_fin.strftime('%d/%m/%Y')} (Courbe)", 
                                                 fontsize=14, pad=20)
                            ax_company.set_xlabel("Date", fontsize=12)
                            ax_company.set_ylabel("Nombre de tickets", fontsize=12)
                            ax_company.grid(True, linestyle='--', alpha=0.6)
                            fig_company.autofmt_xdate()

                        plt.tight_layout()
                        pdf.savefig(fig_company)
                        plt.close(fig_company)
        
        # Message de succès
        msg_text.set_text(f"Rapport PDF généré : {fichier_pdf}")
        msg_text.set_color('green')
    except Exception as e:
        # Message d'erreur
        msg_text.set_text(f"Erreur PDF : {str(e)}")
        msg_text.set_color('red')
    
    # Mise à jour de l'interface principale
    if radio_chart_type.value_selected == 'Barres':
        update_graph(text_box_debut.text, text_box_fin.text, colonnes_disponibles[radio.value_selected], 'Barres')
    else:
        ax_main.clear()
        ax_main.text(0.5, 0.5, "Sélectionnez 'Barres' pour afficher le graphique ici, ou ouvrez un autre type de graphique.",
                     horizontalalignment='center', verticalalignment='center', transform=ax_main.transAxes, fontsize=12, color='gray', wrap=True)
        fig_main.canvas.draw_idle()
# CONFIGURATION DES ÉVÉNEMENTS ET LANCEMENT DE L'APPLICATION
# Fonctions de rappel pour les événements
def on_submit_date(text):
    """Met à jour le graphique quand une date est soumise."""
    update_graph(text_box_debut.text, text_box_fin.text, colonnes_disponibles[radio.value_selected], radio_chart_type.value_selected)
def on_radio_selected(label):
    #Met à jour le graphique quand une catégorie est sélectionnée.
    update_graph(text_box_debut.text, text_box_fin.text, colonnes_disponibles[label], radio_chart_type.value_selected)
def on_chart_type_selected(label):
    #Met à jour le graphique quand un type de visualisation est sélectionné.
    if label != 'Barres':
        ax_main.clear()
        ax_main.text(0.5, 0.5, 
                     horizontalalignment='center', verticalalignment='center', transform=ax_main.transAxes, fontsize=12, color='gray', wrap=True)
        fig_main.canvas.draw_idle()
    update_graph(text_box_debut.text, text_box_fin.text, colonnes_disponibles[radio.value_selected], label)
# Liaison des événements aux widgets
text_box_debut.on_submit(on_submit_date)
text_box_fin.on_submit(on_submit_date)
radio.on_clicked(on_radio_selected)
radio_chart_type.on_clicked(on_chart_type_selected)
bouton.on_clicked(generer_rapport)
bouton_pdf.on_clicked(exporter_tout_pdf)
# Initialisation de l'interface avec les données par défaut
update_graph(str(min_date), str(max_date), 'compagnie', 'Barres')
plt.show()