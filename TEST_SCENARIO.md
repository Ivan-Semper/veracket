# 🧪 Test Scenario's voor Ronde-gebaseerde Planning

## 📊 Training Capaciteiten
- **Maandag 19:00 - Beginners Training (Niveau 6-9)**: Capaciteit 3 personen
- **Dinsdag 20:00 - Gevorderden Training (Niveau 3-5)**: Capaciteit 2 personen  
- **Woensdag 18:00 - Gemengd Training (Niveau 4-7)**: Capaciteit 4 personen

## 👥 Test Personen & Hun Edge Cases

### 🎯 **Ronde 1 - Eerste Training (12 personen)**

#### ✅ **Verwachte Succesvolle Toewijzingen:**
1. **Jan de Vries** (Niveau 5, 2x/week) → Zou NIET passen in Maandag Beginners (niveau te laag)
2. **Marie Jansen** (Niveau 8, 1x/week) → Maandag Beginners Training ✅
3. **Piet Bakker** (Niveau 3, 3x/week) → Dinsdag Gevorderden Training ✅  
4. **Anna Smit** (Niveau 1, 2x/week) → Zou NIET passen in Dinsdag Gevorderden (niveau te laag)
5. **Lisa van Dam** (Niveau 9, 1x/week) → Maandag Beginners Training ✅
6. **Tom Hendriks** (Niveau 6, 3x/week) → Maandag Beginners Training ✅
7. **Emma de Wit** (Niveau 4, 2x/week) → Woensdag Gemengd Training ✅
8. **Kevin Mulder** (Niveau 2, 1x/week) → Zou NIET passen in Dinsdag Gevorderden (niveau te laag)
9. **Sarah Koning** (Niveau 7, 2x/week) → Zou proberen Maandag Beginners (vol), dan Woensdag Gemengd ✅
10. **Mike Peters** (Niveau 5, 3x/week) → Woensdag Gemengd Training ✅

#### ❌ **Verwachte Handmatige Gevallen:**
- **Sophie Berg** (Niveau 10) - "Niveau te hoog voor alle trainingen"
- **Alex de Jong** (Niveau 0) - "Niveau te laag voor alle trainingen"  
- **Jan de Vries** (Niveau 5) - "Alle voorkeuren zaten vol of geen match"
- **Anna Smit** (Niveau 1) - "Alle voorkeuren zaten vol of geen match"
- **Kevin Mulder** (Niveau 2) - "Alle voorkeuren zaten vol of geen match"

### 🎯 **Ronde 2 - Tweede Training (8 personen die 2x/3x willen)**

**Gefilterd:** Alleen Jan, Piet, Anna, Tom, Emma, Sarah, Mike, Alex

**Verwachte capaciteit na Ronde 1:**
- Maandag Beginners: 0 plekken over (Marie, Lisa, Tom)
- Dinsdag Gevorderden: 1 plek over (Piet)  
- Woensdag Gemengd: 2 plekken over (Emma, Mike)

#### ✅ **Verwachte Succesvolle Toewijzingen:**
- **Sarah Koning** → Dinsdag Gevorderden (1 plek beschikbaar) ✅
- **Tom Hendriks** → Mogelijk Woensdag Gemengd ✅

#### ❌ **Verwachte Handmatige Gevallen:**
- **Jan de Vries, Anna Smit, Alex de Jong** - Niveau problemen
- **Piet Bakker, Mike Peters** - Mogelijk capaciteitsproblemen

### 🎯 **Ronde 3 - Derde Training (3 personen die 3x willen)**

**Gefilterd:** Alleen Piet, Tom, Mike

**Minimale capaciteit over** - Meeste edge cases voor handmatige toewijzing.

## 🧪 **Test Checklist**

### ✅ **Te Testen Functionaliteiten:**

1. **Automatische Filtering:**
   - [ ] Ronde 1: Alle 12 personen zichtbaar
   - [ ] Ronde 2: Alleen 8 personen (2x/3x per week)
   - [ ] Ronde 3: Alleen 3 personen (3x per week)

2. **Edge Cases:**
   - [ ] Niveau te hoog (Sophie Berg - niveau 10)
   - [ ] Niveau te laag (Alex de Jong - niveau 0)  
   - [ ] Capaciteit vol (meerdere mensen willen Maandag Beginners)
   - [ ] Niveau net buiten range (Jan niveau 5 voor Beginners 6-9)

3. **Handmatige Toewijzing:**
   - [ ] Dropdown toont alle trainingen
   - [ ] Handmatige toewijzing werkt
   - [ ] Handmatig toegewezen mensen worden uitgesloten van volgende ronde

4. **Capaciteit Beheer:**
   - [ ] Ronde 2 houdt rekening met bezette plekken uit Ronde 1
   - [ ] Ronde 3 houdt rekening met bezette plekken uit Ronde 1 & 2

5. **Ronde Voltooiing:**
   - [ ] Ronde kan pas worden voltooid na behandeling edge cases
   - [ ] Volgende ronde wordt beschikbaar na voltooiing
   - [ ] Reset functionaliteit werkt

6. **Download Functie:**
   - [ ] Finale planning bevat alle rondes
   - [ ] Toont automatische en handmatige toewijzingen
   - [ ] Correct ronde nummer per toewijzing

## 🎮 **Hoe te Testen:**

1. **Start Admin Dashboard** → **🎯 Ronde Planning**
2. **Ronde 1:** Klik "🚀 Start Ronde 1 Planning"
3. **Bekijk resultaten** en behandel handmatige gevallen
4. **Voltooi Ronde 1** en ga naar Ronde 2
5. **Herhaal** voor Ronde 2 en 3
6. **Download** finale planning

## 🔍 **Verwachte Uitkomst:**

- **~6-7 mensen** automatisch toegewezen in Ronde 1
- **~5-6 mensen** handmatig in Ronde 1  
- **~3-4 mensen** automatisch toegewezen in Ronde 2
- **~4-5 mensen** handmatig in Ronde 2
- **~1-2 mensen** automatisch toegewezen in Ronde 3
- **~1-2 mensen** handmatig in Ronde 3

Dit geeft een goede mix van automatische en handmatige toewijzingen om het systeem volledig te testen! 