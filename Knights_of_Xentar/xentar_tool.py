#!/usr/bin/env python3
"""
Knights of Xentar (1994) - Save Editor & God Mode Patcher
---------------------------------------------------------
Permet de modifier le niveau (Level), les points de vie (HP),
les points de magie (MP), l'or (Gold) et l'expérience (EXP) dans SAUVEGAR.REC
et d'activer/désactiver la vie infinie (God Mode) dans KX.EXE.
"""

import sys
import os
import shutil
import struct

SAVE_FILE = "SAUVEGAR.REC"
SAVE_BACKUP = "SAUVEGAR.REC.ORIG"
EXE_FILE = "KX.EXE"
EXE_BACKUP = "KX.EXE.ORIG"

PARTY_OFFSETS = [0x410, 0x448, 0x480]
GOLD_OFFSET = 0x7A0


def decrypt_save(file_path):
    with open(file_path, "rb") as f:
        data = bytearray(f.read())

    if len(data) < 16 or data[0:2] != b"KX":
        raise ValueError(f"Fichier invalide ou signature 'KX' manquante dans {file_path}")

    if (sum(data[:16]) & 0xFF) != 0:
        raise ValueError("Checksum de l'entête du fichier de sauvegarde invalide !")

    seed_dx = data[4] | (data[5] << 8)
    length = data[6] | (data[7] << 8)
    expected_chk = data[8] | (data[9] << 8)
    slot_type = data[10]

    dl = seed_dx & 0xFF
    dh = (seed_dx >> 8) & 0xFF

    decrypted = bytearray(data[16 : 16 + length])
    al = 0
    ah = 0

    for i in range(length):
        b = (decrypted[i] - dh) & 0xFF
        b = (b ^ dl) & 0xFF
        decrypted[i] = b

        al = (al + b) & 0xFF
        ah = (ah ^ b) & 0xFF

        dl = (dl + dh + 0x49) & 0xFF
        dh = (dh ^ dl ^ 0xC5) & 0xFF

    calc_chk = al | (ah << 8)
    if calc_chk != expected_chk:
        raise ValueError(f"Erreur checksum données: calculé {hex(calc_chk)} != attendu {hex(expected_chk)}")

    return decrypted, seed_dx, slot_type


def encrypt_save(decrypted_data, seed_dx=0x71FB, slot_type=0x43):
    length = len(decrypted_data)
    enc = bytearray(decrypted_data)

    dl = seed_dx & 0xFF
    dh = (seed_dx >> 8) & 0xFF

    al = 0
    ah = 0

    for i in range(length):
        b = enc[i]
        al = (al + b) & 0xFF
        ah = (ah ^ b) & 0xFF

        b = (b ^ dl) & 0xFF
        b = (b + dh) & 0xFF
        enc[i] = b

        dl = (dl + dh + 0x49) & 0xFF
        dh = (dh ^ dl ^ 0xC5) & 0xFF

    h = bytearray(16)
    h[0] = ord("K")
    h[1] = ord("X")
    h[2] = 1
    h[3] = 0
    h[4] = seed_dx & 0xFF
    h[5] = (seed_dx >> 8) & 0xFF
    h[6] = length & 0xFF
    h[7] = (length >> 8) & 0xFF
    h[8] = al
    h[9] = ah
    h[10] = slot_type

    s = sum(h) & 0xFF
    h[3] = (-s) & 0xFF

    return bytes(h + enc)


