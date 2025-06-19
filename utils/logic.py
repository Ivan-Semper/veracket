import pandas as pd
from collections import defaultdict

def plan_spelers(inschrijvingen, trainingen):
    trainingen = trainingen.copy()
    trainingen["Beschikbaar"] = trainingen["Capaciteit"] + 1
    toegewezen_per_training = defaultdict(list)
    handmatig = []

    inschrijvingen["Inschrijfdatum"] = pd.to_datetime(inschrijvingen["Inschrijfdatum"], errors='coerce')
    inschrijvingen = inschrijvingen.sort_values("Inschrijfdatum")

    def naar_niveau(nv):
        try:
            return float(str(nv).replace(",", "."))
        except:
            return None

    def vind_training(keuze, niveau):
        if pd.isna(keuze):
            return None, None
        for i, rij in trainingen.iterrows():
            if keuze.strip().startswith(rij["Dag"]):
                if rij["MinNiveau"] <= niveau <= rij["MaxNiveau"] and trainingen.at[i, "Beschikbaar"] > 1:
                    trainingen.at[i, "Beschikbaar"] -= 1
                    # Create training label based on available columns
                    if 'Training Naam' in rij and pd.notna(rij['Training Naam']):
                        # Backward compatibility: use Training Naam if available
                        label = f"{rij['Dag']} {rij['Tijd']} - {rij['Training Naam']}"
                    else:
                        # New format: use trainer name if available
                        trainer_text = f" - {rij['Trainer']}" if pd.notna(rij['Trainer']) and rij['Trainer'].strip() else ""
                        label = f"{rij['Dag']} {rij['Tijd']}{trainer_text}"
                    return label, i
        return None, None

    for _, speler in inschrijvingen.iterrows():
        naam = speler["Naam"]
        niveau = naar_niveau(speler["Niveau"])

        if pd.isna(speler.get("Voorkeur_1")) and pd.isna(speler.get("Voorkeur_2")) and pd.isna(speler.get("Voorkeur_3")):
            reden = "Geen voorkeuren opgegeven"
        elif niveau is None:
            reden = "Niveau ontbreekt"
        elif niveau < trainingen["MinNiveau"].min():
            reden = "Niveau te laag voor alle trainingen"
        elif niveau > trainingen["MaxNiveau"].max():
            reden = "Niveau te hoog voor alle trainingen"
        else:
            reden = "Alle voorkeuren zaten vol of geen match"

        toegewezen, _ = (
            vind_training(speler.get("Voorkeur_1"), niveau)
            or vind_training(speler.get("Voorkeur_2"), niveau)
            or vind_training(speler.get("Voorkeur_3"), niveau)
        )

        if toegewezen:
            toegewezen_per_training[toegewezen].append((naam, niveau))
        else:
            handmatig.append((naam, niveau if niveau is not None else "?", reden))

    return toegewezen_per_training, handmatig