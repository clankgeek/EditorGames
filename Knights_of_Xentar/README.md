# Knights of Xentar (1994) — Save Editor & God Mode Patcher

[![Python](https://img.shields.io/badge/Python-3.6+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-DOS%20%2F%20DOSBox-0078D4?style=flat)](#)
[![Game](https://img.shields.io/badge/Game-Knights%20of%20Xentar%20(1994)-E056FD?style=flat)](#)
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-None%20(Stdlib)-success)](#)

Outil tout-en-un de rétro-ingénierie pour le jeu de rôle culte **Knights of Xentar** (DOS, 1994, Megatech / ELF Corporation). 

Ce script Python permet d'éditer les fichiers de sauvegarde chiffrés (`SAUVEGAR.REC`) et d'appliquer un patch binaire directement sur l'exécutable (`KX.EXE`) pour conférer la vie infinie (God Mode) en combat.

---

## 🌟 Fonctionnalités

### 1. Éditeur de Sauvegarde (`SAUVEGAR.REC`)
Les sauvegardes de *Knights of Xentar* sont protégées par une entête à somme de contrôle et un chiffrement propriétaire par rotation/XOR. Cet outil gère de manière transparente le déchiffrement, la modification, le recalcul des checksums et le ré-encodage.

* **Niveau (Level)** : Modification du niveau de 1 à 99 (par personnage ou toute l'équipe).
* **Points de Vie (HP)** : Modification des HP actuels et max (avec protection contre l'overflow signé 16 bits de l'assembleur x86 du jeu).
* **Points de Magie (MP)** : Définition des PM actuels et max (par défaut 999).
* **Points d'Expérience (EXP)** : Ajustement de l'expérience globale (entier 32 bits non signé).
* **Or (Gold)** : Modification de la bourse d'or (jusqu'à 999 999 ou plus).
* **Ciblage flexible** : Modifiez toute l'équipe d'un coup (`all`) ou un personnage spécifique par son nom (ex: `desmond`) ou son index (`1`, `2`, `3`).

### 2. Patcher de Vie Infinie / God Mode (`KX.EXE`)
Patch chirurgical de la routine de gestion des dégâts en combat à l'offset `0x200A` (`0x1E0A + 0x200`) de l'exécutable DOS :
* **Immunité sélective** : Les membres de l'équipe du joueur ne subissent plus aucun dégât.
* **Intégrité du gameplay** : Les ennemis continuent de subir des dégâts normalement.
* **Réversible à chaud** : Activation (`godmode on`) ou désactivation (`godmode off`) immédiate avec restauration des octets d'origine.

### 3. Sécurité & Sauvegardes automatiques
* **Backups automatiques** : Toute modification crée automatiquement une copie de sauvegarde `.ORIG` (`SAUVEGAR.REC.ORIG` et `KX.EXE.ORIG`) avant écriture.
* **Restauration en un clic** : Commande `restore` pour revenir instantanément à l'état initial.

---

## 📋 Prérequis

* **Python 3.6+**
* Aucune dépendance externe requise (utilise uniquement les modules standards : `sys`, `os`, `shutil`, `struct`).

---

## 🚀 Installation & Organisation des fichiers

Placez le script `xentar_tool.py` directement dans le dossier d'installation du jeu (où se trouvent `KX.EXE` et `SAUVEGAR.REC`) ou créez un lien symbolique :

```text
Knights_of_Xentar/
├── KX.EXE            # Exécutable principal du jeu
├── SAUVEGAR.REC      # Fichier de sauvegarde active
├── xentar_tool.py    # Cet outil
└── README.md
```

---

## 📖 Guide d'utilisation (CLI)

Exécutez le script avec Python 3 en lui passant la commande souhaitée.

```bash
python3 xentar_tool.py [commande] [valeur] [cible]
```

### 1. Afficher l'état actuel (`status`)
Affiche les informations de la sauvegarde (or, membres du groupe, PV, PM, niveau, EXP) ainsi que le statut du God Mode dans l'exécutable.

```bash
python3 xentar_tool.py status
# ou simplement sans argument :
python3 xentar_tool.py
```

**Exemple de sortie :**
```text
=== État actuel de SAUVEGAR.REC ===
Or (Gold) : 999999
-----------------------------------------------------------------
Personnage 1 : Desmond    | Niv : 99 | HP : 30000/30000 | MP : 999/999 | EXP : 50000
Personnage 2 : Rolf       | Niv : 99 | HP : 30000/30000 | MP : 999/999 | EXP : 50000
-----------------------------------------------------------------
Statut KX.EXE : GOD MODE ACTIF (Vie infinie activée pour l'équipe en combat)
```

---

### 2. Modifier le Niveau (`level`)
Définit le niveau (de 1 à 99).

```bash
# Niveau 99 pour toute l'équipe
python3 xentar_tool.py level 99

# Niveau 50 uniquement pour Desmond
python3 xentar_tool.py level 50 desmond

# Niveau 25 pour le personnage 2
python3 xentar_tool.py level 25 2
```

---

### 3. Modifier les Points de Vie (`hp`)
Met à jour simultanément les HP max et actuels.

```bash
# 30 000 HP pour toute l'équipe
python3 xentar_tool.py hp 30000

# 9 999 HP pour Desmond
python3 xentar_tool.py hp 9999 desmond
```

> [!WARNING]
> **Limite x86 16-bit signée :** Dans l'assembleur de `KX.EXE`, la routine de test de mort utilise un saut signé (`jg`). Si les HP dépassent **32 767**, le jeu interprète la valeur comme un nombre négatif et le personnage meurt instantanément au premier coup reçu. L'outil bride et ajuste automatiquement la valeur maximale recommandée à **30 000**.

---

### 4. Modifier les Points de Magie (`mp`)
Ajuste les MP max et actuels.

```bash
# 999 MP pour toute l'équipe
python3 xentar_tool.py mp 999

# 500 MP pour le 2ème personnage
python3 xentar_tool.py mp 500 2
```

---

### 5. Modifier l'Expérience (`exp`)
Modifie les points d'expérience (entier 32 bits non signé).

```bash
# Donner 50 000 points d'expérience à toute l'équipe
python3 xentar_tool.py exp 50000

# Donner 100 000 points uniquement à Desmond
python3 xentar_tool.py exp 100000 desmond
```

---

### 6. Modifier l'Or (`gold`)
Ajuste la bourse générale d'or du joueur.

```bash
python3 xentar_tool.py gold 999999
```

---

### 7. Activer / Désactiver le God Mode (`godmode`)
Applique ou retire le patch binaire dans `KX.EXE`.

```bash
# Activer l'invulnérabilité de l'équipe
python3 xentar_tool.py godmode on

# Restaurer l'exécutable original
python3 xentar_tool.py godmode off
```

---

### 8. Restaurer les originaux (`restore`)
Restaure immédiatement `SAUVEGAR.REC` et `KX.EXE` depuis leurs sauvegardes de secours `.ORIG`.

```bash
python3 xentar_tool.py restore
```

---

## 🔬 Détails Techniques & Rétro-Ingénierie

### Structure du fichier de sauvegarde `SAUVEGAR.REC`

Le fichier de sauvegarde est composé d'une entête fixe de 16 octets suivie du corps de données chiffrées :

| Offset (hex) | Type | Rôle |
|---|---|---|
| `0x00 - 0x01` | ASCII `KX` | Signature magique du fichier |
| `0x02` | `uint8` | Version / marqueur (0x01) |
| `0x03` | `uint8` | Checksum d'entête (complément à 2 pour `sum(header[0..15]) == 0`) |
| `0x04 - 0x05` | `uint16 LE` | Graine initiale de déchiffrement (`seed_dx`) |
| `0x06 - 0x07` | `uint16 LE` | Longueur des données utiles |
| `0x08 - 0x09` | `uint16 LE` | Somme de contrôle attendue des données déchiffrées |
| `0x0A` | `uint8` | Identifiant du slot (ex: `0x43`) |
| `0x0B - 0x0F` | `bytes[5]` | Réservé / zéros |
| `0x10+` | `stream` | Données du jeu chiffrées |

#### Algorithme de chiffrement / déchiffrement
Le chiffrement est un flux basé sur deux registres 8 bits (`dl`, `dh`) initialisés à partir de `seed_dx` :
```python
# Déchiffrement :
b = (encrypted[i] - dh) & 0xFF
b = (b ^ dl) & 0xFF

# Mise à jour des clés de flux :
dl = (dl + dh + 0x49) & 0xFF
dh = (dh ^ dl ^ 0xC5) & 0xFF
```

#### Offsets dans le flux déchiffré
* **Or (Gold)** : `0x7A0` (4 octets, `uint32 LE`)
* **Personnages (Party)** :
  * Personnage 1 : `0x410`
  * Personnage 2 : `0x448`
  * Personnage 3 : `0x480`
  * Structure relative de chaque personnage :
    * `+0x00` : EXP (`uint32 LE`)
    * `+0x04` : Max HP (`uint16 LE`)
    * `+0x06` : Current HP (`uint16 LE`)
    * `+0x08` : Max MP (`uint16 LE`)
    * `+0x0A` : Current MP (`uint16 LE`)
    * `+0x10` : Niveau (`uint8`)
    * `+0x28 - +0x38` : Nom du personnage (chaîne ASCII terminée par null)

---

### Analyse du patch assembleur x86 (`KX.EXE`)

Dans `KX.EXE`, la routine de combat calcule les dégâts infligés au combattant pointé par `SI`.
Le patch intercepte la routine à l'adresse de fichier `0x200A` (`0x1E0A` en mémoire + en-tête MZ de `0x200`) :

```assembly
; === Code Original ===
mov    si, [bp+06]
mov    dx, [bp+04]
mov    al, [si+07]
mov    ah, 00
shl    ax, 1
mov    bx, ax
mov    di, [bx+0x2296]
test   word ptr [si], 0xE000
jne    0x1E9E
mov    byte ptr [si+0x24], 01
or     dx, dx
jg     0x1E32
mov    dx, 0001
mov    byte ptr [si+0x24], 01

; === Code Patché (God Mode) ===
mov    si, [bp+06]
mov    dx, [bp+04]
mov    bl, [si+07]
xor    bh, bh
shl    bx, 1
mov    di, [bx+0x2296]
test   word ptr [si], 0xE000
jne    0x1E9E
cmp    byte ptr [si+07], 06    ; Est-ce un membre de l'équipe du joueur ?
jae    0x1E9E                  ; Si oui : saut direct, immunité totale !
mov    byte ptr [si+0x24], 01
or     dx, dx
jg     0x1E32
mov    dx, 0001
```

---

## 💡 Workflow recommandé avec DOSBox

1. Lancez **Knights of Xentar** dans DOSBox.
2. Effectuez une sauvegarde dans le jeu (qui écrit dans `SAUVEGAR.REC`).
3. Mettez DOSBox en pause ou basculez vers votre terminal.
4. Lancez vos modifications avec `xentar_tool.py` (ex: `python3 xentar_tool.py hp 30000 && python3 xentar_tool.py gold 999999`).
5. Dans le jeu, rechargez la sauvegarde : les nouvelles statistiques sont immédiatement actives !

---

## 📜 Licence & Décharge

Cet outil est distribué à des fins éducatives et de préservation du patrimoine vidéoludique. *Knights of Xentar* est une œuvre originale de ELF Corporation / Megatech Software (1994).