def get_party_info(decrypted):
    party = []
    for base in PARTY_OFFSETS:
        name_raw = decrypted[base + 0x28 : base + 0x38]
        null_idx = name_raw.find(b"\x00")
        if null_idx != -1:
            name_raw = name_raw[:null_idx]
        name = name_raw.decode("latin1", errors="ignore")

        exp_val = struct.unpack("<I", decrypted[base : base + 4])[0]
        max_hp = struct.unpack("<H", decrypted[base + 4 : base + 6])[0]
        cur_hp = struct.unpack("<H", decrypted[base + 6 : base + 8])[0]
        max_mp = struct.unpack("<H", decrypted[base + 8 : base + 10])[0]
        cur_mp = struct.unpack("<H", decrypted[base + 10 : base + 12])[0]
        
        # Le niveau est un octet (uint8) à l'offset +0x10
        lvl = decrypted[base + 0x10]

        party.append({
            "name": name,
            "base": base,
            "exp": exp_val,
            "max_hp": max_hp,
            "cur_hp": cur_hp,
            "max_mp": max_mp,
            "cur_mp": cur_mp,
            "level": lvl
        })
    gold = struct.unpack("<I", decrypted[GOLD_OFFSET : GOLD_OFFSET + 4])[0]
    return party, gold


def show_save_status():
    if not os.path.exists(SAVE_FILE):
        print(f"Fichier {SAVE_FILE} introuvable.")
        return

    decrypted, _, _ = decrypt_save(SAVE_FILE)
    party, gold = get_party_info(decrypted)

    print(f"\n=== État actuel de {SAVE_FILE} ===")
    print(f"Or (Gold) : {gold}")
    print("-" * 65)
    for i, p in enumerate(party, 1):
        if p["name"]:
            print(f"Personnage {i} : {p['name']:<10} | Niv : {p['level']:<2} | HP : {p['cur_hp']}/{p['max_hp']:<5} | MP : {p['cur_mp']}/{p['max_mp']:<3} | EXP : {p['exp']}")
    print("-" * 65)


def _filter_party(party, target):
    target = target.lower()
    if target in ["all", "tous", "all_party", "*"]:
        return party
    res = []
    for i, p in enumerate(party, 1):
        if target in [str(i), p["name"].lower()]:
            res.append(p)
    if not res:
        print(f"Attention : personnage '{target}' non trouvé. Application à toute l'équipe.")
        return party
    return res


def modify_level(level_value=99, target="all"):
    if not os.path.exists(SAVE_FILE):
        print(f"Erreur : {SAVE_FILE} introuvable.")
        return

    if not os.path.exists(SAVE_BACKUP):
        shutil.copy(SAVE_FILE, SAVE_BACKUP)
        print(f"Sauvegarde originale copiée vers {SAVE_BACKUP}")

    if level_value < 1:
        level_value = 1
    elif level_value > 99:
        print(f"Note : Le niveau maximum officiel dans Knights of Xentar est 99.")
        if level_value > 255:
            level_value = 99

    decrypted, seed_dx, slot_type = decrypt_save(SAVE_FILE)
    party, _ = get_party_info(decrypted)
    targets = _filter_party(party, target)

    for p in targets:
        base = p["base"]
        decrypted[base + 0x10] = level_value
        print(f"Niveau de {p['name']} réglé à {level_value}")

    re_encrypted = encrypt_save(decrypted, seed_dx, slot_type)
    with open(SAVE_FILE, "wb") as f:
        f.write(re_encrypted)
    print(f"Fichier {SAVE_FILE} mis à jour avec succès !")


def modify_hp(hp_value=30000, target="all"):
    if not os.path.exists(SAVE_FILE):
        print(f"Erreur : {SAVE_FILE} introuvable.")
        return

    if not os.path.exists(SAVE_BACKUP):
        shutil.copy(SAVE_FILE, SAVE_BACKUP)
        print(f"Sauvegarde originale copiée vers {SAVE_BACKUP}")

    # Limite signée x86 dans KX.EXE : la vérification de mort en combat utilise 'jg' (signed 16-bit)
    if hp_value > 32767:
        print(f"Attention : la valeur {hp_value} dépasse 32767 (limite entière signée 16-bit).")
        print("Ajustement automatique à 30000 pour éviter d'être considéré comme mort en combat.")
        hp_value = 30000

    decrypted, seed_dx, slot_type = decrypt_save(SAVE_FILE)
    party, _ = get_party_info(decrypted)
    targets = _filter_party(party, target)

    hp_bytes = struct.pack("<H", hp_value)

    for p in targets:
        base = p["base"]
        decrypted[base + 4 : base + 6] = hp_bytes
        decrypted[base + 6 : base + 8] = hp_bytes
        print(f"HP de {p['name']} réglés à {hp_value}/{hp_value}")

    re_encrypted = encrypt_save(decrypted, seed_dx, slot_type)
    with open(SAVE_FILE, "wb") as f:
        f.write(re_encrypted)
    print(f"Fichier {SAVE_FILE} ré-encodé et sauvegardé avec succès !")


