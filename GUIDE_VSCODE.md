# 🔧 Guide Rapide : Changer l'Environnement Python dans VS Code

## ✨ Méthode la plus simple (Recommandée)

### Étape 1 : Ouvrir la sélection d'interpréteur
Appuyez sur : **`Ctrl + Shift + P`**

### Étape 2 : Taper la commande
Tapez : **`Python: Select Interpreter`** puis **Entrée**

### Étape 3 : Sélectionner l'environnement
Choisissez : **`Python 3.x.x ('./venv': venv)`**

---

## 📍 OU : Via la barre d'état

**En bas à gauche** de VS Code, vous verrez : `Python 3.13.x`
- **Cliquez dessus** directement
- Sélectionnez **`('./venv': venv)`**

---

## ✅ Comment savoir si ça a marché ?

Après sélection, en bas à gauche vous verrez :
```
Python 3.x.x ('./venv': venv)
```

---

## 🚀 Prochaine étape : Installer les packages

Une fois l'environnement `venv` sélectionné, dans le terminal :

```powershell
pip install -r requirements.txt
```

Cela installera toutes les dépendances nécessaires pour le projet TER.

---

## ❓ Si vous ne voyez pas 'venv' dans la liste

1. Fermez et rouvrez VS Code
2. Ou cliquez sur **"Refresh"** dans la liste des interpréteurs
3. Ou appuyez sur **`Ctrl + Shift + P`** → **`Python: Refresh Interpreters`**