def modify_mp(mp_value=999, target="all"):
    if not os.path.exists(SAVE_FILE):
        print(f"Erreur : {SAVE_FILE} introuvable.")
        return

    if not os.path.exists(SAVE_BACKUP):
        shutil.copy(SAVE_FILE, SAVE_BACKUP)
        print(f"Sauvegarde originale copiée vers {SAVE_BACKUP}")

    if mp_value > 32767:
        mp_value = 999

    decrypted, seed_dx, slot_type = decrypt_save(SAVE_FILE)
    party, _ = get_party_info(decrypted)
    targets = _filter_party(party, target)

    mp_bytes = struct.pack("<H", mp_value)

    for p in targets:
        base = p["base"]
        decrypted[base + 8 : base + 10] = mp_bytes
        decrypted[base + 10 : base + 12] = mp_bytes
        print(f"MP de {p['name']} réglés à {mp_value}/{mp_value}")

    re_encrypted = encrypt_save(decrypted, seed_dx, slot_type)
    with open(SAVE_FILE, "wb") as f:
        f.write(re_encrypted)
    print(f"Fichier {SAVE_FILE} ré-encodé et sauvegardé avec succès !")


def modify_exp(exp_value=50000, target="all"):
    if not os.path.exists(SAVE_FILE):
        print(f"Erreur : {SAVE_FILE} introuvable.")
        return

    if not os.path.exists(SAVE_BACKUP):
        shutil.copy(SAVE_FILE, SAVE_BACKUP)
        print(f"Sauvegarde originale copiée vers {SAVE_BACKUP}")

    decrypted, seed_dx, slot_type = decrypt_save(SAVE_FILE)
    party, _ = get_party_info(decrypted)
    targets = _filter_party(party, target)

    exp_bytes = struct.pack("<I", exp_value)

    for p in targets:
        base = p["base"]
        decrypted[base : base + 4] = exp_bytes
        print(f"EXP de {p['name']} réglée à {exp_value}")

    re_encrypted = encrypt_save(decrypted, seed_dx, slot_type)
    with open(SAVE_FILE, "wb") as f:
        f.write(re_encrypted)
    print(f"Fichier {SAVE_FILE} ré-encodé et sauvegardé avec succès !")


def modify_gold(gold_value=999999):
    if not os.path.exists(SAVE_FILE):
        print(f"Erreur : {SAVE_FILE} introuvable.")
        return

    if not os.path.exists(SAVE_BACKUP):
        shutil.copy(SAVE_FILE, SAVE_BACKUP)
        print(f"Sauvegarde originale copiée vers {SAVE_BACKUP}")

    decrypted, seed_dx, slot_type = decrypt_save(SAVE_FILE)
    decrypted[GOLD_OFFSET : GOLD_OFFSET + 4] = struct.pack("<I", gold_value)

    re_encrypted = encrypt_save(decrypted, seed_dx, slot_type)
    with open(SAVE_FILE, "wb") as f:
        f.write(re_encrypted)
    print(f"Or réglé à {gold_value} dans {SAVE_FILE} !")


# --- PATCH KX.EXE POUR VIE INFINIE (GOD MODE) ---
PATCH_OFFSET = 0x1E0A + 0x200  # 0x200a dans le fichier

ORIGINAL_BYTES = bytes([
    0x8B, 0x76, 0x06,             # mov si, [bp+6]
    0x8B, 0x56, 0x04,             # mov dx, [bp+4]
    0x8A, 0x44, 0x07,             # mov al, [si+7]
    0xB4, 0x00,                   # mov ah, 0
    0xD1, 0xE0,                   # shl ax, 1
    0x8B, 0xD8,                   # mov bx, ax
    0x8B, 0xBF, 0x96, 0x22,       # mov di, [bx+0x2296]
    0xF7, 0x04, 0x00, 0xE0,       # test word ptr [si], 0xe000
    0x75, 0x7B,                   # jne 0x1e9e
    0xC6, 0x44, 0x24, 0x01,       # mov byte ptr [si+0x24], 1
    0x0B, 0xD2,                   # or dx, dx
    0x7F, 0x07,                   # jg 0x1e32
    0xBA, 0x01, 0x00,             # mov dx, 1
    0xC6, 0x44, 0x24, 0x01        # mov byte ptr [si+0x24], 1
])

GODMODE_PATCH_BYTES = bytes([
    0x8B, 0x76, 0x06,             # mov si, [bp+6]
    0x8B, 0x56, 0x04,             # mov dx, [bp+4]
    0x8A, 0x5C, 0x07,             # mov bl, [si+7]
    0x30, 0xFF,                   # xor bh, bh
    0xD1, 0xE3,                   # shl bx, 1
    0x8B, 0xBF, 0x96, 0x22,       # mov di, [bx+0x2296]
    0xF7, 0x04, 0x00, 0xE0,       # test word ptr [si], 0xe000
    0x75, 0x7D,                   # jne 0x1e9e
    0x80, 0x7C, 0x07, 0x06,       # cmp byte ptr [si+7], 6 (membre de l'équipe ?)
    0x73, 0x77,                   # jae 0x1e9e (si joueur : IMMUNITÉ TOTALE AUX DÉGÂTS !)
    0xC6, 0x44, 0x24, 0x01,       # mov byte ptr [si+0x24], 1
    0x0B, 0xD2,                   # or dx, dx
    0x7F, 0x03,                   # jg 0x1e32
    0xBA, 0x01, 0x00              # mov dx, 1
])


def check_exe_status():
    if not os.path.exists(EXE_FILE):
        print(f"Fichier {EXE_FILE} introuvable.")
        return

    with open(EXE_FILE, "rb") as f:
        exe = f.read()

    current_bytes = exe[PATCH_OFFSET : PATCH_OFFSET + len(ORIGINAL_BYTES)]
    if current_bytes == GODMODE_PATCH_BYTES:
        print(f"Statut {EXE_FILE} : GOD MODE ACTIF (Vie infinie activée pour l'équipe en combat)")
    elif current_bytes == ORIGINAL_BYTES:
        print(f"Statut {EXE_FILE} : Normal (Original)")
    else:
        print(f"Statut {EXE_FILE} : Inconnu ou personnalisé")


def patch_exe(enable_god_mode=True):
    if not os.path.exists(EXE_FILE):
        print(f"Erreur : {EXE_FILE} introuvable.")
        return

    if not os.path.exists(EXE_BACKUP):
        shutil.copy(EXE_FILE, EXE_BACKUP)
        print(f"Exécutable original copié vers {EXE_BACKUP}")

    with open(EXE_FILE, "rb") as f:
        exe = bytearray(f.read())

    current_bytes = bytes(exe[PATCH_OFFSET : PATCH_OFFSET + len(ORIGINAL_BYTES)])

    if enable_god_mode:
        if current_bytes == GODMODE_PATCH_BYTES:
            print("Le God Mode est déjà activé dans KX.EXE.")
            return
        exe[PATCH_OFFSET : PATCH_OFFSET + len(GODMODE_PATCH_BYTES)] = GODMODE_PATCH_BYTES
        with open(EXE_FILE, "wb") as f:
            f.write(exe)
        print("God Mode (Vie Infinie) ACTIVÉ avec succès dans KX.EXE !")
    else:
        if current_bytes == ORIGINAL_BYTES:
            print("KX.EXE est déjà en version originale.")
            return
        exe[PATCH_OFFSET : PATCH_OFFSET + len(ORIGINAL_BYTES)] = ORIGINAL_BYTES
        with open(EXE_FILE, "wb") as f:
            f.write(exe)
        print("KX.EXE restauré en version originale (God Mode désactivé) !")


def restore_all():
    restored = []
    if os.path.exists(SAVE_BACKUP):
        shutil.copy(SAVE_BACKUP, SAVE_FILE)
        restored.append(SAVE_FILE)
    if os.path.exists(EXE_BACKUP):
        shutil.copy(EXE_BACKUP, EXE_FILE)
        restored.append(EXE_FILE)

    if restored:
        print(f"Fichiers restaurés depuis leurs sauvegardes originales : {', '.join(restored)}")
    else:
        print("Aucun fichier de sauvegarde originale (.ORIG) trouvé.")


def main():
    if len(sys.argv) < 2:
        print("=== Knights of Xentar Tool ===")
        print("Commandes disponibles :")
        print("  python3 xentar_tool.py status                    -> Afficher les stats actuelles")
        print("  python3 xentar_tool.py level [val] [perso]       -> Changer le niveau (1 à 99, ex: level 50 ou level 99 desmond)")
        print("  python3 xentar_tool.py hp [val] [perso]          -> Changer les PV (ex: hp 9999 ou hp 30000)")
        print("  python3 xentar_tool.py mp [val] [perso]          -> Changer la magie (ex: mp 999)")
        print("  python3 xentar_tool.py exp [val] [perso]         -> Changer les points d'expérience")
        print("  python3 xentar_tool.py gold [val]                -> Définir l'or (ex: gold 999999)")
        print("  python3 xentar_tool.py godmode on                -> Activer vie infinie dans KX.EXE")
        print("  python3 xentar_tool.py godmode off               -> Désactiver vie infinie (KX.EXE original)")
        print("  python3 xentar_tool.py restore                   -> Restaurer sauvegarde et exe originaux")
        show_save_status()
        check_exe_status()
        return

    cmd = sys.argv[1].lower()
    target = sys.argv[3] if len(sys.argv) > 3 else "all"

    if cmd == "status":
        show_save_status()
        check_exe_status()
    elif cmd in ["level", "lvl", "niveau"]:
        val = int(sys.argv[2]) if len(sys.argv) > 2 else 99
        modify_level(val, target)
        show_save_status()
    elif cmd == "hp":
        val = int(sys.argv[2]) if len(sys.argv) > 2 else 30000
        modify_hp(val, target)
        show_save_status()
    elif cmd == "mp":
        val = int(sys.argv[2]) if len(sys.argv) > 2 else 999
        modify_mp(val, target)
        show_save_status()
    elif cmd == "exp":
        val = int(sys.argv[2]) if len(sys.argv) > 2 else 50000
        modify_exp(val, target)
        show_save_status()
    elif cmd == "gold":
        val = int(sys.argv[2]) if len(sys.argv) > 2 else 999999
        modify_gold(val)
        show_save_status()
    elif cmd == "godmode":
        sub = sys.argv[2].lower() if len(sys.argv) > 2 else "on"
        if sub in ["on", "1", "enable", "true"]:
            patch_exe(True)
        elif sub in ["off", "0", "disable", "false"]:
            patch_exe(False)
        else:
            print("Argument invalide pour godmode (choisir 'on' ou 'off')")
        check_exe_status()
    elif cmd == "restore":
        restore_all()
        show_save_status()
        check_exe_status()
    else:
        print(f"Commande inconnue: {cmd}")


if __name__ == "__main__":
    main()
